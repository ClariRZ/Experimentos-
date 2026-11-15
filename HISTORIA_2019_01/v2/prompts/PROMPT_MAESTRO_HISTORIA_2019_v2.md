# PROMPT MAESTRO v2 — EXPERIMENTO HISTORIA 2019
## DMEyF 2026 — Diseño experimental, recuperación de C3 y de la VM, optimización de ganancia económica

Actuá como un científico de datos senior especializado en competencias de Data Mining, LightGBM, feature engineering histórico, estadística experimental y optimización de ganancia económica.

**Objetivo:** ganar la competencia mediante experimentos controlados que permitan identificar qué funciona realmente.

Integrar tres fuentes:

1. **Mi diseño original:** cuánto aportan lags, deltas, tendencias y otras representaciones de la historia del cliente.
2. **Lo ya ejecutado:** C3 de la primera competencia y las iteraciones 000–007 de `HISTORIA_2019_01` (Google Cloud).
3. **Las normas de Alejandro Bolaños** para la segunda competencia.

No empezar de cero, no repetir corridas, no construir variables indiscriminadamente.

---

## 0. REGLAS FIJAS (valen para todas las fases)

Estas reglas están decididas. No las reinterpretes; si alguna resulta inaplicable, detenete y avisame.

### R1. Una modificación por experimento
Entre un experimento y su control cambia una sola familia de variables o un solo elemento del procedimiento. Se mantienen constantes: filas de entrenamiento (meses y clientes), target, semillas, hiperparámetros, early stopping, validación, función de ganancia y regla de envíos. Nunca cambian a la vez variables, hiperparámetros y meses.

### R2. Compuerta de cobertura (se aplica antes de entrenar)
Una familia es **identificable** solo si tiene dato en **todos** los meses de entrenamiento, con una cobertura de clientes por mes ≥ 90% de los clientes presentes ese mes (umbral provisorio; informar la cobertura real).

- Familia no identificable → estado `NO IDENTIFICABLE`, no se entrena, se documenta el motivo.
- Una columna 100% NA en train no puede ser usada por LightGBM: el experimento no mide nada y solo agrega ruido vía `feature_fraction`.
- Una columna con NA en algunos meses de train y nunca NA en agosto/octubre codifica el mes y genera un desfase train/score. No es un experimento válido de "aporte del lag".
- Análisis secundario permitido: restringir el train a los meses con cobertura completa y reconstruir el **control sobre exactamente esas mismas filas**. Se informa aparte, rotulado como "universo restringido", y no se compara contra corridas del universo completo.

### R3. Hiperparámetros
- **Screening:** un único set fijo para todos los experimentos: el que resulte de Optuna sobre el baseline oficial (B4). Declarar en cada informe que esto favorece a B4 y que `feature_fraction` fijo regulariza distinto según la cantidad de columnas.
- **Finalistas:** reoptimizar control y finalista con **el mismo presupuesto de Optuna** (mismos trials, mismo espacio, misma semilla del sampler). Informar por separado el efecto de variables (HP fijos) y el efecto de HP (variables fijas).
- Espacio de Alejandro: `num_leaves`, `learning_rate`, `min_data_in_leaf`, `feature_fraction`, `bagging_fraction`, con `bagging_freq >= 1`. Optimización y early stopping por AUC.

### R4. Semillas
- Recuperar la lista de 20 semillas de la VM y usarla siempre, en el mismo orden.
- **Screening:** las primeras 5, pareadas contra el control. **Finalistas:** las 20.
- Las semillas miden varianza del algoritmo, no del muestreo de clientes. No tratarlas como observaciones independientes.

### R5. Regla de decisión (preregistrada, sobre agosto)
Para cada experimento vs. su control calcular, pareado por semilla: ΔAUC y Δganancia en agosto.

- **Ganancia en agosto:** función económica oficial (verificar parámetros en el libro de la cátedra, no asumirlos). Usar el máximo de la curva de ganancia **suavizada** (media móvil sobre cantidad de envíos; ventana provisoria: 2.001 envíos), no el máximo puntual.
- **Incertidumbre de muestreo:** bootstrap pareado de clientes de agosto (≥ 1.000 réplicas) sobre ΔAUC y Δganancia, con las predicciones promediadas entre semillas.

Veredicto:

| Veredicto | Condición |
|---|---|
| **APORTA** | Δganancia media > σ de las diferencias pareadas entre semillas **y** ≥ 80% de las semillas mejoran **y** el IC 90% bootstrap de Δganancia excluye 0 |
| **INDICIO** | ΔAUC > 0 en ≥ 80% de las semillas, sin cumplir lo anterior |
| **NO APORTA** | Resto |

Solo las familias con `APORTA` pasan a combinaciones. Las de `INDICIO` se reevalúan con 20 semillas una sola vez.

### R6. Multiplicidad
Declarar al inicio la cantidad total de comparaciones que se harán sobre agosto. Tratar el screening como un ranking de candidatos, no como una prueba. Ninguna familia se da por demostrada sin la confirmación con 20 semillas.

### R7. Octubre
- No se usa para elegir variables, hiperparámetros, combinaciones ni cortes.
- Se evalúa **una sola configuración candidata congelada**, más el baseline oficial (B4) como referencia. No se elige entre finalistas mirando octubre.
- Cantidad de envíos en octubre: la proporción de clientes que surge del corte óptimo suavizado en agosto. Se fija antes de puntuar octubre.

### R8. Selección de variables sin contaminar la validación
Todo ranking o filtro de variables se calcula **solo con datos de entrenamiento**. Si el método necesita holdout (permutation importance), usar junio con train marzo–mayo. Nunca agosto ni octubre.

### R9. Definiciones
- **lag_k:** valor de la variable del mismo cliente en el mes calendario t−k (join exacto cliente–mes; nunca desplazar filas). Si el mes no existe para el cliente → NA.
- **delta_k:** verificar la definición de Alejandro (¿x_t − x_{t−k} o lag_{k−1} − lag_k?) y usar la suya en toda la escalera. Documentar.
- **Ventana de n meses:** incluye el mes actual (t, t−1, …, t−n+1). "Seis meses anteriores" ≠ "ventana de seis observaciones".
- **Tendencia_n:** pendiente OLS del valor contra el índice de mes sobre la ventana de n meses; exige los n meses consecutivos observados, si no → NA.
- **Estadísticos móviles:** exigen la ventana completa; no calcular sobre ventanas parciales.
- No imputar faltantes. Distinguir cero real, cero por ausencia de producto, NA genuino, ausencia de historia y cero por rotura.

### R10. Hechos vs. interpretaciones
No asumir que un archivo existe ni que contiene lo que recordamos: verificarlo. Marcar cada afirmación como **verificado** (con ruta de archivo) o **hipótesis**. Una mejora de AUC no es una mejora económica demostrada. Una mejora de 2021 no se traslada automáticamente a 2019.

---

## 1. NORMAS DE ALEJANDRO (referencia de cumplimiento)

| Elemento | Configuración |
|---|---|
| Datos | 2019 |
| Entrenamiento | Marzo–junio de 2019 |
| Muestreo | Sin sampling |
| Target de entrenamiento | BAJA+1 y BAJA+2 |
| Validación | Agosto de 2019 |
| Test | Octubre de 2019 |
| Algoritmo | LightGBM |
| Optimización | Optuna, métrica AUC |
| Early stopping | AUC |
| Comparación final | Ganancia económica |

Verificar esta tabla contra el libro de la cátedra y las instrucciones guardadas; informar cualquier diferencia.

El baseline de Alejandro tiene lags y delta-lags de orden 1 y 2. Nuestro diseño empieza antes (RAW) para medir cada incorporación. Conservar siempre una corrida equivalente al baseline oficial.

---

## 2. PRIMERA TAREA: AUDITAR, NO ENTRENAR

No modificar archivos ni ejecutar modelos en esta etapa.

### 2.1. Computadora — carpeta `DMEyF`
Scripts de la primera competencia, C3 y variantes, configuraciones, resultados, código de FE, importancias, bibliografía, instrucciones de Alejandro, experimentos previos de historia y tarjetas.

### 2.2. C3
Qué variables usó; cómo construyó lags y deltas; transformaciones históricas; variables de tarjetas; resultado de cada variante; qué parte de la mejora es atribuible a una transformación concreta (y cuál no puede atribuirse); cómo seleccionó variables; hiperparámetros y semillas; ganancias pública y privada.

Para cada transformación de C3 que aparezca efectivamente en el código (lags/deltas, tarjetas Visa/Master, combinaciones entre productos, ratios entre montos, normalizadas, cambios relativos, estadísticos temporales, otras):

fórmula · variables de origen · evidencia de utilidad · compatibilidad con 2019 · cobertura · riesgo de leakage · experimento aislado necesario.

### 2.3. VM — `~/HISTORIA_2019_01/`
`historia.py`, `config_historia.json`, `resultados.json`, `resultados.tsv`, `B0_importance.csv`, `leaders_selected.json`, logs, predicciones de octubre, archivos de Optuna, semillas e hiperparámetros.

Determinar qué iteraciones se ejecutaron, cuáles terminaron y cuáles quedaron pendientes. Recuperar resultados sin reentrenar.

Antecedente a verificar: iteración 000 con 760 variables; iteración 003 con cuatro ratios más y AUC de agosto ≈ 0,914136 → 0,915105.

**Verificar además si en la VM se miró octubre durante el desarrollo.** Si ocurrió, declararlo: esas decisiones están contaminadas y no pueden usarse como evidencia limpia.

### 2.4. Calidad de datos
Por variable y mes: % NA, % ceros, clientes con observación válida, variables constantes o casi constantes, meses rotos, cambios anómalos de distribución, cambios de escala o definición.

### 2.5. Cobertura histórica (decide qué se puede experimentar)
Primero: **¿cuál es el primer mes disponible en el dataset?** Verificarlo en los datos.

Luego completar, para cada mes de train (marzo, abril, mayo, junio), agosto y octubre:

| Familia | Mar | Abr | May | Jun | Ago | Oct | ¿Identificable (R2)? |
|---|---|---|---|---|---|---|---|
| lag1 … lag6 | | | | | | | |
| delta1 … delta6 | | | | | | | |
| ventana 3 (mean/min/max/std/streak/ratio) | | | | | | | |
| tendencia 3, 4, 5, 6 | | | | | | | |

Expectativa a contrastar si los datos empiezan en enero de 2019: lag1–lag2 y ventana 3 cubren los 4 meses; lag3 cubre 3; lag4 cubre 2; lag5 solo junio; lag6 ninguno. En ese caso la escalera válida termina en B4, con B5–B6 solo como análisis de universo restringido (abril–junio).

### 2.6. Preguntas que debe responder la auditoría
1. ¿Qué transformaciones funcionaron realmente en C3 y con qué evidencia?
2. ¿Qué iteraciones de la VM están completas y cuáles faltan?
3. ¿Qué diferencias hay entre el histórico de la VM y este diseño (variables, semillas, HP, uso de octubre)?
4. ¿Qué familias son identificables según R2?
5. ¿Qué meses o variables tienen problemas de calidad?
6. ¿Qué método de selección de variables conviene (sección 3)?
7. ¿Qué experimentos ya están resueltos con resultados reutilizables bajo estas reglas?
8. ¿Cuáles faltan?
9. ¿Qué requiere consulta con Alejandro (sección 8)?
10. ¿Qué orden de ejecución maximiza aprendizaje por costo?

Cerrar con la tabla:

**Experimento | Hipótesis | Único cambio | Variables nuevas | Cobertura por mes | Identificable | Control | Estado | Costo estimado | Prioridad**

y con el conteo total de comparaciones previstas sobre agosto (R6).

**Esperá mi aprobación antes de ejecutar cualquier corrida.**

---

## 3. SELECCIÓN DE VARIABLES (shortlist única y congelada)

- La escalera B (lags y deltas) se construye sobre **todas** las variables RAW elegibles, como el baseline oficial.
- Las demás familias (M, Z, R, K, T, C3) se construyen sobre una **shortlist única de 20 variables**, congelada antes del primer experimento y usada por todas las familias.
- Las RAW nunca se eliminan: la shortlist decide dónde construir transformaciones.

Construcción de la shortlist (todo según R8):

1. Recuperar el método de C3 y el de la VM (`B0_importance.csv`, `leaders_selected.json`) e informar cómo se eligieron.
2. Comparar: gain de LightGBM, estabilidad del ranking entre semillas, permutation importance, variabilidad temporal, calidad histórica, redundancia.
3. Fijar el criterio de combinación **antes** de ver el ranking resultante.
4. No asumir que las variables más importantes en el mes actual son las que más ganan con historia: incluir en el informe un screening barato (lag1/delta1 por variable) como criterio adicional.

Si la VM eligió a mano (`ctrx_quarter`, `mpayroll`, `mcaja_ahorro` en la iteración 002), informarlo como tal.

---

## 4. EXPERIMENTOS

### 4.1. Escalera progresiva B (estructura principal)

| Exp. | Configuración | Único cambio | Control |
|---|---|---|---|
| B0 | RAW | — | — |
| B1 | RAW + lag1 | lag1 | B0 |
| B2 | B1 + delta1 | delta1 | B1 |
| B3 | B2 + lag2 | lag2 | B2 |
| B4 | B3 + delta2 | delta2 | B3 |
| B5 | B4 + lag3 | lag3 | B4 |
| B6 | B5 + delta3 | delta3 | B5 |
| B7–B12 | lag4 … delta6 | uno por paso | paso anterior |

- **B4 = estructura del baseline de Alejandro**, previa verificación de que las definiciones coinciden. Verificar también que coincida con la iteración 000 de la VM.
- Cada paso se compara con el inmediato anterior, y además con B0 y B4.
- B5 en adelante se ejecutan **solo si pasan R2**. Si no, quedan como `NO IDENTIFICABLE` o como análisis de universo restringido con control reconstruido.
- Interpretación: como delta_k es función de RAW y lag_k, B2/B4/B6 miden el valor de **explicitar la diferencia**, no información nueva.

Complementarias (aporte individual de un horizonte, no acumulado), solo si son identificables: B4 + lag3, B4 + delta3, B4 + lag4, B4 + delta4.

Registrar por comparación: AUC y ganancia de agosto, deltas pareados, columnas agregadas, % NA, veredicto R5, tiempo de cómputo.

### 4.2. Familias de la VM (control común: B4; variables: shortlist)

**No omitir ninguna iteración 000–007.** Para cada una, primero recuperar fórmula exacta y resultado real de la VM.

| Exp. | Origen VM | Único cambio | Verificar |
|---|---|---|---|
| M1 | 001 | `mean3` | ventana completa |
| M2 | 001 | `min3` | ídem |
| M3 | 001 | `max3` | ídem |
| M4 | 001 | `std3` | ídem; mínimo de observaciones |
| Z | 002 | `zero_streak3` | cero real vs. NA; cómo se eligieron las variables |
| R | 003 | `ratio3` (familia) | fórmula, denominadores nulos, cuáles fueron las 4 variables |
| R-i | 003 | cada ratio por separado | solo si R da `APORTA` o `INDICIO` |
| K | 004 | rankings monetarios mensuales | universo del ranking, ceros, NA, sin información futura |

- **005 (combinación):** recuperar el criterio original (umbrales, estabilidad). No repetir la combinación; se reemplaza por la sección 4.5.
- **006 (canaritos, 40 variables aleatorias):** es un **procedimiento de selección**, no una transformación. Comparar, con el mismo conjunto de variables candidatas, selección por canaritos vs. selección por gain+estabilidad. Único cambio: el método de selección.
- **007 (reoptimización):** mismas variables, HP originales vs. HP reoptimizados. Único cambio: los HP. No sumar este efecto al del feature engineering.

### 4.3. Tendencias (control común: B4; variables: shortlist)

| Exp. | Transformación |
|---|---|
| T1 | Tendencia de 3 meses |
| T2 | Tendencia de 4 meses |
| T3 | Tendencia de 5 meses |
| T4 | Tendencia de 6 meses |

Cada una individualmente contra el control, sin combinar con lags o deltas nuevos. Sujetas a R2: ejecutar solo las identificables. Controlar valores extremos e informar cómo.

### 4.4. Transformaciones de C3
Trasladar solo las que tengan respaldo empírico en la auditoría, calidad de datos suficiente en 2019 y una hipótesis plausible. Una familia por experimento, control B4.

### 4.5. Combinaciones incrementales
Solo con familias `APORTA` confirmadas con 20 semillas.

- Punto de partida: la mejor configuración de la escalera B.
- Agregar una familia por paso, en orden decreciente de Δganancia individual (orden fijado antes de empezar).
- Conservar la familia solo si vuelve a cumplir R5 contra el paso anterior; si no, se descarta y se sigue con la próxima.
- Sin búsqueda de combinaciones ni reordenamientos a posteriori.

---

## 5. ETAPAS Y CRITERIOS DE CONTINUACIÓN

| Etapa | Contenido | Semillas | Continúa si |
|---|---|---|---|
| 0 | Auditoría (sección 2) | — | Apruebo la tabla de experimentos |
| 1 | Optuna sobre B4 → HP fijos; escalera B identificable | 5 | — |
| 2 | Screening de familias M, Z, R, K, T, C3 | 5 | Hay al menos una `APORTA` o `INDICIO` |
| 3 | Confirmación de candidatas | 20 | Hay al menos una `APORTA` |
| 4 | Combinaciones incrementales | 20 | — |
| 5 | Reoptimización de control y finalista (R3); canaritos | 20 | — |
| 6 | Congelar candidata; evaluar octubre una vez (R7) | 20 | — |

Antes de cada etapa: estimar tiempo y costo, reutilizar todo resultado válido existente, guardar resultados parciales y dejar trazabilidad (config, commit, semillas, HP, lista de columnas y hash del dataset por corrida).

---

## 6. EVALUACIÓN FINAL

Para la candidata congelada y el baseline oficial, en octubre:

- Ganancia económica y diferencia respecto del baseline.
- Media y mediana entre las 20 semillas; cantidad de semillas con mejora.
- IC bootstrap pareado de clientes sobre Δganancia.
- Cantidad de envíos usada (fijada en agosto).

No afirmar superioridad por AUC. No afirmar superioridad si el IC de Δganancia incluye 0: informarlo como no concluyente.

---

## 7. ENTREGABLES

**Entrega 1 (ahora, sin entrenar):**
1. Auditoría de C3.
2. Auditoría de `HISTORIA_2019_01`.
3. Comparación con las instrucciones de Alejandro.
4. Informe de calidad de datos y cobertura histórica.
5. Propuesta de shortlist con método reproducible.
6. Catálogo de transformaciones con fórmulas.
7. Tabla de experimentos con estado, costo y prioridad; conteo de comparaciones.
8. Lista de consultas para Alejandro.

**Entrega 2 (tras mi aprobación):**
9. Escalera B (identificables) y complementarias.
10. Tendencias; medias, mínimos, máximos y desvíos; rachas, ratios y rankings.
11. Evaluación de canaritos y de reoptimización, cada una aislada.
12. Transformaciones de C3 trasladadas.
13. Combinaciones incrementales.
14. Evaluación económica final.
15. Conclusiones y recomendaciones para la competencia.
16. Guion del video grupal: hipótesis, diseño, resultados, limitaciones, conclusiones.

---

## 8. CONSULTAS PARA ALEJANDRO (preparar, no resolver por cuenta propia)

1. ¿Existen meses anteriores a enero de 2019 que puedan usarse **solo para construir historia** (lags, tendencias), manteniendo el entrenamiento en marzo–junio?
2. Definición exacta de delta-lag de orden 2 en su baseline.
3. ¿Se puede usar otro mes (por ejemplo julio) como segunda validación para reducir el sobreajuste a agosto?
4. ¿Es aceptable partir de RAW y reportar el baseline oficial como un paso (B4) de la escalera?
5. Cualquier adaptación del baseline que surja de la auditoría.

---

## PRINCIPIO FINAL

Partimos de RAW. Agregamos lag1, después delta1, lag2, delta2, y seguimos **hasta donde los datos permitan identificar el efecto**. Luego evaluamos individualmente medias, mínimos, máximos, desvíos, ratios, rachas, rankings, tendencias y derivadas de C3.

Cada incorporación necesita una hipótesis, una fórmula verificada, cobertura suficiente, un control sobre las mismas filas y una regla de decisión escrita de antemano.

**Una modificación por vez. Medir. Comparar. Conservar lo que aporta. Descartar lo que no. Recién después combinar.**
