# PROMPT MAESTRO — HISTORIA 2019 v3
## Experimento postmortem:  historia de rankings, pérdida de actividad y disponibilidad histórica

**Versión del protocolo:** 3.0 — 10 de noviembre de 2026.
**Estado:** propuesta para auditar y aprobar; no constituye autorización para entrenar.
**Ubicación:** `HISTORIA_2019_01/v3/`.

Actuá como científico de datos senior especializado en LightGBM, datos longitudinales, diseño experimental y evaluación económica. Trabajá de forma autónoma dentro de cada fase autorizada. Verificá archivos, fórmulas y resultados; no reemplaces evidencia por recuerdos de la conversación.

## 1. Objetivo y pregunta principal

Determinar si una ampliación pequeña y controlada del modelo de Historia v2 mejora la ganancia económica de agosto de 2019 mediante:

1. La posición relativa mensual del cliente y su evolución.
2. Señales de pérdida de actividad y caídas consecutivas.
3. Indicadores de disponibilidad de historia.

La pregunta central es: **¿la historia de la posición relativa agrega valor por encima de conocer solamente la posición actual?**

El objetivo no es reproducir todas las entregas de 2021 ni agregar muchas columnas. Cada familia debe tener una hipótesis, fórmula, control y regla de decisión verificables. Los resultados de 2021 son antecedentes para formular hipótesis, no evidencia de mejora en 2019.

## 2. Alcance y autorizaciones

La primera fase es de auditoría y preparación. Se permite leer archivos y escribir exclusivamente documentos, inventarios y propuestas dentro de la carpeta de esta ampliación. No entrenar, lanzar Optuna, modificar modelos, cambiar la corrida v2 ni abrir etiquetas o métricas de octubre.

La orden previa de ejecutar Historia v2 corresponde a esa corrida. **No asumir que autoriza esta ampliación.** Presentar un protocolo ejecutable, costos y controles, y esperar una aprobación explícita antes del primer entrenamiento de esta ampliación. Una vez aprobada, continuar las etapas previstas sin pedir permiso por cada semilla o reanudación idéntica.

Si v2 sigue corriendo, preparar la auditoría y esperar su cierre para fijar el control. No ejecutar entrenamientos concurrentes en la VM sin revisar recursos y autorización. No detener la VM por cuenta propia: la usuaria pidió dejarla encendida.

Este protocolo define Historia 2019 v3, una ampliación independiente que toma v2 como antecedente y fuente del control. No editar el prompt, las configuraciones ni los manifiestos congelados de v2 para adaptarlos retroactivamente.

## 3. Antecedentes que deben verificarse

Recuperar del experimento original y de v2:

- Dataset y hash, rango real de meses, etiquetas, claves cliente–mes, sanitización y máscaras de roturas.
- Recetas exactas B0–B4, cantidad de columnas, hiperparámetros, rondas, semillas, predicciones de agosto y estados finales.
- Shortlist congelada, criterio de selección, familias M/Z/R/K/T/C3 y resultados de selección, combinaciones y reoptimización.
- Completitud de los archivos y posibles fallos, interrupciones o resultados parciales.

Antecedentes orientativos, que no sustituyen la verificación:

- La iteración 000 original tenía 760 variables; la 003 incorporaba cuatro ratios.
- B4 adaptado de v2 tenía 588 columnas: 152 RAW y cuatro derivados para 109 fuentes elegibles.
- El dataset disponible comenzaba en enero de 2019. Marzo solo tiene enero y febrero como pasado.
- La conversación describió B2/B3 en un orden que no coincide con la tabla del prompt original. **Recuperar las recetas reales: no inferir las columnas por el nombre del brazo.**
- La familia K mensual no equivale automáticamente a calcular lags y deltas sobre rankings.
- Con tres observaciones completas, igualmente espaciadas, la pendiente OLS es `(x_t − x_t−2)/2`; no tratarla como información independiente de delta2.
- Hay antecedentes de consulta de octubre en otros experimentos. Auditar y declarar la exposición previa. No afirmar que octubre es globalmente virgen por estar bloqueado en esta corrida.

Cerrar la auditoría con hechos verificados, hipótesis y pendientes, cada hecho con ruta y evidencia.

## 4. Protocolo temporal y económico

Verificar las instrucciones originales de Alejandro. Configuración prevista:

| Elemento | Regla |
|---|---|
| Entrenamiento principal | 201903, 201904, 201905, 201906 |
| Muestreo | Todas las filas elegibles, sin submuestreo |
| Target de entrenamiento | Positivo BAJA+1 o BAJA+2; negativo CONTINUA |
| Validación y selección | 201908 |
| Clase que genera beneficio | BAJA+2 |
| Modelo | LightGBM |
| Optuna y early stopping, cuando correspondan | AUC con definición verificada |
| Decisión de promoción | Ganancia, estabilidad y comparación con control |
| Octubre | Bloqueado durante todo el desarrollo |

Verificar documentalmente los importes. Valores utilizados previamente: +1.072.500 por BAJA+2 contactado y −27.500 por cualquier otro cliente contactado. Son beneficios netos por contacto: no descontar nuevamente el costo al acierto.

Fijar antes de entrenar si AUC se calcula sobre BAJA+2; la propuesta es mantener esa definición para comparabilidad con v2. Distinguirla del target binario usado para entrenar.

No cambiar simultáneamente target, meses, filas, pesos, parámetros y variables. No trasladar a 2019 los cortes de envíos ni las máscaras de roturas de 2021.

## 5. Controles: tres identidades diferentes

### C0 — Control experimental

Congelar el modelo de referencia resultante de v2 según su regla registrada, con receta, columnas, parámetros, rondas y semillas. Si v2 no tiene una salida válida y concluyente, declarar el bloqueo y proponer como alternativa su B4 adaptado verificado; no elegir el fallback retrospectivamente según cómo le vaya a esta ampliación.

C0 es el control de las pruebas, no necesariamente el baseline oficial. Conservar su matriz de entrenamiento y sus claves exactas.

### BOF — Baseline oficial

Verificar por separado la equivalencia con las instrucciones de Alejandro: fuentes, lags, deltas, tratamiento de nulos, etiquetas, meses e hiperparámetros aplicables. Compartir el nombre B4 o tener historia de orden 2 no basta para demostrar equivalencia. Una adaptación de 588 columnas no es automáticamente la receta original de 760.

La discrepancia no invalida una comparación interna bien controlada, pero impide presentarla como mejora contra el baseline oficial. Su resolución es una compuerta para el cierre final.

### A — Control específico de la historia del ranking

A contiene C0 más los rankings actuales definidos abajo. B contiene exactamente A más sus derivados históricos. El contraste B–A responde la pregunta principal; B–C0 mide el valor del paquete completo.

Si C0 ya contiene exactamente las columnas de A, A=C0: reutilizar predicciones y eliminar el contraste duplicado. Si solo coinciden algunas, agregar únicamente las faltantes. Si C0 ya contiene historia de rankings equivalente, revisar si la pregunta ya está resuelta; no duplicar columnas ni inventar una variante para forzar un resultado nuevo.

## 6. Universo de variables y controles de calidad

### 6.1 Fuentes congeladas

Para A y B, partir de las variables monetarias de la shortlist de 20 fuentes congelada en v2. Usar la intersección con variables elegibles y semánticamente monetarias; no completar cupos mirando agosto. Conservar fuentes en pesos y dólares identificadas por separado. No rankear códigos nominales de estado ni fechas como si fueran montos.

Para C usar la siguiente lista propuesta, condicionada a existencia, semántica y calidad comprobadas en train:

- Haberes: `cpayroll_trx`.
- Actividad: `ctrx_quarter`, `ctarjeta_visa_transacciones`, `ctarjeta_master_transacciones`, `ctarjeta_debito_transacciones`, `chomebanking_transacciones`.
- Servicios: `ccuenta_debitos_automaticos`, `ctarjeta_visa_debitos_automaticos`, `ctarjeta_master_debitos_automaticos`.

La lista es pequeña y específica de comportamiento; no se fuerza a pertenecer a una shortlist dominada por montos. Es una diferencia explícita respecto de v2, registrada antes de entrenar. No sustituir fuentes excluidas por otras elegidas según resultados.

### 6.2 Cobertura

Construir todas las transformaciones sobre el panel sanitizado antes de filtrar las filas de entrenamiento, mediante uniones exactas por cliente y mes calendario. Nunca usar la fila anterior como sustituto del mes anterior.

Aplicar como regla principal cobertura de valores definidos ≥90% en cada mes de entrenamiento a cada columna nueva que se conserve. Publicar numerador, denominador y motivo de indefinición. Excluir columnas por reglas de calidad fijadas antes del entrenamiento y registrar la familia efectivamente probada. Si la familia queda vacía, marcar `NO_IDENTIFICABLE`.

Para A/B fijar un único conjunto de fuentes: exigir cobertura de las cinco columnas necesarias por fuente (rank actual, dos lags y dos deltas). Usar ese mismo conjunto en A y B. Si las exclusiones cambian sustancialmente el significado de una familia, informarlo antes de aprobar la ejecución.

Conservar todas las columnas originales de C0. Detectar columnas nuevas constantes, idénticas y nombres duplicados; retirar las nuevas constantes o duplicadas antes del entrenamiento y documentarlo. No descartar señales binarias solo por ser poco frecuentes; informar su frecuencia y soporte.

D tiene cobertura de definición del 100% si las claves están verificadas: la ausencia de una fila histórica es precisamente el valor 0 del indicador, no un NA imputado de una variable bancaria.

No reducir el umbral, imputar NA como cero ni filtrar clientes para conseguir que pase una familia. Las alternativas de universo restringido quedan fuera de este protocolo.

Inspeccionar cobertura y distribuciones en agosto como diagnóstico, sin cambiar la lista en función de su ganancia. Posponer diagnósticos de octubre hasta el cierre. Una anomalía grave de calidad produce un bloqueo documentado, no cambios silenciosos de receta.

## 7. Fórmulas y brazos

### A — Posición relativa actual

Para cada fuente x y mes t, calcular rank con signo y cero fijo, dentro del universo completo de clientes presentes ese mes, antes de cualquier submuestreo o selección de contactos:

- NA → NA; cero → 0.
- Positivos → rango promedio entre positivos / cantidad de positivos.
- Negativos → menos el rango promedio de su valor absoluto entre negativos / cantidad de negativos.

Esto conserva el signo y la posición dentro de cada signo; no es un percentil global. Los empates reciben el rango promedio. No usar datos de otros meses para construir el ranking mensual. Conservar las variables nominales originales de C0.

**A = C0 + rank_t(x).** Hipótesis: la posición relativa complementa al nivel nominal.

### B — Historia de esa posición

Para exactamente las mismas fuentes de A:

- `rank_lag1 = rank(x del mismo cliente en t−1, calculado en t−1)`.
- `rank_lag2 = rank(x del mismo cliente en t−2, calculado en t−2)`.
- `rank_delta1 = rank_t − rank_lag1`.
- `rank_delta2 = rank_t − rank_lag2`.

**B = A + esas cuatro columnas por fuente.** NA si falta el mes o el dato requerido. No confundir `rank_t(x_t−x_t−1)` con `rank_t(x_t)−rank_t−1(x_t−1)`.

Hipótesis: perder posición relativa puede anticipar la baja aunque el monto nominal no disminuya. Esta es una representación complementaria, no una garantía de inmunidad a inflación o cambios de población.

### C — Pérdida de actividad

Para las fuentes de conteo aprobadas:

1. `apago1 = 1[x_t−1 > 0 y x_t = 0]`.
2. `prendio1 = 1[x_t−1 = 0 y x_t > 0]`.
3. `caidas_consecutivas3`: 0 si no cayó entre t−1 y t; 1 si cayó solo en ese último paso; 2 si `x_t < x_t−1 < x_t−2`.

Los dos primeros requieren ambos meses y valores válidos. La tercera exige las tres observaciones válidas y consecutivas incluso para devolver 0. Los empates no son caídas. No usar umbrales porcentuales elegidos mirando agosto.

Agregar un conteo de servicios apagados entre los tres servicios listados, solo si todos sus indicadores requeridos están definidos. Si alguno falta, el agregado es NA; no sumar silenciosamente un número variable de servicios. Si no quedan al menos dos fuentes de servicios elegibles, omitir ese agregado.

**C = C0 + familia de actividad.** Hipótesis: la persistencia y la pérdida de vínculos aportan más que la magnitud aislada de los cambios. Esta prueba identifica el paquete; no atribuir su resultado a una columna particular sin otra prueba registrada.

### D — Disponibilidad estructural

- `registro_lag1_disponible`: existe fila única del cliente exactamente en t−1.
- `registro_lag2_disponible`: existe fila única del cliente exactamente en t−2.

**D = C0 + esos dos indicadores.** No derivarlos de si el saldo está nulo. No interpretar primera aparición en el archivo como fecha real de alta en el banco.

Hipótesis: explicitar la disponibilidad ayuda al modelo a interpretar sus variables históricas. Es representación de información ya parcialmente contenida en el patrón de NA.

### Fuera de alcance

Distancia al máximo reciente, promedios ponderados, deltas simétricos, deflación, historia de tarjetas adicional, cambios de target, pesos por grupo, ensambles entre modelos y ventanas largas quedan como backlog. No agregarlos si las pruebas principales fallan. Tampoco repetir T1 como novedad independiente de delta2.

## 8. Entrenamiento comparable y reutilización

Recuperar las 20 semillas de v2. Lista esperada, a verificar:
`101, 211, 307, 401, 503, 601, 701, 809, 907, 1009, 1103, 1201, 1301, 1409, 1511, 1601, 1709, 1801, 1901, 2003`.

Screening con las primeras cinco; confirmación con las veinte totales, reutilizando las cinco ya calculadas. No llamarlas veinte semillas nuevas.

Usar los parámetros y la cantidad fija de rondas de C0 para todas las familias en la fase de variables. No hacer early stopping independiente para cada brazo: cambiaría además la duración efectiva de entrenamiento. Registrar la procedencia de las rondas, incluidos los usos previos de agosto. No realizar nueva búsqueda por familia.

Mantener presupuesto de cómputo, versiones y determinismo. Comprobar que los parámetros de bagging están activos si se declaran. Explicar que `feature_fraction` fijo no implica igual cantidad de columnas consideradas al variar el tamaño de la matriz.

Reutilizar modelos o predicciones solo si coinciden dataset, etiquetas, sanitización, filas y orden, receta, columnas y orden, parámetros, rondas, semillas y cálculo de métricas. Validar hashes y alineación por cliente. La igualdad del nombre del archivo no prueba equivalencia.

## 9. Ganancia, incertidumbre y decisiones

### Métrica primaria

Ordenar scores de mayor a menor, desempatando por `numero_de_cliente`. Construir ganancia acumulada según etiquetas BAJA+2. Suavizar con una media móvil centrada de **2.001 posiciones y ventana completa**, sin rellenar bordes. Seleccionar el máximo suavizado; si hay empate, elegir el menor número de contactos. Si el universo es demasiado pequeño para esa ventana, detenerse: no cambiar el suavizado automáticamente.

Guardar ganancia suavizada, corte, proporción de contactos y ganancia puntual en ese corte. No confundirlas. Calcularlas por semilla y sobre el promedio de scores de todas las semillas de la etapa.

### Comparación pareada

Para cada contraste guardar diferencias por semilla de ganancia y AUC, media, mediana, desvío muestral y proporción de victorias. La ganancia primaria de cada brazo utiliza su propio corte suavizado de agosto. Guardar además la diferencia usando para ambos el corte del control como diagnóstico, sin usarlo para escoger ganadores alternativamente.

Bootstrap pareado de clientes de agosto, al menos 1.000 réplicas, semilla fija y los mismos índices para todos los brazos. Usar el promedio de scores entre semillas. Recalcular en cada réplica la curva y el máximo suavizado con la regla congelada; conservar multiplicidades de los clientes remuestreados. Reportar IC percentil 90% de la diferencia y número de réplicas válidas.

Este intervalo es condicional a los modelos entrenados y al procedimiento de selección. No incluye toda la incertidumbre de entrenamiento, dependencia temporal o búsqueda acumulada. Las semillas tampoco equivalen a veinte muestras independientes de clientes.

### Regla operativa

Mantener para comparabilidad la regla económica de v2:

- **APORTA:** media de Δganancia > desvío de Δganancia entre semillas; al menos 80% de victorias; límite inferior del IC 90% bootstrap >0. Exigir además Δganancia positiva en el ensamble.
- **INDICIO_ECONOMICO:** media y mediana de Δganancia positivas y al menos 60% de victorias, sin cumplir APORTA.
- **INDICIO_AUC:** ΔAUC positiva en al menos 80% de semillas, sin evidencia económica suficiente.
- **NO_APORTA:** resto.

APORTA con cinco semillas es provisional. Pasar una sola vez a veinte todo brazo con cualquiera de los tres estados de interés. La inclusión de INDICIO_ECONOMICO es un cambio explícito respecto de v2: evita descartar una señal económica porque no mejoró AUC. No cambiar estos umbrales después de observar los resultados.

Con veinte semillas solo APORTA habilita una combinación. Indicios restantes son inconclusos. No ampliar a 40/100 semillas ni probar otras listas para rescatar una familia.

Para atribuir aporte específicamente a historia de rankings, B debe superar A. Para promover el paquete B, debe aportar también frente a C0. Si se confirma B, confirmar A con veinte semillas para que el contraste sea pareado completo.

## 10. Comparaciones y multiplicidad

Contrastes únicos primarios, máximo cinco:

1. A–C0.
2. B–A (pregunta principal).
3. B–C0 (paquete).
4. C–C0.
5. D–C0.

Si A=C0, eliminar duplicados. Un brazo idéntico no es una prueba adicional.

Combinaciones: como máximo tres incorporaciones, en orden fijo **ranking → actividad → disponibilidad**. En ranking, elegir B si cumple sus condiciones; si no, A si aporta. Nunca incorporar A y B como familias independientes. Partir de C0 y conservar una incorporación solo si vuelve a cumplir APORTA contra el paso anterior con veinte semillas. Si falla, continuar desde la última receta conservada. No probar otro orden.

Agregar como máximo un contraste del compuesto final contra C0, si no está ya calculado. Si no supera C0, conservar C0.

Reoptimización final opcional prevista en el presupuesto aprobado: como máximo tres contrastes adicionales (C0 reoptimizado–C0, finalista reoptimizado–finalista, finalista reoptimizado–C0 reoptimizado).

**Máximo: 12 contrastes únicos sobre agosto** (5 + 3 + 1 + 3), antes de deduplicar. Informar también las revisiones de cinco y veinte semillas y los trials de Optuna; doce contrastes no describen toda la búsqueda acumulada.

La regla APORTA es una decisión operativa, no un control formal del error familiar. El IC 90% no demuestra superioridad luego de múltiples búsquedas. Informar toda la tabla, incluidos negativos, y el historial previo de selección sobre agosto. No presentar agosto como test independiente.

## 11. Comprobación temporal secundaria

Si las etiquetas y fuentes lo permiten, registrar antes de ejecutar una comprobación **train marzo–abril → evaluación junio**, dejando mayo fuera del entrenamiento. Usar C0 y los mismos A–D, fórmulas y fuentes; parámetros y rondas fijados de antemano, sin optimizar con junio.

La función es diagnosticar consistencia y cambio de régimen. Junio ya intervino en entrenamiento/selección de v2: no es una validación independiente ni una nueva confirmación estadística. Publicar todos los contrastes viables, no solo los favorables. No usar este diagnóstico para fabricar variantes, cambiar fuentes o elegir otro corte de agosto. Los costes de esta fase deben estar incluidos en la propuesta aprobada; si no lo están, dejarla pendiente.

## 12. Reoptimización y cierre

Solo después de congelar una candidata por variables, reoptimizar C0 y candidata con igual presupuesto: propuesta de 50 trials por brazo, mismo espacio y sampler, misma política de early stopping AUC, mismos meses y recursos. Verificar el espacio de Alejandro y fijarlo en configuración antes de lanzar. No asignar a la candidata un presupuesto mayor ni comparar un control sin ajuste contra una candidata ajustada como si fuera efecto de variables.

Separar los informes de efecto de variables y efecto de hiperparámetros. Si la candidata ajustada no supera al control ajustado según la regla, conservar el control ajustado. No reabrir familias descartadas.

Antes de cualquier test final, emitir un manifiesto congelado con modelos, hashes, columnas, parámetros, rondas, semillas y proporciones de contacto fijadas en agosto. Resolver la equivalencia BOF y documentar la exposición histórica de octubre.

**Esta ampliación termina por defecto con candidata congelada y octubre pendiente.** Solo abrir octubre cuando exista autorización explícita de cierre y estén resueltas sus compuertas. Evaluar una sola candidata y el baseline oficial, sin elegir entre alternativas mirando sus resultados.

En el test, cada modelo usa su proporción de contactos fijada previamente; `k = floor(proporción_agosto × N_octubre)`. No reoptimizar cortes en octubre, tampoco dentro del bootstrap. Reportar ganancia, diferencia pareada, media y mediana por semilla, victorias e IC de clientes con proporciones fijas. Si octubre ya fue usado para decisiones previas, declarar la limitación y no prometer un test limpio retroactivamente.

## 13. Operación, errores y trazabilidad

Guardar en la misma carpeta del experimento original:

```text
HISTORIA_2019_01/v3/
  prompts/
  auditoria/
  configuraciones/
  scripts/
  pruebas/
  logs/
  resultados/
  manifiestos/
```

Versionar en el repositorio correcto código, prompt, configuración y resultados agregados permitidos. No agregar datos de clientes, credenciales, predicciones individuales ni modelos pesados a Git. No hacer push sin autorización correspondiente. La copia local y la de VM deben identificarse con rutas y hashes; nunca afirmar que algo está guardado en la VM si solo existe localmente.

### Registro incremental en Git

Guardar los archivos a medida que se producen y crear un commit local al cerrar cada hito: protocolo aprobado, auditoría, implementación y pruebas, screening, confirmación, combinaciones y cierre. Registrar también correcciones relevantes antes de continuar, con un mensaje que indique qué cambió y por qué. No esperar al final del experimento para versionar.

Antes de cada commit, revisar el diff y agregar únicamente archivos de esta versión. Incluir código, prompt, configuraciones congeladas, manifiestos sin información sensible y resultados agregados; excluir datos individuales, credenciales, predicciones, modelos pesados y archivos temporales. No incluir cambios ajenos ni modificar el historial de v2. No crear commits vacíos ni uno por cada línea del log.

Los checkpoints por semilla y trial se guardan en el almacenamiento del experimento; Git registra su identidad y ubicación mediante manifiestos, no sus archivos pesados. Distinguir siempre cuatro estados: archivo guardado, commit local creado, commit enviado al remoto y artefacto respaldado. Un commit local no es un respaldo remoto. Si la ejecución ocurre en la VM, verificar la sincronización de los archivos versionables al repositorio antes de declarar un hito registrado.

Hacer push por hito solo si existe autorización explícita vigente y acceso al remoto. Si no, mantener los commits locales e informar que el respaldo remoto está pendiente. Ante un fallo de guardado o de integridad, detener la etapa; ante un fallo de push, conservar lo local e informar el fallo sin afirmar que quedó respaldado.

Antes del lanzamiento: verificar espacio, RAM, procesos existentes, ambiente, dependencias y estimación de costo. Proponer límite explícito de tiempo/costo; detener de forma recuperable al alcanzarlo. No adivinar el precio de la VM ni prometer supervisión futura sin un mecanismo real.

Checkpoint por semilla y trial, escritura atómica de estados y bloqueo contra procesos duplicados. Reanudar solo la misma identidad. Un fallo de integridad detiene la cadena; no continuar con resultados incompletos. Un fallo transitorio puede reintentarse de forma limitada con igual configuración, dejando registro.

Verificar con casos sintéticos: meses faltantes y cambio de año; ranking con signos, empates y NA; historia del ranking vs ranking de la historia; transiciones con datos rotos; disponibilidad de registro; ganancia y suavizado; alineación de clientes; reutilización de checkpoints; compuerta de octubre. No entrenar modelos reales para sustituir estos controles.

## 14. Entregables y etapas

**Fase 0, ahora:**

1. Auditoría de v2 y recuperación de resultados válidos.
2. Identidad de C0, estado de BOF y discrepancias.
3. Catálogo final de fuentes y fórmulas; cobertura por mes y columnas excluidas.
4. Tabla `brazo | hipótesis | control | único cambio | columnas | cobertura | estado | reutilizable | costo`.
5. Lista exacta de contrastes, presupuesto máximo y plan de comprobación temporal.
6. Configuración propuesta, pruebas previstas y puntos que requieren resolución.
7. Informe breve y solicitud de aprobación sobre ese plan concreto.

**Tras aprobar:** pruebas → screening cinco semillas → confirmación veinte → combinaciones → reoptimización pareja, si fue presupuestada → congelamiento. No avanzar por completar una lista: si ninguna familia aporta, terminar con el control y un resultado negativo válido.

**Informe final de la ampliación:** tabla completa de contrastes, ganancias y AUC por semilla y ensamble, intervalos, cortes, costos, cobertura, cambios frente a v2, límites estadísticos y recomendación. Explicar por separado si sirvió el ranking actual, su historia, la actividad o la disponibilidad. No sumar mejoras individuales como si fueran aditivas.

## 15. Fuentes del cribado y límites

Se cribaron las secciones de historia y tratamiento de montos de las 66 fichas del postmortem. Se revisaron en detalle siete entregas y fragmentos de cinco implementaciones; esto no equivale a auditar todos los repositorios ni a reproducir resultados.

- Índice: https://postmortem-indol.vercel.app/data/index.json
- Historia sobre rankings: https://postmortem-indol.vercel.app/entregas/agustinlovrich/ y https://postmortem-indol.vercel.app/entregas/juandurbano/
- Transiciones y caídas: https://postmortem-indol.vercel.app/entregas/jaquelinegirabel/ y https://postmortem-indol.vercel.app/entregas/lulimontero/
- Comportamiento y máximos: https://postmortem-indol.vercel.app/entregas/fsteeb1/
- Disponibilidad: https://postmortem-indol.vercel.app/entregas/mldevgit/
- Promedios ponderados, reservado al backlog: https://postmortem-indol.vercel.app/entregas/ssmito/
- Antecedente C3 propio: https://postmortem-indol.vercel.app/entregas/clarirz/

Verificar en código cada fórmula que se traslade. Las fichas son descripciones asistidas por IA y no un ranking de eficacia. Adaptar con reglas explícitas: no copiar rellenos de NA, ventanas por filas, exclusiones por drift futuro, cortes de 2021 ni decisiones basadas en el leaderboard.

**Principio de cierre:** una pregunta por contraste, un control verificable, mismas condiciones, ganancia con incertidumbre y todos los resultados a la vista. Conservar C0 es una conclusión válida.
