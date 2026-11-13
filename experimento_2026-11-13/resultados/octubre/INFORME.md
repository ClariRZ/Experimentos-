# Evaluación de octubre — v4

Evaluada el 13/11/2026. Corrida `octubre_20261113_01`, modelos de `completa_20261111_03`. Estado: completado; VM verificada TERMINATED.

## Resultado principal

F1 obtuvo la mayor ganancia del ensemble: 289,30 M, +12,155 M (+4,39%) frente al baseline. F4a mostró mayor consistencia individual: ganó en 5/5 semillas, con +6,5175 M de diferencia media. F3 ganó en 4/5. F4b perdió en las cinco. El baseline mantuvo el mayor AUC del ensemble.

Esto describe la evaluación cerrada de los cinco brazos; no reemplaza retrospectivamente la decisión de agosto ni declara un nuevo ganador de desarrollo. F4a había empeorado la ganancia en agosto, por lo que su resultado positivo aquí también muestra dependencia del período.

## Qué se ejecutó

Se reutilizaron 25 modelos LightGBM guardados (5 brazos × semillas 101, 211, 307, 401, 503), entrenados marzo–junio. Cero entrenamientos nuevos, cero búsquedas de hiperparámetros, cero búsquedas de corte en octubre. Evaluación de 135.754 clientes, 630 BAJA+2. Tiempo del evaluador: 167,14 segundos.

Antes de leer etiquetas de octubre se congelaron hashes de modelos, columnas, resultados de agosto y política de contactos. Las cinco matrices de agosto se reconstruyeron y coincidieron exactamente con las originales. Las 25 predicciones de agosto coincidieron con error máximo 0. Se validó además el corte proporcional y el desempate por identificador con un caso sintético.

Se conservaron las nueve máscaras de saneamiento originales. No se incorporaron las máscaras adicionales del pipeline del equipo después de conocer octubre. Cada brazo usa las mismas columnas, orden, transformaciones, parámetros y árboles con que fue entrenado.

## Ganancia del ensemble

Ensemble significa promedio de las probabilidades/puntajes de los cinco modelos, antes de ordenar clientes. La ganancia es una simulación con +1.072.500 por BAJA+2 contactado y −27.500 por cualquier otro contacto.

| Brazo | Contactos | BAJA+2 acertadas | Ganancia M | Diferencia vs B0 M | Diferencia % | AUC BAJA+2 |
|---|---:|---:|---:|---:|---:|---:|
| B0: Baseline histórico | 3682 | 344 | 277.1450 | +0.0000 | +0.00% | 0.925106 |
| F1: Media, mínimo, máximo y rango W3 | 4400 | 373 | 289.3000 | +12.1550 | +4.39% | 0.923743 |
| F3: Cambios relativos | 4222 | 364 | 284.2950 | +7.1500 | +2.58% | 0.924758 |
| F4a: Rankings del mes | 4109 | 364 | 287.4025 | +10.2575 | +3.70% | 0.923777 |
| F4b: Rankings y su historia | 5889 | 392 | 269.2525 | -7.8925 | -2.85% | 0.921956 |

La cantidad de contactos se fijó como `floor(proporción del ensemble de agosto × población de octubre)`, por separado para cada brazo. Esa cantidad se aplicó a sus cinco semillas y a su ensemble. Por lo tanto, se comparan modelos con sus políticas de contactos predefinidas, no modelos con igual cantidad de envíos. No se eligió el máximo de ninguna curva de octubre.

## Estabilidad entre semillas

| Brazo | Ganancia media M | Desvío entre semillas M | Diferencia media vs B0 M | Semillas favorables |
|---|---:|---:|---:|---:|
| B0 | 280.0050 | 3.2631 | — | — |
| F1 | 280.2800 | 3.8421 | +0.2750 | 2/5 |
| F3 | 283.1950 | 2.9103 | +3.1900 | 4/5 |
| F4a | 286.5225 | 2.3847 | +6.5175 | 5/5 |
| F4b | 272.9925 | 4.6409 | -7.0125 | 0/5 |

F1 gana mucho al combinar predicciones, pero su diferencia media individual es solo +0,275 M y gana en 2/5. No confundir ambos resultados. Las cinco semillas comparten clientes y período: no son cinco pruebas temporales independientes ni prueban significancia por sí solas.

## Interpretación y límites

- El objetivo económico y el AUC pueden ordenar modelos de forma distinta: el AUC mide el ranking global; la ganancia depende de los contactos seleccionados.
- F3 conserva una señal económica positiva en agosto y octubre, pero esto no equivale a una confirmación independiente de todo el proceso de búsqueda.
- F4a revierte su resultado económico de agosto; F4b permanece desfavorable. No concluir que cualquier ranking mejora.
- Antes de esta evaluación ya se conocían resultados grupales sobre octubre. Se declara esa exposición; no se presenta como un test totalmente virgen.
- Los +12,155 M de F1 aquí no son comparables directamente con los +9 M/mes de PAQ_P3: cambian controles, calendarios, ponderación BAJA+2 y cálculo de ganancia.
- No se ha usado octubre para cambiar una receta, hiperparámetro, saneamiento o corte durante esta corrida. Cualquier decisión futura basada en estos resultados será exploratoria.

## Respaldo

Código, resultados completos por semilla/ensemble, verificaciones, autorización y resumen del protocolo guardados en Git local. El paquete completo del protocolo con listas de columnas está conservado en la VM y en Cloud Shell; la copia local del protocolo contiene cantidades y hashes de esas listas. Los modelos y predicciones individuales permanecen fuera de Git. El JSON recuperado fue verificado por SHA256; ver `transferencia.json`. No se realizó push a GitHub.
