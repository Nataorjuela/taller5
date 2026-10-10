# Taller 5: análisis de la tasa de transferencia con iperf3

**Autores:** Natalia Orjuela, Jimmy Millán y Santiago León.

## Descripción de la práctica

En esta práctica se estudió cómo cambia la tasa de transferencia al configurar distintos niveles de tráfico en iperf3. Se siguió la alternativa propuesta por el docente, de acuerdo con los datos disponibles para desarrollar el ejercicio.

Se utilizó una conexión de red compartida desde un celular para conectar dos máquinas: una actuó como servidor y la otra como cliente. Se realizaron tres pruebas TCP con tasas configuradas de **5M, 10M y 15M**, equivalentes a **5, 10 y 15 Mbps**. Estos valores indican la tasa objetivo de cada prueba; no representan la capacidad total de la red.

El informe analiza el caudal obtenido, sus variaciones, las retransmisiones TCP y los cambios en la ventana de congestión (Cwnd). También presenta una regresión lineal para estimar la tasa medida a partir de la tasa configurada.

## Contenido de la entrega

| Archivo o carpeta | Contenido |
|---|---|
| `informe.pdf` | Informe de cinco páginas con el método, las figuras, los resultados y las conclusiones. |
| `analisis.py` | Programa que procesa las trazas, construye las tablas, ajusta el modelo y genera las figuras. |
| `datos/` | Registros originales de las pruebas: `traza5.txt`, `traza10.txt` y `traza15.txt`. |
| `intervalos.csv` | Datos extraídos de los 900 intervalos registrados. |
| `ventanas.csv` | Datos agrupados en 15 ventanas de aproximadamente 60 segundos. |
| `resumen_escenarios.csv` | Resumen de las mediciones para cada tasa configurada. |
| `predicciones.csv` | Predicciones y errores de las cinco ventanas de la prueba de 15 Mbps. |
| `resultados.json` | Coeficientes, métricas, versiones de las bibliotecas y códigos SHA-256 para comprobar la integridad de las trazas. |
| `figuras/` | Las tres figuras utilizadas en el informe. |
| `main.tex` | Fuente principal del informe en LaTeX. |
| `resultados.tex`, `tabla_resumen.tex`, `tabla_predicciones.tex` | Resultados y tablas que el programa genera para incorporarlos al informe. |
| `requirements.txt` | Bibliotecas de Python y versiones utilizadas. |
| `DICCIONARIO_DATOS.md` | Descripción de las columnas, sus unidades y los campos vacíos. |

## Cómo se realizó el análisis

Los registros se agruparon en ventanas de 60 intervalos consecutivos. Cada ventana dura aproximadamente un minuto. Para calcular su tasa de transferencia se sumaron los bytes reportados y se dividieron por la duración efectiva:

```text
tasa_medida_mbps = 8 * bytes_iperf_tx_aprox / (duracion_s * 1e6)
```

Los bytes son aproximados porque las salidas de texto de iperf3 contienen valores redondeados. Para convertir las unidades se usaron 1024 bytes por KByte y 1048576 bytes por MByte. Las tasas se expresan en Mbps y la Cwnd en KiB.

La regresión se entrenó con las pruebas completas de **5 y 10 Mbps**, que reúnen diez ventanas. La prueba completa de **15 Mbps**, con cinco ventanas, se dejó para evaluar el modelo. Así, ninguna prueba aporta ventanas a ambos conjuntos. Las ventanas de una misma prueba son segmentos de esa medición, no repeticiones independientes.

La evaluación se hizo con registros que ya estaban disponibles. Además, el nivel de 15 Mbps está fuera del rango de entrenamiento de 5 a 10 Mbps. Por ello, se presenta como una **evaluación retrospectiva por extrapolación**, no como una predicción registrada antes de realizar la prueba.

## Principales resultados

El modelo obtenido en el informe es:

```text
tasa_predicha_mbps = 0.0188 + 0.9966 * tasa_configurada_mbps
```

Para 15 Mbps predice aproximadamente **14,9675 Mbps**. Su error absoluto medio (MAE) es de **0,0456 Mbps** y su RMSE es de **0,0464 Mbps**. Los coeficientes de la ecuación están redondeados; el programa calcula las predicciones con los valores completos.

El modelo se comparó con dos alternativas: usar siempre la mediana de las tasas de entrenamiento o asumir que la tasa medida será igual a la configurada (`y = x`). Esta última obtuvo un MAE menor, de **0,0132 Mbps**. En estas pruebas, la regresión no ofrece una mejora frente a usar directamente la tasa objetivo.

El R² de la regresión es negativo (**−29,0830**). Esto puede ocurrir aunque el error absoluto sea pequeño, porque las tasas de las cinco ventanas evaluadas son muy similares entre sí. El informe explica esta diferencia y limita sus conclusiones a las pruebas disponibles.

También se identificaron caídas puntuales del caudal y cambios en Cwnd. Se contaron los intervalos cuya tasa fue inferior al 70 % del objetivo para describir esas caídas. Ese criterio, junto con las retransmisiones, no basta para confirmar congestión ni determinar su causa.

## Cómo ejecutar el programa

El análisis se realizó con **Python 3.12.14**. Las versiones de las bibliotecas están en `requirements.txt` y `resultados.json`.

Abre una terminal en la carpeta de la entrega y crea un entorno virtual:

```text
python -m venv .venv
```

En Windows PowerShell:

```text
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe analisis.py
```

En Linux o macOS:

```text
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python analisis.py
```

El programa vuelve a generar los CSV, los resultados JSON, las tablas LaTeX y las figuras. Comprueba la continuidad de los intervalos, las duraciones y los totales de retransmisiones; si encuentra una inconsistencia, muestra un error. Para analizar los archivos existentes no es necesario instalar iperf3 ni repetir las mediciones de red.

## Cómo generar el PDF

El PDF ya está incluido. Para volver a generarlo, instala una distribución LaTeX, ejecuta primero el análisis y luego utiliza estos comandos desde la carpeta de la entrega:

```text
pdflatex -interaction=nonstopmode -halt-on-error -jobname=informe main.tex
pdflatex -interaction=nonstopmode -halt-on-error -jobname=informe main.tex
```

La segunda compilación actualiza los marcadores del documento. El informe se compiló con **MiKTeX 25.12 y pdfTeX 1.40.28**.

## Alcance de los datos

Se trabajó únicamente con los registros obtenidos en la práctica. No se midieron RTT, pérdida ICMP, capacidad del enlace, carga total de la red, contadores RX/TX de interfaz, descartes ni errores. Tampoco se registraron marcas de tiempo absolutas. Los campos correspondientes permanecen vacíos; no se reemplazaron por ceros.

La conexión mediante el celular describe el montaje de la práctica, pero las trazas no incluyen los detalles técnicos del medio, la interfaz o la topología. Tampoco contienen las versiones de iperf3 y del sistema operativo de las máquinas utilizadas. Las versiones documentadas en esta entrega corresponden al procesamiento posterior de los datos.

Los resultados describen las tres pruebas disponibles. Para comprobar si se mantienen en otras condiciones o estudiar una posible saturación, sería necesario realizar nuevas pruebas con repeticiones independientes y mediciones adicionales.
