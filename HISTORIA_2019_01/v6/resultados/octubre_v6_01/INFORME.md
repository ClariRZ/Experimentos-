# V6 — Cierre económico en octubre de 2019

Evaluación realizada el 13/11/2026 por autorización de Clara. Once alternativas congeladas, cinco modelos por alternativa, cero ajustes nuevos. Entrenamiento original: junio de 2019. Octubre contiene 135.754 clientes.

## Método

Cada modelo conserva sus columnas, hiperparámetros y árboles originales. Se verificaron los hashes del dataset y de los 55 modelos y sus predicciones archivadas. Antes de puntuar octubre, se reconstruyeron las variables y se reprodujeron exactamente las 55 predicciones de agosto (error máximo cero). No se hizo selección de columnas con octubre.

Para cada semilla se fijó su proporción de contacto obtenida en agosto; para el ensemble se fijó la proporción de su propio promedio de scores. En octubre se contactó `floor(proporción_agosto × N_octubre)`, con desempate por ID. Ganancia: +1.072.500 por BAJA+2 y −27.500 por el resto. No se buscó el mejor corte en octubre. No se agregaron pesos de clases ni bootstrap en este cierre.

## Resultados completos

Ganancia del ensemble: promedio de scores de cinco modelos, no promedio de sus ganancias. Importes en millones. Agosto usa ganancia suavizada de desarrollo; octubre usa ganancia puntual al corte congelado. No comparar directamente ambos niveles de ganancia. Las ventanas incluyen la observación actual.

| Brazo | Representación | Contactos octubre | Ganancia octubre (M) | Diferencia vs B0_J (M) | Semillas favorables octubre | Diferencia agosto (M) | Semillas favorables agosto |
|---|---|---:|---:|---:|---:|---:|---:|
| B0_J | Baseline de junio | 4558 | 261.8550 | +0.0000 | — | +0.0000 | — |
| L4 | Rezagos hasta 3 meses atrás | 4361 | 266.1725 | +4.3175 | 2/5 | +0.1131 | 1/5 |
| L6 | Rezagos hasta 5 meses atrás | 4887 | 268.2075 | +6.3525 | 3/5 | +2.1808 | 3/5 |
| S3 | Resúmenes de 3 observaciones | 4386 | 268.7850 | +6.9300 | 4/5 | +0.6774 | 2/5 |
| S4 | Resúmenes de 4 observaciones | 3921 | 268.3725 | +6.5175 | 2/5 | -2.9781 | 1/5 |
| S6 | Resúmenes de 6 observaciones | 3631 | 268.6475 | +6.7925 | 2/5 | -7.0824 | 0/5 |
| T4 | Tendencia de 4 observaciones | 4190 | 268.6750 | +6.8200 | 5/5 | +6.2295 | 5/5 |
| T6 | Tendencia de 6 observaciones | 5529 | 263.7525 | +1.8975 | 4/5 | -4.7444 | 0/5 |
| R3 | Cambios relativos, 3 observaciones | 4293 | 273.5425 | +11.6875 | 5/5 | +5.4535 | 5/5 |
| R4 | Cambios relativos, 4 observaciones | 4128 | 276.9800 | +15.1250 | 5/5 | +4.7587 | 4/5 |
| R6 | Cambios relativos, 6 observaciones | 3854 | 277.9150 | +16.0600 | 4/5 | -3.5055 | 1/5 |

## Interpretación

T4, R3 y R4 habían cumplido la regla operativa de agosto. Los tres superaron al control en las cinco semillas de octubre. R4 suma 15,125 M en el ensemble (+5,78% respecto de B0_J), R3 suma 11,6875 M (+4,46%) y T4 suma 6,82 M (+2,60%).

R6 obtiene el mayor valor del ensemble de octubre (+16,06 M), pero había perdido contra el control en agosto (−3,506 M, 1/5 semillas favorables). Es una reversión entre meses, no una validación de superioridad estable ni motivo para cambiar retrospectivamente la selección de agosto.

Todas las alternativas superaron al baseline en el ensemble de octubre, pero varias no lo hicieron de forma consistente por semilla. Los cortes difieren entre alternativas: se evalúan las políticas congeladas completas, no un presupuesto idéntico de contactos.

Octubre ya había sido observado en versiones anteriores; esta continuación es exploratoria. Cinco semillas no son cinco períodos independientes y no se calculó significación estadística en este cierre. Los resultados no demuestran que la mejora se repetirá en meses futuros. Tampoco son directamente comparables con v5, cuyo calendario de entrenamiento es diferente.

## Evidencia

- `policy_frozen.json`: brazos, cortes y hashes previos a la evaluación.
- `august_verification.json`: 55 reproducciones exactas de agosto.
- `FINAL.json` y `<brazo>/result.json`: métricas y 18 contrastes.
- `private_artifacts_sha256.json`: identidad de predicciones y etiquetas privadas.
- `supervisor.json`: finalización sin errores; evaluación en aproximadamente 157 segundos.
- `../../auditoria/octubre_v6_01/control.json`: respaldo y estado de VM.
- `../../scripts/verificar_octubre.py`: comprueba cortes, ganancias compatibles con aciertos enteros y contrastes a partir de agregados; no vuelve a puntuar datos privados.

Se aprobaron 17 pruebas locales, incluidas equivalencia de variables de agosto y aplicación del corte fijo con desempate. Datos, modelos y predicciones individuales permanecen en el disco privado de la VM.
