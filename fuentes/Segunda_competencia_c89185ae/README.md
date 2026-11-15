# Segunda Competencia — Registro de experimentos

Este repositorio centraliza la documentación de experimentos de Data Mining en Economía y Finanzas. No contiene datos bancarios, identificadores de clientes ni predicciones individuales.

## Experimento 13/11/2026 — Historia 2019 v4

- [Diseño, resultados y reproducción paso a paso](experimento_2026-11-13/README.md).
- Cinco alternativas con optimización independiente y cinco semillas; evaluación de octubre sin reentrenar.
- Incluye reconstrucción desde el dataset, resultados esperados y controles de reproducción.

## Experimentos derivados de C3

- [Auditoría, hiperparámetros y diseños](experimentos_c3/README.md).
- Veinte modelos originales auditados; ensayo C3/B6 intrames completado y verificado.

## Experimento ejecutado: históricas B0–B5

- [Abrir carpeta, resultados y guía de reproducción](experimento_historicas_B0_B5/README.md).
- Corrida del 7 de noviembre de 2026: 120 evaluaciones y comparación final de octubre completadas.
- B0 usa originales; B2 es la referencia de Ale; B3 obtuvo la mayor ganancia observada con políticas individuales.
- Código, modelos y resultados agregados incluidos; datos y predicciones individuales permanecen fuera de GitHub.
- Es un experimento distinto de `HISTORIA_2019_01`; sus baselines y targets de validación no son intercambiables.

## Experimento recuperado: HISTORIA_2019_01

- [Informe metodológico, bitácora y resultados](HISTORIA_2019_01/README.md)
- Fuente de verdad: artefactos locales de la VM `clari-c1-fundados`, en `/home/clarirz/HISTORIA_2019_01/`.
- Corrida finalizada: 2026-11-05 05:52:52 (Argentina).
- **Modelo seleccionado en validación:** iteración 003, `ratios_personales`.
- **Estado:** modelos congelados; evaluación externa de ganancia en octubre de 2019 pendiente.

### Alcance de esta documentación

Se reconstruye a partir de `LEEME.txt`, `CAMBIOS.txt`, `VALIDACION.txt`, resultados individuales y `FINAL.json`, contenidos en el resumen exportado de la VM. Los documentos iniciales describen el paquete antes de ejecutarse; los resultados de noviembre son evidencia de la ejecución real.

No confundir este experimento con el protocolo distinto de lags 2–6 versus tendencia de seis meses, documentado en el repositorio `Experimentos-cloud/segunda_competencia_experimento_variables_historicas`.

### Pendiente para reproducibilidad integral

Agregar en una segunda etapa, tras inspección de datos sensibles: scripts fuente, configuración congelada, hashes/manifiestos, dependencias y reportes agregados. Los archivos de predicciones individuales y el dataset original permanecen fuera de Git.

## Nuevo diseño comparable en 2019

[Baseline de Ale + subconjunto intrames de C3, con y sin ensemble](experimento_Ale_C3_2019/README.md). Protocolo A/B/C/D documentado; ejecutado y verificado el 8 de noviembre de 2026: 40 modelos, 20 semillas por representación. B mejora en la semilla principal, pero no aparece una mejora consistente entre semillas.
