# Informe de los experimentos de historia 2019 v4 v5 y v6

Secuencia de prompts, resultados verificables y bases para el próximo protocolo

Clara Rodríguez · Corte documental del 13 de noviembre de 2026

El resultado más defendible es una lista de hipótesis con evidencia desigual, no un ganador universal. V4 no promovió ninguna familia bajo su regla original de AUC. V5 priorizó mínimo, rango y promedio por ganancia de agosto; octubre sigue pendiente. V6 priorizó T4, R3 y R4 en agosto y los tres mejoraron también en octubre, con cinco de cinco semillas favorables.

Este informe cubre los tres experimentos recientes: v4, archivado como experimento_2026-11-13; v5, descomposición de historia corta; y v6, profundidad histórica. V1–v3 y C3 son antecedentes y no se suman a sus cifras. Se separan propuesta, ejecución y evaluación posterior. No se ejecutó ningún ajuste nuevo para elaborar el informe.

| Versión | Pregunta ejecutada | Ajustes | Estado |
|---|---|---|---|
| v4 | Familias cortas frente al mismo B0 | 75 | Agosto y octubre |
| v5 | Componentes separados y retiro de deltas | 105 | Agosto completo |
| v6 | Ventanas y representaciones con junio común | 165 | Agosto y octubre |

Son 23 brazos, 230 ajustes Optuna y 115 reentrenamientos por semilla: 345 ajustes registrados. Las evaluaciones de octubre reutilizaron modelos congelados. Duración registrada del desarrollo: v4 2 h 32 min, v5 2 h 26 min, v6 1 h 24 min; no son horas totales de VM ni facturación. No equivalen a 345 modelos independientes ni a 345 pruebas temporales.

### Cómo leer este informe

Primero se reconstruyen los prompts y las reglas. Luego se sintetizan los resultados y las hipótesis. El anexo contiene una ficha y una tabla por cada uno de los 23 brazos, incluidos los controles y los resultados negativos. Los archivos de apoyo conservan parámetros completos, nombres de columnas disponibles, métricas por semilla y hashes de las fuentes.

Las cifras monetarias se expresan en millones de pesos de la regla del concurso, no en ingresos efectivamente cobrados. Ninguna suma de mejoras entre modelos representa una ganancia acumulable. “Superador” siempre debe acompañarse de control, mes, métrica y criterio.

## 1 La secuencia real de prompts

### V4 de una auditoría amplia a cinco brazos

El archivo 01_prompt_original.txt era un protocolo corregido de auditoría y pruebas sintéticas, con cero entrenamientos en esa etapa. Describía además futuras combinaciones, canaritos y una rama W3/W4/W6; mencionaba presupuestos posteriores de 50 trials y 20 semillas. No es evidencia de haber corrido ese alcance. Su filtro de cobertura del 90 % quedó reemplazado por el plan adaptado.

El plan 02_plan_adaptado.md eliminó el filtro automático del 90 %, mantuvo faltantes y limitó la primera comparación a B0, F1, F3, F4a y F4b. Proponía dos mediciones y 75 ajustes, con un techo inicial de dos horas. El contrato definitivo cambió ese presupuesto: cero pilotos dentro de esa corrida, 75 ajustes y techo de 16 horas después de la calibración. El tiempo registrado del trabajador fue 2 h 32 min; no es el tiempo de toda la preparación.

El contrato 03_contrato_ejecutado.json es idéntico al contrato original de la carpeta reproducible y describe la corrida completa_20261111_03. Octubre tuvo un protocolo y autorización posteriores. La fecha de la carpeta 13/11 corresponde a organización y cierre; no debe confundirse con la fecha de inicio de entrenamiento.

### V5 separar lo que estaba combinado

El prompt maestro v5 mantuvo el objetivo de incorporar historia en un proceso reutilizable. Cambió la prioridad económica: AUC siguió eligiendo hiperparámetros, pero la ganancia del ensemble y la estabilidad individual pasaron a decidir qué confirmar. Separó F1 en promedio, mínimo, máximo y rango; agregó el retiro de deltas. Su segunda etapa de historia larga y las pruebas de canaritos, combinaciones y faltantes quedaron condicionadas a contratos propios.

La corrida entrenamiento_20261113_01 ejecutó solamente siete brazos, 105 ajustes y cinco semillas distintas de la usada en Optuna. No ejecutó octubre ni la rama larga del prompt. El estado histórico “sin entrenamientos” de procedencia.json describe cuándo se guardó el prompt, no el cierre actual. El config congelado también conserva un texto de estado antiguo; los campos de autorización, los resultados y el registro de corrida deben leerse juntos.

### V6 hacer explícita la rama de profundidad

El prompt v6 separó la pregunta pendiente y fijó once brazos, 18 contrastes y 165 ajustes. Todos usan junio, incluido B0_J, para disponer de historia desde enero sin cambiar las filas entre controles y candidatos. No dependía de que alguna familia ganara en v5. La corrida completa es v6_20261113_02; el cierre octubre_v6_01 se autorizó y ejecutó después, sin reentrenamiento. El sufijo de corrida no es el número de versión del experimento. El intento v6_20261113_01 se detuvo en preparación por un timeout de despacho SSH, con cero ajustes completados; el incidente y la corrección quedaron registrados antes de la corrida _02.

No se reescriben los prompts históricos para hacerlos coincidir con los resultados. El próximo protocolo deberá conservar esta cadena y establecer una única especificación ejecutable sin estados contradictorios. Fuentes P4, P5 y P6 en el índice final.

## 2 Reglas de datos y significado de las variables

Se usó el mismo archivo analistasr_competencia_2026.csv.gz, identificado por SHA256 459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872. Las etiquetas ya vienen en ese archivo. No se reconstruyeron desde el crudo de Ezequiel. V4/v5 entrenan 507.328 filas de marzo–junio; v6 entrena 128.474 filas de junio. Agosto tiene 131.887 clientes y octubre 135.754. No se hizo sampling ni ponderación adicional de BAJA+2.

Se conservaron 152 variables originales como punto de partida y 129 fuentes candidatas para construir historia, revisadas semánticamente. No son 129 variables finales: las derivaciones y la depuración cambian el número de columnas. Identificador, mes y clase quedan fuera de los predictores. Las listas ordenadas de columnas de los 23 brazos se adjuntan en evidencia.json; las de v4 se recuperaron en la auditoría complementaria y se contrastan con el protocolo de octubre.

| Mes | Variables saneadas como nulas |
|---|---|
| Abril 2019 | ctarjeta_visa_debitos_automaticos; mttarjeta_visa_debitos_automaticos |
| Mayo 2019 | mrentabilidad; mrentabilidad_annual; mcomisiones; mactivos_margen; mpasivos_margen; mcomisiones_otras; ccomisiones_otras |

Son nueve pares variable–mes, no una garantía de ausencia de otras anomalías. Se aplican antes de generar historia y de la misma forma a todos los brazos. Se preservan nulos y negativos válidos; los no finitos pasan a nulos. No se convierte automáticamente una ausencia de producto en cero. Los rezagos unen cliente y mes calendario exactos; una fila anterior disponible no sustituye un mes faltante.

| Derivado | Definición y política |
|---|---|
| Lag k | Valor del mismo cliente k meses antes. Si falta la fila o el valor, NA. |
| Delta k | Actual menos lag k. Requiere ambos extremos; no todos los meses intermedios. |
| Media mínimo máximo rango | Sobre W observaciones consecutivas, incluida la actual. Rango = máximo − mínimo. Exigen ventana completa no nula. |
| Cambio relativo | (actual − referencia) / abs(referencia). Referencias: media W, lag1 y lag W−1. Ventana completa y referencia distinta de cero; en otro caso NA. |
| Tendencia | Pendiente OLS contra tiempo 0 a W−1; cambio por mes. W4 y W6. Con tres puntos completos equivale a delta2/2. |
| Ranking mensual | Rango promedio entre clientes del mismo mes dividido por cantidad no nula. Incluye ceros y negativos; nulos permanecen nulos. |

Depuración solo con entrenamiento: vacías, constantes incluyendo el patrón de nulos y duplicadas exactas en la representación del modelo. Se preserva un valor finito más nulos si ese patrón varía. V6 congela pares fuente–fórmula comunes dentro de S, T y R para comparar ventanas; no elimina clientes sin historia completa. Más ventana implica también menos cobertura, un componente real del tratamiento.

## 3 Qué optimizamos y qué medimos

Todos los brazos son LightGBM binarios con boosting por árboles. Entrenamiento positivo = BAJA+1 o BAJA+2; validación AUC positiva = BAJA+2. El score sirve para ordenar clientes y no es una probabilidad calibrada de BAJA+2. No se usaron canaritos, pesos extra, nuevos algoritmos ni bagging externo de filas en estas tres corridas.

| Hiperparámetro | Espacio común |
|---|---|
| num_leaves | 16–128 entero logarítmico |
| learning_rate | 0,01–0,1 logarítmico |
| min_data_in_leaf | 100–2.000 entero logarítmico |
| feature_fraction | 0,3–1,0 |
| bagging_fraction | 0,5–1,0 |

Cada brazo recibió Optuna TPE con 10 trials, 5 iniciales, sampler seed 20261111 y modelo seed 101. Máximo 1.500 árboles, early stopping de 100 por AUC de agosto; se elige el mayor AUC y, ante empate, el primer trial. Fijos explícitos: bagging_freq=1, cuatro hilos, deterministic=true, force_col_wise=true, objective=binary, metric=auc y feature_pre_filter=false. El runner fija además las semillas internas de LightGBM. Los parámetros no explicitados dependen de la versión registrada y deben exportarse en el próximo protocolo.

V4 evaluó 101, 211, 307, 401 y 503: la semilla 101 ya había participado de Optuna. V5/v6 corrigen esa dependencia usando 211, 307, 401, 503 y 601. Tras Optuna se congelan hiperparámetros y árboles, sin early stopping nuevo por semilla. El ensemble promedia scores alineados por cliente. Su ganancia no es el promedio de las ganancias individuales. Cada brazo se optimiza por separado, aunque dos búsquedas pueden elegir los mismos valores: R3 y R4 comparten los cinco hiperparámetros, con 220 y 250 árboles respectivamente.

### La regla económica exacta

Ganancia = 1.072.500 × aciertos BAJA+2 − 27.500 × otros contactos. Equivalentemente, con k contactos y h aciertos: G = 1.100.000 × h − 27.500 × k. El premio ya es neto: no se descuenta otra vez el costo a un acierto.

En agosto se ordena por score descendente y cliente ascendente. Se maximiza la media móvil centrada completa de 2.001 posiciones de la curva acumulada; empate, menor corte. Se guardan máximo suavizado, ganancia puntual en ese corte y proporción. El máximo suavizado es una medida de desarrollo optimizada en el mismo mes, no una estimación independiente de campaña futura.

En octubre se aplica floor(proporción de agosto × 135.754), sin buscar otro corte. V4 aplica la proporción del ensemble a todas las semillas del brazo. V6 congela la proporción propia de cada semilla y del ensemble. Esta diferencia impide tratar sus victorias por semilla como una comparación idéntica entre versiones. Agosto y octubre además usan ganancias suavizadas y puntuales, respectivamente.

El conteo 4/5 es una regla de asignación de cómputo, no una prueba de significación. Repetir semillas mide variabilidad del entrenamiento; no añade meses independientes. Reoptimizar por brazo con igual presupuesto mide una receta más su ajuste, no un efecto puro de variables con hiperparámetros fijos.

## 4 Qué modelos fueron superadores y en qué sentido

La tabla siguiente compara cada candidato con el control de su propia versión. Δ agosto corresponde al ensemble suavizado; Δ octubre al ensemble en el corte congelado. Las victorias son diferencias individuales positivas pareadas. M significa millones de pesos. Un control no compite contra sí mismo.

| Brazo | Δ ago M | Gana ago | Δ oct M | Gana oct | Regla original |
|---|---|---|---|---|---|
| v4 F1 | +3,1975 | 2/5 | +12,1550 | 2/5 | No |
| v4 F3 | +2,7326 | 4/5 | +7,1500 | 4/5 | No |
| v4 F4a | -7,5050 | 0/5 | +10,2575 | 5/5 | No |
| v4 F4b | -11,1762 | 0/5 | -7,8925 | 0/5 | No |
| v5 L | -1,6601 | 1/5 | Pendiente | — | No |
| v5 P | +3,9866 | 4/5 | Pendiente | — | Sí |
| v5 MIN | +5,1097 | 5/5 | Pendiente | — | Sí |
| v5 MAX | +2,5144 | 2/5 | Pendiente | — | No |
| v5 RANGO | +4,1824 | 5/5 | Pendiente | — | Sí |
| v5 F1 | +1,4774 | 1/5 | Pendiente | — | No |
| v6 L4 | +0,1131 | 1/5 | +4,3175 | 2/5 | No |
| v6 L6 | +2,1808 | 3/5 | +6,3525 | 3/5 | No |
| v6 S3 | +0,6774 | 2/5 | +6,9300 | 4/5 | No |
| v6 S4 | -2,9781 | 1/5 | +6,5175 | 2/5 | No |
| v6 S6 | -7,0824 | 0/5 | +6,7925 | 2/5 | No |
| v6 T4 | +6,2295 | 5/5 | +6,8200 | 5/5 | Sí |
| v6 T6 | -4,7444 | 0/5 | +1,8975 | 4/5 | No |
| v6 R3 | +5,4535 | 5/5 | +11,6875 | 5/5 | Sí |
| v6 R4 | +4,7587 | 4/5 | +15,1250 | 5/5 | Sí |
| v6 R6 | -3,5055 | 1/5 | +16,0600 | 4/5 | No |

V4: ningún candidato cumplió su regla de AUC. F1 dio el mayor ensemble de octubre, pero solo ganó en 2/5 semillas; F3 mejoró económicamente en ambos meses con 4/5; F4a pasó de perder en agosto a ganar en las cinco semillas de octubre. No se cambia retrospectivamente la selección original de B0.

V5: MIN, RANGO y P cumplieron la regla económica de agosto. El paquete F1 no la cumplió aunque su ensemble subió. Ninguna variante mejoró el AUC medio individual contra B0; eso no impide una mejora económica. No se conocen ganancias de octubre de v5 en la evidencia versionada.

V6: T4, R3 y R4 cumplieron la regla de agosto y ganaron en 5/5 semillas de octubre. R6 logró el mayor ensemble de octubre, pero había perdido en agosto y no era elegible. No conviene declararlo ganador robusto por elegir después el mes favorable. R3 superó a R4 en ganancia del ensemble de agosto; R4 lo superó en octubre. La evidencia no identifica una longitud óptima universal.

## 5 Lectura de los resultados y límites de atribución

### Qué aporta evidencia y qué sigue siendo una hipótesis

Los cambios relativos muestran una señal útil: F3 en v4 y R3/R4 en v6 mejoraron la ganancia del ensemble en agosto y octubre. No son réplicas exactas: cambian calendario, fuentes efectivamente retenidas, hiperparámetros y semillas. T4 aporta una segunda familia con señal favorable en v6. MIN y RANGO son candidatos fuertes de agosto, pero aún no tienen cierre de octubre en v5.

F1 de v5 combina cuatro componentes que por separado dieron ganancias positivas del ensemble, y sin embargo su mejora fue menor y poco estable. Posibles mecanismos son redundancia, dilución de variables útiles con feature_fraction, interacción de particiones, presupuesto de búsqueda escaso y azar del entrenamiento. Los datos no permiten elegir una explicación causal. Para demostrar interacción hacen falta el conjunto, sus componentes y controles reoptimizados bajo el mismo protocolo.

La hipótesis de Ale de que los lags podrían bastar fue probada parcialmente por L en v5. Retirar deltas empeoró agosto. Eso respalda conservarlos en ese escenario; no demuestra que los deltas siempre sean necesarios ni contradice que un árbol más profundo pueda reconstruir diferencias. La búsqueda tiene solo diez trials por brazo.

El ranking actual F4a fue fuerte en octubre pero débil en agosto. Agregar su historia F4b fue desfavorable frente a B0 y frente a F4a en octubre. Conviene distinguir ranking del nivel actual, ranking previo de montos e historia del ranking: no son la misma intervención. La rama de rankings sigue abierta como hipótesis específica, no como componente obligatorio del híbrido.

### Por qué no se comparan millones entre versiones como una carrera

B0 de v4 ganó 277,1450 M en octubre y B0_J de v6 261,8550 M. Ese contraste cambia cuatro meses de entrenamiento por uno, columnas, ajuste y política de cortes individuales. No mide cuánto “pierde la historia larga”. Cada mejora debe atribuirse contra su propio control. Tampoco se suman +15,125 M de R4 y +6,820 M de T4 para anticipar una combinación.

Octubre ya había sido observado incluso antes de este ciclo de análisis. Congelar cortes protege contra optimizarlos con sus etiquetas, pero no devuelve independencia a un período conocido. Los nuevos híbridos tendrán evidencia exploratoria. Declarar esta condición es compatible con usar octubre como comparación económica solicitada por Ale.

Los resultados de cinco semillas no justifican intervalos de precisión extrema ni afirmaciones de significancia por sí solos. No se calculó aquí un bootstrap nuevo porque requiere contribuciones o predicciones privadas, no solamente las métricas agregadas de Git. Tampoco se reprodujo todo el entrenamiento desde cero en otra máquina.

## 6 Hipótesis de mejora derivadas de la tutoría

La tutoría compartida por Clara orienta el diseño; el resumen siguiente es una paráfrasis, no una cita literal verificada contra una grabación. La consigna publicada fija 2019, LightGBM, entrenamiento marzo–junio sin sampling, BAJA+1 y BAJA+2 combinadas, AUC en agosto para optimizar y ganancia en octubre. Ale permite adaptar el baseline a la pregunta. La rama junio es una adaptación explícita.

| Prioridad | Hipótesis y contraste | Razón y límite |
|---|---|---|
| Primera | Completar octubre de los siete brazos de v5 | Cerrar evidencia ya producida, sin elegir solo MIN o RANGO después de ver resultados. No implica reentrenar. |
| Primera | R4 + T4 frente a R4 y T4 | La tendencia resume trayectoria y los relativos escala. Ambos funcionaron; complementariedad todavía no probada. |
| Primera | R4 + relativos simétricos frente a R4 | Fórmula acotada de Ezequiel. Probar el paquete, sin atribuir su efecto solo a la fórmula si cambia cobertura. |
| Segunda | Relativos con máscara mínima frente a máscara W completa | Ale busca información útil; exigir meses no utilizados puede descartar señal. Mantener fórmula y fuentes para aislar faltantes. |
| Segunda | MIN o RANGO añadidos al control elegido | Señal consistente en agosto v5. Rehacer sobre junio si el control es de junio; no reutilizar marzo–junio. |
| Posterior | Ranking previo de montos y su historia | Responde al desplazamiento de escalas discutido por Ale. Limitar a montos y congelar universo mensual. |
| Posterior | Conjunto completo frente a filtrado con canaritos | Selección solo en entrenamiento, sin agosto en importancia, umbral ni early stopping del filtro. Reoptimizar ambos. |
| Posterior | Quiebres y caídas de actividad | Inspiración ACH_Q de Ezequiel; interpretable. Separar de tarjetas y pesos para saber qué aportó. |
| Posterior | Ventana de entrenamiento alternativa dentro de 2019 | Evaluar estabilidad temporal y disponibilidad de historia con control idéntico. No usar 2020. |

Ale advirtió que más variables cambia el efecto de feature_fraction y exige reoptimizar. Por eso no heredamos los parámetros ganadores de R4 para evaluar una unión más grande. También señaló que medias, extremos y tendencias facilitan a los árboles representar historia. El 3–5 % fue una magnitud interesante, no un umbral garantizado ni una exigencia para ocultar resultados negativos.

Desvío estándar, varianza y promedios ponderados quedan en menor prioridad: en la tutoría se cuestionó su interpretabilidad y se prefirió estudiar rango y tendencias. Esto no demuestra que nunca funcionen. Tampoco se incorpora peso extra para BAJA+2, conforme a la decisión explícita de Clara.

## 7 Qué tomar de la evaluación de Ezequiel

La versión revisada es 770abaa9cad412647211c255360cb6dfe364e697. Sus aportes más útiles son comparación pareada por cliente y semilla, evaluación sobre varios meses con control temporal equivalente, bootstrap de clientes y comprobación de huellas de configuración y predicciones. No se copiaron sus ganancias ni se reentrenó su pipeline.

Su bloque R calcula (actual − previo) / (abs(actual) + abs(previo)), para lag1 y lag2. Ambos valores cero producen cero; un faltante produce NA. El resultado queda entre −1 y 1. Nuestro cambio relativo divide por abs(referencia), conserva NA para denominador cero y exige W completa. Comparar ambas recetas tal cual cambia fórmula, referencias y cobertura; para atribuir solo a la fórmula hay que igualar los pares y la máscara primero.

Su evaluación usa una banda de 3.000–6.000 contactos y promedia ganancia entre cortes, meses y semillas. El bootstrap remuestrea 2.000 veces clientes con sus contribuciones agregadas, conservando el vínculo de un cliente entre meses. Combina su error con la variación entre semillas. Es una herramienta más elaborada, no una prueba de que una mejora generalice a meses nuevos ni una corrección por búsqueda repetida.

La regla de incorporación de cambios usa diferencia media positiva y al menos 3/5 semillas, sin exigir que el intervalo excluya cero. Incluye octubre: junio–octubre para ramas simples y septiembre–octubre para ramas que seleccionaron configuraciones. El README declara exploración. Ese uso no conserva octubre como un test independiente; no debe describirse como tal.

Además, PAQ_P3 usa peso 3 para BAJA+2 y el control peso 1. La mejora del paquete no puede atribuirse solo a las variables. Sus tablas de +8,9986 M/mes contra AC y +12,5970 M/mes contra A-consigna corresponden a la referencia histórica PAQ_P3; el MAIN actual declara otros hiperparámetros. Antes de comparar hay que reconciliar configuración y tabla, y usar el mismo dataset, población y calendario que nosotros.

### Cómo adaptar el bootstrap sin exagerar su alcance

Para nuestro próximo experimento propongo un análisis pareado de diferencias de contribución económica por cliente a los cortes congelados, manteniendo juntos los meses del mismo cliente si se agrega una rama temporal. Debe registrarse antes la población de remuestreo, número de réplicas, semilla, normalización, intervalo y tratamiento de semillas. No copiar automáticamente la suma de errores ni suponer que el intervalo corresponde al ensemble si se construye a partir de ganancias individuales.

Un bootstrap de contribuciones con selección fija describe incertidumbre condicional a los modelos y políticas ya elegidos. No vuelve a entrenar, no incluye toda la incertidumbre de Optuna y no reproduce por sí solo el cambio de ranking y del top-k al cambiar la población. Si se busca ese segundo estimando, se requiere un remuestreo que recalcule selección y un protocolo distinto. Esta distinción debe estar escrita antes de mostrar un “IC 95 %”.

## 8 Base recomendada para el próximo prompt

Recomiendo separar el cierre pendiente de v5 del nuevo entrenamiento. Después, formular un núcleo pequeño con controles suficientes para interpretar el híbrido. Esta propuesta amplía los tres brazos tentativos de la presentación anterior: agrega B0_J, R3 y T4 como referencias explícitas. Su presupuesto sería 90 ajustes, no 45. No se autoriza ni se ejecuta por incluirla en este informe.

| Brazo propuesto | Contenido | Contraste principal |
|---|---|---|
| B0_J | Baseline reconstruido en junio | Ancla común |
| R3 | B0_J + relativos W3 | R3 contra B0_J |
| R4 | B0_J + relativos W4 | R4 contra B0_J y R3 |
| T4 | B0_J + tendencia W4 | T4 contra B0_J |
| H_T | Unión R4 y T4, sin duplicar B0_J | H_T contra R4 y T4 |
| H_S | R4 + relativos simétricos lag1 y lag2 | H_S contra R4 |

R3 se conserva porque ganó más que R4 en agosto; no se lo elimina solo porque R4 obtuvo mejor octubre. H_T probaría si juntar familias mejora el rendimiento, sin presuponer aditividad. H_S prueba un paquete adicional; una atribución aislada a fórmula o faltantes exige una comparación posterior diseñada para ese propósito.

Condiciones propuestas: junio para todos; agosto para Optuna; octubre para comparación económica exploratoria. Mismo dataset, filas, fuentes, saneamiento y política de nulos. Diez trials propios más cinco semillas nuevas respecto de optimización por cada brazo. Primero auditoría sin entrenamiento; después 6 × (10 + 5) = 90 ajustes. Un aumento posterior de semillas debe incluir controles y candidatos pareados, con presupuesto separado.

Las uniones deben partir de columnas congeladas y respetar prioridad del control al eliminar duplicados. Si la fórmula simétrica altera ceros y cobertura, documentar ambos cambios; no introducir simultáneamente ponderación, imputación, otro calendario o selección de fuentes por octubre. No mezclar medias ponderadas, canaritos y tarjetas en la misma primera prueba.

La variable principal será la ganancia del ensemble bajo una política de contactos predefinida. Reportar adicionalmente ganancia individual, AUC, deltas pareados, victorias, tamaño, cobertura y costo. Como diagnóstico, puede añadirse una comparación a igual presupuesto de contactos fijado en agosto para todos: separa parte del efecto del ranking de la política de corte. Debe distinguirse de la métrica principal con corte propio.

Antes de correr, preregistrar contrastes y una mejora mínima económicamente relevante acordada con Ale. No inventar retrospectivamente 5 % como condición. Si se exige inferencia estadística, fijar familia de contrastes, método y corrección por multiplicidad, reconociendo los períodos ya usados. Una regla económica favorable no es una prueba de generalización.

## 9 Requisitos de reproducción y cierre

La base del próximo prompt debe ser un contrato ejecutable versionado y validado contra su descripción, no una acumulación de instrucciones de distintas épocas. El mismo identificador debe vincular prompt, autorización, código, dataset, entorno, matrices, modelos, políticas y resultados. Ningún cambio posterior puede entrar silenciosamente en una corrida empezada.

| Hito | Evidencia exigida para darlo por terminado |
|---|---|
| Diseño congelado | Pregunta, brazos, fórmulas, máscaras, fuentes, meses, métricas, semillas, contrastes, presupuesto y criterio de cierre. Hash del contrato y commit. |
| Auditoría real | Claves únicas, tipos, clases, roturas, conteos de nulos por causa, filas y orden, nombres y orden de columnas, aliases, dimensiones y hashes de matrices. |
| Entorno | Python, bibliotecas y sistema efectivamente usados; configuración resuelta de LightGBM; archivos de dependencias reproducibles. |
| Ajustes | Los 10 trials de cada brazo, estado, parámetros, AUC, árboles y tiempos; selección comprobable del mejor; modelos por semilla con hash. |
| Congelamiento | Modelos, predicciones de agosto y proporciones por semilla y ensemble. Validación del hash antes de abrir octubre. |
| Evaluación | Regenerar agosto desde modelos, comparar predicciones; puntuar octubre sin reentrenar; comprobar cortes y aciertos con la identidad económica. |
| Respaldo | Git público con agregados y código; almacenamiento privado duradero de dataset, modelos y predicciones con ubicación, hashes y prueba de recuperación. |
| Reproducción independiente | Reconstruir desde el mismo dataset en otra máquina y comparar columnas, trials, árboles, predicciones y métricas. Registrar tolerancias antes de comparar. |

La auditoría complementaria de v4 cerró tres dudas: recuperó calibrar.py con el hash original, confirmó que los 25 modelos ya tenían SHA256 y recuperó las cinco listas ordenadas de columnas de octubre con igualdad del hash del protocolo completo. Por lo tanto, las afirmaciones anteriores de ausencia de esos elementos quedaron superadas. Siguen pendientes la recuperación y respaldo privado verificable de los archivos de modelos, evidencia histórica de Python/scikit-learn y una réplica integral del entrenamiento. No se debe afirmar “reproducido” por pasar un manifiesto.

V5/v6 guardan entorno, parámetros, columnas y hashes privados más completos. V6 verificó 55 predicciones de agosto con error máximo cero antes de octubre. Eso valida la reutilización de esos modelos y matrices; no equivale a reproducir los 165 ajustes en otro equipo. La existencia de un hash tampoco acredita que el artefacto privado sea recuperable hoy.

Para el próximo experimento: pruebas de huecos temporales, nulos, ceros, signos, fórmulas, selección solo en entrenamiento, empates, alineación de clientes, corte, reinicio y bloqueo de octubre; supervisor con límite medido y apagado verificado; recuperación de agregados antes del apagado. No publicar datos individuales ni credenciales. El cierre debe informar completos, parciales y pendientes, sin ocultar negativos.

## Anexo de modelos 1 a 2

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v4 B0

| Característica | Valor observado |
|---|---|
| Representación | Actuales + lag1/2 + delta1/2; control de historia corta. |
| Diseño | 652 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (101, 211, 307, 401, 503). Trial elegido 3 (índice desde 0); 224 árboles; AUC Optuna 0,915360. |
| Hiperparámetros | num_leaves=81; min_data_in_leaf=1158; learning_rate=0,01926286; feature_fraction=0,85225954; bagging_fraction=0,66572713. |
| Agosto ensemble | AUC 0,914415; G suavizada 206,9278; Δ 0,0000; G puntual 209,6050. |
| Agosto corte | 3578 contactos (2,7129 %); 280 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 205,3192; Δ medio 0,0000; DE Δ 0,0000; victorias no aplica. Δ AUC medio 0,000000. |
| Octubre ensemble | AUC 0,925106; G 277,1450; Δ 0,0000 (0,000 %); 3682 contactos y 344 aciertos. |
| Octubre semillas | G media 280,0050; Δ medio 0,0000; DE Δ 0,0000; victorias no aplica. |
| Decisión y fuente | Control; no se aplica promoción. Fuente V4/B0; características comunes en secciones 2 y 3. |

### v4 F1

| Característica | Valor observado |
|---|---|
| Representación | B0 + promedio, mínimo, máximo y rango W3. |
| Diseño | 1156 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (101, 211, 307, 401, 503). Trial elegido 5 (índice desde 0); 183 árboles; AUC Optuna 0,914810. |
| Hiperparámetros | num_leaves=85; min_data_in_leaf=1601; learning_rate=0,03492470; feature_fraction=0,37349908; bagging_fraction=0,78174487. |
| Agosto ensemble | AUC 0,914789; G suavizada 210,1254; Δ +3,1975; G puntual 209,1375. |
| Agosto corte | 4275 contactos (3,2414 %); 297 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 204,7485; Δ medio -0,5707; DE Δ 2,2628; victorias 2/5. Δ AUC medio -0,000221. |
| Octubre ensemble | AUC 0,923743; G 289,3000; Δ +12,1550 (+4,386 %); 4400 contactos y 373 aciertos. |
| Octubre semillas | G media 280,2800; Δ medio +0,2750; DE Δ 4,0715; victorias 2/5. |
| Decisión y fuente | No cumple promoción por AUC. Ganancia económica informada descriptivamente. Fuente V4/F1; características comunes en secciones 2 y 3. |

## Anexo de modelos 3 a 4

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v4 F3

| Característica | Valor observado |
|---|---|
| Representación | B0 + relativos frente a media W3, lag1 y lag2. |
| Diseño | 1030 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (101, 211, 307, 401, 503). Trial elegido 5 (índice desde 0); 145 árboles; AUC Optuna 0,913849. |
| Hiperparámetros | num_leaves=85; min_data_in_leaf=1601; learning_rate=0,03492470; feature_fraction=0,37349908; bagging_fraction=0,78174487. |
| Agosto ensemble | AUC 0,913837; G suavizada 209,6605; Δ +2,7326; G puntual 211,6950. |
| Agosto corte | 4102 contactos (3,1102 %); 295 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 208,2374; Δ medio +2,9183; DE Δ 3,7060; victorias 4/5. Δ AUC medio -0,001060. |
| Octubre ensemble | AUC 0,924758; G 284,2950; Δ +7,1500 (+2,580 %); 4222 contactos y 364 aciertos. |
| Octubre semillas | G media 283,1950; Δ medio +3,1900; DE Δ 5,8518; victorias 4/5. |
| Decisión y fuente | No cumple promoción por AUC. Ganancia económica informada descriptivamente. Fuente V4/F3; características comunes en secciones 2 y 3. |

### v4 F4a

| Característica | Valor observado |
|---|---|
| Representación | B0 + ranking transversal actual de las fuentes revisadas. |
| Diseño | 778 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (101, 211, 307, 401, 503). Trial elegido 7 (índice desde 0); 459 árboles; AUC Optuna 0,914427. |
| Hiperparámetros | num_leaves=38; min_data_in_leaf=808; learning_rate=0,01473136; feature_fraction=0,81758007; bagging_fraction=0,88667233. |
| Agosto ensemble | AUC 0,913799; G suavizada 199,4228; Δ -7,5050; G puntual 201,5200. |
| Agosto corte | 3992 contactos (3,0268 %); 283 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 199,0911; Δ medio -6,2280; DE Δ 2,5784; victorias 0/5. Δ AUC medio -0,000391. |
| Octubre ensemble | AUC 0,923777; G 287,4025; Δ +10,2575 (+3,701 %); 4109 contactos y 364 aciertos. |
| Octubre semillas | G media 286,5225; Δ medio +6,5175; DE Δ 4,3027; victorias 5/5. |
| Decisión y fuente | No cumple promoción por AUC. Ganancia económica informada descriptivamente. Fuente V4/F4a; características comunes en secciones 2 y 3. |

## Anexo de modelos 5 a 6

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v4 F4b

| Característica | Valor observado |
|---|---|
| Representación | F4a + lag1/2, delta1/2, media, mínimo, máximo y rango W3 del ranking. |
| Diseño | 1786 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (101, 211, 307, 401, 503). Trial elegido 3 (índice desde 0); 290 árboles; AUC Optuna 0,912574. |
| Hiperparámetros | num_leaves=81; min_data_in_leaf=1158; learning_rate=0,01926286; feature_fraction=0,85225954; bagging_fraction=0,66572713. |
| Agosto ensemble | AUC 0,911733; G suavizada 195,7516; Δ -11,1762; G puntual 191,3450. |
| Agosto corte | 5722 contactos (4,3386 %); 317 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 196,0183; Δ medio -9,3009; DE Δ 4,2432; victorias 0/5. Δ AUC medio -0,002862. |
| Octubre ensemble | AUC 0,921956; G 269,2525; Δ -7,8925 (-2,848 %); 5889 contactos y 392 aciertos. |
| Octubre semillas | G media 272,9925; Δ medio -7,0125; DE Δ 6,3857; victorias 0/5. |
| Decisión y fuente | No cumple promoción por AUC. Ganancia económica informada descriptivamente. Fuente V4/F4b; características comunes en secciones 2 y 3. |

### v5 B0

| Característica | Valor observado |
|---|---|
| Representación | Actuales + lag1/2 + delta1/2; control recalculado de v5. |
| Diseño | 652 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 3 (índice desde 0); 224 árboles; AUC Optuna 0,915360. |
| Hiperparámetros | num_leaves=81; min_data_in_leaf=1158; learning_rate=0,01926286; feature_fraction=0,85225954; bagging_fraction=0,66572713. |
| Agosto ensemble | AUC 0,913983; G suavizada 205,0447; Δ 0,0000; G puntual 204,5725. |
| Agosto corte | 3761 contactos (2,8517 %); 280 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 204,0623; Δ medio 0,0000; DE Δ 0,0000; victorias no aplica. Δ AUC medio 0,000000. |
| Octubre | Pendiente. No se extrapola la ganancia de agosto ni se imputa cero. |
| Decisión y fuente | Control; no se aplica promoción. Fuente V5/B0; características comunes en secciones 2 y 3. |

## Anexo de modelos 7 a 8

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v5 L

| Característica | Valor observado |
|---|---|
| Representación | Actuales + lag1/2; se retiran los deltas. |
| Diseño | 400 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 3 (índice desde 0); 199 árboles; AUC Optuna 0,912702. |
| Hiperparámetros | num_leaves=81; min_data_in_leaf=1158; learning_rate=0,01926286; feature_fraction=0,85225954; bagging_fraction=0,66572713. |
| Agosto ensemble | AUC 0,912833; G suavizada 203,3846; Δ -1,6601; G puntual 204,7650. |
| Agosto corte | 3954 contactos (2,9980 %); 285 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 202,7810; Δ medio -1,2814; DE Δ 2,1982; victorias 1/5. Δ AUC medio -0,001040. |
| Octubre | Pendiente. No se extrapola la ganancia de agosto ni se imputa cero. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V5/L; características comunes en secciones 2 y 3. |

### v5 P

| Característica | Valor observado |
|---|---|
| Representación | B0 + promedio W3. |
| Diseño | 778 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 3 (índice desde 0); 246 árboles; AUC Optuna 0,914085. |
| Hiperparámetros | num_leaves=81; min_data_in_leaf=1158; learning_rate=0,01926286; feature_fraction=0,85225954; bagging_fraction=0,66572713. |
| Agosto ensemble | AUC 0,914013; G suavizada 209,0313; Δ +3,9866; G puntual 212,3000. |
| Agosto corte | 3960 contactos (3,0026 %); 292 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 207,8427; Δ medio +3,7803; DE Δ 3,2452; victorias 4/5. Δ AUC medio -0,000167. |
| Octubre | Pendiente. No se extrapola la ganancia de agosto ni se imputa cero. |
| Decisión y fuente | Cumple la regla económica de agosto; no es significancia estadística. Fuente V5/P; características comunes en secciones 2 y 3. |

## Anexo de modelos 9 a 10

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v5 MIN

| Característica | Valor observado |
|---|---|
| Representación | B0 + mínimo W3. |
| Diseño | 778 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 7 (índice desde 0); 432 árboles; AUC Optuna 0,913944. |
| Hiperparámetros | num_leaves=108; min_data_in_leaf=524; learning_rate=0,01011503; feature_fraction=0,45934084; bagging_fraction=0,51241459. |
| Agosto ensemble | AUC 0,913405; G suavizada 210,1544; Δ +5,1097; G puntual 211,1725. |
| Agosto corte | 4161 contactos (3,1550 %); 296 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 209,0762; Δ medio +5,0139; DE Δ 2,9235; victorias 5/5. Δ AUC medio -0,000425. |
| Octubre | Pendiente. No se extrapola la ganancia de agosto ni se imputa cero. |
| Decisión y fuente | Cumple la regla económica de agosto; no es significancia estadística. Fuente V5/MIN; características comunes en secciones 2 y 3. |

### v5 MAX

| Característica | Valor observado |
|---|---|
| Representación | B0 + máximo W3. |
| Diseño | 778 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 5 (índice desde 0); 124 árboles; AUC Optuna 0,913286. |
| Hiperparámetros | num_leaves=85; min_data_in_leaf=1601; learning_rate=0,03492470; feature_fraction=0,37349908; bagging_fraction=0,78174487. |
| Agosto ensemble | AUC 0,913880; G suavizada 207,5591; Δ +2,5144; G puntual 204,4900. |
| Agosto corte | 3844 contactos (2,9146 %); 282 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 204,5997; Δ medio +0,5374; DE Δ 3,9071; victorias 2/5. Δ AUC medio -0,000486. |
| Octubre | Pendiente. No se extrapola la ganancia de agosto ni se imputa cero. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V5/MAX; características comunes en secciones 2 y 3. |

## Anexo de modelos 11 a 12

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v5 RANGO

| Característica | Valor observado |
|---|---|
| Representación | B0 + máximo menos mínimo W3. |
| Diseño | 778 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 8 (índice desde 0); 274 árboles; AUC Optuna 0,914009. |
| Hiperparámetros | num_leaves=105; min_data_in_leaf=1015; learning_rate=0,01860732; feature_fraction=0,57541938; bagging_fraction=0,50776066. |
| Agosto ensemble | AUC 0,913322; G suavizada 209,2271; Δ +4,1824; G puntual 207,0200. |
| Agosto corte | 4192 contactos (3,1785 %); 293 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 207,5209; Δ medio +3,4585; DE Δ 2,2995; victorias 5/5. Δ AUC medio -0,001049. |
| Octubre | Pendiente. No se extrapola la ganancia de agosto ni se imputa cero. |
| Decisión y fuente | Cumple la regla económica de agosto; no es significancia estadística. Fuente V5/RANGO; características comunes en secciones 2 y 3. |

### v5 F1

| Característica | Valor observado |
|---|---|
| Representación | B0 + promedio, mínimo, máximo y rango W3. |
| Diseño | 1156 columnas; train marzo–junio; 507.328 filas; control B0. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 5 (índice desde 0); 183 árboles; AUC Optuna 0,914810. |
| Hiperparámetros | num_leaves=85; min_data_in_leaf=1601; learning_rate=0,03492470; feature_fraction=0,37349908; bagging_fraction=0,78174487. |
| Agosto ensemble | AUC 0,914267; G suavizada 206,5221; Δ +1,4774; G puntual 205,1775. |
| Agosto corte | 4299 contactos (3,2596 %); 294 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 202,9868; Δ medio -1,0755; DE Δ 1,9014; victorias 1/5. Δ AUC medio -0,000347. |
| Octubre | Pendiente. No se extrapola la ganancia de agosto ni se imputa cero. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V5/F1; características comunes en secciones 2 y 3. |

## Anexo de modelos 13 a 14

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v6 B0_J

| Característica | Valor observado |
|---|---|
| Representación | Actuales + lag1/2 + delta1/2; control depurado en junio. |
| Diseño | 634 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 7 (índice desde 0); 320 árboles; AUC Optuna 0,906745. |
| Hiperparámetros | num_leaves=38; min_data_in_leaf=808; learning_rate=0,01473136; feature_fraction=0,81758007; bagging_fraction=0,88667233. |
| Agosto ensemble | AUC 0,905565; G suavizada 191,5266; Δ 0,0000; G puntual 192,8025. |
| Agosto corte | 4429 contactos (3,3582 %); 286 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 190,7026; Δ medio 0,0000; DE Δ 0,0000; victorias no aplica. Δ AUC medio 0,000000. |
| Octubre ensemble | AUC 0,917038; G 261,8550; Δ 0,0000 (0,000 %); 4558 contactos y 352 aciertos. |
| Octubre semillas | G media 266,0075; Δ medio 0,0000; DE Δ 0,0000; victorias no aplica. |
| Decisión y fuente | Control; no se aplica promoción. Fuente V6/B0_J; características comunes en secciones 2 y 3. |

### v6 L4

| Característica | Valor observado |
|---|---|
| Representación | B0_J + lag3; historia directa de hasta cuatro observaciones. |
| Diseño | 760 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 8 (índice desde 0); 149 árboles; AUC Optuna 0,905800. |
| Hiperparámetros | num_leaves=50; min_data_in_leaf=1095; learning_rate=0,02841852; feature_fraction=0,30629135; bagging_fraction=0,64149986. |
| Agosto ensemble | AUC 0,903174; G suavizada 191,6397; Δ +0,1131; G puntual 191,4825. |
| Agosto corte | 4237 contactos (3,2126 %); 280 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 186,3560; Δ medio -4,3466; DE Δ 3,3367; victorias 1/5. Δ AUC medio -0,003427. |
| Octubre ensemble | AUC 0,919003; G 266,1725; Δ +4,3175 (+1,649 %); 4361 contactos y 351 aciertos. |
| Octubre semillas | G media 265,6885; Δ medio -0,3190; DE Δ 4,7505; victorias 2/5. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V6/L4; características comunes en secciones 2 y 3. |

## Anexo de modelos 15 a 16

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v6 L6

| Característica | Valor observado |
|---|---|
| Representación | L4 + lag4 y lag5; hasta seis observaciones. |
| Diseño | 1012 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 5 (índice desde 0); 135 árboles; AUC Optuna 0,904767. |
| Hiperparámetros | num_leaves=85; min_data_in_leaf=1601; learning_rate=0,03492470; feature_fraction=0,37349908; bagging_fraction=0,78174487. |
| Agosto ensemble | AUC 0,906836; G suavizada 193,7074; Δ +2,1808; G puntual 193,9300. |
| Agosto corte | 4748 contactos (3,6001 %); 295 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 190,9064; Δ medio +0,2038; DE Δ 3,1494; victorias 3/5. Δ AUC medio -0,000322. |
| Octubre ensemble | AUC 0,918758; G 268,2075; Δ +6,3525 (+2,426 %); 4887 contactos y 366 aciertos. |
| Octubre semillas | G media 266,5300; Δ medio +0,5225; DE Δ 4,2877; victorias 3/5. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V6/L6; características comunes en secciones 2 y 3. |

### v6 S3

| Característica | Valor observado |
|---|---|
| Representación | B0_J + media, mínimo, máximo y rango W3. Pares comunes entre S3/S4/S6. |
| Diseño | 1102 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 4 (índice desde 0); 122 árboles; AUC Optuna 0,903884. |
| Hiperparámetros | num_leaves=37; min_data_in_leaf=1344; learning_rate=0,03570530; feature_fraction=0,90878952; bagging_fraction=0,64472860. |
| Agosto ensemble | AUC 0,904436; G suavizada 192,2039; Δ +0,6774; G puntual 189,6950. |
| Agosto corte | 4262 contactos (3,2316 %); 279 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 190,4527; Δ medio -0,2499; DE Δ 2,2005; victorias 2/5. Δ AUC medio -0,002073. |
| Octubre ensemble | AUC 0,917851; G 268,7850; Δ +6,9300 (+2,647 %); 4386 contactos y 354 aciertos. |
| Octubre semillas | G media 269,1205; Δ medio +3,1130; DE Δ 4,2020; victorias 4/5. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V6/S3; características comunes en secciones 2 y 3. |

## Anexo de modelos 17 a 18

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v6 S4

| Característica | Valor observado |
|---|---|
| Representación | B0_J + media, mínimo, máximo y rango W4. Pares comunes entre S3/S4/S6. |
| Diseño | 1102 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 9 (índice desde 0); 165 árboles; AUC Optuna 0,905820. |
| Hiperparámetros | num_leaves=17; min_data_in_leaf=902; learning_rate=0,02566708; feature_fraction=0,54718953; bagging_fraction=0,84411128. |
| Agosto ensemble | AUC 0,903606; G suavizada 188,5484; Δ -2,9781; G puntual 192,2250. |
| Agosto corte | 3810 contactos (2,8888 %); 270 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 188,3790; Δ medio -2,3236; DE Δ 3,5641; victorias 1/5. Δ AUC medio -0,002102. |
| Octubre ensemble | AUC 0,918670; G 268,3725; Δ +6,5175 (+2,489 %); 3921 contactos y 342 aciertos. |
| Octubre semillas | G media 265,5565; Δ medio -0,4510; DE Δ 3,2224; victorias 2/5. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V6/S4; características comunes en secciones 2 y 3. |

### v6 S6

| Característica | Valor observado |
|---|---|
| Representación | B0_J + media, mínimo, máximo y rango W6. Pares comunes entre S3/S4/S6. |
| Diseño | 1102 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 4 (índice desde 0); 136 árboles; AUC Optuna 0,906068. |
| Hiperparámetros | num_leaves=37; min_data_in_leaf=1344; learning_rate=0,03570530; feature_fraction=0,90878952; bagging_fraction=0,64472860. |
| Agosto ensemble | AUC 0,903511; G suavizada 184,4442; Δ -7,0824; G puntual 186,7800. |
| Agosto corte | 3528 contactos (2,6750 %); 258 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 184,0248; Δ medio -6,6778; DE Δ 2,6385; victorias 0/5. Δ AUC medio -0,003545. |
| Octubre ensemble | AUC 0,916086; G 268,6475; Δ +6,7925 (+2,594 %); 3631 contactos y 335 aciertos. |
| Octubre semillas | G media 264,6930; Δ medio -1,3145; DE Δ 5,1248; victorias 2/5. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V6/S6; características comunes en secciones 2 y 3. |

## Anexo de modelos 19 a 20

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v6 T4

| Característica | Valor observado |
|---|---|
| Representación | B0_J + pendiente OLS W4. Pares comunes entre T4/T6. |
| Diseño | 751 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 6 (índice desde 0); 399 árboles; AUC Optuna 0,904400. |
| Hiperparámetros | num_leaves=26; min_data_in_leaf=168; learning_rate=0,01304420; feature_fraction=0,46015573; bagging_fraction=0,89402734. |
| Agosto ensemble | AUC 0,903687; G suavizada 197,7560; Δ +6,2295; G puntual 197,1475. |
| Agosto corte | 4071 contactos (3,0867 %); 281 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 196,3754; Δ medio +5,6729; DE Δ 4,4184; victorias 5/5. Δ AUC medio -0,002006. |
| Octubre ensemble | AUC 0,920432; G 268,6750; Δ +6,8200 (+2,604 %); 4190 contactos y 349 aciertos. |
| Octubre semillas | G media 269,8850; Δ medio +3,8775; DE Δ 1,4409; victorias 5/5. |
| Decisión y fuente | Cumple la regla económica de agosto; no es significancia estadística. Fuente V6/T4; características comunes en secciones 2 y 3. |

### v6 T6

| Característica | Valor observado |
|---|---|
| Representación | B0_J + pendiente OLS W6. Pares comunes entre T4/T6. |
| Diseño | 751 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 6 (índice desde 0); 247 árboles; AUC Optuna 0,908308. |
| Hiperparámetros | num_leaves=82; min_data_in_leaf=1861; learning_rate=0,03505909; feature_fraction=0,48230215; bagging_fraction=0,55185883. |
| Agosto ensemble | AUC 0,907069; G suavizada 186,7821; Δ -4,7444; G puntual 189,9700. |
| Agosto corte | 5372 contactos (4,0732 %); 307 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 182,6512; Δ medio -8,0514; DE Δ 2,5559; victorias 0/5. Δ AUC medio -0,001088. |
| Octubre ensemble | AUC 0,916125; G 263,7525; Δ +1,8975 (+0,725 %); 5529 contactos y 378 aciertos. |
| Octubre semillas | G media 268,3725; Δ medio +2,3650; DE Δ 2,3747; victorias 4/5. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V6/T6; características comunes en secciones 2 y 3. |

## Anexo de modelos 21 a 22

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v6 R3

| Característica | Valor observado |
|---|---|
| Representación | B0_J + relativos frente a media W3, lag1 y lag2. Pares comunes R3/R4/R6. |
| Diseño | 985 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 3 (índice desde 0); 220 árboles; AUC Optuna 0,905435. |
| Hiperparámetros | num_leaves=81; min_data_in_leaf=1158; learning_rate=0,01926286; feature_fraction=0,85225954; bagging_fraction=0,66572713. |
| Agosto ensemble | AUC 0,904419; G suavizada 196,9801; Δ +5,4535; G puntual 198,7975. |
| Agosto corte | 4171 contactos (3,1626 %); 285 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 195,1800; Δ medio +4,4774; DE Δ 2,3797; victorias 5/5. Δ AUC medio -0,001384. |
| Octubre ensemble | AUC 0,917394; G 273,5425; Δ +11,6875 (+4,463 %); 4293 contactos y 356 aciertos. |
| Octubre semillas | G media 275,5500; Δ medio +9,5425; DE Δ 7,4282; victorias 5/5. |
| Decisión y fuente | Cumple la regla económica de agosto; no es significancia estadística. Fuente V6/R3; características comunes en secciones 2 y 3. |

### v6 R4

| Característica | Valor observado |
|---|---|
| Representación | B0_J + relativos frente a media W4, lag1 y lag3. Pares comunes R3/R4/R6. |
| Diseño | 985 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 3 (índice desde 0); 250 árboles; AUC Optuna 0,906199. |
| Hiperparámetros | num_leaves=81; min_data_in_leaf=1158; learning_rate=0,01926286; feature_fraction=0,85225954; bagging_fraction=0,66572713. |
| Agosto ensemble | AUC 0,905073; G suavizada 196,2853; Δ +4,7587; G puntual 197,6975. |
| Agosto corte | 4011 contactos (3,0412 %); 280 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 195,2691; Δ medio +4,5665; DE Δ 5,4218; victorias 4/5. Δ AUC medio -0,000766. |
| Octubre ensemble | AUC 0,917923; G 276,9800; Δ +15,1250 (+5,776 %); 4128 contactos y 355 aciertos. |
| Octubre semillas | G media 275,7975; Δ medio +9,7900; DE Δ 6,2628; victorias 5/5. |
| Decisión y fuente | Cumple la regla económica de agosto; no es significancia estadística. Fuente V6/R4; características comunes en secciones 2 y 3. |

## Anexo de modelos 23

Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.

### v6 R6

| Característica | Valor observado |
|---|---|
| Representación | B0_J + relativos frente a media W6, lag1 y lag5. Pares comunes R3/R4/R6. |
| Diseño | 985 columnas; train junio; 128.474 filas; control B0_J. |
| Ajuste propio | 10 trials + 5 semillas (211, 307, 401, 503, 601). Trial elegido 4 (índice desde 0); 187 árboles; AUC Optuna 0,907498. |
| Hiperparámetros | num_leaves=37; min_data_in_leaf=1344; learning_rate=0,03570530; feature_fraction=0,90878952; bagging_fraction=0,64472860. |
| Agosto ensemble | AUC 0,905320; G suavizada 188,0210; Δ -3,5055; G puntual 190,7125. |
| Agosto corte | 3745 contactos (2,8396 %); 267 aciertos BAJA+2 en el corte. |
| Agosto semillas | G media 187,2320; Δ medio -3,4706; DE Δ 3,8246; victorias 1/5. Δ AUC medio -0,001709. |
| Octubre ensemble | AUC 0,916514; G 277,9150; Δ +16,0600 (+6,133 %); 3854 contactos y 349 aciertos. |
| Octubre semillas | G media 270,9465; Δ medio +4,9390; DE Δ 5,4971; victorias 4/5. |
| Decisión y fuente | No cumple la regla económica de agosto; no es significancia estadística. Fuente V6/R6; características comunes en secciones 2 y 3. |

## 10 Contrastes de profundidad adicionales de v6

Estos contrastes fueron registrados antes de correr v6. No basta con que dos brazos ganen contra B0_J para afirmar que el de mayor ventana supera al menor. La tabla conserva diferencias directas, sin cambiar retrospectivamente el control. La regla de agosto se aplica al contraste pertinente.

| Contraste | Δ ago M | Gana ago | Δ oct M | Gana oct | Regla ago |
|---|---|---|---|---|---|
| S4 − S3 | -3,6555 | 2/5 | -0,4125 | 1/5 | No |
| S6 − S3 | -7,7597 | 0/5 | -0,1375 | 2/5 | No |
| S6 − S4 | -4,1042 | 1/5 | +0,2750 | 2/5 | No |
| T6 − T4 | -10,9739 | 0/5 | -4,9225 | 1/5 | No |
| R4 − R3 | -0,6949 | 2/5 | +3,4375 | 4/5 | No |
| R6 − R3 | -8,9591 | 0/5 | +4,3725 | 2/5 | No |
| R6 − R4 | -8,2642 | 0/5 | +0,9350 | 1/5 | No |
| L6 − L4 | +2,0676 | 4/5 | +2,0350 | 3/5 | Sí |

El signo entre meses puede cambiar. En particular, el mejor R4 en octubre no elimina el mejor R3 en agosto, y extender tendencia de W4 a W6 no dio una mejora económica consistente. Las cifras representan cada receta con su búsqueda propia y la política de cobertura congelada, no una prueba causal sobre cualquier cliente y cualquier mes.

### Lectura para el próximo prompt

Cada nueva hipótesis debe nombrar un control directo antes de correr. Una unión debe compararse con sus componentes; una poda con su conjunto completo; un cambio de máscara con la misma fórmula; un cambio de longitud con pares fuente–fórmula comparables. Si cambian varias condiciones a la vez, el resultado debe describirse como el efecto del paquete, no como el efecto aislado de una de ellas.

## 11 Fuentes y archivos que acompañan el informe

La fuente de verdad de los números es cada result.json por brazo y semilla, contrastada con FINAL.json, best.json, trials.json, contratos y políticas congeladas. Se verificaron 23 brazos, diez trials y cinco semillas por brazo, elección del mejor AUC, diferencias pareadas y cortes de octubre. Los aciertos se recalcularon con la identidad económica y son enteros. Los nombres y cantidades de columnas se cotejaron para los 23 brazos; para v4 se usó el protocolo completo recuperado en auditoria_trazabilidad_2026-11-13.

Repositorio propio consultado: ClariRZ/Experimentos-, commit e7c9db8d98bb84759d2458799ea42ca43dce5f64. Los estados de los documentos históricos se conservan; las fechas de carpetas no sustituyen la identidad de corrida.

P4 — Original, plan adaptado y contrato ejecutado.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/experimento_2026-11-13/prompts/

P5 — Prompt maestro v5; la corrida cubrió su primera etapa.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/HISTORIA_2019_01/v5/prompts/PROMPT_MAESTRO_HISTORIA_2019_v5.md

P6 — Prompt maestro v6 y rama de profundidad.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/HISTORIA_2019_01/v6/prompts/PROMPT_MAESTRO_HISTORIA_2019_v6.md

V4 — Agosto por brazo y FINAL de octubre; código original y README en la carpeta raíz del experimento.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/experimento_2026-11-13/resultados/

V5 — Config, columnas, trials, best y result por brazo. Sin octubre.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01/

V6 — Config, columnas, trials, best y result por brazo.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/HISTORIA_2019_01/v6/resultados/v6_20261113_02/

O6 — Política congelada, verificación de agosto y resultados de octubre.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/HISTORIA_2019_01/v6/resultados/octubre_v6_01/

A4 — Cierre de calibrador, hashes de modelos y listas completas de columnas de v4.

https://github.com/ClariRZ/Experimentos-/tree/e7c9db8d98bb84759d2458799ea42ca43dce5f64/auditoria_trazabilidad_2026-11-13/

Tutoría de Ale: transcripción y mensaje de Zulip aportados por Clara en esta conversación. No se atribuyen a Ale los conteos de brazos, diez trials, cinco semillas ni nuestras reglas de promoción. Las fórmulas concretas ejecutadas se contrastan con fe_core.py; no con el nombre informal de una variable en una lámina.

Comparación externa: ezequielabregu/DMEyF-2026-experi-colab-feature_historico, commit 770abaa9cad412647211c255360cb6dfe364e697; pipeline/parametros.py, pipeline/funciones.py, pipeline/README.md y resultados/pipeline/main_comparacion.csv.

Archivos de apoyo: evidencia.json con parámetros sin redondeo, métricas y listas disponibles; modelos_resumen.csv y semillas.csv con métricas agregadas no identificables; prompts_originales con copias exactas; fuentes_sha256.json con procedencia; scripts de extracción y de redacción; manifiesto de integridad de la entrega. Las cifras impresas se redondean solo para lectura.
