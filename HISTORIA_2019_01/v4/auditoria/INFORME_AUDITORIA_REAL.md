# Auditoría real de Historia 2019 v4 — 11 de noviembre de 2026

La auditoría corregida terminó con código 0. La VM quedó apagada (TERMINATED). No se entrenaron modelos ni se evaluaron resultados de octubre. Las 21 pruebas sintéticas pasaron tanto localmente como en la VM.

## Datos y corrección

Se verificaron el SHA-256 del dataset, las veinte semillas contra la configuración previa, la presencia de enero–agosto, la unicidad de cliente/mes y las etiquetas en entrenamiento/validación. Se aplicaron en memoria las nueve máscaras de roturas conocidas, conservando el archivo original.

`cmobile_app_trx` se infería como texto. Se corrigió exclusivamente su lectura mediante conversión numérica estricta, conservando nulos y abortando ante texto inválido. No se imputaron ceros.

Entrenamiento marzo–junio: 507.328 filas. Validación agosto: 131.887 filas. El informe contiene conteos mensuales y cobertura por transformación. La auditoría no demuestra ausencia de todas las posibles roturas nuevas ni ausencia de leakage en un runner de entrenamiento aún no implementado.

## Variables disponibles con la regla provisional del 90 %

Se auditaron 129 fuentes semánticamente elegibles. Estos conteos indican disponibilidad, no mejora predictiva.

| Comparación | Transformaciones que cumplen cobertura |
|---|---:|
| Rama corta, promedios/mínimos/máximos/rango W3 | 376 (94 fuentes × 4) |
| Rama corta, cambios relativos W3 | 30 |
| Ranking mensual actual | 94 |
| Historia del ranking propuesta | 759 |
| Rama larga W3, paquete completo | 500 |
| Rama larga W4, paquete completo | 498 |
| Rama larga W6, paquete completo | 451 |
| Pares fuente–fórmula comunes a W3/W4/W6 | 451 |

Las 451 transformaciones comunes se distribuyen en 344 de nivel/extremos, 86 pendientes y 21 cambios relativos. Deben mantenerse las mismas fórmulas, fuentes y clientes entre ventanas para comparar longitudes. La pendiente W3 sigue siendo delta2/2; no atribuirle información independiente.

El baseline enumerado tiene 666 columnas (150 originales no completamente vacías en entrenamiento y 516 rezagos/deltas). Es un conteo previo a la depuración final: incluye derivados de fuentes sin información en entrenamiento. `tmobile_app` y `cmobile_app_trx` se excluyeron como originales por estar completamente vacías en marzo–junio. Este baseline es una adaptación nueva, no el B4 de 588 columnas de v2.

No hubo constantes ni duplicados exactos dentro de las transformaciones F1/F2/F3 que pasaron el 90 %, según el control implementado. Esto no descarta redundancias contra el baseline, entre familias o en la historia del ranking.

## Decisión pendiente: cobertura

El 90 % excluye variables plausiblemente útiles: varias fuentes Mastercard tienen alrededor del 84,3 % de ventanas W3 completas; varias fuentes Visa quedan cerca del 89,9 % en W6. Los ratios también pierden cobertura porque denominador cero produce nulo. Estas ausencias pueden reflejar producto no contratado, historia insuficiente o saneamiento; no son por sí solas prueba de inutilidad.

| Cobertura exigida | F1 corta | F3 corta | Transformaciones comunes rama larga |
|---|---:|---:|---:|
| 80 % | 440 | 58 | 557 |
| 85 % | 376 | 34 | 500 |
| 90 % | 376 | 30 | 451 |
| 95 % | 344 | 18 | 0 |

Esta sensibilidad se calculó sobre cobertura de entrenamiento, sin entrenar ni observar métricas de validación. No se cambió automáticamente el umbral. Recomendación: revisar el filtro por cobertura antes de fijar el experimento; separar ausencia estructural, roturas e historia insuficiente y conservar el tratamiento uniforme entre control y alternativas. No bajar el umbral solo para obtener más columnas.

## Recursos y siguiente paso

VM de 8 CPU y aproximadamente 62,8 GiB de RAM, con 28,9 GiB de disco libre al medir. Auditoría: 52,72 segundos y 20,6 GiB de memoria máxima. Estos tiempos no estiman el costo de Optuna.

Antes de entrenar: cerrar la regla de cobertura y la depuración del baseline, fijar los brazos y el presupuesto de búsqueda comparable. La medición de un trial requiere autorización de entrenamiento. Octubre se mantiene para la comparación final según la consigna de Ale.

El JSON completo, el registro y el manifiesto de cierre están en `real_20261111_03`. Resultados guardados localmente; no publicados a GitHub.
