# Baseline de Ale + variables de C3 en 2019

**Estado: protocolo previo; no ejecutado. La VM permanece apagada.**

## Pregunta
¿Agregar un subconjunto intrames de C3 al baseline B2 de Ale y/o promediar 20 semillas mejora la ganancia de octubre de 2019? Todas las comparaciones se hacen sobre los mismos meses, clientes, etiquetas y fórmula económica.

## Cuatro brazos
| Brazo | Variables | Predicción |
|---|---|---|
| A | B2: originales + lags/deltas 1 y 2 | Una semilla fijada antes de correr |
| B | B2 + variables_propuestas.csv | La misma semilla que A |
| C | Las de A | Promedio aritmético de scores de 20 semillas, incluyendo A |
| D | Las de B | Promedio aritmético de scores de las mismas 20 semillas, incluyendo B |

No se promedian ganancias ni rankings: primero scores, después selección de clientes y cálculo de ganancia. Son 40 modelos finales, no 42: A y B son miembros de los ensembles. No elegir la mejor semilla mirando resultados.

## Qué se transfiere de C3
El manifiesto enumera exclusivamente tickets monto/operaciones y sumas del mismo campo Visa+Master presentes en el esquema original de C3. Es un subconjunto de C3, no la receta completa ni los siete ratios del B6 anterior. No se agregan historias de estas nuevas columnas, diferencias entre marcas, indicadores ni nuevas interacciones.
Las sumas originales requieren ambas marcas observadas; no sustituirlas por sumas que ignoran faltantes. Los tickets requieren denominador positivo finito y conservan numeradores negativos finitos. No mezclar monedas ni corregir escalas sin documentar otro experimento. La comparabilidad de Visa_msaldototal con sus componentes requiere diagnóstico; conservar advertencia del código original.
Antes de entrenar: comprobar fuentes en 2019, esquema, orden, tipos, duplicados, NA/inf y equivalencia de fórmulas con C3. Una fuente ausente o una exclusión exige revisar/versionar el manifiesto antes de optimizar, nunca una omisión silenciosa basada en resultados. Registrar cobertura por mes sin usar etiquetas de octubre.

## Calendario y selección
Sólo datos de 2019. Entrenamiento marzo–junio completo, sin sampling. Agosto para AUC, early stopping y política de contactos. Octubre para evaluación final. Enero/febrero y otros meses anteriores aportan historia por cliente y mes calendario cuando corresponda. No incorporar noviembre/diciembre. Entrenamiento y AUC: BAJA+1 o BAJA+2 positivas; ganancia: sólo BAJA+2.

Optimizar una vez cada representación con el mismo presupuesto de 20 trials, mismo espacio B2 y semilla de búsqueda. Elegir por AUC de agosto; desempatar por trial anterior. bagging_freq=1. Fijar parámetros y número de árboles del mejor trial para las 20 semillas de esa representación. No reoptimizar por semilla ni usar octubre para early stopping. Registrar semillas efectivas de LightGBM, versiones y orden de columnas.

A histórico obtuvo $282.645.000 a 5.042 contactos. Es una referencia a reproducir, no el resultado asumido de esta corrida. Reconstruir el B2 guardado y verificar sus scores/curva antes de comparar. Si una nueva búsqueda arroja otra receta, identificarla como control nuevo y explicar la diferencia sin seleccionar retrospectivamente el mejor A.

## Contactos y métrica
Ganancia = 1.100.000 × aciertos BAJA+2 − 27.500 × contactos.
Para cada brazo, ordenar agosto por score descendente y cliente ascendente para empates. Elegir k de máxima ganancia, incluyendo k=0 y el menor k en empate. Transferir la fracción a octubre mediante floor(n_octubre × k_agosto/n_agosto). Cada ensemble define su política con sus propios scores de agosto. No limitar la búsqueda a 3.600–5.700: ese rango observado no es una regla universal.
El resultado principal es la ganancia de cada política fijada en agosto. Comparaciones principales B−A (representación reoptimizada), C−A y D−B (ensemble), D−C (representación reoptimizada con ensemble), D−A (paquete completo). Reportar todas, no sólo la favorable. Mejora observada significa delta estrictamente positivo; no implica significancia ni mejora futura.
Para separar ranking de cantidad de contactos, reportar los cuatro brazos al presupuesto elegido por A en agosto y, como referencia secundaria, a 11.000 contactos. No buscar un nuevo corte ganador en octubre. 11.000 sigue siendo válido; puede ser menos rentable sin dejar de ser una comparación útil.

## Alcance de las conclusiones
B frente a A y D frente a C cambian variables y parámetros optimizados: miden la receta reoptimizada, no el efecto exclusivo de variables. Si se busca atribución exclusiva, hará falta una ablación posterior con parámetros y árboles comunes; no afirmar que B>A demuestra por sí solo que las variables causaron la mejora.
C−A y D−B comparan el ensemble con una semilla previamente elegida. Complementar con los 20 resultados individuales, diferencias pareadas, mediana, dispersión y victorias/empates/derrotas, bajo el corte común definido en agosto. No comparar un ensemble contra la mejor semilla elegida después. No tratar 20 semillas como 20 meses independientes.
Octubre ya fue observado: no es holdout virgen. Usar agosto para selección evita nueva optimización directa sobre octubre, pero no borra esa exposición previa. El estudio es exploratorio, de un único mes. C3 original 2021 sólo aporta fórmulas; sus $308,7 millones privados y $385 millones locales no son controles económicos de este ensayo.

## Congelamiento y entrega
Antes de evaluar octubre guardar commit, hashes de datos/código/manifiesto, configuración, modelos finales, número de árboles, seeds, scores y cortes elegidos en agosto. Evaluar los cuatro brazos juntos una vez congelados; no ampliar presupuesto ni cambiar recetas por el test.
Entregar hipótesis, diseño y limitaciones, tabla de AUC agosto/ganancia octubre/contactos/aciertos/deltas, resultados por semilla y ensemble, conclusiones y próximos pasos; guion de video y bibliografía. Guardar código, versiones, auditorías y métricas agregadas en Git; datos, IDs y scores sólo en almacenamiento privado autorizado. Registrar comandos reproducibles y verificar las ganancias desde los scores.

## Insumos y evidencia
- ../experimento_historicas_B0_B5/: código, B2, modelos, configuración y resultados originales.
- ../experimentos_c3/config/c3_plan_original.json: esquema original.
- ../experimentos_c3/02_intrames_C3_B6/vendor/fe_relaciones.py: fórmulas fuente; hash registrado en config_propuesta.json.
- variables_propuestas.csv: lista cerrada de candidatos extraída del esquema C3, pendiente de preflight 2019.
- config_propuesta.json: calendario, presupuesto, semillas y decisiones previas.

Este paquete documenta el diseño. No contiene runner nuevo ni resultados inventados; la implementación y preflight deben completarse antes de la ejecución en VM.
