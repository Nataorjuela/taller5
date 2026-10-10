# Diccionario de datos

Los CSV usan UTF-8, coma como separador y punto decimal. Una celda vacía representa un dato no medido o no disponible; no representa cero.

## ventanas.csv

| Campo | Unidad / significado | Fuente o cálculo |
|---|---|---|
| archivo | Nombre del registro de origen | Traza |
| sesion | Identificador único por prueba | Archivo de origen |
| escenario_mbps | Mbps; tasa configurada declarada: 5, 10 o 15 | Asociación del informe original con cada archivo |
| replica | 1; una sola sesión por nivel | Inventario de trazas |
| ventana | 1 a 5; bloque de 60 intervalos | Orden dentro del archivo |
| inicio | Hora ISO 8601; vacía | No disponible |
| inicio_rel_s | s desde inicio de la sesión | Primera marca de la ventana |
| fin_rel_s | s desde inicio de la sesión | Última marca de la ventana |
| duracion_s | s efectivos | fin_rel_s - inicio_rel_s |
| bytes_iperf_tx_aprox | bytes estimados de transferencia reportada; no son bytes TX de interfaz | Suma de valores impresos convertidos con unidades binarias |
| tasa_medida_mbps | Mbps | 8 * bytes_iperf_tx_aprox / (duracion_s * 1e6) |
| cumplimiento_objetivo_pct | % del objetivo; no utilización del enlace | 100 * tasa_medida_mbps / escenario_mbps |
| retransmisiones | Conteo TCP acumulado en la ventana; no porcentaje de pérdida | Suma de Retr |
| cwnd_min_kib | KiB | Mínimo de Cwnd |
| cwnd_media_kib | KiB | Media ponderada por duración de intervalos |
| intervalos_bajo_70pct | Conteo de intervalos con tasa reportada < 0.7 * objetivo | Umbral exploratorio |
| cv_tasa_intervalos | Adimensional | Desviación estándar muestral de tasas reportadas / media |
| rtt_medio_ms | ms; vacío | No medido |
| perdida_pct | %; vacío | No medido |
| bytes_rx | bytes RX de interfaz; vacío | No medido |
| bytes_tx_interfaz | bytes TX de interfaz; vacío | No medido |
| descartes | Conteo de interfaz; vacío | No medido |
| errores | Conteo de interfaz; vacío | No medido |

## intervalos.csv

Una fila representa un intervalo de aproximadamente un segundo; no un paquete. Conserva archivo, sesión, escenario, ventana, marcas relativas, duración, transferencia aproximada, tasa reportada en Mbps, retransmisiones y Cwnd en KiB. La tasa reportada ya está redondeada en la salida original.

## predicciones.csv

Contiene las columnas de las cinco ventanas reservadas y:

- `prediccion_mbps`: salida de la regresión entrenada con las sesiones de 5 y 10 Mbps.
- `residuo_mbps`: tasa medida menos predicción, en Mbps.
- `error_absoluto_mbps`: valor absoluto del residuo.
- `referencia_mediana_mbps`: mediana de las diez ventanas de entrenamiento.
- `referencia_objetivo_mbps`: tasa configurada de la ventana; referencia y = x.

## resumen_escenarios.csv y resultados.json

El resumen informa número de ventanas, mediana, mínimo, máximo y tasa agregada, total de retransmisiones, Cwnd mínima, caídas y transferencia aproximada por sesión. JSON conserva las métricas sin redondeo de presentación, el diseño de partición, las versiones del entorno de análisis y hashes SHA-256 para comprobar que las trazas originales no cambiaron.

## Precisión

Los CSV se exportan con ocho decimales para facilitar cálculos reproducibles. Esa cantidad de dígitos no significa que la medición tenga esa precisión: las transferencias y tasas de origen están redondeadas. Las tablas del informe se presentan con cuatro decimales para mostrar diferencias pequeñas sin tratarlas como evidencia de precisión instrumental.
