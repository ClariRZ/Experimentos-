# Comparación de experimentos y verificación de Git

Revisión del 13/11/2026. Se inspeccionaron código, protocolos, recetas y resultados guardados. No se entrenó, no se abrió octubre y no se encendió la VM. El estado remoto se consultó en GitHub mediante `git ls-remote`; no se infiere de una referencia local antigua.

## Qué pregunta responde el experimento actual

En v4 se pregunta si reformular la historia corta mejora un LightGBM que ya tiene variables actuales, rezagos y deltas de uno y dos meses. Se entrenó con marzo–junio, se optimizó con AUC de agosto y se compararon cinco semillas por alternativa. Octubre queda reservado para evaluar la ganancia después de congelar las decisiones.

Las alternativas fueron baseline B0, B0 más resúmenes W3, B0 más cambios relativos, B0 más rankings y B0 más rankings con historia. W3 contiene el mes actual y los dos anteriores. Cada alternativa tuvo 10 pruebas Optuna propias y cinco reajustes; hubo 75 ajustes. Las semillas miden sensibilidad al azar; no son cinco períodos independientes.

## Versiones: no confundir sus nombres

| Aspecto | v1 | v2 | v3 | v4 ejecutada |
|---|---|---|---|---|
| Pregunta | Familias adicionales sobre baseline histórico amplio | Construir la escalera RAW→historia y probar familias | Separar ranking actual de historia del ranking; actividad y ausencia de registros | Revisar semántica/cobertura y reoptimizar cada representación |
| Control | Iteración 000: 760 columnas | B0=RAW 152; control histórico B4=588 | C0=B4 de v2, 588 | B0 histórico adaptado, 652 |
| Fuentes para historia | 152 originales en el baseline amplio | 109 fuentes que superan cobertura 90% | Hereda B4; familias acotadas y filtro de cobertura | 129 fuentes revisadas con diccionario; sin umbral 90% |
| Familias | Resúmenes, inactividad, ratios personales, paquete de rangos | Media, mínimo, máximo, desvío, ceros, ranks, tendencia | A ranks; B ranks+lags/deltas; C actividad; D presencia de registros | F1 media/mín/máx/rango; F3 cambios relativos; F4a rank; F4b historia de rank |
| Hiperparámetros | BO baseline; parámetros comunes para familias; BO final separado | 50 pruebas sobre B4; parámetros comunes para comparaciones | Parámetros y 271 árboles heredados de B4 | 10 pruebas independientes por alternativa |
| Semillas observadas | 20 en iteraciones documentadas | 5 por alternativa evaluada | 20 para C0/A/B/D; 5 para C | 5 en cada alternativa |
| Ganancia suavizada | Ventana 1.001 | Ventana 2.001 | Ventana 2.001 | Ventana 2.001 |
| Decisión | Regla de AUC y ensemble | Ganancia/variación/80% victorias/bootstrap; indicio por AUC | Regla económica y bootstrap; indicios económicos o AUC | ΔAUC medio positivo y ≥4/5 victorias |
| Cierre | Seleccionada 003 ratios personales | Sin familias promovibles; B4 queda como control | Congelado C0 | Sin candidatos que superen la regla; queda B0 |

La v1 se reconstruye principalmente desde la bitácora y fuentes preservadas en `v2/auditoria/fuentes_vm`. No hay aquí una carpeta autónoma v1 con todas sus salidas originales. Es evidencia de menor completitud que los resultados JSON de v2–v4.

## Similitudes comprobadas

Las versiones comparten el problema bancario, LightGBM, entrenamiento marzo–junio de 2019, validación agosto, entrenamiento positivo BAJA+1/BAJA+2 y AUC de validación BAJA+2. La regla económica es +1.072.500 para BAJA+2 y −27.500 para los demás contactos. El dataset registrado de v2/v3/v4 tiene el mismo SHA256. Se preservan faltantes y se aplican máscaras de nueve pares variable-mes adoptados como rotos; no equivalen a confirmación oficial de negocio.

Se usan lags por calendario y comparación con control. Octubre no figura evaluado en los cierres recuperados: v1 exportó predicciones pero dejó métricas de test nulas; v2/v3/v4 documentan octubre cerrado. Esto no certifica toda posible exposición fuera de estos registros. El código v2 contiene un evaluador de octubre, pero su mera existencia no demuestra ejecución.

## Diferencias que cambian la interpretación

1. **B0 no significa lo mismo.** En v2 no tiene historia; en v4 sí. La comparación conceptualmente próxima es B4(v2)/C0(v3) frente a B0(v4), pero tampoco son idénticos: 588 contra 652 columnas, diferentes fuentes y parámetros.
2. **Los ratios no son la misma receta.** v1 usa actual/media personal para cuatro fuentes y restringe negativos; v4 usa `(actual-referencia)/abs(referencia)` frente a tres referencias sobre 129 fuentes, conserva negativos válidos y anula denominadores cero. No es una reproducción del ganador de v1. En v2 la familia R quedó no identificable por las reglas de cobertura, no derrotada en un entrenamiento.
3. **Rankings distintos.** v3 rankea montos separando positivos y negativos, conserva cero como cero y parte de 13 ranks. v4 rankea conjuntamente todos los valores válidos dentro del mes, incluidos ceros/negativos, y agrega 126 columnas de rank. F4b además suma resúmenes móviles, que el brazo B de v3 no tenía.
4. **Optimización distinta.** v2/v3 congelaban parámetros elegidos para B4; eso facilita aislar cambios con parámetros fijos, pero puede favorecer al control. v4 asigna el mismo presupuesto de optimización a cada representación. Compara representaciones con su ajuste, no solo variables a hiperparámetros constantes.
5. **Filtros distintos.** v2 exigía cobertura ≥90% de todas las derivadas de una fuente en cada mes de entrenamiento. v4 conserva variables parcialmente observadas, retira vacías/duplicadas y evita transformar genéricamente categorías, indicadores y tiempos relativos. No es solo quitar o agregar columnas al mismo baseline.
6. **Cinco contra veinte semillas.** v3 tuvo confirmación en 20 para varias alternativas; v4 aún no. Cambió también la regla de promoción. Las etiquetas “no aporta” no expresan exactamente la misma condición.
7. **Junio tuvo un uso específico en v2.** Se entrenó marzo–mayo y se usó junio para preseleccionar fuentes sin mirar agosto; los modelos comparados finales se entrenaron marzo–junio. Esto explica la mención previa de “testear junio”; no era el test final.

## Qué aprendimos y qué no

En v1, 003 ratios personales superó a 000 en AUC medio por aproximadamente 0,000950, con 16/20 victorias; el AUC combinado pasó de 0,914136 a 0,915105. La ganancia puntual diagnóstica en cortes distintos pasó de 205,563 M a 210,045 M (+2,18%). No comparar esa cifra directamente con una ganancia suavizada de ventana 2.001.

En v2, B4 frente a RAW mejoró AUC medio en 0,006373 y ganancia suavizada media en 4,913 M (aproximadamente +2,48%), con 5/5 victorias en ambas. Su veredicto fue INDICIO, no confirmación. Los parámetros estaban optimizados para B4. Las siete familias evaluadas después no superaron B4 y la cadena terminó sin combinar/reoptimizar. Media, mínimo y máximo se probaron por separado sobre 20 fuentes, a diferencia del paquete amplio F1 de v4.

En v3, C0 conserva exactamente las columnas de B4 y reutiliza sus primeras cinco semillas verificadas: el AUC combinado de cinco semillas coincide en 0,914436. Se ampliaron C0/A/B/D a 20 semillas. A perdió 1,090 M frente a C0; B ganó apenas 0,036 M y perdió AUC; D perdió 0,628 M. C quedó descartado tras cinco semillas. B ganó 1,126 M frente a A, pero eso no bastó contra C0. D pasó de una señal positiva con cinco semillas a negativa con veinte: ejemplo concreto de por qué no confirmar por pocas semillas.

En v4, el baseline conserva el mejor AUC medio. F3 gana +1,42% de ganancia media pero pierde AUC; F1 combinado gana +1,55% de ganancia suavizada y mejora AUC, aunque su media individual no mejora. F4a/F4b empeoran. Son indicios para hipótesis futuras, no una mejora final demostrada. Ninguna versión muestra aquí test de octubre completado.

Los resultados económicos anteriores no se acumulan: no se puede sumar el +2,18% de v1 al +1,42% de v4. Tampoco puede declararse que v4 ganó a v3 comparando directamente AUC combinados de cinco contra veinte modelos.

## Auditoría de guardado

Al comenzar, Git local estaba limpio, en `bf7cd96`. Todos los JSON versionados se pudieron leer. La comprobación de conectividad de Git no encontró objetos necesarios faltantes; informó cinco blobs sueltos, que no constituyen pérdida de los commits activos. No se detectaron datasets, predicciones individuales ni archivos de modelos con las extensiones examinadas entre los archivos versionados de HISTORIA_2019_01; no es un escaneo universal de secretos.

GitHub `main`, consultado en vivo, apuntaba a `06fd6357c46b348f593dd456da0eaf6d9d8c69a3`: **13 commits por detrás antes de esta auditoría**. El número aumenta con el commit que guarda este informe. No se hizo push.

| Carpeta | Archivos versionados locales al inicio | En GitHub consultado |
|---|---:|---:|
| v2 | 162 | 162 |
| v3 | 128 | 13 |
| v4 | 68 | 0 |

Los archivos v2 del árbol remoto coinciden con los locales por pertenecer al mismo historial sin cambios posteriores en esa carpeta. De v3 estaba publicada la preparación, no los resultados de screening/cierre. v4 no estaba publicada.

**Qué está guardado de v4:** configuración ejecutada, scripts, propuesta recibida, auditorías, pruebas, pilotos/calibración, registro de inicio, análisis y 22 objetos JSON originales de resultados/búsquedas/identidades, con hash verificado. No hay un archivo llamado PROMPT_MAESTRO_v4: el contrato efectivo está repartido entre `prompts/propuesta_recibida.txt`, `configuraciones/ejecucion_completa.json` y el código.

**Qué falta para decir “todo respaldado”:** publicar commits locales; recuperar el manifiesto completo de variables/cobertura y logs finales v4 desde el agregado conservado en Cloud Shell; conservar modelos/predicciones de manera externa a Git si se necesita restauración íntegra. La carpeta local v1 no contiene todos sus resultados originales. No se verificó nuevamente el contenido actual del disco de la VM en esta revisión.

El runner completo v4 reutiliza matrices de `resultados/inicial_20261111_01/private`; esas matrices no están en Git. Un clon nuevo necesita reconstruirlas con el código de preparación y el dataset autorizado, o restaurarlas desde almacenamiento externo. Guardar el código no significa guardar un entorno ejecutable completo con datos.

Se encontraron README desactualizados que presentaban v4 como auditoría pendiente de entrenamiento. Se agregó un encabezado de estado actual y enlaces a los resultados, preservando el texto histórico.

## Qué falta del programa experimental

Confirmación independiente de v4, rama larga W3/W4/W6 con entrenamiento común y su propio baseline reoptimizado, selección/poda con canaritos si se justifica, combinaciones y test final de octubre. Los scripts que contienen estas etapas no demuestran que se ejecutaran. La pregunta a resolver antes de seguir es si confirmaremos ganancia del ensemble como objetivo final manteniendo AUC para Optuna, y con qué criterio fijado antes de ver nuevos resultados.
