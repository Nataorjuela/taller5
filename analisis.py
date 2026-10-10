"""Reconstruye el análisis del Taller 5 a partir de tres salidas de iperf3.

Ejecutar: python analisis.py
No obtiene datos de la red ni instala paquetes. Los bytes reconstruidos son
aproximados porque las salidas de texto de iperf3 contienen valores redondeados.
"""
from pathlib import Path
import hashlib
import json
import platform
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent
PATTERN = re.compile(
    r"\[\s*5\]\s+([\d.]+)-([\d.]+)\s+sec\s+([\d.]+)\s+"
    r"(Bytes|KBytes|MBytes)\s+([\d.]+)\s+(bits|Kbits|Mbits)/sec\s+"
    r"(\d+)\s+([\d.]+)\s+(Bytes|KBytes|MBytes)"
)
BYTE_FACTORS = {"Bytes": 1, "KBytes": 1024, "MBytes": 1024**2}
RATE_FACTORS = {"bits": 1e-6, "Kbits": 1e-3, "Mbits": 1}


def parse_trace(path, target):
    text = path.read_text(encoding="utf-8", errors="strict")
    records = []
    for match in PATTERN.finditer(text):
        start, end, amount, unit, rate, rate_unit, retr, cwnd, cwnd_unit = match.groups()
        start, end = float(start), float(end)
        if end <= start:
            raise ValueError(f"Intervalo inválido en {path.name}")
        records.append({
            "archivo": path.name, "sesion": f"sesion_{target}",
            "escenario_mbps": target, "inicio_rel_s": start,
            "fin_rel_s": end, "duracion_s": end-start,
            "bytes_iperf_tx_aprox": float(amount)*BYTE_FACTORS[unit],
            "tasa_reportada_mbps": float(rate)*RATE_FACTORS[rate_unit],
            "retransmisiones": int(retr),
            "cwnd_kib": float(cwnd)*BYTE_FACTORS[cwnd_unit]/1024,
        })
    if len(records) != 300:
        raise ValueError(f"Se esperaban 300 intervalos en {path.name}; hay {len(records)}")
    df = pd.DataFrame(records)
    if not np.allclose(df.inicio_rel_s.iloc[1:].to_numpy(),
                       df.fin_rel_s.iloc[:-1].to_numpy(), atol=0.011):
        raise ValueError(f"Intervalos discontinuos en {path.name}")
    summary = re.search(
        r"\[\s*5\]\s+0\.00-[\d.]+\s+sec\s+[\d.]+\s+MBytes\s+"
        r"[\d.]+\s+Mbits/sec\s+(\d+)\s+sender", text)
    if not summary or int(summary.group(1)) != int(df.retransmisiones.sum()):
        raise ValueError(f"Retransmisiones incompatibles con resumen en {path.name}")
    df["ventana"] = np.arange(len(df))//60+1
    return df


def metrics(real, predicted):
    return {"mae_mbps": float(mean_absolute_error(real, predicted)),
            "rmse_mbps": float(np.sqrt(mean_squared_error(real, predicted))),
            "r2": float(r2_score(real, predicted))}


def main():
    (ROOT/"figuras").mkdir(exist_ok=True)
    frames = [parse_trace(ROOT/"datos"/f"traza{n}.txt", n) for n in (5, 10, 15)]
    intervals = pd.concat(frames, ignore_index=True)
    windows = []
    for (session, window), group in intervals.groupby(["sesion", "ventana"], sort=False):
        duration = float(group.fin_rel_s.iloc[-1]-group.inicio_rel_s.iloc[0])
        total = float(group.bytes_iperf_tx_aprox.sum())
        target = int(group.escenario_mbps.iloc[0])
        rate = 8*total/(duration*1e6)
        windows.append({
            "archivo": group.archivo.iloc[0], "sesion": session,
            "escenario_mbps": target, "replica": 1, "ventana": int(window),
            "inicio": None, "inicio_rel_s": float(group.inicio_rel_s.iloc[0]),
            "fin_rel_s": float(group.fin_rel_s.iloc[-1]), "duracion_s": duration,
            "bytes_iperf_tx_aprox": total, "tasa_medida_mbps": rate,
            "cumplimiento_objetivo_pct": 100*rate/target,
            "retransmisiones": int(group.retransmisiones.sum()),
            "cwnd_min_kib": float(group.cwnd_kib.min()),
            "cwnd_media_kib": float(np.average(group.cwnd_kib, weights=group.duracion_s)),
            "intervalos_bajo_70pct": int((group.tasa_reportada_mbps < .7*target).sum()),
            "cv_tasa_intervalos": float(group.tasa_reportada_mbps.std(ddof=1)/group.tasa_reportada_mbps.mean()),
            "rtt_medio_ms": None, "perdida_pct": None, "bytes_rx": None,
            "bytes_tx_interfaz": None, "descartes": None, "errores": None,
        })
    df = pd.DataFrame(windows)
    if len(df) != 15 or not df.duracion_s.between(59, 61).all():
        raise ValueError("Número o duración de ventanas incorrectos")
    intervals.to_csv(ROOT/"intervalos.csv", index=False, float_format="%.8f")
    df.to_csv(ROOT/"ventanas.csv", index=False, float_format="%.8f", na_rep="")

    # La reserva por escenario se fija explícitamente; no se ajusta el modelo
    # ni se eligen características usando resultados de la sesión de 15 Mbps.
    train = df[df.escenario_mbps.isin([5, 10])].copy()
    test = df[df.escenario_mbps.eq(15)].copy()
    assert set(train.sesion).isdisjoint(test.sesion)
    predictor = ["escenario_mbps"]
    model = LinearRegression().fit(train[predictor], train.tasa_medida_mbps)
    pred = model.predict(test[predictor])
    baseline = np.repeat(train.tasa_medida_mbps.median(), len(test))
    identity = test.escenario_mbps.to_numpy(dtype=float)
    test["prediccion_mbps"] = pred
    test["residuo_mbps"] = test.tasa_medida_mbps-pred
    test["error_absoluto_mbps"] = abs(test.residuo_mbps)
    test["referencia_mediana_mbps"] = baseline
    test["referencia_objetivo_mbps"] = identity
    test.to_csv(ROOT/"predicciones.csv", index=False, float_format="%.8f", na_rep="")
    summaries = []
    for target, group in df.groupby("escenario_mbps"):
        original = intervals[intervals.escenario_mbps.eq(target)]
        summaries.append({"escenario_mbps": int(target), "n_ventanas": len(group),
            "tasa_mediana_mbps": float(group.tasa_medida_mbps.median()),
            "tasa_min_mbps": float(group.tasa_medida_mbps.min()),
            "tasa_max_mbps": float(group.tasa_medida_mbps.max()),
            "tasa_total_mbps": float(8*group.bytes_iperf_tx_aprox.sum()/group.duracion_s.sum()/1e6),
            "retransmisiones": int(group.retransmisiones.sum()),
            "cwnd_min_kib": float(group.cwnd_min_kib.min()),
            "intervalos_bajo_70pct": int(group.intervalos_bajo_70pct.sum()),
            "transferencia_aprox_mib": float(original.bytes_iperf_tx_aprox.sum()/1024**2)})
    pd.DataFrame(summaries).to_csv(ROOT/"resumen_escenarios.csv", index=False, float_format="%.8f")
    result = {
        "modelo": "tasa_medida_mbps = intercepto + pendiente * escenario_mbps",
        "intercepto_mbps": float(model.intercept_), "pendiente": float(model.coef_[0]),
        "entrenamiento": {"sesiones": train.sesion.unique().tolist(), "ventanas": len(train), "rango_x_mbps": [5, 10]},
        "evaluacion": {"sesiones": test.sesion.unique().tolist(), "ventanas": len(test), "x_mbps": 15, "tipo": "retrospectiva por extrapolación"},
        "metricas_modelo": metrics(test.tasa_medida_mbps, pred),
        "metricas_mediana": metrics(test.tasa_medida_mbps, baseline),
        "metricas_identidad": metrics(test.tasa_medida_mbps, identity),
        "mediana_entrenamiento_mbps": float(train.tasa_medida_mbps.median()),
        "prediccion_15_mbps": float(pred[0]), "resumen": summaries,
        "versiones": {"python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "matplotlib": matplotlib.__version__, "scikit_learn": sklearn.__version__},
        "sha256_trazas": {f"traza{n}.txt": hashlib.sha256((ROOT/"datos"/f"traza{n}.txt").read_bytes()).hexdigest() for n in (5,10,15)},
    }
    (ROOT/"resultados.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    def tex_number(value, decimals=4):
        return f"{value:.{decimals}f}".replace(".", "{,}")
    macros = {"Intercepto": result["intercepto_mbps"], "Pendiente": result["pendiente"],
              "PredAlta": result["prediccion_15_mbps"],
              "MedianaTrain": result["mediana_entrenamiento_mbps"]}
    latex = [f"\\newcommand{{\\{key}}}{{{tex_number(value)}}}" for key, value in macros.items()]
    for label, key in [("Modelo","metricas_modelo"),("Mediana","metricas_mediana"),("Objetivo","metricas_identidad")]:
        for symbol, metric in [("MAE","mae_mbps"),("RMSE","rmse_mbps"),("Rdos","r2")]:
            latex.append(f"\\newcommand{{\\{symbol}{label}}}{{{tex_number(result[key][metric])}}}")
    (ROOT/"resultados.tex").write_text("\n".join(latex)+"\n", encoding="utf-8")
    summary_rows = [f"{s['escenario_mbps']} & {tex_number(s['tasa_mediana_mbps'])} & "
                    f"{tex_number(s['tasa_min_mbps'])}--{tex_number(s['tasa_max_mbps'])} & "
                    f"{s['retransmisiones']} & {tex_number(s['cwnd_min_kib'],1)} & "
                    f"{s['intervalos_bajo_70pct']} \\\\" for s in summaries]
    (ROOT/"tabla_resumen.tex").write_text("\n".join(summary_rows)+"\n",encoding="utf-8")
    prediction_rows = [f"{int(row.ventana)} & {tex_number(row.tasa_medida_mbps)} & "
                       f"{tex_number(row.prediccion_mbps)} & {tex_number(row.residuo_mbps)} & "
                       f"{tex_number(row.error_absoluto_mbps)} \\\\" for _,row in test.iterrows()]
    (ROOT/"tabla_predicciones.tex").write_text("\n".join(prediction_rows)+"\n",encoding="utf-8")
    plot_figures(intervals, df, train, test, model)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def plot_figures(intervals, df, train, test, model):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    colors = {5: "#176b9b", 10: "#c77812", 15: "#268366"}
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 4.7), sharex=True)
    for n, g in intervals.groupby("escenario_mbps"):
        axes[0].plot(g.fin_rel_s, g.tasa_reportada_mbps, color=colors[n], lw=.8, label=f"Objetivo {n} Mbps")
        axes[1].plot(g.fin_rel_s, g.cwnd_kib, color=colors[n], lw=.9)
    for ax in axes:
        for t in (60,120,180,240): ax.axvline(t, color="gray", ls=":", lw=.6)
        ax.grid(alpha=.15)
    axes[0].set_ylabel("Tasa medida (Mbps)"); axes[0].legend(ncol=3, fontsize=8)
    axes[1].set(ylabel="Cwnd (KiB)", xlabel="Tiempo relativo al inicio de cada sesión (s)")
    fig.tight_layout(); fig.savefig(ROOT/"figuras"/"fig1_series.png", dpi=220); plt.close(fig)

    fig, axes = plt.subplots(1,2,figsize=(8.4,3.2))
    for n, g in df.groupby("escenario_mbps"):
        axes[0].scatter(g.escenario_mbps, g.tasa_medida_mbps, color=colors[n], label=f"{n} Mbps", s=26)
    axes[0].plot([4,16],[4,16], color="gray", ls="--", label="y = x")
    axes[0].set(xlabel="Tasa configurada (Mbps)", ylabel="Tasa por ventana (Mbps)")
    axes[0].legend(fontsize=8)
    axes[1].boxplot([df.loc[df.escenario_mbps.eq(n),"retransmisiones"] for n in (5,10,15)], tick_labels=["5","10","15"])
    axes[1].set(xlabel="Tasa configurada (Mbps)", ylabel="Retransmisiones por ventana")
    fig.tight_layout(); fig.savefig(ROOT/"figuras"/"fig2_exploracion.png", dpi=220); plt.close(fig)

    fig, axes = plt.subplots(1,2,figsize=(8.4,3.2))
    axes[0].scatter(train.escenario_mbps,train.tasa_medida_mbps,s=28,label="Entrenamiento (2 sesiones)")
    axes[0].scatter(test.escenario_mbps,test.tasa_medida_mbps,s=28,color=colors[15],label="Evaluación (1 sesión)")
    x=np.linspace(4.5,15.5,100)
    axes[0].plot(x,model.intercept_+model.coef_[0]*x,color="#c77812",label="Regresión")
    axes[0].axvspan(5,10,color="gray",alpha=.12)
    axes[0].set(xlabel="Tasa configurada (Mbps)",ylabel="Tasa por ventana (Mbps)")
    axes[0].legend(fontsize=7)
    axes[1].scatter(test.ventana,test.residuo_mbps,color=colors[15])
    axes[1].axhline(0,color="gray",ls="--")
    axes[1].set(xlabel="Ventana de evaluación (sesión de 15 Mbps)",ylabel="Residuo: medido - predicho (Mbps)",xticks=[1,2,3,4,5])
    fig.tight_layout(); fig.savefig(ROOT/"figuras"/"fig3_modelo.png", dpi=220); plt.close(fig)


if __name__ == "__main__":
    main()
