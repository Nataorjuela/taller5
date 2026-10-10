# Taller 5

## Alcance

Esta entrega estudia la **tasa de transferencia medida en función de la tasa configurada** en iperf3, conforme a la alternativa docente comunicada por la estudiante. No estima latencia ni presenta 5, 10 y 15 Mbps como capacidad del enlace. Sus autores son Natalia Orjuela, Jimmy Millán y Santiago León.

Las tres salidas de texto aportan 300 intervalos por sesión: 900 intervalos y 15 ventanas de aproximadamente 60 segundos. Hay una sesión por nivel; cinco ventanas consecutivas no son cinco réplicas independientes. La asignación de cada archivo a su nivel se toma del informe original: el comando y la tasa objetivo no están registrados explícitamente en las trazas.

## Archivos

- `informe.pdf`: informe final de hasta cinco páginas.
- `main.tex`, `resultados.tex`, `tabla_resumen.tex`, `tabla_predicciones.tex`: fuentes LaTeX. Los tres últimos se regeneran mediante el programa.
- `analisis.py`: extracción, controles, agregación, ajuste, evaluación y figuras. No genera tráfico de red.
- `requirements.txt`: versiones principales utilizadas para el análisis.
- `datos/traza5.txt`, `datos/traza10.txt`, `datos/traza15.txt`: copias sin cambios de las trazas proporcionadas.
- `intervalos.csv`: los 900 intervalos extraídos.
- `ventanas.csv`: las 15 ventanas agregadas.
- `resumen_escenarios.csv`: resumen por nivel.
- `predicciones.csv`: resultados de las cinco ventanas reservadas de 15 Mbps.
- `resultados.json`: coeficientes, métricas, versiones y hashes SHA-256 de las trazas.
- `figuras/`: las tres figuras usadas en el informe.
- `DICCIONARIO_DATOS.md`: campos, unidades, fórmulas y significado de vacíos.

## Reproducir el análisis

Se probó con Python 3.12; las versiones exactas del análisis se conservan en `resultados.json` y `requirements.txt`. Desde esta carpeta:

```text
python -m venv .venv
```

En Windows PowerShell, sin necesidad de activar el entorno:

```text
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe analisis.py
```

En Linux/macOS:

```text
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python analisis.py
```

El programa regenera CSV, JSON, tablas y figuras junto a `analisis.py`, independientemente del directorio desde el que se invoque. Falla si encuentra un número inesperado de intervalos, discontinuidades, duraciones inválidas o discrepancias en el total de retransmisiones. No necesita tener instalado iperf3 para analizar estas trazas existentes.

## Compilar el informe

Se verificó con pdfLaTeX de MiKTeX 25.12 (pdfTeX 1.40.28). En esta carpeta, después de ejecutar el análisis:

```text
pdflatex -interaction=nonstopmode -halt-on-error -jobname=informe main.tex
pdflatex -interaction=nonstopmode -halt-on-error -jobname=informe main.tex
```

Requiere una distribución LaTeX con los paquetes indicados en `main.tex`. La instrucción `\spanishplainpercent` evita la incompatibilidad local de porcentajes de babel encontrada al revisar el original. La segunda compilación resuelve referencias y marcadores. Los archivos auxiliares no forman parte de la entrega.

## Decisiones metodológicas

1. Cada ventana contiene 60 intervalos consecutivos, no exactamente 60 segundos de reloj. Su duración es la diferencia entre la última marca final y la primera inicial.
2. Las transferencias de texto se convierten con KBytes = 1024 bytes y MBytes = 1048576 bytes. Como los números impresos están redondeados, los bytes reconstruidos son aproximados.
3. La tasa agregada es `8 * bytes_iperf_tx_aprox / (duracion_s * 1e6)`. No se obtiene como promedio simple de tasas impresas. Estas últimas se conservan para gráficas temporales y variabilidad.
4. El entrenamiento usa completas las sesiones de 5 y 10 Mbps (10 ventanas). La evaluación usa completa la sesión de 15 Mbps (5 ventanas). No se mezclan ventanas de una sesión entre ambos conjuntos.
5. La evaluación es retrospectiva y por extrapolación. Las trazas existían antes de preparar el análisis. El nivel configurado, no el caudal futuro medido, es la entrada del modelo. No hubo pronóstico prospectivo ni registro previo a una nueva medición.
6. Se comparan la regresión, la mediana del caudal de entrenamiento y la referencia `y = x` (seguir el objetivo configurado). Todos los errores se calculan sobre la misma sesión reservada.
7. El R² usa la media del conjunto de evaluación como referencia matemática. La muy pequeña variación de caudal dentro de ese conjunto hace que el R² sea sensible a sesgos pequeños. Se reporta aun cuando resulte negativo.
8. El 70 % de la tasa objetivo es un umbral exploratorio para contar intervalos de caída, no una prueba de congestión. Cwnd y retransmisiones no determinan por sí solos la causa de una perturbación.

## Qué no puede recuperarse

No se inventan RTT, pérdida ICMP, capacidad nominal, carga total del enlace, RX/TX de interfaz, descartes, errores, marcas de reloj, medio o topología. Los campos correspondientes están vacíos. Los resúmenes del receptor no permiten reconstruir bytes RX por ventana. Las versiones del iperf3 y del sistema operativo de medición son desconocidas; las versiones de Python y bibliotecas corresponden al análisis posterior.

Esta entrega documenta el análisis completo que permiten las trazas disponibles. No contiene sesiones nuevas ni acredita un escenario de saturación. Para una validación prospectiva se requieren nuevas mediciones, réplicas y registro previo de predicciones.
