# Relevamiento de v4, v5 y v6 y propuesta de híbrido


Estado: análisis y propuesta. No se entrenaron modelos nuevos. Pesos de clases iguales, según decisión de Clara.


## 1. Historia 2019

Relevamiento de v4, v5 y v6
Comparación con Ezequiel y propuesta de híbrido

Clara Rodríguez

Resultados al 13 de noviembre de 2026

Alcance: los tres experimentos recientes v4, v5 y v6. C3 figura como antecedente, no como una cuarta corrida comparable. Esta presentación no ejecuta entrenamiento nuevo.

Fuentes: 



## 2. Tres preguntas, tres experimentos


| Versión | Pregunta | Entrenamiento | Ajustes | Octubre |
|---|---|---|---|---|
| v4 | ¿Qué representación corta ayuda? | Marzo–junio | 75 | Evaluado |
| v5 | ¿Qué componente aporta por separado? | Marzo–junio | 105 | Pendiente |
| v6 | ¿Aporta más profundidad histórica? | Junio | 165 | Evaluado |
345 ajustes registrados: 230 pruebas Optuna y 115 modelos por semilla.

La suma contabiliza ajustes de las tres corridas, no garantiza 345 modelos distintos. v4: 5 brazos; v5: 7; v6: 11. Cada brazo tiene 10 trials y 5 ajustes por semilla. v5 no tiene evaluación de octubre en los archivos revisados.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/experimento_2026-11-13/README.md
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01/FINAL.json
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/v6_20261113_02/FINAL.json



## 3. Reglas comunes y cambios entre versiones



Datos de 2019, LightGBM y entrenamiento sin muestreo. Positivos: BAJA+1 y BAJA+2. Pesos iguales.

AUC de BAJA+2 en agosto para Optuna y early stopping. Diez pruebas propias por alternativa.

Ganancia: +$1.072.500 por BAJA+2 contactada y −$27.500 por otro contacto.

v4 decidió por AUC. v5 y v6 usaron una regla exploratoria de ganancia y consistencia.

Saneamiento de nueve pares variable-mes antes de la historia. Conservar faltantes, rezagos calendario exactos y depuración solo en entrenamiento. Semillas v4: 101,211,307,401,503; la 101 también participó de Optuna. v5/v6: 211,307,401,503,601, separadas de la 101 de Optuna. Ninguna de estas etapas ejecutó canaritos.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/experimento_2026-11-13/configuracion/contrato_original.json
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v5/configuraciones/etapa1_autorizada_20261113.json



## 4. Qué representan las variables históricas

Ejemplo de tres meses: 100, 80 y 60. El valor actual es 60.
| Variable | Cálculo | Lectura |
|---|---|---|
| Lag1 / lag2 | 80 / 100 | Valores previos |
| Delta1 / delta2 | −20 / −40 | Cambio absoluto |
| Promedio / mínimo / máximo | 80 / 60 / 100 | Nivel y extremos |
| Rango | 100 − 60 = 40 | Amplitud de los valores |
| Cambio relativo al primero | (60 − 100) / |100| = −40% | Caída proporcional |
Las ventanas incluyen el mes actual. Las fórmulas de resúmenes y ratios requieren ventana completa y no nula en nuestras corridas. La tendencia T4/T6 es la pendiente de una recta ajustada a cuatro/seis observaciones equiespaciadas, no un cambio relativo.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/scripts/fe_core.py



## 5. v4: familias de historia corta

B0: variables actuales + lag1/2 + delta1/2. 652 columnas después de depurar.
| Brazo | Qué agrega a B0 | Δ agosto M | Δ octubre M | Gana en octubre |
|---|---|---|---|---|
| F1 | Promedio, mínimo, máximo y rango | +3,20 | +12,16 | 2/5 |
| F3 | Cambios relativos | +2,73 | +7,15 | 4/5 |
| F4a | Ranking dentro del mes | −7,51 | +10,26 | 5/5 |
| F4b | Historia de rankings | −11,18 | −7,89 | 0/5 |
F3 mejoró la ganancia en ambos meses. F4a cambió de signo entre agosto y octubre.

Deltas del ensemble frente al B0 de v4. Agosto: ganancia suavizada; octubre: ganancia puntual al corte congelado. B0 octubre 277,145 M. La regla original por AUC no promovió ninguna variante y mantuvo B0. F1 ganó en el ensemble, pero solo 2/5 semillas de octubre. Estos resultados descriptivos no cambian esa decisión.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/experimento_2026-11-13/resultados/octubre/FINAL.json
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/experimento_2026-11-13/documentacion/analisis_agosto.md



## 6. v5: mínimo y rango funcionaron por separado

Misma historia corta. Cada componente parte del mismo baseline.
| Alternativa | Δ ensemble agosto M | Favorables | Regla de ganancia |
|---|---|---|---|
| Mínimo | +5,11 | 5/5 | Cumple |
| Rango | +4,18 | 5/5 | Cumple |
| Promedio | +3,99 | 4/5 | Cumple |
| Máximo | +2,51 | 2/5 | No cumple |
| Todos los resúmenes | +1,48 | 1/5 | No cumple |
| Rezagos sin deltas | −1,66 | 1/5 | No cumple |
Combinar todas las variables no sumó sus mejoras. Octubre sigue pendiente para v5.

B0 ensemble agosto 205,0447 M. Regla: delta ensemble >0, delta medio por semilla >0 y al menos 4/5 victorias. Es una regla operativa, no una prueba de significación. Ninguna alternativa aumentó el AUC medio frente a B0. No atribuir causalmente el peor resultado conjunto a correlación sin una prueba específica.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01/FINAL.json



## 7. v6: más historia con el mismo mes de entrenamiento


| Uso | Meses / detalle |
|---|---|
| Historia disponible | Enero a junio para entrenar |
| Filas de entrenamiento | Junio, 128.474 clientes |
| Validación | Agosto, 131.887 clientes |
| Comparación económica | Octubre, 135.754 clientes |
| Alternativas | Más rezagos, resúmenes, tendencias y cambios relativos |
El baseline también usa solo junio. Esto permite comparar ventanas de 3, 4 y 6 observaciones.

No equivale a entrenar con seis meses: cada fila de junio tiene historia previa. B0_J tiene 634 columnas. L4/L6 760/1012; S3/S4/S6 1102; T4/T6 751; R3/R4/R6 985. Selección de pares fuente-fórmula comunes usando junio. v6 no compara causalmente con v5 porque cambian las filas.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/v6_20261113_02/data_identity.json
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/v6_20261113_02/feature_manifest.json



## 8. v6: T4, R3 y R4 mejoraron en ambos meses

Diferencia de ganancia del ensemble contra B0_J, en millones

T4, R3 y R4 ganaron en 5/5 semillas de octubre. R6 revirtió una pérdida de agosto.

En octubre, T4 +6,82 M, R3 +11,6875 M y R4 +15,125 M, cada uno 5/5 semillas. R6 +16,06 M y 4/5, pero agosto −3,5059 M y 1/5. Los dos meses usan definiciones de ganancia diferentes, que se declaran en las series. Comparar signo y consistencia, no tomar el incremento de barra entre meses como un efecto causal.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/octubre_v6_01/INFORME.md



## 9. Qué resultados podemos sostener



Los cambios relativos muestran señales favorables en v4 y v6, con recetas y calendarios diferentes.

El mínimo aislado fue consistente en agosto de v5. Falta comprobarlo en octubre.

T4 añadió una señal favorable en los dos meses de v6. Su combinación con R4 sigue sin probarse.

Más meses y más variables no garantizaron una mejora. Las combinaciones necesitan su propia comparación.

No sumar millones de distintos experimentos ni calcular una ganancia total entre ellos. En v4, F3 contiene W3, en v6 R4 W4 y solo junio de entrenamiento. Todos los resultados posteriores usan períodos ya explorados. Es información para diseñar hipótesis, no garantía de rendimiento futuro.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/octubre_v6_01/INFORME.md
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01/FINAL.json



## 10. El paquete de Ezequiel combina ocho bloques


| Bloque | Qué representa | Cols. |
|---|---|---|
| AC | Originales, rezagos y deltas 1/2 | 760 |
| CURADA | Ratios, normalización y ranking sobre 30 fuentes | 120 |
| ACH_V | Dispersión de valores y de cambios | 60 |
| ACH_Q | Quiebres, peor caída y cantidad de caídas | 90 |
| ACH_T | Relación con historia y tiempo desde máximo | 90 |
| ACH_Z | Percentiles de cambios con cero fijo | 60 |
| MVH | Visa + Master y su historia de 1/2 meses | 215 |
| R | Cambios relativos simétricos de 1/2 meses | 258 |
Total 1653. AC aplica lags/deltas a 152 fuentes; nuestros baselines usan 129 fuentes históricas revisadas y depuración adicional. CURADA y ACH usan 30 fuentes elegidas previamente. Su disponibilidad admite historia parcial en algunas fórmulas. No asumir que nuestras 129 fuentes son la misma lista por tener igual número.

Fuentes: https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/funciones.py
https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/parametros.py



## 11. La comparación exige igualar las condiciones


| Aspecto | Nuestros v4 / v5 / v6 | PAQ_P3 de Ezequiel |
|---|---|---|
| Target al entrenar | BAJA+1 y BAJA+2 | BAJA+1 y BAJA+2 |
| Pesos de clases | Iguales | BAJA+2 pesa 3 |
| Entrenamiento | Marzo–junio o junio fijo | Se amplía hasta dos meses antes |
| Evaluación | Agosto y cierre en octubre | Banco de junio a octubre |
| Ganancia | Corte propio congelado | Promedio de banda 3.000–6.000 |
| Incertidumbre | Cinco semillas | Cinco semillas y bootstrap |
Ventana reciente no es móvil de largo fijo: se expande desde marzo hasta t−2. Así, octubre entrena marzo–agosto en PAQ_P3, mientras nuestros modelos conservan marzo–junio o junio. El bootstrap de Ezequiel remuestrea clientes sobre contribuciones a la banda y combina ese error con uno de semillas. No prueba generalización a meses no observados. Nuestra decisión de no ponderar BAJA+2 se mantiene.

Fuentes: https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/funciones.py
https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/parametros.py



## 12. Dos fórmulas distintas para el cambio relativo


| Situación | Nuestro cambio relativo | Simétrico de Ezequiel |
|---|---|---|
| Fórmula | (actual − referencia) / |referencia| | (actual − previo) / (|actual| + |previo|) |
| De 100 a 60 | −0,40 | −0,25 |
| De 0 a 60 | Faltante | +1 |
| De 0 a 0 | Faltante | 0 |
| Historia requerida | W3, W4 o W6 completa | El par actual y rezago |
El simétrico queda entre −1 y 1. Su manejo de ceros cambia también la cobertura.

En la primera fórmula la referencia puede ser promedio, mes anterior o primer mes de la ventana. En la segunda solo los rezagos 1/2 en el bloque R. Un faltante produce NA en ambas. La comparación de recetas cambia fórmula y máscara: si se quiere aislar la fórmula, comparar antes con la misma máscara y los mismos pares.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/scripts/fe_core.py
https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/funciones.py



## 13. Los resultados de Ezequiel pertenecen a PAQ_P3


| Contraste publicado | Δ media M/mes | Intervalo 95% | Semillas |
|---|---|---|---|
| PAQ_P3 vs AC, misma ventana | +9,00 | +5,18 a +12,82 | 5/5 |
| PAQ_P3 vs A-consigna | +12,60 | +7,73 a +17,46 | 5/5 |
El código actual declara 451 árboles y 113 hojas. Las tablas conservan la referencia PAQ_P3 de 296 árboles y 50 hojas.

No atribuir estas mejoras al nuevo ajuste ni compararlas directamente con nuestros millones de octubre.

Copia revisada: commit 770abaa9cad412647211c255360cb6dfe364e697. main_comparacion.csv y valores esperados PAQ_P3 coinciden en 8.9986 y 12.5970. El código MAIN sobreescribe HIPER_03 con HIPER_MAIN. No se encontró una tabla de resultados identificada de forma inequívoca con esos nuevos parámetros. No se reentrenó ni se ejecutó reproducción cruzada del repo de Ezequiel.

Fuentes: https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/resultados/pipeline/main_comparacion.csv
https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/parametros.py
https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/README.md



## 14. Qué podemos recuperar para un híbrido


| Prioridad | Componente | Por qué probarlo |
|---|---|---|
| Primera | R4 + tendencia T4 | Ambos mejoraron en agosto y octubre de v6 |
| Primera | Cambio relativo simétrico | Nueva representación, acotada y sensible a ceros |
| Después | Quiebre y caídas de ACH_Q | Describe cambios abruptos de actividad |
| Después | Visa + Master con historia | Agrega relaciones entre productos |
| Evaluación | Bootstrap pareado por cliente | Cuantifica incertidumbre de la diferencia |
Son hipótesis, no aportes confirmados del híbrido. No incorporar peso 3 por decisión de Clara. No priorizar desvíos/z-scores: Ale favoreció variables más interpretables, aunque su utilidad empírica debe evaluarse. C3 contenía transiciones, recencia y tarjetas, pero era 2021 y no valida estas fórmulas en 2019. El antecedente Ale+C3 en 2019 sumó 43 variables intrames y no produjo una mejora consistente entre 20 semillas.

Fuentes: https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/funciones.py
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/octubre_v6_01/INFORME.md
https://github.com/ClariRZ/Segunda_competencia/tree/main/experimento_Ale_C3_2019



## 15. Propuesta de primera prueba híbrida

Diseño pendiente de aprobación. Todas las alternativas usan el mismo calendario.
| Brazo propuesto | Contenido | Pregunta |
|---|---|---|
| H0 | R4: baseline + relativos W4 | Control común reoptimizado |
| H1 | H0 + T4 | ¿La tendencia agrega información? |
| H2 | H0 + relativos simétricos | ¿Complementan los cambios actuales? |
10 pruebas Optuna y 5 semillas por brazo: 45 ajustes propuestos. Pesos iguales.

Misma selección de fuentes, saneamiento y presupuesto. La unión H1 + H2 queda para otra etapa.

H0 se elige después de observar octubre, así que la nueva prueba será exploratoria. Elegir R4 como control es una hipótesis práctica, no una confirmación de que sea superior a R3 en general. Se congelarían fórmulas y tratamiento de ceros antes de entrenar. H2 prueba una adición de paquete; para atribuir el efecto a la fórmula se necesita una ablación de igual máscara. No se lanzó ningún entrenamiento para esta presentación.

Fuentes: Propuesta propia basada en los resultados anteriores. No ejecutada.



## 16. La evaluación del híbrido



Agosto seguirá guiando la optimización. Los cortes y modelos se congelarán antes de informar octubre.

Octubre será una comparación exploratoria: ya lo usamos para formular esta propuesta.

Bootstrap pareado sobre los mismos clientes, con políticas fijas. Reportar su incertidumbre junto a las cinco semillas.

Una rama temporal posterior podrá evaluar varios meses de 2019, siempre con controles entrenados en las mismas filas.

Para reproducir el bootstrap de Ezequiel hay que mantener su estimando de contribuciones a una banda. Para nuestro corte fijo, documentar un estimando propio: remuestrear contribuciones pareadas de clientes a políticas congeladas, sin volver a buscar N. Si se remuestrean scores y se reordena la muestra, es otro estimador y debe declararse. Si hay varios meses, remuestrear por ID preservando su trayectoria. Los intervalos son condicionales al proceso elegido y no corrigen la selección repetida de meses/modelos. Nunca usar 2020 en esta propuesta por instrucción de Clara.

Fuentes: https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/funciones.py
Propuesta metodológica propia, pendiente de ejecución.



## 17. Pendientes antes de gastar más cómputo



Cerrar octubre de v5 para el mínimo y el rango, con sus modelos y cortes ya congelados.

Acordar el protocolo del híbrido y dejar explícito qué cambia en cada brazo.

Conciliar la versión de Ezequiel: código actual, resultados publicados y definición de ganancia.

Mantener los originales intactos y guardar el híbrido en una carpeta nueva con su contrato.

No ejecutar automáticamente la corrida propuesta al entregar la presentación. La evaluación de v5 requeriría autorización específica si se decide avanzar. Los modelos/predicciones siguen privados. Prioridades propuestas: terminar evidencia pendiente, comparar metodologías, recién después nueva combinación. El objetivo futuro es un pipeline que incorpore historia al llegar nuevos meses y la compare con un control equivalente.

Fuentes: Síntesis y próximos pasos propuestos.



## 18. Anexo: las once alternativas de v6


| Brazo | Ganancia oct. M | Δ oct. M | Gana oct. | Δ ago. M | Gana ago. |
|---|---|---|---|---|---|
| B0_J | 261,86 | — | — | — | — |
| L4 | 266,17 | +4,32 | 2/5 | +0,11 | 1/5 |
| L6 | 268,21 | +6,35 | 3/5 | +2,18 | 3/5 |
| S3 | 268,79 | +6,93 | 4/5 | +0,68 | 2/5 |
| S4 | 268,37 | +6,52 | 2/5 | −2,98 | 1/5 |
| S6 | 268,65 | +6,79 | 2/5 | −7,08 | 0/5 |
| T4 | 268,68 | +6,82 | 5/5 | +6,23 | 5/5 |
| T6 | 263,75 | +1,90 | 4/5 | −4,74 | 0/5 |
| R3 | 273,54 | +11,69 | 5/5 | +5,45 | 5/5 |
| R4 | 276,98 | +15,13 | 5/5 | +4,76 | 4/5 |
| R6 | 277,92 | +16,06 | 4/5 | −3,51 | 1/5 |
L: rezagos. S: resúmenes. T: tendencia. R: relativos. Ventanas con mes actual.

Diferencias contra B0_J. Agosto suavizado y octubre puntual. Cada seed tiene corte propio congelado en v6; en v4 todos los seeds de un brazo compartieron el corte del ensemble. Ganancias de ensemble no equivalen a media de ganancias individuales.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/octubre_v6_01/FINAL.json
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/v6_20261113_02/FINAL.json



## 19. Fuentes y alcance de la trazabilidad



Experimentos propios: contratos, trials, resultados por semilla, métricas y verificadores versionados.

Octubre v6: 55 predicciones de agosto reproducidas exactamente antes de evaluar. VM apagada y agregados publicados.

Ezequiel: lectura del código y tablas del commit 770abaa9. Sin reproducción independiente del entrenamiento.

La presentación conserva las fuentes de cada lámina en las notas. Los resultados siguen siendo exploratorios.

Repositorio propio revisado hasta ad41bae. Fuentes: experimento_2026-11-13 para v4; HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01; HISTORIA_2019_01/v6/resultados/v6_20261113_02 y octubre_v6_01. v4 mantiene límites de trazabilidad de entorno/auxiliar y no se ha vuelto a entrenar en otra máquina. La ganancia de un único mes no equivale a una promesa de rendimiento futuro.

Fuentes: https://github.com/ClariRZ/Experimentos-/blob/ad41bae/experimento_2026-11-13/README.md
https://github.com/ClariRZ/Experimentos-/blob/ad41bae/HISTORIA_2019_01/v6/resultados/octubre_v6_01/INFORME.md
https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/770abaa9cad412647211c255360cb6dfe364e697/pipeline/README.md

