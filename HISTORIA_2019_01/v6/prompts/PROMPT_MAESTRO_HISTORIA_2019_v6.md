# PROMPT MAESTRO — HISTORIA 2019 v6
## Profundidad histórica: más rezagos, resúmenes, tendencias y cambios relativos

**Versión:** 6.0 — 13 de noviembre de 2026.
**Estado:** protocolo propuesto; no implementado ni ejecutado. Redactar este documento no autoriza encender una VM ni entrenar.
**Ubicación:** `ClariRZ/Segunda_competencia/HISTORIA_2019_01/v6/`.

Actuá como especialista en LightGBM, datos longitudinales, diseño experimental y evaluación económica. Ejecutá únicamente el alcance aprobado, conservá evidencia y comunicá las diferencias entre propuesta, implementación y corrida real. No prometas mejoras ni sustituyas una rama por otra sin explicarlo antes.

## 1. Objetivo y pregunta principal

**¿Ampliar la historia de tres a cuatro y seis observaciones, o representarla mediante tendencias y cambios relativos, mejora la ganancia frente a un baseline con historia de dos meses anteriores?**

Trabajar exclusivamente con datos de 2019, desde enero. No utilizar 2020 ni datos anteriores a enero de 2019.

Mirar al futuro significa construir un procedimiento que pueda incorporar nuevos meses cuando estén disponibles: calendario parametrizable, historia causal, comparación justa, registro de cobertura y costo. No significa usar meses futuros para construir una variable pasada ni afirmar que una mejora de 2019 se trasladará a otro año.

El resultado negativo también es válido. El 3–5 % mencionado en la reunión es una referencia de magnitud interesante, no una meta garantizada ni una condición para ocultar resultados.

## 2. Antecedentes y diferencias respecto de las versiones anteriores

Leer antes de implementar:

1. `HISTORIA_2019_01/v2/prompts/PROMPT_MAESTRO_HISTORIA_2019_v2.md`.
2. `HISTORIA_2019_01/v3/prompts/PROMPT_MAESTRO_HISTORIA_2019_v3.md`.
3. `experimento_2026-11-13/prompts/01_prompt_original.txt`, `02_plan_adaptado.md` y `03_contrato_ejecutado.json`.
4. `experimento_2026-11-13/configuracion/contrato_original.json` y código de fórmulas.
5. `HISTORIA_2019_01/v5/prompts/PROMPT_MAESTRO_HISTORIA_2019_v5.md`.
6. El contrato ejecutado de v5, su auditoría real y sus registros de corrida.
7. Las pautas de Alejandro del 28 de octubre y la transcripción de la reunión compartidas por la usuaria.
8. El notebook `monday/z402_Feature_Engineering_en_SQL.ipynb`, registrando versión y hash de la copia consultada.

| Versión | Qué distingue su diseño | Qué no trasladar automáticamente |
|---|---|---|
| v2/v3 | Escalera y familias, shortlist, filtros de cobertura y parámetros compartidos en screening | Sus nombres B0/B4, filtros del 90 %, fuentes o resultados no identifican el baseline actual |
| v4 | B0, F1, F3, ranking actual e historia de ranking; optimización propia por brazo | El prompt original era más amplio que la corrida ejecutada |
| v5 ejecutada | B0, L, P, MIN, MAX, RANGO y F1, entrenados marzo–junio | Su contrato de 105 ajustes no ejecuta la rama larga del prompt maestro |
| v6 propuesta | Historia larga con junio común; más rezagos, resúmenes, tendencias y cambios relativos | No reemplazarla por otra descomposición de historia corta |

**V6 no depende de que gane una familia en v5.** Sus hipótesis, brazos y comparaciones se fijan ahora. V5 aporta antecedentes y código verificable; sus resultados no decidirán qué ventanas o familias de este núcleo se ejecutan.

Terminar y documentar v5 según su contrato. No interrumpirla ni ejecutar v6 simultáneamente. La redacción y preparación local de v6 pueden avanzar mientras v5 corre. No esperar resultados de v5 para formular este protocolo ni seleccionar retrospectivamente su mejor variante como nuevo baseline de v6.

## 3. Pautas de Alejandro y decisiones propias del protocolo

Conservar las pautas: 2019, LightGBM, sin sampling, entrenamiento BAJA+1 y BAJA+2 combinadas, AUC para Optuna y early stopping, agosto como validación y octubre como test económico. No usar noviembre ni diciembre como filas de entrenamiento o evaluación: están destinados al dashboard y no tienen la misma disponibilidad de etiquetas.

De la reunión se toma: probar más historia aun entrenando con un solo mes; resúmenes y tendencias; reoptimizar cada variante porque cambia la cantidad de variables y el efecto de `feature_fraction`; considerar selección de variables sin confundirla con feature engineering.

**Adaptación central de v6:** todos los brazos se entrenan únicamente en junio. Es una decisión de este diseño para comparar W3/W4/W6 con un calendario común, siguiendo la posibilidad discutida en la reunión; no afirmar que sustituye la consigna general marzo–junio.

Los once brazos, los 18 contrastes, el presupuesto de diez trials y cinco semillas, y la regla económica operativa de este documento son decisiones del equipo, no citas textuales de Ale.

## 4. Calendario y control comparable

| Función | Meses y uso |
|---|---|
| Historia del entrenamiento | Enero–junio; solo pasado y mes actual de cada fila |
| Entrenamiento de todos los brazos | Junio de 2019, todas sus filas válidas |
| Validación y optimización | Agosto de 2019 |
| Historia para agosto | Los meses previos necesarios, incluyendo julio; julio no se agrega como fila de entrenamiento |
| Test económico al cierre | Octubre de 2019, con modelos y cortes congelados |
| Historia para octubre | Los meses previos necesarios, incluyendo septiembre; no usar sus etiquetas |

- W3 = actual y dos anteriores: para junio, abril–junio.
- W4 = actual y tres anteriores: para junio, marzo–junio.
- W6 = actual y cinco anteriores: para junio, enero–junio.
- W6 no significa seis meses anteriores: su rezago más antiguo es lag5.
- No eliminar clientes por tener historia incompleta. Mantener las mismas filas y orden entre brazos; los derivados faltantes quedan nulos.

**B0_J:** originales + lag1/lag2 + delta1/delta2, reconstruido, depurado y optimizado usando exclusivamente junio. Las fuentes y reglas parten del contrato v5, pero el número final de columnas se recalcula sobre junio: no imponer 652 ni reutilizar sin comprobación el modelo marzo–junio.

El control de v5 puede aparecer como contexto descriptivo. No atribuir a la historia una diferencia contra ese control, porque cambian las filas de entrenamiento. Los contrastes válidos de v6 usan B0_J o el control específico de la tabla siguiente.

## 5. Datos, fuentes, saneamiento y cobertura

Identificar el dataset por SHA256. Referencia de partida:
`459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872`.

Usar las 129 fuentes históricas revisadas del contrato v5 como conjunto candidato, con su diccionario y exclusiones semánticas. No construir tendencias de códigos nominales o fechas crudas solo por estar almacenados como números. No elegir fuentes según AUC o ganancia de agosto/octubre.

Conservar las nueve máscaras variable–mes del contrato v5, los negativos válidos y los nulos; convertir valores no finitos a nulos con conteos. No imputar ceros, rellenar con datos posteriores ni reemplazar un mes faltante por la fila anterior disponible.

Separar en la auditoría: ausencia de cliente–mes, nulo original, rotura documentada y denominador cero. No deducir ausencia de producto sin respaldo del diccionario.

Depurar en junio: columnas totalmente vacías, constantes incluyendo patrón de nulos y duplicadas exactas en la representación numérica del modelo. Conservar una columna de un único valor finito más nulos cuando el patrón varía. Prioridad de conservación: B0_J y luego nombres en orden lexicográfico; publicar todos los alias.

Para comparar ventanas con un mismo paquete:

- Congelar los mismos pares fuente–fórmula para S3/S4/S6, para T4/T6 y para R3/R4/R6, respectivamente.
- Determinar elegibilidad únicamente con junio. Si un par es vacío, constante o una copia exacta descartable en alguna de las ventanas del grupo, excluir ese par en todo ese grupo y registrar la razón y el alias. Resolver iterativamente de manera determinista antes de congelar listas.
- Este criterio común no se aplica para quitar lag4/lag5 de L6: agregar esos rezagos es la intervención que se quiere medir. L6 conserva las columnas de L4 y agrega los nuevos rezagos elegibles.
- No reinstalar el umbral automático del 90 %. Informar cobertura por fuente, fórmula, ventana y mes, sin usarla para filtrar clientes.
- Si una familia queda sin columnas identificables, informar `NO_IDENTIFICABLE`; no inventar reemplazos ni reasignar su presupuesto silenciosamente.

La comparación mide el efecto práctico de más historia, incluyendo cambios de cobertura. No demuestra un efecto puro de longitud entre clientes con seis observaciones completas. Esta limitación debe figurar en el informe.

## 6. Fórmulas exactas y relación con el notebook

Sea x_t el valor de una fuente para un cliente en el mes t, saneado previamente.

**Rezago:** `lag_k = x_(t-k)`, con unión exacta cliente–mes calendario. Si falta el mes o valor requerido, nulo.

**Delta del baseline:** `delta_k = x_t - x_(t-k)`, k = 1, 2; exige ambos extremos, no los meses intermedios.

**Resúmenes S_W:** media aritmética, mínimo, máximo y rango `máximo - mínimo` de las W observaciones consecutivas, incluido el mes actual. Exigir W valores finitos no nulos. Sin ventana completa, cada resumen queda nulo.

**Tendencia T_W:** pendiente OLS del valor contra los índices de tiempo `0,...,W-1`, del mes más antiguo al actual:

`beta_W = sum((j - media(j)) * (x_j - media(x))) / sum((j - media(j))**2)`.

Exigir ventana completa. La unidad es cambio de la variable por mes. Probar W4 y W6. No agregar T3 como nueva señal: con tres puntos completos y equiespaciados equivale a delta2/2. Con faltantes, las máscaras pueden diferir; no confundir esa diferencia con una nueva geometría temporal.

**Cambios relativos R_W:** tres columnas por fuente, con referencias `media_W`, `lag1` y `lag_(W-1)`:

`c(x_t, r) = (x_t - r) / abs(r)`.

En el núcleo de v6, exigir la ventana completa para las tres fórmulas, siguiendo F3 de v4/v5. Referencia cero, nula o resultado no finito produce nulo. No agregar épsilon, recortar extremos ni imputar sin un nuevo contrato. Este cambio relativo no es el cociente crudo `actual / referencia`.

La variante que exige solo los valores realmente utilizados por cada fórmula es una hipótesis diferente sobre faltantes. Queda identificada para un contrato posterior; no mezclarla con la comparación de longitud de ventana.

**Precauciones verificadas en z402:**

- `ROWS BETWEEN 3 PRECEDING AND CURRENT ROW` contiene hasta cuatro filas, aunque el alias diga «3»; no equivale a W3.
- Una ventana por filas no garantiza meses consecutivos cuando hay huecos.
- Los agregados SQL pueden omitir nulos; v6 exige explícitamente ventana completa.
- El ejemplo de `regr_slope` usa `cliente_antiguedad` como eje. V6 usará mes calendario equiespaciado y lo documentará como adaptación, sin suponer equivalencia cuando haya anomalías de antigüedad.
- En una celda, el alias `lag_2_ctrx_quarter` corresponde a una resta. Verificar la expresión, no copiar el nombre como si fuera un rezago.

## 7. Núcleo obligatorio: once brazos

Todas las ampliaciones parten del mismo B0_J, salvo la comparación incremental L6–L4 indicada. No acumular ganadores durante la corrida.

| Brazo | Contenido | Hipótesis |
|---|---|---|
| B0_J | Originales + lag1/2 + delta1/2 | Control común entrenado en junio |
| L4 | B0_J + lag3 | Información directa hasta cuatro observaciones |
| L6 | L4 + lag4 y lag5 | Aporte adicional de los dos meses más antiguos |
| S3 | B0_J + media, mínimo, máximo, rango W3 | Ancla de resúmenes en el calendario nuevo |
| S4 | B0_J + los mismos resúmenes W4 | Ampliar resúmenes a cuatro observaciones |
| S6 | B0_J + los mismos resúmenes W6 | Ampliar resúmenes a seis observaciones |
| T4 | B0_J + pendiente W4 | Representar dirección de cuatro observaciones |
| T6 | B0_J + pendiente W6 | Representar dirección de seis observaciones |
| R3 | B0_J + los tres cambios relativos W3 | Ancla relativa en el calendario nuevo |
| R4 | B0_J + los mismos cambios relativos W4 | Aporte de referencias históricas más largas |
| R6 | B0_J + los mismos cambios relativos W6 | Aporte de referencias de seis observaciones |

Contrastes preregistrados, **18 únicos**:

1. Cada uno de los diez candidatos contra B0_J.
2. S4–S3, S6–S3 y S6–S4.
3. T6–T4.
4. R4–R3, R6–R3 y R6–R4.
5. L6–L4.

Registrar también toda la búsqueda previa en agosto; 18 contrastes no resumen la multiplicidad acumulada. No agregar otros contrastes para rescatar un resultado desfavorable. No afirmar que una pendiente gana a los resúmenes como conclusión principal de este diseño sin registrar la comparación correspondiente.

**No presentar once brazos como «v6 completa» si se ejecuta solo una parte.** Informar por brazo: propuesto, auditado, implementado, iniciado, completo, parcial o no identificable.

## 8. Modelo, optimización y semillas

LightGBM binario, sin sampling. Entrenar positivo BAJA+1 o BAJA+2; validar AUC con positivo BAJA+2 y negativo el resto. El score sirve para ordenar clientes, no es probabilidad calibrada de BAJA+2.

Optimizar cada brazo, incluido B0_J, por separado y con igual presupuesto. No heredar los hiperparámetros del ganador v5 ni volver al screening con parámetros fijos de v2/v3.

| Parámetro | Espacio común heredado de v5 |
|---|---|
| num_leaves | Entero 16–128, logarítmico |
| learning_rate | 0,01–0,1, logarítmico |
| min_data_in_leaf | Entero 100–2.000, logarítmico |
| feature_fraction | 0,3–1,0 |
| bagging_fraction | 0,5–1,0 |

Fijos: `bagging_freq=1`, cuatro hilos, `deterministic=true`, `force_col_wise=true`, objetivo binario, métrica AUC y `feature_pre_filter=false`, coherentes con el runner v5. Registrar todas las semillas internas de LightGBM.

- Optuna TPE: diez trials por brazo, cinco iniciales, sampler seed 20261111; modelo seed 101.
- Máximo 1.500 árboles y early stopping de 100 rondas por AUC de agosto.
- Elegir el mayor AUC; empate: primer trial. Congelar parámetros y cantidad de árboles por brazo.
- Evaluación: semillas `211, 307, 401, 503, 601`, distintas de la semilla usada en Optuna. Reentrenar con las rondas congeladas, sin nuevo early stopping por semilla.
- Ensemble: promedio aritmético de los cinco scores, con clientes alineados. No optimizar pesos en esta etapa.

El contraste mide una representación con su optimización bajo igual presupuesto, no un efecto de variables con hiperparámetros fijos. Diez trials no garantizan el óptimo.

Reutilizar solo con igualdad verificada de datos, filas y orden, columnas y orden, fórmulas, faltantes, parámetros, rondas, semillas, versiones y procedimiento. Los modelos de v5 entrenados marzo–junio no sustituyen los controles de junio.

## 9. Evaluación económica y estabilidad

Regla económica: **+1.072.500 por BAJA+2 contactado y −27.500 por cualquier otro contacto**. Son valores netos; no descontar nuevamente el costo al acierto.

AUC es el objetivo de Optuna y early stopping. Ganancia del ensemble es el resultado económico principal. Informar ambas incluso cuando discrepen.

En agosto, ordenar por score descendente y cliente ascendente. Usar la curva acumulada suavizada mediante media móvil centrada de 2.001 posiciones, con ventana completa y sin rellenar bordes. Elegir el máximo suavizado; empate: menor cantidad de contactos. Guardar también la ganancia puntual, contactos, BAJA+2 acertadas y proporción contactada en ese corte. El máximo de agosto es una métrica de desarrollo, no una estimación independiente de ganancia futura.

Por cada contraste, informar AUC y ganancia individual y del ensemble, diferencias pareadas por semilla, media, mediana, desviación muestral, semillas favorables, variables, cobertura, duración y memoria. No confundir media de ganancias individuales con ganancia del promedio de scores.

Regla operativa heredada de v5 para priorizar una eventual confirmación: mejora de ganancia suavizada del ensemble, diferencia media individual positiva y al menos cuatro de cinco semillas favorables contra el control pertinente. Es una regla de cómputo, no significación estadística. Las semillas no son períodos independientes.

No condicionar la ejecución de los once brazos a esa regla. Todos los brazos identificables del núcleo aprobado se ejecutan y reportan. Una ampliación a más semillas requiere presupuesto propio para candidato y controles pareados; no se ejecuta automáticamente.

## 10. Octubre: test económico conforme a la consigna

Octubre se usa para la comparación económica final. No se reemplaza por 2020. Como octubre ya fue observado en versiones previas, reportar honestamente que esta continuación es exploratoria; congelar v6 no vuelve independiente un mes ya conocido.

Antes de abrir sus etiquetas, congelar los once brazos identificables completados, columnas, código, modelos, semillas y proporciones de contacto obtenidas en agosto. Evaluar todos los brazos congelados para evitar mostrar solo el favorable; un brazo incompleto se informa aparte y no participa como comparación completa.

Para cada modelo individual y ensemble usar su propia proporción de agosto:

`k_octubre = floor(proporción_agosto * N_octubre)`.

No entrenar nuevamente, cambiar rondas, elegir nuevos pesos, buscar el mejor corte ni cambiar familias por su resultado de octubre. Las variables de octubre usan solo información disponible hasta octubre, sin etiquetas como predictores.

Tabla final: brazo, ventana, columnas, ganancia del ensemble, diferencia absoluta y porcentual contra B0_J, contactos, aciertos, media de ganancia individual, diferencia pareada y semillas favorables. Si el denominador de un porcentaje no es positivo, informar la diferencia absoluta y no un porcentaje engañoso. Mostrar también los contrastes de profundidad preregistrados.

El cierre de octubre es una fase explícita del plan, con evaluación sin nuevos ajustes. Al aprobar la ejecución debe constar si se incluye ese cierre; no dejarlo implícito ni afirmar «experimento terminado» cuando quede pendiente.

## 11. Presupuesto, alcance y ejecución

**Núcleo propuesto:** 11 brazos × (10 trials + 5 semillas) = **165 ajustes máximos nuevos**: 110 de búsqueda y 55 de evaluación. Sin pilotos, canaritos, combinaciones ni confirmaciones incluidos. Un brazo no identificable se registra; no se gasta su cupo en otra hipótesis.

No copiar automáticamente las seis horas autorizadas para v5. Antes del lanzamiento de v6, preparar un presupuesto explícito con tiempos medidos disponibles, incertidumbre, hardware, costo estimado con tarifa verificada y un límite independiente. Una medición que entrene cuenta como ajuste y requiere estar incluida en el presupuesto aprobado.

Etapas:

1. **Cerrar v5 operativamente:** confirmar su estado real, recuperar resultados o parciales, verificar apagado y respaldar evidencias. No reinterpretar sus resultados ni tocar sus contratos.
2. **Auditar v6:** calendario, claves, saneamiento, cobertura de W3/W4/W6, fuentes, depuración común, columnas finales, memoria y disco. Sin entrenar.
3. **Implementar y probar:** fórmulas, contrato, runner, persistencia, recuperación y apagado. Preparar el plan ejecutable que coincida con los once brazos y 18 contrastes.
4. **Ejecutar el núcleo aprobado:** controles y candidatos con igual presupuesto; guardar resultados por trial y semilla.
5. **Congelar y evaluar octubre** según el alcance aprobado para el cierre.
6. **Informe y reproducción:** resultados completos y negativos, limitaciones, costo y receta reutilizable.

No cambiar ventanas, fuentes, calendario, política de faltantes, semillas, trials o controles sin registrar una revisión antes de ejecutar. Un subconjunto por restricciones de presupuesto necesita un acuerdo explícito: no sustituye silenciosamente este núcleo.

Un modelo por vez. Supervisor independiente con límite de memoria, disco y tiempo; apagado máximo configurado en GCE y verificado antes de encender. Recuperar agregados antes del apagado normal. Registrar fallos de transferencia; no afirmar respaldo si no se comprobó. Reanudar solo checkpoints de la misma identidad y evitar procesos duplicados. Al agotar presupuesto, guardar y reportar `PARCIAL`, no reducir ensayos solo en algunos brazos para aparentar cierre.

## 12. Pruebas y trazabilidad

Pruebas necesarias antes de entrenar: huecos de calendario; orden temporal; ventana incluyendo actual; nulos y máscaras; denominador cero y signos; pendiente en serie conocida; identidad T3/delta2 donde corresponda; depuración con entrenamiento solamente; coincidencia de filas; fórmulas comunes entre ventanas; corte y ganancia; bloqueo de octubre durante desarrollo; protección contra sobrescritura y ejecución duplicada; timeout y recuperación.

Guardar en `HISTORIA_2019_01/v6/`: `prompts/`, `auditoria/`, `configuraciones/`, `scripts/`, `pruebas/`, `logs/`, `resultados/` y `manifiestos/`. No copiar resultados v5 bajo el nombre v6.

Por hito, versionar prompt, revisión, contrato, procedencia y hashes, recetas, columnas, exclusiones, versiones reales del entorno, trials, parámetros, semillas, métricas agregadas, consumo y errores. Registrar el commit exacto de cada corrida y hashes de matrices, modelos y predicciones. Mantener fuera de Git dataset, datos individuales, modelos y credenciales; documentar ubicación privada y recuperación.

Distinguir guardado local, commit local, push remoto y respaldo de artefactos privados. Publicar conforme a la autorización vigente, sin esperar al final para guardar los hitos. Una prueba sintética o un manifiesto válido no equivale a reproducir el entrenamiento completo en otra máquina.

## 13. Hipótesis posteriores: explícitamente fuera del núcleo

- Combinaciones entre resúmenes, tendencias y cambios relativos, contra componentes y control.
- Canaritos: selección solo con entrenamiento, sin usar agosto para importancia o umbral; conjunto completo y filtrado reoptimizados con igual presupuesto. No son una familia histórica.
- Ranking previo de montos y su historia: fijar convención, universo mensual, faltantes y fórmulas antes de probar; no mezclarlo con profundidad nominal en el núcleo.
- Cambios relativos con requerimientos mínimos de datos, frente a la receta estricta: comparación aislada de faltantes.
- Medias ponderadas, desvío estándar y varianza: sin ejecución automática; el rango ofrece una alternativa interpretable, sin afirmar que los demás nunca puedan funcionar.
- Confirmación temporal con otro calendario dentro de 2019: nuevo contrato, mismo control y sin presentarla como independiente si el mes ya intervino en decisiones.

Esta lista registra pendientes, no promete que se ejecuten como parte de los 165 ajustes.

## 14. Entregable final y explicación sencilla

El informe y el video deben responder: hipótesis, cambio contra control, condiciones comunes, resultados completos en agosto y octubre, sensibilidad a semillas, cobertura, costo, limitaciones y qué se probaría después. Separar estabilidad del entrenamiento, repetición en meses observados y generalización futura.

Explicación en pocas frases:

> Entrenamos todos los modelos con junio de 2019 para poder mirar hasta enero sin cambiar los clientes de la comparación. Partimos del mismo baseline con dos rezagos y dos deltas. Probamos más rezagos, resúmenes de 3/4/6 observaciones, tendencias de 4/6 y cambios relativos de 3/4/6. Cada alternativa elige sus hiperparámetros con el mismo presupuesto y AUC de agosto; después se repite con cinco semillas. Congelamos modelos y cortes y comparamos la ganancia en octubre. Buscamos una estrategia histórica reproducible que pueda extenderse cuando haya más meses, sin prometer que más historia siempre mejore.

**Regla de cierre:** ejecutar lo acordado, comparar sobre las mismas filas, publicar también los negativos y distinguir con precisión lo terminado de lo pendiente.
