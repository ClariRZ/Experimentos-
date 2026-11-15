# Protocolo propuesto — pendiente de ejecución

No es una orden de lanzar todas las corridas. Requisitos previos: reconstrucción del control, auditoría de cobertura y definición explícita de evaluación temporal. Junio de 2021 y octubre de 2019 ya se observaron; resultados nuevos allí son exploratorios. No usar agosto privado conocido para elegir variantes.

## E00 — control congelado

Receta exacta C3 del plan original, sin modificaciones. La auditoría de artefactos está completada; regenerar matrices y reentrenar el control sigue pendiente. Registrar versiones, hashes, datos, orden de features, target, semillas y costo.

## E01 — tamaño mínimo de hoja

Mantener features, target, meses, num_leaves=64, learning_rate=.03, 300 rondas y restantes parámetros C3. Comparar min_data_in_leaf=100 (control), 500, 1500 y 2500. Valores exploratorios propuestos, no optimizados ni supuestamente ganadores. Reconstruir Dataset por brazo para no contaminar la comparación por feature_pre_filter. Comparar las mismas semillas y el ensemble; no elegir la mejor semilla.

Hipótesis: hojas más grandes pueden mejorar estabilidad, o perder señales de grupos pequeños. Reportar ambas posibilidades. No inferir transferencia del valor 2355 obtenido en otro período/target.

## E02 — ablaciones de representación

Con receta C3 fija, quitar por separado transiciones numéricas, recencia, tarjetas/ratios e historia numérica. No eliminar retrospectivamente columnas basándose en importancia de modelos que ya vieron las etiquetas del mes evaluado. Esta prueba identifica aporte marginal de bloques; no una selección automática causal.

## E03 — extensión de historia y transformaciones

Primero verificar que enero/febrero de competencia_02 sean compatibles con competencia_01. Comparar extensión de cobertura en un ensayo separado. Luego usar el mismo panel extendido en control y variantes: C3+lag2, C3+delta2, C3+media3; combinaciones sólo justificadas por resultados. S3 original entrena marzo–abril sin enero/febrero: lag2 sería todo faltante y el experimento no sería interpretable.

## E04 — interacción representación × hiperparámetros

Tras exploración, cruzar C3 y una representación candidata con configuración original y una alternativa de regularización fijada previamente. Los cuatro brazos separan efectos y su interacción. Si hay BO, igual presupuesto y búsqueda que incluya min_data_in_leaf=100; seleccionar en validación, no en el test. Ajustar aprendizaje y rondas conjuntamente, no atribuir a una familia diferencias de entrenamiento.

## E05 — puente con B0–B5

Comparar representaciones en el mismo período y con el mismo target, codificación, calidad, historia, semillas y política. No confrontar directamente la ganancia C3 agosto2021 con B4 octubre2019. La adaptación al protocolo de Ale mantiene BO/early stopping por AUC y test económico, explicitando cualquier diferencia con tutores.

## Evaluación común

- Ganancia principal a 11.000 contactos; 10.500 y 11.500 secundarios, congelados antes.
- Deltas pareados por seed y ganancia del promedio de scores, por separado.
- AUC, precisión/BAJA+2, faltantes por mes, RAM y tiempo.
- Sin claims de significación temporal basados sólo en veinte semillas.
- Hipótesis, método y limitaciones, resultados, conclusiones y próximos pasos para el video de Ale.
- Reproducción del control antes de las variantes; resultados reales sólo después de ejecutar. Preservar el modelo original.
