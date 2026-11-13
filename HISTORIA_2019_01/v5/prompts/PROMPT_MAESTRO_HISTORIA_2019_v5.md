# PROMPT MAESTRO — HISTORIA 2019 v5
## Continuación experimental: representación, profundidad histórica y selección de variables

### 1. Objetivo

Determinar qué estrategias de construcción de variables históricas mejoran la ganancia de un modelo LightGBM que ya dispone de variables actuales, rezagos y deltas.

Trabajar exclusivamente con **2019**. No utilizar 2020.

El experimento debe producir un procedimiento reproducible que permita incorporar más historia cuando existan nuevos meses disponibles. Esa posibilidad futura no autoriza a cambiar el período de este estudio.

No prometer mejoras. Informar también resultados negativos, limitaciones y costo computacional.

### 2. Antecedentes obligatorios

Antes de implementar, revisar en `ClariRZ/Segunda_competencia`:

- `experimento_2026-11-13/prompts/`
- `experimento_2026-11-13/configuracion/contrato_original.json`
- Los scripts y resultados de agosto y octubre.
- Los antecedentes de v1, v2 y v3.
- Las instrucciones de Alejandro y las fórmulas verificables del notebook `z402_Feature_Engineering_en_SQL.ipynb`.

Distinguir entre lo propuesto, lo implementado y lo efectivamente ejecutado. La especificación técnica de partida es el **contrato ejecutado de v4**, no los borradores previos.

Registrar estos antecedentes:

- V4 evaluó B0, F1, F3, F4a y F4b.
- Cada alternativa tuvo 10 pruebas Optuna propias y cinco semillas.
- Ninguna superó la regla original de promoción por AUC de agosto.
- En octubre, F1 obtuvo la mayor ganancia del ensemble; F4a mostró mayor consistencia individual; F4b resultó desfavorable.
- Promedio, mínimo y máximo ya se probaron por separado en v2, con otras fuentes y parámetros compartidos. Las nuevas pruebas deben explicar esa diferencia.
- No se ejecutaron en v4 la rama larga, combinaciones ni canaritos.

**Octubre ya fue observado.** Los nuevos resultados serán exploratorios. No presentar esta continuación como una evaluación independiente ni modificar retrospectivamente las conclusiones de v4.

### 3. Reglas comunes

Mantener, salvo modificación explícita y documentada:

- Dataset identificado por su hash.
- Saneamiento de los nueve pares variable–mes adoptados en v4.
- Nulos conservados; no imputar ceros.
- Negativos válidos conservados.
- Valores no finitos convertidos a nulos.
- Rezagos por coincidencia exacta de cliente y mes calendario.
- Identificadores, mes y clase fuera de los predictores.
- Fuentes históricas revisadas mediante el diccionario.
- Eliminación de columnas vacías, constantes o duplicadas usando exclusivamente entrenamiento.
- Ningún filtro automático de cobertura del 90 %.
- Ninguna selección de variables usando octubre.

Auditar nuevas anomalías y reportarlas. Si una corrección adicional resulta necesaria, aplicarla de forma común al baseline y sus variantes, identificando que cambia la comparación.

Las reglas de faltantes de cada transformación deben quedar explícitas. No confundir un mes ausente, una variable saneada y un valor originalmente nulo.

### 4. Modelo, etiquetas y regla económica

Usar LightGBM binario:

- **Entrenamiento:** positivos BAJA+1 y BAJA+2.
- **AUC de validación:** positivo BAJA+2.
- **Ganancia:** +1.072.500 por BAJA+2 contactado y −27.500 por cualquier otro contacto.

El score se utiliza para ordenar clientes; no se interpreta como probabilidad calibrada de BAJA+2.

Separar dos funciones:

1. **AUC:** objetivo de Optuna y early stopping.
2. **Ganancia del ensemble:** resultado económico principal de v5.

Reportar siempre ambas métricas. Esta prioridad económica es una decisión nueva de v5, no una reinterpretación de la regla de v4.

### 5. Primera etapa: representación de historia corta

**Calendario común:**

- Entrenamiento: marzo, abril, mayo y junio de 2019, completos y sin sampling.
- Validación: agosto.
- Evaluación posterior: octubre, con alcance exploratorio.
- Enero y febrero aportan historia a marzo.

W3 significa **mes actual y dos anteriores**.

Evaluar los siguientes brazos:

| Brazo | Variables | Comparación principal |
|---|---|---|
| B0 | Originales + lag1/2 + delta1/2 | Control |
| L | Originales + lag1/2, sin deltas | B0 |
| P | B0 + promedio W3 | B0 |
| MIN | B0 + mínimo W3 | B0 |
| MAX | B0 + máximo W3 | B0 |
| RANGO | B0 + máximo W3 − mínimo W3 | B0 |
| F1 | B0 + promedio, mínimo, máximo y rango W3 | B0 y componentes individuales |

Las ampliaciones P, MIN, MAX y RANGO parten del mismo B0; no se acumulan.

Usar las mismas fuentes elegibles y reglas de ventana de v4. Los resúmenes requieren las tres observaciones no nulas.

El brazo L conserva las mismas variables actuales y rezagos del control; se retiran las columnas delta. Auditar duplicados para comprobar que la comparación representa esa intervención.

**Preguntas:**

- ¿Los deltas aportan sobre los rezagos?
- ¿Qué componente de F1 funciona por separado?
- ¿El paquete completo supera a sus componentes?
- ¿La mejora aparece en modelos individuales, en el ensemble o en ambos?

No atribuir causalmente toda la mejora de F1 a un componente solo porque ese componente funcione aislado. Las interacciones requerirían pruebas adicionales.

### 6. Segunda etapa: profundidad histórica

Esta rama tendrá un contrato y presupuesto propios.

**Calendario común:**

- Entrenar todos los brazos únicamente con junio de 2019.
- Validar en agosto.
- Evaluar posteriormente en octubre, con alcance exploratorio.
- Reentrenar y reoptimizar el baseline sobre exactamente las mismas filas de junio.

Comparar ventanas:

- **W3:** actual + dos meses anteriores.
- **W4:** actual + tres anteriores.
- **W6:** actual + cinco anteriores.

No comparar directamente un candidato entrenado en junio contra el resultado del baseline entrenado marzo–junio para atribuir una mejora a la historia.

Definir antes de ejecutar un paquete idéntico de fórmulas para W3/W4/W6. Comenzar con promedio, mínimo, máximo y rango. Evaluar las tendencias como una comparación adicional identificable, evitando cambiar simultáneamente fórmulas y longitud de ventana.

Para la tendencia lineal, usar la pendiente de los valores respecto del tiempo, ordenados del mes más antiguo al actual. Registrar que con tres observaciones completas y equiespaciadas equivale a delta2/2.

Mantener iguales clientes, fuentes y política de depuración dentro de la comparación. Auditar columnas vacías y duplicadas entre ventanas y documentar cómo se resuelven antes de entrenar.

No eliminar clientes por no disponer de historia completa. Conservar sus filas y producir nulos según la receta. Reportar cobertura por fuente y ventana.

Interpretar esta rama como el efecto práctico de ampliar historia, incluyendo los faltantes que esa ampliación genera; no afirmar que todos los clientes tienen seis observaciones.

### 7. Pruebas posteriores condicionadas

No ejecutar automáticamente:

**A. Cambios relativos y faltantes**

Auditar F3 de v4:

- Cuánto de la ausencia proviene de denominadores cero.
- Cuánto de meses ausentes o saneamiento.
- Cuánto de exigir W3 completa para fórmulas que utilizan solo dos valores.

Si se prueba una regla menos restrictiva, crear un brazo nuevo y mantener idéntica la fórmula:

`(actual − referencia) / abs(referencia)`

Denominador cero produce nulo. No usar un épsilon arbitrario para evitarlo.

**B. Combinaciones**

Combinar únicamente familias seleccionadas bajo una regla escrita antes de consultar sus nuevos resultados de octubre.

Comparar la combinación contra B0 y contra sus componentes. No asumir que dos mejoras individuales se suman.

**C. Canaritos**

Aplicar selección únicamente sobre un conjunto completo ya evaluado.

- Construir y utilizar canaritos exclusivamente en entrenamiento.
- No usar agosto para decidir qué variables sobreviven.
- Fijar previamente cantidad de canaritos, semillas, modelo de importancia y umbral.
- Comparar conjunto completo contra conjunto filtrado.
- Reoptimizar ambos con igual presupuesto.

No presentar los canaritos como una familia histórica: son un método de selección.

### 8. Hiperparámetros y semillas

Optimizar cada brazo por separado con el mismo espacio y presupuesto.

Mantener como punto de partida:

- `num_leaves`
- `learning_rate`
- `min_data_in_leaf`
- `feature_fraction`
- `bagging_fraction`
- `bagging_freq = 1`

Usar el espacio exacto del contrato v4, salvo cambio previo justificado para todos los controles afectados.

Propuesta inicial: diez pruebas Optuna por brazo. Reconocer que este presupuesto no garantiza encontrar el óptimo.

Después de optimizar, congelar hiperparámetros y cantidad de árboles. Evaluar todos los brazos con las mismas cinco semillas, distintas de la semilla usada para optimizar. Registrar sus valores antes de entrenar.

Los resultados anteriores pueden reutilizarse solo si coinciden datos, columnas, fórmulas, parámetros, semillas y procedimiento. Si la evaluación cambia, regenerar el control comparable.

Una eventual ampliación de semillas debe incluir al candidato y su control. Más semillas miden sensibilidad al entrenamiento; no crean nuevos períodos independientes.

### 9. Evaluación y selección

La unidad económica principal es el **ensemble obtenido promediando los scores de las semillas**.

Reportar por brazo:

- AUC individual y del ensemble.
- Ganancia individual y del ensemble.
- Diferencias pareadas contra el control.
- Media, mediana y desviación de las diferencias.
- Cantidad de semillas favorables.
- Contactos y BAJA+2 acertadas.
- Cantidad de variables, tiempo y memoria.

No confundir promedio de ganancias con ganancia del ensemble.

En agosto:

- Mantener la curva acumulada suavizada con ventana completa de 2.001 posiciones.
- Registrar máximo suavizado, ganancia puntual en el corte y proporción de contactos.
- Desempatar por score descendente y cliente ascendente.

Como regla exploratoria para priorizar confirmación, exigir:

- Mejora de ganancia suavizada del ensemble frente al control.
- Diferencia media de ganancia individual positiva.
- Al menos cuatro de cinco semillas económicamente favorables.

Esta es una regla de asignación de cómputo, no una prueba de significación. Si mejora el ensemble pero no la estabilidad individual, registrar una hipótesis específica sin declararla confirmada.

Antes de evaluar octubre, congelar recetas, modelos, combinación de semillas y proporción de contactos de agosto por brazo. Aplicar:

`contactos_octubre = floor(proporción_agosto × población_octubre)`

No buscar el mejor corte de octubre. Mantener un registro de todos los brazos y sus resultados, sin omitir los desfavorables.

### 10. Auditoría, ejecución y presupuesto

Antes de entrenar:

1. Verificar archivos, dataset, entorno y resultados reutilizables.
2. Construir el manifiesto de fuentes y columnas de cada brazo.
3. Ejecutar pruebas sintéticas de calendario, faltantes, fórmulas, rankings cuando corresponda y ganancia.
4. Estimar recursos mediante dimensiones reales y una medición acotada si está autorizada.
5. Presentar el plan concreto con número de ajustes, semillas, límite de tiempo y apagado.

La primera etapa contiene siete brazos: con diez pruebas y cinco semillas por brazo son **105 ajustes**, antes de cualquier medición adicional o reutilización verificada.

No reutilizar automáticamente los límites horarios de los borradores anteriores. No encender ni entrenar por el solo hecho de redactar este protocolo.

Durante la ejecución, guardar avances y errores. Ante fallas metodológicas, detener el proceso afectado; no corregir silenciosamente una receta y mezclar sus resultados.

### 11. Organización y reproducibilidad

Crear una carpeta identificada como **Historia 2019 v5**, separada de v4, dentro del repositorio existente.

Guardar:

- Este prompt y sus revisiones.
- Contrato final de cada etapa.
- Procedencia y hashes.
- Fórmulas, fuentes, columnas y exclusiones.
- Código y entorno.
- Pruebas.
- Ensayos Optuna y parámetros elegidos.
- Resultados por semilla y ensemble.
- Consumo, errores y estado de ejecución.
- Instrucciones de reproducción.

No guardar en Git datos de clientes, credenciales, matrices privadas ni predicciones individuales. Documentar dónde se conservan los artefactos necesarios fuera de Git.

No sobreescribir resultados históricos. Identificar los commits de cada corrida y publicar conforme a la autorización vigente.

### 12. Entregable final

Preparar un informe que responda:

1. ¿Qué hipótesis se probó?
2. ¿Qué cambió respecto del control?
3. ¿Qué permaneció igual?
4. ¿Mejoró AUC, ganancia o ambas?
5. ¿La mejora fue individual, del ensemble o de ambos?
6. ¿Fue consistente entre semillas y períodos observados?
7. ¿Qué costo y complejidad agregó?
8. ¿Qué limitaciones impiden generalizar?
9. ¿Qué conviene conservar, descartar o seguir estudiando?

Distinguir claramente **hallazgo exploratorio, estabilidad entre semillas y generalización temporal**.

El objetivo es encontrar estrategias históricas útiles y reproducibles dentro de 2019, no obtener una mejora a cualquier costo ni seleccionar únicamente el resultado más favorable.