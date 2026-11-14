# PROMPT MAESTRO — HISTORIA 2019 v7

## Integración de v4, v5 y v6 con trazabilidad y reproducción independiente

Fecha de edición: 13 de noviembre de 2026. Estado: protocolo documental publicado; contrato ejecutable, auditoría real y presupuesto pendientes. Publicar este prompt no autoriza iniciar entrenamientos.

## 1. Objetivo

Ejecutar desde cero un experimento de diez brazos para determinar qué información histórica mejora la ganancia de LightGBM frente a un baseline común. Integrar ranking actual de v4; promedio, mínimo y rango de v5; relativos y tendencias de v6; y dos ampliaciones nuevas.

La pregunta principal es si combinar cambios relativos y tendencias mejora a cada componente por separado, y si agregar relativos simétricos mejora la receta de relativos. La comparación económica principal tendrá el mismo presupuesto de contactos para todos los brazos.

Conservar las definiciones anteriores y construir un procedimiento reutilizable cuando haya nuevos meses. No garantizar una mejora ni descartar resultados negativos. Esta ejecución utiliza únicamente 2019.

## 2. Fuentes y decisiones

Consultar y registrar versiones, commits y hashes de:

1. La consigna de Alejandro compartida por Clara desde Zulip.
2. La transcripción de la tutoría aportada en el chat; no presentarla como transcripción verificada contra el audio.
3. Prompts, contratos, código y resultados auditados de v4, v5 y v6.
4. El diccionario de variables.
5. La carpeta [monday de Ale](https://github.com/alejandro-bolanos/dmeyf2026/tree/main/monday), en particular z402, z301, z601 y z701.
6. La implementación del relativo simétrico en el repositorio de Ezequiel.

Distinguir instrucciones de Ale, decisiones propias e hipótesis nuevas. Los ejemplos didácticos no reemplazan automáticamente nuestras fórmulas, saneamiento, clases o calendarios.

Fuentes internas, relativas a la raíz del repositorio:

- `experimento_2026-11-13/`: v4.
- `auditoria_trazabilidad_2026-11-13/`: complemento de la auditoría de v4.
- `HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01/`: resultados de agosto de v5.
- `HISTORIA_2019_01/v6/resultados/v6_20261113_02/`: entrenamiento de v6.
- `HISTORIA_2019_01/v6/resultados/octubre_v6_01/`: cierre de octubre de v6.
- `informes/prompts_modelos_2019_2026-11-13/`: reconstrucción de prompts, resultados y definiciones.

V5 y v6 sí tienen resultados publicados. V6 ya se evaluó en octubre; el cierre de octubre de v5 no está completado en la evidencia revisada. No interpretar estados antiguos de preparación como ausencia de corridas posteriores.

## 3. Alcance y límites

- LightGBM binario, sin pesos especiales para BAJA+2 y sin sampling previo del dataset.
- Diez brazos definidos antes de entrenar; ejecutar y reportar todos.
- No incluir canaritos, nuevas familias de ranking, otros algoritmos ni 2020.
- No ampliar brazos ni modificar fórmulas después de observar resultados.
- No afirmar que esto mejora el modelo del grupo: requeriría un contraste separado contra ese modelo congelado.
- Agosto y octubre ya fueron observados. Este es un experimento exploratorio con protocolo congelado; repetir desde cero no restablece la independencia de esos meses.

## 4. Ejecución desde cero

Partir del dataset original identificado por SHA256. Reconstruir matrices, realizar búsquedas nuevas y entrenar todos los modelos.

No reutilizar modelos, predicciones, matrices precalculadas ni hiperparámetros ganadores como sustitutos de la búsqueda. Sí reutilizar código auditado, fórmulas y pruebas de equivalencia. Los resultados previos justifican hipótesis, pero no se incorporan como resultados de v7.

V4/v5 entrenaron marzo–junio y v6 entrenó junio. V7 entrenará abril–junio. Por ello, v7 integra sus recetas con un calendario común; no constituye una reproducción exacta de esas corridas. La reproducción independiente exigida al cierre será la de v7.

## 5. Auditoría bloqueante de datos

### Identidad y población

El dataset de referencia de nuestras corridas tiene SHA256:

`459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872`

Si difiere, detener la preparación y reconciliar la diferencia. Verificar tipos, clases, conteos por mes, claves cliente–mes únicas, orden y alineación. Excluir identificador, mes y target de predictores, según el contrato histórico. Bloquear variables derivadas del target y datos futuros.

### Saneamiento

Revisar las nueve correcciones históricas de abril/mayo y extender la auditoría a julio–octubre. Contrastar en nuestro dataset las anomalías que señala Ezequiel:

- Julio: `Visa_fultimo_cierre`, `Master_fultimo_cierre`.
- Octubre: `mrentabilidad`, `mrentabilidad_annual`, `mpasivos_margen`, `mactivos_margen`, `mcomisiones`, `mcomisiones_otras`, `ccomisiones_otras`, `chomebanking_transacciones`, `mcajeros_propios_descuentos`, `ccajeros_propios_descuentos`, `ctarjeta_visa_descuentos`, `mtarjeta_visa_descuentos`, `ctarjeta_master_descuentos`, `mtarjeta_master_descuentos`.

El listado externo es una pista, no una prueba de rotura en nuestra población. Examinar ceros, nulos, valores distintos, distribución temporal y significado de negocio. No decidir correcciones por su efecto en ganancia o AUC. No convertir ceros legítimos en nulos ni imputar automáticamente ausencias como cero.

Guardar variable, mes, evidencia, decisión, justificación y diferencia respecto del saneamiento anterior. Aplicar las reglas comunes antes de construir historia. No rellenar con información futura. La auditoría de octubre no usará etiquetas ni resultados de modelos; tampoco extenderá el alcance a noviembre/diciembre sin decisión documentada.

### Cobertura y condiciones de bloqueo

Los rezagos deben corresponder a meses calendario exactos. W4 incluye actual y tres anteriores: abril dispone de enero–abril a nivel calendario, pero no todos los clientes tienen todos los valores.

Medir nulos por ausencia del cliente, faltante original, saneamiento y exigencia de la fórmula. No eliminar clientes por historia incompleta.

Bloquear ventanas temporalmente imposibles, información futura, matrices desalineadas, población diferente entre brazos y columnas homónimas con definiciones distintas. Depurar columnas vacías/constantes con entrenamiento y documentarlo; no permitir que una columna sin soporte de entrenamiento aparezca silenciosamente como nueva información al puntuar.

## 6. Definiciones históricas congeladas

Conservar las definiciones verificadas de B0, F4a, promedio/mínimo/rango W3, R3, R4 y T4: fuentes, extremos, ventanas, denominadores, ceros, negativos, faltantes y empates.

El contrato debe escribir las fórmulas y vincularlas a las funciones originales, no limitarse a mencionar nombres de familias. En particular:

- Rezago k: valor del mismo cliente k meses calendario antes.
- Delta k: actual menos rezago k; requiere sus extremos.
- W3 y W4 incluyen el mes actual.
- Promedio, mínimo y rango: conservar ventana completa según la implementación original; rango = máximo menos mínimo.
- R3/R4: conservar los cambios relativos a media de la ventana, lag1 y primer mes de la ventana; denominador absoluto y reglas originales de ventana completa y denominador cero.
- T4: pendiente OLS sobre cuatro posiciones temporales, con ventana completa.
- RK: ranking actual F4a original; no sustituirlo por percent_rank, cero fijo u otra convención.

Congelar las listas de fuentes y las reglas de depuración heredadas. Las listas finales pueden cambiar por el calendario abril–junio y por saneamiento confirmado; cada diferencia debe quedar explicada. No forzar cantidades históricas de columnas.

Pruebas sintéticas propias: huecos temporales, ceros, negativos, nulos, ventanas, empates, pendientes conocidas, equivalencia de fórmulas y preservación de claves. Comparar con el código anterior antes de entrenar.

Si aparece un error anterior real, registrar su impacto y resolverlo antes de congelar. No corregir silenciosamente durante la corrida.

## 7. Calendario común

| Uso | Período |
|---|---|
| Entrenamiento | Abril, mayo y junio de 2019 completos |
| Historia | Datos de 2019 disponibles hasta el mes de cada observación |
| Optimización y decisión de desarrollo | Agosto de 2019 |
| Evaluación económica de cierre | Octubre de 2019 |

Este calendario permite W4 desde abril y aporta más filas que junio solo. No garantiza menor variabilidad: los mismos clientes pueden aparecer en varios meses. Septiembre no se incorpora como mes de decisión dentro de v7.

## 8. Diez brazos

| ID | Contenido | Antecedente |
|---|---|---|
| B0 | Variables actuales + rezagos 1/2 + deltas 1/2 | Control común |
| RK | B0 + ranking actual F4a | v4 |
| P3 | B0 + promedio W3 | v5 |
| MIN3 | B0 + mínimo W3 | v5 |
| RAN3 | B0 + rango W3 | v5 |
| R3 | B0 + relativos W3 | v6 |
| R4 | B0 + relativos W4 | v6 |
| T4 | B0 + tendencia W4 | v6 |
| H_T | Unión de R4 y T4 sin duplicar B0 | Combinación nueva |
| H_S | R4 + relativos simétricos lag1 y lag2 | Ampliación nueva |

No acumular familias entre brazos. Depurar vacías, constantes y duplicadas exactas únicamente con entrenamiento, preservando las columnas del control cuando sean duplicadas. Registrar cada eliminación. Las ampliaciones no pueden eliminar silenciosamente una variable del baseline.

### Relativo simétrico nuevo

Para cada fuente elegible congelada, calcular respecto de lag1 y lag2:

`(actual - anterior) / (abs(actual) + abs(anterior))`

Ambos valores cero: cero. Algún extremo faltante: NA. Preservar negativos válidos. No exigir meses adicionales que la definición no utiliza.

Para valores estrictamente positivos, es una transformación monótona del cociente correspondiente. Por eso no se presupone mucha información nueva frente al relativo convencional. Un aporte puede involucrar ceros, signos, cobertura o detalles del aprendizaje e histogramas. No atribuirlo automáticamente a una sola causa. H_S evalúa el bloque completo; aislar causas requeriría otros brazos fuera de v7.

## 9. Hipótesis y contrastes

Principales:

1. H_T contra R4.
2. H_T contra T4.
3. H_S contra R4.

H_T debe superar a ambos componentes para sostener que la combinación mejora frente a ambos. Ganarle solo a B0 no basta.

Secundarios: RK, P3, MIN3, RAN3, R3, R4 y T4 contra B0; R4 contra R3. Son ocho contrastes.

No convertir retrospectivamente un contraste secundario favorable en principal. Las conclusiones de desarrollo se fijan usando agosto. Octubre evalúa persistencia de las hipótesis congeladas y no permite volver a seleccionar el diseño.

## 10. Optimización y semillas

LightGBM binario. Positivo de entrenamiento: BAJA+1 o BAJA+2. AUC de agosto: BAJA+2 contra resto. Pesos iguales, sin sampling previo; bagging interno permitido, con `bagging_freq=1`.

Cada brazo recibe su propia búsqueda con igual espacio y presupuesto:

| Parámetro | Espacio |
|---|---|
| num_leaves | 16–128, entero logarítmico |
| learning_rate | 0,01–0,1, logarítmico |
| min_data_in_leaf | 100–2.000, entero logarítmico |
| feature_fraction | 0,3–1 |
| bagging_fraction | 0,5–1 |

Diez trials Optuna TPE, cinco iniciales; máximo 1.500 árboles y early stopping 100 por AUC de agosto. Seleccionar mayor AUC, desempatar por primer trial. Congelar hiperparámetros y árboles; entrenar cinco semillas posteriores sin nuevo early stopping.

Usar cinco semillas de evaluación comunes entre brazos, diferentes de las de búsqueda y verificadas contra las corridas anteriores. Congelar valores concretos en el contrato antes de ejecutar. Registrar también semillas internas, hilos, opciones deterministas, configuración efectiva y versiones.

No ampliar búsqueda o semillas selectivamente después de ver quién pierde. Diez trials son un presupuesto acotado, no optimización exhaustiva. La elección de AUC sigue la consigna de Ale; informar desacuerdos con ganancia.

## 11. Ganancia y presupuesto común

Regla económica:

`G = 1.072.500 * aciertos_BAJA2 - 27.500 * otros_contactos`

Equivalente:

`G = 1.100.000 * aciertos_BAJA2 - 27.500 * contactos`

No descontar dos veces el costo de un acierto. Ordenar score descendente y cliente ascendente para desempatar.

### Política principal

Una vez entrenado B0, promediar sus cinco scores por cliente. En agosto, elegir su corte con la política histórica de media móvil centrada completa de 2.001 posiciones sobre la curva acumulada, sin relleno en extremos, y menor corte ante empate. Guardar posición exacta, ganancia suavizada, ganancia puntual y proporción.

Congelar `p_B0 = k_B0_agosto / N_agosto`. Este presupuesto no puede cambiar al ver otro brazo. Optuna sigue usando AUC, por lo que no depende de este presupuesto.

- Agosto: evaluar todos los ensembles y todas las semillas en el mismo `k_B0_agosto`.
- Octubre: evaluar todos en `floor(p_B0 * N_octubre)`.

La métrica principal es la diferencia de ganancia puntual del ensemble a ese presupuesto común. No comparar como si fueran iguales ganancias suavizadas y puntuales. Conservar el entero original de agosto para evitar errores de redondeo.

El presupuesto de B0 se optimiza en agosto: reportar ese sesgo de desarrollo y su anclaje en el control. Igualar contactos no garantiza menor varianza ni convierte la comparación en causal.

### Política propia como diagnóstico

Calcular en agosto los cortes propios por semilla y ensemble con la misma regla de 2.001 posiciones. Congelarlos y transferir sus proporciones a octubre, sin optimización allí.

Presentar esas ganancias por separado. No elegir después entre política común y propia según cuál favorezca a cada candidato.

El ensemble promedia scores, no ganancias. Reportar por separado ganancia del ensemble y media de ganancias individuales, contactos, aciertos, AUC y diferencias absolutas/porcentuales. Verificar cada ganancia mediante aciertos y contactos enteros.

## 12. Decisión de desarrollo y evaluación de cierre

Agosto decide las conclusiones de desarrollo de los contrastes principales. Antes de abrir la evaluación económica de octubre, guardar una tabla con las conclusiones, las métricas comunes y los diagnósticos propios.

Una señal económica favorable en agosto requiere delta del ensemble positivo y media de diferencias individuales positiva. Informar cuántas semillas favorecen; 4/5 no será una prueba de significación. La interpretación de incertidumbre corresponde a la sección siguiente. No utilizar esta regla para omitir ningún brazo de octubre.

Octubre evalúa todos los brazos con modelos, columnas y presupuestos congelados. Reportar persistencia, reversión o inconclusión respecto de agosto. No rescatar un brazo desfavorable cambiando después la hipótesis. Octubre ya conocido no constituye confirmación independiente.

## 13. Incertidumbre y multiplicidad

Para cada contraste y por separado para agosto y octubre, reportar delta del ensemble, media y mediana de deltas pareados por semilla, dispersión, peor delta y semillas favorables.

Bootstrap principal sobre las contribuciones económicas del ensemble a presupuesto común: 2.000 réplicas, semilla congelada, toda la población de clientes incluidos no contactados, mismos clientes remuestreados para ambos modelos y, preferiblemente, para todos los contrastes del mes. Usar modelos y decisiones de contacto fijos. No combinar agosto y octubre como muestras independientes de clientes.

Congelar método percentil y cuantiles antes de ejecutar. Para los tres contrastes principales, informar intervalos individuales 95% y aproximadamente 98,33% por contraste mediante Bonferroni (cuantiles 0,008333 y 0,991667). Estos últimos son un control aproximado y conservador dentro de la familia principal de cada mes, no una corrección de toda la exploración previa o de elegir el mes más favorable.

Los ocho contrastes secundarios son exploratorios: mostrar intervalos 95% sin afirmar superioridad simultánea. No mezclar conclusiones corregidas y no corregidas.

El bootstrap condicional no reentrena, no vuelve a elegir top-k, no incorpora la incertidumbre de Optuna o del presupuesto elegido y no corrige el uso previo de los meses. Cinco semillas tampoco equivalen a cinco períodos independientes. No interpretar el intervalo como garantía de una campaña futura.

No inventar retrospectivamente un umbral económico para favorecer conclusiones. Informar magnitudes, porcentajes, complejidad y costo. Las ganancias son de la regla del concurso, no ingresos reales demostrados.

## 14. Congelamiento y controles antes de octubre

Guardar contrato, commit, entorno, listas ordenadas de columnas, identidades de matrices, modelos, hashes, parámetros, árboles, predicciones de agosto, proporción común, cortes propios, contrastes y conclusiones de desarrollo.

Regenerar predicciones de agosto desde los modelos respaldados y compararlas con las archivadas usando tolerancias definidas de antemano. Bloquear octubre si hay discrepancias no explicadas.

No reentrenar ni seleccionar columnas con octubre. Evaluarlo para los diez brazos completados. Registrar incidentes, conservar resultados previos y no sobrescribirlos silenciosamente.

## 15. Presupuesto y operación

Diez brazos por diez trials y cinco entrenamientos: 100 ajustes Optuna + 50 modelos de evaluación = 150 ajustes principales.

No incluye auditoría, preparación de matrices, evaluación, bootstrap ni repetición independiente. Presupuestar la réplica completa por separado: no queda financiada por contabilizar los 150 ajustes iniciales.

Antes de encender o contratar recursos, verificar acceso y almacenamiento; estimar memoria, tiempo y costo; fijar límite de duración y gasto; preparar respaldo y mecanismo de apagado verificable; obtener aprobación del contrato y presupuesto completos. No suponer seis horas ni extrapolar linealmente v4 como garantía.

Tras aprobarse el plan, continuar sin pedir otra autorización para cada brazo. Las ampliaciones fuera del presupuesto requieren un plan nuevo.

Una interrupción puede reanudarse desde checkpoints si permanecen idénticos contrato, datos y código y se valida su integridad. Cambios metodológicos requieren revisión nueva. Apagar no significa borrar discos ni destruir respaldos.

## 16. Trazabilidad obligatoria

Destino: `ClariRZ/Experimentos-/HISTORIA_2019_01/v7`. El guion final forma parte del nombre real del repositorio.

Antes de entrenar, congelar prompt, contrato, commit, dataset, saneamiento, calendario, fórmulas, fuentes, semillas, búsqueda, entorno y tolerancias de reproducción. Un cambio posterior no puede entrar silenciosamente en el mismo identificador de corrida.

Durante la ejecución:

- Identificar cada brazo, trial y modelo con un ID único.
- Guardar parámetros, métricas, árboles, tiempos, estados y errores.
- Conservar todas las búsquedas, incluidos trials fallidos o podados.
- Registrar claves, filas y columnas ordenadas de cada matriz.
- Guardar modelos, predicciones y políticas con hashes.
- Comprobar alineación y población común.
- Vincular cada cifra del informe con el archivo que la origina.

Git público contendrá código, documentación, configuración, dependencias, pruebas, manifiestos y agregados. No publicar credenciales, datos individuales ni predicciones identificables.

Dataset, modelos y predicciones individuales tendrán respaldo privado duradero. Registrar su ubicación privada y probar recuperación e integridad antes de dar el respaldo por cerrado. Un hash sin archivo recuperable no es suficiente.

## 17. Verificación y reproducción independiente

### Verificación de la corrida

Regenerar predicciones desde modelos guardados; recalcular cortes, contactos, aciertos y ganancias; generar automáticamente las tablas desde archivos de resultados. El verificador debe fallar ante diferencias no toleradas, archivos ausentes o inconsistencias.

Incluir pruebas de huecos temporales, fórmulas, ceros, signos, nulos, empates, alineación, presupuesto común, política propia, selección solo con entrenamiento, reanudación y bloqueo de octubre. No limitarse a contar pruebas aprobadas.

### Repetición independiente de v7

En otra máquina o entorno limpio, usar únicamente el dataset identificado y el código/contrato versionados para reconstruir matrices y repetir búsqueda, entrenamiento y evaluación. No usar como insumos modelos o matrices de la primera ejecución.

Fijar versiones exactas y registrar sistema, arquitectura, librerías, hilos y configuración efectiva. Usar la misma secuencia determinista de trials; no paralelizar adaptativamente Optuna si cambia la propuesta de trials.

Antes de comparar, definir tolerancias. Exigir identidad exacta de claves, clases, fórmulas, orden de columnas, reglas y parámetros cuando corresponda. Establecer tolerancias numéricas para matrices y scores; comprobar además rankings, contactos y ganancias, porque un error pequeño de score puede cambiar el corte.

Comparar trials, mejor configuración, árboles, predicciones y métricas. Documentar cualquier diferencia y su causa; no ampliar tolerancias después para declarar éxito. No garantizar igualdad bit a bit entre hardware diferente sin haberlo comprobado.

Esta repetición requiere presupuesto propio. Hasta completarla, describir el estado como trazable y preparado para reproducción, o como predicciones regeneradas, según la evidencia. No llamarlo reproducido independientemente.

## 18. Entregable final

Informe completo con hipótesis; diseño; población; saneamiento y diferencias históricas; definiciones de diez brazos; parámetros; resultados de agosto y octubre bajo ambas políticas; contrastes principales y secundarios; semillas; intervalos y límites; cobertura; costos; negativos e inconclusos; y estado de reproducción.

Explicar qué recetas provienen de v4/v5/v6 y que cambiaron al calendario abril–junio. No sumar ganancias de componentes para anticipar una combinación. No comparar millones entre versiones como si fueran el mismo control.

Entregar instrucciones para reconstruir desde el dataset original y un verificador automático. Separar claramente archivo verificado, predicción regenerada y entrenamiento reproducido de forma independiente.

## 19. Primera acción del ejecutor

Comenzar por auditoría, sin entrenar. Informar dataset accesible e identificado, saneamiento julio–octubre resuelto, definiciones preservadas, matrices válidas, cobertura, población común, semillas concretas, configuración, tolerancias, presupuesto inicial y de réplica, respaldo y apagado.

Si falta evidencia, decir exactamente qué falta y cómo obtenerla. No sustituirla por suposiciones ni interpretar este documento como una corrida ya realizada.

Una vez aprobado el contrato ejecutable y presupuesto, ejecutar el alcance cerrado de diez brazos. No agregar pruebas a partir de sus resultados.

## Resolución de saneamiento y revisión previa — 2026-11-14

Esta resolución posterior prevalece sobre las propuestas anteriores de correcciones nuevas. Clara indicó: «tratemos octubre como siempre, documentemos anomalías y sigamos adelante».

Conservar las nueve máscaras históricas de abril/mayo por continuidad con v4/v5/v6, sin presentarlas como una confirmación oficial nueva. No agregar máscaras de julio ni octubre. Preservar ceros y faltantes originales de esos meses; registrar las anomalías con su evidencia, hipótesis y causa no confirmada. Ningún listado externo se toma como autoridad para modificar el dataset. El archivo de origen permanece intacto.

La auditoría del dataset y la decisión de tratamiento son diferentes: el hash certifica qué archivo se examinó, no demuestra la causa de los ceros. El tratamiento de todos los brazos será idéntico y no se escogerá según el resultado de octubre.

El control de entorno se realiza antes de entrenar, exige las versiones centrales del contrato y captura el inventario completo de distribuciones. Los controles de cobertura y fórmulas distinguen causas de faltantes, sin imputar. Guardar advertencias y abortar ante identidad, claves, calendario o entorno incompatibles. La autorización comprende continuar con este protocolo; las verificaciones técnicas siguen siendo obligatorias.

El apagado del sistema y el límite independiente de GCE son defensas complementarias. Si falla la conexión, el apagado inmediato y la recuperación externa no pueden darse por hechos; verificar su estado. No ampliar presupuesto ni iniciar reproducción independiente automáticamente.
