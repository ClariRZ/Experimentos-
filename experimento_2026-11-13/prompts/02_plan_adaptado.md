# Historia 2019 v4 — plan inicial para aprobar

Estado: propuesta preparada, sin autorización de entrenamiento. VM apagada en la última verificación. No se modificaron la auditoría previa ni sus resultados. Este plan reemplaza el filtro automático del 90 % para el próximo ensayo.

## Pregunta

¿Mejoran las representaciones históricas el desempeño de un LightGBM con variables originales, rezagos y cambios, cuando cada alternativa recibe el mismo presupuesto de optimización? Miramos hacia un proceso que pueda incorporar más historia a medida que llegan nuevos meses.

## Datos y variables

Entrenar marzo–junio completos, validar en agosto. Enero y febrero aportan historia. Entrenamiento positivo: BAJA+1 y BAJA+2; AUC de agosto positivo: BAJA+2. Octubre se reserva para la evaluación final conforme a Ale; no se usa en esta etapa.

Aplicar las mismas nueve máscaras de saneamiento a todos los brazos. Mantener los nulos y los negativos válidos. La lectura de `cmobile_app_trx` se convierte estrictamente a número.

Se elimina el descarte automático por cobertura del 90 %. La cobertura se informa por mes, pero un nulo no implica que la variable sea inútil. Documentar por separado las roturas conocidas, la falta de una fila histórica y los nulos originales de causa desconocida. No atribuir automáticamente los nulos a falta de producto.

Antes de entrenar, depurar usando exclusivamente entrenamiento: quitar columnas completamente vacías, constantes en todas las filas y duplicadas exactas. Conservar una columna con un único valor finito y nulos si su patrón de ausencia varía: puede aportar información. Las columnas del baseline tienen prioridad frente a copias añadidas por una familia. No hacer selección usando agosto en esta depuración.

Las 129 fuentes del diccionario son candidatas. Los 666 campos enumerados en la auditoría no son un número final: se recalcularán después de depurar. El baseline es una adaptación de v4 y no debe presentarse como el B4 de v2.

## Cinco comparaciones iniciales

| Brazo | Contenido | Comparación |
|---|---|---|
| B0 | Originales + lag1/2 + delta1/2 | Control |
| F1 | B0 + promedio, mínimo, máximo y rango de 3 observaciones | B0 |
| F3 | B0 + cambios relativos frente a promedio, lag1 y lag2 | B0 |
| F4a | B0 + ranking mensual actual | B0 |
| F4b | F4a + rezagos, cambios y resúmenes del ranking | F4a y B0 |

Cada ventana incluye el mes actual y los dos anteriores, por calendario exacto. Los resúmenes requieren ventana completa. Los cambios relativos usan `(actual − referencia) / abs(referencia)`; denominador cero o resultado no finito produce nulo. Los rankings usan rango promedio mensual dividido por la cantidad no nula. No se añade pendiente de tres puntos a la rama corta porque equivale a delta2/2.

Las familias F1, F3 y F4a parten del mismo control, sin acumularse. F4b es la comparación incremental explícita para separar ranking actual e historia del ranking.

## Presupuesto inicial propuesto

- Dos entrenamientos de medición de 100 árboles: B0 y F4b. No intervienen en la elección de variables/modelo.
- Diez trials de Optuna por brazo: 50 entrenamientos, con el mismo espacio de búsqueda y objetivo AUC de agosto.
- Cinco semillas por brazo con los parámetros y la cantidad de árboles elegidos para ese brazo: 25 reentrenamientos.
- Total máximo: 77 entrenamientos. Un modelo por vez, cuatro hilos, máximo 1.500 árboles por trial y early stopping de 100 rondas en Optuna.
- Límite de ejecución: dos horas de VM para esta etapa, incluyendo preparación y medición. Es un techo propuesto, no una predicción de duración ni un precio.
- No superar 48 GiB de memoria por proceso de trabajo ni continuar con menos de 10 GiB libres. Un supervisor externo debe guardar el estado, detener esta corrida al límite y apagar la VM.

Después de los dos entrenamientos de medición, revisar tiempo y memoria. Si no parece viable terminar los cinco brazos con el mismo presupuesto restante, pausar antes de Optuna. No reducir trials o semillas solo a algunos brazos. No declarar una comparación terminada con presupuestos desiguales.

Este presupuesto explora, no agota la optimización. La diferencia estimada incluye la representación y su ajuste de hiperparámetros; no representa exclusivamente un efecto de variables con parámetros fijos. Las dos horas no incluyen nuevas corridas de confirmación. No se estimó costo monetario.

## Cómo se decide qué seguir

Reportar AUC, ganancia, media/mediana de las diferencias pareadas, desviación entre semillas y cantidad de victorias. Elegibilidad para confirmación: diferencia media de AUC positiva y al menos cuatro victorias de cinco contra B0. Para atribuir aporte a la historia del ranking, F4b también debe cumplir esa regla contra F4a. Siempre mostrar ambas comparaciones.

Esta es una regla operativa de cómputo, no una prueba de significación. La ganancia se informa aunque contradiga al AUC; no cambiar de criterio después de mirar los resultados. No prometer una mejora por una corrida favorable.

Regla económica sin cambios: +1.072.500 por BAJA+2 contactado y −27.500 para los demás. En agosto, elegir el corte con la curva suavizada completa de 2.001 posiciones. Antes del test final, congelar la proporción de contactos de cada ensemble; octubre se evalúa sin volver a elegir el corte.

## Etapas posteriores, fuera de este presupuesto

Confirmar candidatos con veinte semillas. Probar combinaciones y canaritos solo con controles completos comparables y protocolos propios. La rama de historia larga compara W3/W4/W6 entrenando todas las alternativas y su control en junio, con iguales clientes y pares fuente–fórmula. Recalcular sus columnas comunes bajo la nueva regla de nulos: las 451 de la auditoría corresponden al filtro anterior.

## Entregable y autorización

Guardar configuración, código, manifiestos, resultados agregados y consumo en Git local. No publicar a GitHub sin resolver esa autorización. No incorporar datos individuales, predicciones por cliente ni credenciales al repositorio.

Al aprobar este plan, el siguiente trabajo será implementar y verificar el runner, la depuración y el supervisor; luego ejecutar la etapa inicial dentro del límite acordado y apagar la VM. No existe todavía un runner v4 verificado para este plan. La aprobación solicitada cubre esos trabajos y hasta 77 entrenamientos exploratorios dentro de dos horas, no las etapas posteriores ni octubre.
