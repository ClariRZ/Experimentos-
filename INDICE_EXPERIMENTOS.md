# Índice central de experimentos y evidencia

Este repositorio reúne el material publicable antes distribuido entre `Segunda_competencia` y `Experimentos-`. Los documentos de una corrida son históricos: consultar la evidencia de cierre antes de interpretar «pendiente» o «sin ejecutar».

| Experimento | Documentación y código | Evidencia / límite |
|---|---|---|
| Historia v1 | [Bitácora de la primera corrida](HISTORIA_2019_01/README.md) | [Verificación de respaldo privado v1/v6](informes/respaldo_local_v1_v6_2026-11-14/README.md). Test económico de v1 quedó pendiente en su FINAL histórico. |
| Historia v2 | [Carpeta completa](HISTORIA_2019_01/v2/) | Auditoría, scripts, configuraciones y cierre recuperados del origen. |
| Historia v3 | [Carpeta completa](HISTORIA_2019_01/v3/) | Prompt, auditoría, ejecución y evidencias publicadas del origen. |
| Historia v4 | [Preparación y auditoría](HISTORIA_2019_01/v4/) | [Paquete del 13/11 con reproducción y octubre](experimento_2026-11-13/README.md). Conservar ambos: no son copias intercambiables. |
| Historia v5 | [Carpeta integrada](HISTORIA_2019_01/v5/) | README de preparación histórico; contrastar con resultados y [relevamiento posterior](informes/cierre_v1_v7_2026-11-14/INFORME.md). |
| Historia v6 | [Ejecución y cierre](HISTORIA_2019_01/v6/README.md) | Se mantiene el README actualizado del destino; versión antigua de origen archivada. |
| Historia v7 | [Carpeta](HISTORIA_2019_01/v7/) | Código, protocolo, resultados de agosto/octubre y auditorías existentes. |
| Historia v8 | [Cierre consolidado ejecutado](HISTORIA_2019_01/v8/cierre_consolidado/README.md) | [Prompt correspondiente](HISTORIA_2019_01/v8/prompts/cierre_consolidado/PROMPT_MAESTRO_V8.md). [Cierre reportado: 144 ajustes y evaluación completa](HISTORIA_2019_01/v8/evidencia_cierre/v8_20261115_021908_c48e9d/README.md); R3/T4/RR4 prometedores inconclusos. [Tablas originales, recibo y verificación pública](HISTORIA_2019_01/v8/resultados/v8_20261115_021908_c48e9d/README.md). Archivo privado no incluido en la copia local recibida. |
| Ale C3 2019 | [Carpeta](experimento_Ale_C3_2019/) | Código, auditorías y resultados agregados del origen. |
| Históricas B0–B5 | [Carpeta](experimento_historicas_B0_B5/README.md) | Modelos y base Optuna conservados localmente; no incluidos en GitHub central. No se renombra como v1. |
| Experimentos C3 / intrames | [Carpeta](experimentos_c3/) | Configuraciones, preparación, auditorías y resultados del origen. |

**Lectura integral:** [ingeniería inversa v1–v8 en HTML](informes/ingenieria_inversa_v1_v8_2026-11-15/README.md): decisiones, resultados, fortalezas y debilidades, actualizado con el cierre v8.

## Procedencia y verificación

[Informe de consolidación](informes/consolidacion_repos_2026-11-15/README.md) · [Inventario archivo por archivo](informes/consolidacion_repos_2026-11-15/INVENTARIO.json) · [Versiones discrepantes originales](fuentes/Segunda_competencia_c89185ae/).

`python3 herramientas/verificar_consolidacion.py` comprueba los 895 archivos publicables del origen y la exclusión de los siete privados. No necesita VM, datos ni entrenamiento.
