# Historia explicada: qué hicimos, por qué y qué pasó

[**Informe HTML**](index.html). Descargar y abrir en un navegador; funciona sin conexión y permite imprimir/guardar como PDF.

Versión más directa que la auditoría integral: seis pasos del cierre v8, significado de las cuatro alternativas, resultados económicos, tiempos registrados y recorrido v1–v8. No reemplaza la documentación técnica ni sus reglas.

## Qué se verificó

Los tiempos se obtuvieron de los JSON originales y se contrastaron con el cronómetro del código:

- V7: `seconds` por semilla incluye entrenamiento y predicción de agosto. B0 34,3 s; R3 68,6 s; T4 59,3 s (medias de cinco semillas finales).
- V8: `seconds` por trial incluye entrenamiento, predicción, guardado y AUC. La tabla suma sólo los 20 trials de búsqueda por brazo; no representa toda la corrida ni su facturación.
- No se atribuyen tiempos separados a features o inferencia cuando no están publicados ni se certifica el límite mensual de 15 minutos.

`datos.json` conserva métricas; `fuentes_sha256.json` identifica las fuentes. `construir.py` reconstruye el HTML con Python estándar desde la raíz del repositorio. `QA_HTML.json` registra la prueba de presentación y enlaces internos en escritorio y móvil.

No se entrenó ni encendió la VM. T4 permanece prometedor, inconcluso; septiembre y octubre no se presentan como meses nuevos independientes.
