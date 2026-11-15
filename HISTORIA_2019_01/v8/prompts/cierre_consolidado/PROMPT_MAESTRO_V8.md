# PROMPT MAESTRO v8 — Cierre experimental Historia 2019

## 1. Objetivo y criterio de cierre

Actuá como especialista en data mining, evaluación económica y reproducibilidad. Cerrá la investigación de Historia 2019 con un experimento acotado que permita explicar qué representaciones aportan, cuáles no justifican su complejidad y qué sigue siendo incierto. Buscamos una construcción correcta y conclusiones defendibles, no fabricar un ganador.

Este es el último ciclo experimental previsto sobre estas hipótesis. Después de completar el protocolo, entregar el balance y cerrar: no ampliar familias, semillas, ventanas o cortes para perseguir un resultado favorable. Un resultado negativo o inconcluso también completa el objetivo. Corregir un defecto de implementación es distinto de abrir una hipótesis: registrar el defecto, los artefactos afectados y la necesidad de repetirlos antes de hacerlo.

Conservar las fortalezas de v1–v7: definiciones verificables, comparación pareada, varias semillas, modelos y predicciones respaldados, evaluación económica y trazabilidad. Corregir sus debilidades: poca confirmación del ajuste, comparaciones entre políticas diferentes, cobertura histórica desigual, sensibilidad al corte, confusión entre ensemble y media por semilla e incidentes operativos de disco y recuperación.

Cuatro brazos: **B0, R3, T4 y RR4**. Son **144 ajustes planificados**: cuatro veces veinte búsquedas, seis confirmaciones y diez modelos finales. No agregar pesos BAJA+2, P3, R4, TR1, canaritos, rankings, tarjetas ni híbridos de variables. El blend R3/T4 es un único diagnóstico secundario sin entrenamiento adicional.

## 2. Autorización, versiones y fuentes

Este prompt autoriza preparación local, inspección, pruebas sintéticas y diagnóstico sin entrenamiento. **No autoriza entrenar LightGBM ni encender la VM.** Al completar el preflight, presentar resultados concretos y pedir aprobación para la ejecución. No pedir de nuevo decisiones ya fijadas en este documento.

Guardar este cierre en `HISTORIA_2019_01/v8/cierre_consolidado/`, dentro de `ClariRZ/Experimentos-`. Mantener intacto el borrador anterior de v8 de 60 ajustes móviles y todos los resultados v1–v7. Este cierre lo reemplaza como propuesta vigente, no como supuesto historial ejecutado.

Fuentes de referencia:

- Dataset identificado por SHA256 `459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872`. Verificar el archivo real; no sustituirlo por otro de nombre parecido. La identidad del archivo no certifica su calidad.
- Repositorio experimental auditado en `d514580daa9bad4f1036159cadfd35d2137f8613`; código y configuración de `HISTORIA_2019_01/v7/`. Registrar también el commit efectivo de la nueva implementación.
- Modelos de `v7_20261114_120354` y predicciones de su continuación `octubre_20261114_182415`; verificar sus manifiestos. Los agregados de `recálculo_v7.json` no sustituyen los archivos de predicciones individuales.
- C3, snapshot `Experimentos-cloud` en `1d88507e875c62c0f872a922f0c92ab6d2666b0a`, registro original y generador de recencia/rachas.
- Consigna de Ale del 28/10, tutoría transcripta y consigna de competencia 2. El experimento conserva AUC para optimización y ganancia para octubre; abril–junio es una adaptación explícita del calendario original marzo–junio.

Agosto, septiembre y octubre tienen exposición histórica acumulada. Ninguna nueva congelación convierte esos meses en un test virgen. La corrección por tres contrastes no elimina la selección previa entre experimentos.

## 3. Fase A — Auditoría local antes de entrenar

### 3.1 Inventario, integridad y límites

Inventariar código, dataset, modelos, esquemas, predicciones, políticas, versiones de entorno y respaldos. Registrar rutas, tamaños, SHA256, origen y comprobación de lectura. Identificar faltantes, sin reemplazarlos silenciosamente. Verificar orden y unicidad de claves cliente–mes, columnas y etiquetas válidas, cobertura mensual y ausencia de target/ID/mes entre predictores. Si falta el dataset, avanzar con revisión documental, importancias y pruebas sintéticas posibles; el diagnóstico sobre datos reales y la aprobación de entrenamiento quedan pendientes.

Revisar las afirmaciones históricas de victorias 21/23 y 15/29 con una definición uniforme de control, meses, política, ensemble y semillas. Si no son homologables, presentar denominadores por escenario y no fabricar un total comparable. Cotejar los porcentajes 0,8% y 1,8% de importancia de C3 contra su archivo y definición de gain/split. La importancia no es una ablación causal ni prueba suficiente para elegir una familia.

### 3.2 Diagnóstico de octubre de v7

Identificar por nombre y procedencia las 14 variables señaladas por reglas del repositorio de Ezequiel. No presentarlas como errores confirmados por la cátedra. Informar ceros, faltantes y cobertura por mes, su intersección con las 129 fuentes históricas y sus descendientes en cada esquema.

Extraer gain y split por modelo y semilla, distinguiendo columnas contemporáneas y derivadas. Reportar numerador y total del modelo, evitando doble conteo de descendientes. No inferir causalidad de importancias en variables correlacionadas.

Estimar recursos y ejecutar, si están los insumos, tres escenarios sin reentrenar sobre los modelos respaldados de v7:

1. Intacto: reconstruir las entradas con el código y listas originales; comparar todas las predicciones por ID con las respaldadas, antes de interpretar métricas.
2. Contemporáneo: poner en NA solamente las 14 columnas actuales presentes en cada esquema; conservar las demás.
3. Coherente: poner en NA esas fuentes exclusivamente en octubre y regenerar todos sus descendientes con las funciones originales; conservar los meses previos y sus lags. Registrar columnas afectadas.

Mantener población, semillas y 3.583 contactos de la política histórica de v7; ordenar por score descendente e ID ascendente. Comparar cada brazo con B0 dentro del mismo escenario. La perturbación mide sensibilidad a una entrada alternativa fuera de la distribución original; no demuestra que los ceros sean incorrectos ni autoriza una máscara nueva.

Intentar reproducción exacta de las predicciones intactas con el entorno original. Si difiere, detener el diagnóstico, reportar error máximo/medio, orden, contactos y métricas, e investigar dtype, esquema, versión y hardware. No ampliar tolerancias después de ver ganancias. Una equivalencia numérica alternativa, si fuera necesaria, requiere justificación y criterio aprobado antes de interpretar perturbaciones.

Este diagnóstico no elige brazos ni cambia la regla de éxito. No presentar script preparado como diagnóstico ejecutado. La comprobación histórica no abre una búsqueda de saneamientos.

### 3.3 Saneamiento y cobertura

Conservar exactamente las nueve máscaras abril/mayo del contrato v7. Mantener ceros originales de julio/octubre. No imputar ceros, inventar inactividad ni reemplazar faltantes por datos futuros. Registrar no finitos y su conversión a NA conforme al motor original. Las máscaras históricas tienen justificación documentada, no confirmación oficial; declarar esa limitación.

Auditar abril, mayo, junio, agosto, septiembre y octubre por columna y familia; indicar si cada denominador representa celdas o clientes. Registrar causas superpuestas: ausencia de cliente–mes, faltante/no finito original, máscara, referencia cero, ausencia de evento observado y truncamiento de racha.

Para resultados NA, atribuir una categoría principal con prioridad: ausencia requerida; faltante original; máscara sobre valor finito; referencia cero con ventana completa en R3; ventana completa observada sin no-cero en recencia; otra causa. Mantener aparte los solapamientos. Una recencia sin evento en ventana incompleta no equivale a cuatro ceros observados. Valores finitos con rachas truncadas se cuentan como finitos y también en el diagnóstico de truncamiento.

La última categoría debe estar explicada por pruebas y especificación; no entrenar con indeterminaciones inesperadas. Comparar fórmulas con/sin las nueve máscaras solamente para medir pérdida de disponibilidad y truncamiento; la versión sin máscaras nunca alimenta modelos.

## 4. Features y pruebas bloqueantes

### 4.1 B0, R3 y T4

Cargar las listas ordenadas efectivas del manifiesto v7 para abril–junio: B0 652, R3 1.024 y T4 776 columnas. No deducirlas únicamente de 129 fuentes ni volver a seleccionar columnas con agosto/octubre. Verificar que las matrices reconstruidas coincidan con las fórmulas y exclusiones originales. Los 152 predictores crudos excluyen ID, mes y clase; validar nombres, no sólo cantidades.

- B0: variables actuales y lag/delta 1 y 2. Un lag es el mismo cliente en el mes calendario exacto, no la fila anterior disponible.
- R3: `(x_t-r)/abs(r)` para media W3, lag1 y primer valor W3. W3 contiene actual y dos anteriores; exige los tres finitos incluso para lag1. Referencia cero produce NA, sin epsilon. Respetar el subconjunto efectivo v7 y su criterio histórico de elegibilidad compartida con R4, sin añadir columnas antes excluidas.
- T4: pendiente OLS frente a tiempos 0,1,2,3 de antiguo a actual; exige cuatro valores finitos. Conservar subconjunto efectivo v7.

### 4.2 RR4

Adaptar las tres operaciones del generador C3 sobre las 129 fuentes elegibles, usando actual y tres meses calendario previos:

- Recencia observada: menor k entre 0 y 3 con valor finito no cero. Salta huecos para buscar un evento observado; NA si ninguno existe. Puede ser finita aunque el mes actual sea NA. No equivale a recencia real conocida cuando faltan meses.
- Racha cero: longitud consecutiva de ceros finitos desde actual hacia atrás, máximo 4; se detiene ante hueco, NA o no cero. Actual faltante produce NA; actual no cero produce 0.
- Racha no cero: simétrica; negativos cuentan como no cero, sin llamarlos actividad comercial. Actual cero produce 0; actual faltante produce NA.

Ejemplos obligatorios, en orden `[actual, lag1, lag2, lag3]`:

| Valores | Recencia | Racha cero | Racha no cero |
|---|---:|---:|---:|
| `[0, NA, 50, 10]` | 2 | 1 | 0 |
| `[NA, 50, 0, 0]` | 1 | NA | NA |
| `[0, 0, 0, 0]` | NA | 4 | 0 |
| `[-5, -2, 0, 9]` | 0 | 0 | 2 |

Hasta 387 columnas nuevas, máximo 1.039 con B0. Preservar B0 íntegro. Depurar exclusivamente nuevas columnas según train: 100% vacías, constantes exactas o duplicadas exactas incluyendo patrón de NA. Un único valor finito junto a NA no es constante. Prioridad B0; luego nombres nuevos en orden lexicográfico; registrar aliases y motivos. No usar umbral 95%, baja varianza ni validación para filtrar.

T4 y RR4 agregan un mes de información respecto de B0. Sin control adicional de lag3, su efecto es representación más profundidad, no transformación pura. No agregar ese quinto brazo en este cierre.

### 4.3 Pruebas

Pruebas automatizadas de joins calendario, cambio de año, duplicados, orden de filas, ceros, negativos, NA/no finitos, máscaras abril/mayo, ventanas completas e incompletas, ejemplos RR4, depuración y aliases. Comparar B0/R3/T4 con implementación original sobre casos sintéticos y datos reales disponibles. Verificar que cambios futuros no alteren features pasadas. Pruebas de corte, desempates, ganancia y conteo exacto de contactos. No basta comprobar el número de columnas.

## 5. Contrato experimental y ejecución autorizada

### 5.1 Calendario y etiquetas

Train abril–junio 2019 completo, sin sampling; historia desde enero. Agosto selecciona configuración y contactos. Septiembre evalúa persistencia; octubre es evaluación económica principal. No reentrenar entre meses ni usar septiembre/octubre para ajustar.

Train positivo: BAJA+1 o BAJA+2, peso uniforme. Validación AUC/early stopping: BAJA+2 frente a las demás clases. Etiquetas ausentes o desconocidas no se convierten en negativas. La maduración de octubre requiere cobertura hasta diciembre; noviembre/diciembre pueden informar etiquetas e histórico, no aportar filas supervisadas incompletas.

Ganancia: `1.100.000 × aciertos BAJA+2 − 27.500 × contactos`. Son unidades económicas del concurso, no ingresos realizados.

### 5.2 Búsqueda y semillas

LightGBM GBDT binario, bagging_freq=1, feature_pre_filter=False, cuatro threads, deterministic=True y force_col_wise=True. Congelar max_bin=255, demás parámetros efectivos, versiones y semillas internas; comprobar coherencia con v7 antes de aprobar. Usar etiquetas BAJA+2 en el conjunto de validación para AUC, no las etiquetas combinadas de entrenamiento.

20 trials TPE por brazo, n_startup_trials=5; 1.500 rondas máximas y paciencia 100. Distribuciones exactamente:

| Parámetro | Tipo y rango | Escala |
|---|---|---|
| num_leaves | entero 16–128 | logarítmica |
| learning_rate | real 0,01–0,10 | logarítmica |
| min_data_in_leaf | entero 100–2.000 | logarítmica |
| feature_fraction | real 0,30–1 | uniforme |
| bagging_fraction | real 0,50–1 | uniforme |

Sampler 2026111307; modelo de búsqueda 100003. Confirmación 100103,100109. Modelos finales: 100151,100153,100169,100183,100189,100193,100207,100213,100237,100267. Mismos grupos por brazo, disjuntos por función. Registrar todos los parámetros de TPE y LightGBM; veinte trials no demuestran convergencia.

Tomar tres trials completos de mayor AUC, empate por trial_number. Conservar sus best_iteration. Entrenar cada configuración con las dos semillas de confirmación, sin nuevo early stopping. Elegir por AUC medio exclusivamente de esas dos semillas; desempate por desviación estándar poblacional menor, menos rondas y trial_number menor. Luego diez modelos finales con esos parámetros y rondas fijos. No incorporar automáticamente más árboles.

Registrar configuraciones repetidas si aparecen entre trials; no sustituirlas ni extender búsqueda para obtener tres distintas. Registrar intentos, completados, fallidos y recuperados. Ante fallo, pausar y diagnosticar: no imputar un resultado, ampliar selectivamente presupuesto ni declarar 144 completados por haberlos iniciado. No reentrenar un artefacto válido durante recuperación.

### 5.3 Orden, contactos y congelación

Orden B0, R3, T4, RR4; una matriz de brazo activa por vez. Ensemble = promedio simple de scores de diez modelos. Son scores de ranking, no probabilidades calibradas BAJA+2.

Con B0 final en agosto, calcular ganancia acumulada ordenada por score descendente e ID ascendente. Elegir el centro k de mayor promedio móvil centrado completo de 2.001 posiciones, sin padding de bordes; empate, k menor. Reutilizar y probar la función original v7 para evitar desplazamientos de índice. Registrar k, N_agosto, ventana y política; guardar p como fracción exacta k/N_agosto. Para otro mes, K = división entera de k×N_mes por N_agosto. No fijar 3.481 ni 3.583 para v8.

Guardar diagnósticos económicos y clases contactadas de tres finalistas por dos semillas a este corte común y con suavizado propio. Para B0 se calculan después de fijar p. Nunca cambian la selección por AUC. No abrir políticas propias adicionales salvo las que el contrato declare previamente como diagnósticas, sin promoción.

Respaldar modelos, esquema, parámetros y predicciones de agosto por brazo. Sólo después de congelar los cuatro brazos y p puntuar septiembre/octubre. La auditoría previa puede leer cobertura de esos meses; no usarlos para selección. Registrar fecha de congelación, hashes y exposición previa sin afirmar ceguera absoluta.

## 6. Evaluación y conclusiones

### 6.1 Tablas económicas

Por brazo y mes: N, BAJA+2, K, aciertos, ganancia, delta pareado contra B0, porcentaje de cambio (NA si B0=0), AUC, captura y lift con sus fórmulas/denominadores. Mostrar ensemble y media por semilla separadamente, con desviación, diez deltas y victorias/empates/derrotas. Informar contactos compartidos, agregados y perdidos, y composición BAJA+2/BAJA+1/CONTINUA. No promediar meses para cambiar la clasificación final.

Tres contrastes principales: R3−B0, T4−B0, RR4−B0 en octubre con K común.

### 6.2 Incertidumbre

Por cliente, fijar contribución económica de cada decisión y su diferencia frente a B0. Bootstrap pareado no estratificado, 10.000 réplicas de N clientes con reemplazo, semilla 2026111499; sumar contribuciones de cada réplica sin reordenar ni recalcular contactos. Usar los mismos índices por contraste. IC percentil, cuantiles con interpolación lineal: 0,025/0,975 y alpha/2,1−alpha/2 con alpha=0,05/3. Registrar generador y versión. No materializar una matriz enorme de todas las réplicas: procesar por bloques equivalentes y probados.

Esto mide incertidumbre condicional de contribuciones congeladas; no simula reentrenamiento ni garantiza K fijo en cada remuestra. No presentarlo como inferencia de toda la campaña futura. Bonferroni cubre la familia declarada de tres contrastes, no las decisiones históricas.

Por semillas, diez diferencias pareadas, media, desviación muestral e IC t aproximado 95% con nueve grados de libertad, condicionado al mismo dataset. No sumar este error al bootstrap como si fueran independientes.

### 6.3 Sensibilidad y único blend

Evaluar multiplicadores exactos 85/100,925/1000,1,1075/1000,115/100 de p, usando aritmética entera para el piso. No elegir otro corte después. Reportar por separado los cinco deltas de cada mes.

Blend secundario R3/T4: sobre mismas claves y scores finitos, percentil ascendente por mes `rank(average)/N` de cada ensemble, promedio 0,5/0,5. Orden descendente, ID ascendente, K común. No buscar pesos ni otros pares. Reportarlo descriptivamente; no integrarlo a la regla principal ni atribuirle los intervalos ajustados de los tres contrastes.

Predeclarar también diagnóstico coherente de las 14 fuentes señaladas sobre RR4 después de su evaluación intacta, con igual corte y comparación contra B0 perturbado coherentemente. No entrenar versiones corregidas ni cambiar el resultado principal por ese diagnóstico.

### 6.4 Regla de cierre

- Favorable dentro de este análisis: delta de ensemble octubre positivo y límite inferior ajustado positivo; delta de ensemble septiembre positivo; media pareada de semillas positiva en ambos meses; delta no negativo en al menos cuatro de cinco presupuestos de octubre.
- Prometedor/inconcluso: delta octubre positivo sin cumplir todos esos criterios.
- Sin mejora observada: delta octubre cero; describir incertidumbre.
- Desfavorable en este escenario: delta octubre negativo; no afirmar inutilidad universal ni daño demostrado sólo por el signo.

Estas condiciones no garantizan generalización. Si varias pasan, presentar todas, sin proclamar superioridad entre ellas que no se contrastó. Si ninguna pasa, conservar B0 como referencia y documentar una alternativa exploratoria para competencia 2. No abrir un v9 automáticamente ni aumentar pruebas hasta ganar.

## 7. Recursos, respaldo y reproducibilidad

Antes de solicitar ejecución, medir localmente dimensiones reales, RAM pico, disco de matrices, modelos y temporales, más espacio para empaquetado y copia. Definir umbrales numéricos justificados de RAM/disco y reservar espacio para recuperación; no arrancar al borde del guard. Separar estimación de medición y aclarar hardware. Si falta infraestructura para medir, marcarlo pendiente, no aprobado.

Techo propuesto: seis horas incluyendo evaluación y respaldo. Ajustarlo antes de aprobar si el preflight muestra incompatibilidad; no prometer finalización. Checkpoints por trial y modelo; respaldo privado reanudable fuera de la VM, SHA256 y restauración de prueba. Temporizador independiente y apagado al completar; ante límite, detener de forma registrada y conservar los artefactos válidos. Verificar estado apagado, no sólo haber solicitado apagar. No borrar originales ni respaldos para hacer lugar sin verificar alcance y autorización.

Versionar código, contrato, esquemas, dependencias, pruebas, prompts, logs agregados y resultados sin datos personales. Modelos, dataset y predicciones individuales en respaldo privado con manifiesto versionado sin secretos. Identificar commit, árbol de trabajo limpio o parche exacto, Python, paquetes, OS/hardware y semillas. Registrar las funciones y fuentes originales reutilizadas. No publicar datos privados en GitHub.

Contrato JSON completo con estados DRAFT, PREFLIGHT_PASSED, APPROVED, RUNNING, COMPLETE o FAILED, evidencias y hashes. Sólo APPROVED habilita ejecución; el contrato aprobado es inmutable. Reanudaciones registran eventos nuevos, no reescriben hechos. Un script debe validar contrato y preflight antes del primer fit.

Entregar procedimiento de restauración y reproducción desde cero en otro directorio, dependencias fijadas y verificadores por etapas. Comparar claves, features y predicciones con tolerancias previamente especificadas; registrar diferencias. Hasta ejecutar una reproducción independiente, decir «trazable y preparado para reproducir», no «reproducido». Una repetición independiente completa es una tarea separada y no está autorizada por los 144 ajustes.

## 8. Línea independiente para competencia 2

Preparar el esqueleto con B0 sin esperar ganador. No condiciona ni cambia el experimento de historia. Dos estrategias reales serán necesarias para completar la entrega operativa.

Entrada `input/<yyyymm>.csv`, coma, encabezado, sin clase; comprobar mes, esquema, tipos, claves y secuencia. Histórico inmutable, lock de concurrencia, estado por mes, entrada identificada por hash. Un mismo mes/hash completado no se reprocesa; mismo mes con otro hash se bloquea. Reintentos de fallos son idempotentes. Escribir artefactos en staging y publicar una versión consistente antes de marcar COMPLETE; probar interrupciones en cada paso.

Salida `output/churn_<yyyymm>.csv`, coma y encabezado, exactamente `numero_de_cliente,probabilidad,enviar` como campos obligatorios; enviar es 0/1 y probabilidad se documenta como score. Una recomendación oficial por cliente; conservar scores alternativos para comparar. Reporte acumulativo de población, contactos, scores, coincidencia, alertas, tiempos y, con etiquetas maduras, ganancia/lift/captura.

Reconstrucción de clase contrastada con etiquetas conocidas en meses con horizonte completo; ante discrepancias, informe de cobertura/definición y bloqueo de métricas maduras. No inventar target por ausencia si la cobertura del archivo no está validada. Los dos últimos meses incompletos quedan pendientes de evaluación.

Estrategias definidas con 2019; diciembre no tiene target y noviembre no tiene BAJA+2 completa. Probar secuencia 202001–202006 con decisiones congeladas; no usarla para retroseleccionar features y afirmar confirmación en 2019. Si hay reentrenamiento, política predefinida hasta t−2, etiquetas maduras y versiones; su costo cuenta en la operación mensual. No excluirlo artificialmente del SLA.

Medir los 15 minutos desde copia/llegada del archivo, incluida espera para iniciar, hasta salida y reporte consistentes; informar también tareas pendientes. Verificar el presupuesto del proceso completo. P3 de v7 queda como antecedente exploratorio documentado, no descartado por carecer de utilidad ni promovido por octubre. No implementar ahora más estrategias de las necesarias para este alcance.

## 9. Entrega inmediata y cierre final

Al ejecutar este prompt, primero completar Fase A y pruebas: inventario, diagnóstico real o bloqueo preciso, cobertura, implementación verificada de RR4, borrador de contrato y medición de recursos. No entrenar. Presentar un reporte con estados PASÓ, FALLÓ o PENDIENTE por requisito, artefactos y comando reproducible; los pendientes materiales impiden afirmar que está listo.

Luego de aprobar y ejecutar, entregar:

1. Tabla completa por brazo/mes/semilla y políticas, con todos los resultados, no sólo los favorables.
2. Comparación de hipótesis con sus limitaciones: representación, profundidad adicional, ajuste y disponibilidad de historia.
3. Balance v1–v8 y Ezequiel: qué es homologable, qué no, fortalezas y debilidades; no comparar ganancias de calendarios/poblaciones diferentes como una competencia directa.
4. Conclusión clara de qué funcionó en los escenarios medidos, qué no justificó complejidad y qué quedó incierto. Separar hipótesis de causas demostradas.
5. Receta y artefactos reutilizables para competencia 2, estado de su prueba operativa y restricciones de tiempo.
6. Informe de integridad, recuperación, incidentes y estado final de VM. Identificar lo reproducido realmente y lo sólo preparado.

El trabajo termina con este cierre completo, aunque no haya una mejora estadísticamente defendible. No garantizar ganancias, ocultar fallos, reformular hipótesis después de ver resultados ni proponer otra ronda automáticamente.
