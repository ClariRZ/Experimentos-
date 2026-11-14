# Auditoría integral de Historia 2019

**Actualización posterior:** el respaldo privado v7 ya fue recuperado y verificado. Para estado vigente y comparación con la rama actual de Ezequiel, leer el [cierre v1–v7](../cierre_v1_v7_2026-11-14/INFORME.md). Las referencias a respaldo pendiente más abajo describen el momento de esta auditoría.

Fecha: 14/11/2026. Revisión de los experimentos y de su adecuación a la entrega. No se entrenaron modelos, no se encendió la VM y no se modificaron protocolos congelados.

## Dictamen

La evidencia respalda que ciertas representaciones históricas pueden mejorar la ganancia frente a sus controles. No respalda una receta universalmente superior ni permite sumar mejoras entre versiones. La familia con señal más repetida es la de cambios relativos cortos. La tendencia W4 es una alternativa prometedora, pero no ganó en todos los escenarios. Los híbridos no demostraron complementariedad en v7.

El programa experimental ya es suficiente para explicar hipótesis, método, resultados positivos y negativos y límites. El mayor déficit actual es cerrar restauración de artefactos y demostrar operación mensual reproducible; no falta inventar otras veinte familias.

## Alcance y fuentes

Revisión directa de resultados, contratos y código de v4–v7 en este repositorio. V2/v3 se contrastaron adicionalmente con agregados locales recuperados (`work/v2_recuperado`, `work/v3_final`); v1 tiene evidencia parcial en la comparación histórica. C3 se trata como antecedente: no se presenta como una corrida íntegramente reauditable dentro de este repositorio. No se afirma haber auditado todos los experimentos C1 de la VM ni el estado actual de sus archivos.

La consigna de Ale y la tutoría son las que Clara aportó en la conversación: 2019, LightGBM, historia lag/delta 1 y 2, marzo–junio como referencia, agosto para AUC/BO, octubre para ganancia, con adaptaciones justificadas. Los requisitos operativos de dos estrategias, archivos mensuales, 15 minutos y recorrido 202001–202006 proceden del diseño conversado; falta cotejarlos con el texto oficial completo de esa entrega. No convertir una propuesta nuestra en un requisito atribuido al docente.

Fuentes principales: `experimento_2026-11-13`, `HISTORIA_2019_01/v5`, `v6`, `v7`; informe previo `informes/prompts_modelos_2019_2026-11-13`; auditoría `auditoria_trazabilidad_2026-11-13`. La comparación externa usa únicamente la revisión histórica identificada de Ezequiel, commit `770abaa9cad412647211c255360cb6dfe364e697`; no es una auditoría de su main actual.

## Qué hizo cada versión

| Versión | Pregunta y resultado | Fortaleza | Límite decisivo |
|---|---|---|---|
| v1 | Historia amplia y familias; la iteración de ratios mejoró AUC y ganó 16/20 comparaciones individuales de AUC | Primer indicio de normalización personal útil | Archivo parcial; parámetros compartidos; no prueba económica final comparable con v7 |
| v2 | RAW hacia lag/delta; B4 ganó 4,913 M de ganancia suavizada media frente a RAW, 5/5 semillas; familias posteriores no promovidas | Demostró utilidad de historia frente a RAW en ese diseño | Ajuste favorable a B4 y filtro 90% restrictivo; ratios no identificables no significa ratios derrotados |
| v3 | Rankings, historia de rankings, actividad y presencia; conservó C0 tras ampliar varias comparaciones a 20 semillas | Una señal inicial desapareció con más semillas: evitó promoción precipitada | Parámetros heredados; octubre pendiente en el cierre recuperado; no es el mismo ranking de v4 |
| v4 | Cinco brazos, marzo–junio, 75 ajustes; ninguna familia ganó la regla original de AUC | Calendario de referencia, reoptimización propia y octubre congelado | Semilla 101 usada en búsqueda y evaluación; políticas de contactos diferentes entre brazos |
| v5 | Siete brazos, 105 ajustes; separó promedio/mínimo/máximo/rango y retiro de deltas | MIN, RANGO y P fueron favorables en agosto; separa componentes | Sin octubre publicado; no concluir generalización de sus ganadores |
| v6 | Once brazos, junio común, 165 ajustes; profundidad W3/W4/W6 | Control justo dentro del calendario; T4/R3/R4 favorables en agosto y 5/5 en octubre | Un mes de entrenamiento; políticas propias; resultado no transferible automáticamente a marzo–junio |
| v7 | Diez brazos, abril–junio, 150 ajustes; híbridos y presupuesto común | Mejor control económico y de multiplicidad; verificación exacta de agosto antes de octubre | Tres contrastes principales inconcluyentes; octubre ya conocido; búsqueda limitada y problemas de almacenamiento |

V4–v7 suman 33 brazos, 330 ajustes de búsqueda y 165 reajustes por semilla: 495 ajustes registrados. No son 495 pruebas independientes de generalización. La auditoría no volvió a entrenarlos.

## Qué muestran las ganancias

Importes en millones de la regla del concurso, no ingresos cobrados. Para v4–v6 agosto es ganancia suavizada optimizada y octubre ganancia puntual con política propia congelada; v7 usa ganancia puntual con presupuesto común. Cada delta corresponde al control de su propia versión. No comparar las magnitudes entre protocolos como una clasificación única.

| Evidencia | Diferencia agosto | Diferencia octubre | Lectura |
|---|---:|---:|---|
| v4 F3, relativos | +2,733 | +7,150 | Señal económica en ambos meses; no ganó el criterio original de AUC |
| v4 F1, resúmenes juntos | +3,198 | +12,155 | Ensemble favorable; octubre solo 2/5 semillas favorables |
| v4 F4a, ranking actual | −7,505 | +10,258 | Reversión temporal importante |
| v4 F4b, historia del ranking | −11,176 | −7,893 | No priorizar esta receta |
| v5 P / MIN / RANGO | +3,987 / +5,110 / +4,182 | Pendiente | Evidencia de desarrollo, no cierre económico |
| v6 R3 | +5,453 | +11,688 | Favorable en ambos; 5/5 semillas de octubre |
| v6 R4 | +4,759 | +15,125 | Favorable en ambos; no demuestra W4 siempre superior a W3 |
| v6 T4 | +6,229 | +6,820 | Favorable en ambos |
| v6 R6 | −3,506 | +16,060 | No elegirlo retrospectivamente solo por octubre |
| v7 R3 | +3,300 | +7,700 | Persistencia del signo favorable con otro calendario y presupuesto común |
| v7 R4 | −3,300 | +9,900 | No persistente entre meses |
| v7 T4 | −1,100 | +11,000 | Mejor ensemble de octubre; no ganador universal |
| v7 H_S | +6,600 | +4,400 | Mejora contra B0 en ambos; no supera R4 en octubre |
| v7 P3 | −2,200 | +9,900 | Promedio útil en octubre; agosto no lo respalda |

En v7, B0 obtuvo 272,1675 M y T4 283,1675 M en octubre, con 3.583 contactos cada uno: +4,04%. H_T perdió 6,6 M contra R4 y 7,7 M contra T4. H_S perdió 5,5 M contra R4. Los tres intervalos ajustados incluyen cero. T4 vs B0 tiene un intervalo nominal del 95% positivo, pero es secundario y sin corrección por todas las búsquedas. Ganar en 5/5 semillas no elimina esa limitación.

H_S mejora frente a B0 en ambos meses, pero en octubre queda por debajo del componente R4: es evidencia contra asumir que agregar fórmulas suma ganancias. No demuestra que las combinaciones sean siempre perjudiciales.

## Fortalezas que conviene conservar

1. Identidad del dataset, contratos, meses, fuentes, fórmulas y listas ordenadas de columnas. Los nombres de modelos solos no bastan; aquí existe evidencia adicional.
2. Rezagos por mes calendario exacto, sin reemplazar un mes ausente por la última fila disponible; separación de etiquetas y construcción de features. Ventanas W incluyen el mes actual.
3. Depuración de columnas basada en entrenamiento; parámetros propios por alternativa desde v4, con presupuesto comparable y sin reutilizar modelos de una variante como si fueran otra.
4. Etiqueta de entrenamiento BAJA+1/BAJA+2 y AUC BAJA+2 explícitas; fórmula económica consistente. AUC para BO y ganancia para evaluación económica respeta lo pedido: su desacuerdo no es por sí mismo un error.
5. Cortes de agosto congelados antes de puntuar octubre; control común de contactos en v7. La mejora no se compra contactando más clientes.
6. Separación entre ensemble, promedio de ganancias por semilla y estabilidad. Pruebas de equivalencia exacta de predicciones antes de octubre.
7. Registro de resultados negativos y de fallos operativos. No se alteró octubre con máscaras nuevas para mejorar métricas; las anomalías quedaron documentadas.

## Debilidades y cómo resolverlas

**Exposición repetida a agosto y octubre.** Nuevas recetas nacieron después de observar esos meses. Reentrenar desde cero o cambiar semillas no borra ese conocimiento. Presentar los resultados como exploratorios y congelar ahora el sistema que se medirá hacia adelante. No inventar un test independiente dentro de un historial ya usado.

**Cambio simultáneo de calendario, fuentes, semillas y corte.** V4/v5 entrenan 507.328 filas marzo–junio; v6, 128.474 de junio; v7, 381.596 abril–junio. Las diferencias entre versiones son evidencia de recetas completas. Cada comparación causal exige mismo calendario, población, política y presupuesto de búsqueda.

**Poca exploración de hiperparámetros.** Diez trials por brazo constituyen una búsqueda acotada. Un resultado negativo no demuestra inutilidad de una familia. Tampoco justifica optimizar selectivamente hasta que gane. Si hay un presupuesto nuevo, declararlo y mantenerlo parejo.

**Incertidumbre limitada.** Las semillas no son meses. El bootstrap de v7 mantiene contribuciones de clientes y selección fija: no reentrena, no repite Optuna, no recalcula el top-k de cada población remuestreada y no captura toda la variación temporal. Bonferroni controla tres contrastes registrados, no toda la búsqueda histórica v1–v7.

**Saneamiento con evidencia incompleta.** Las nueve máscaras abril–mayo son decisiones históricas conservadas, no una nueva validación oficial de negocio. Ceros de julio/octubre se preservaron: un cero puede ser legítimo. Mantener ficha por anomalía con distribución, cobertura, semántica, fuente y decisión. No modificar ahora la corrida; cualquier sensibilidad futura sería otro protocolo.

**Trazabilidad no equivale a restauración.** Git tiene parámetros, métricas y hashes, no todos los modelos/datos privados. El respaldo privado de octubre v7 quedó incompleto y el apagado actual no está verificado. Antes de limpiar más, recuperar artefactos, comprobar hashes y abrirlos desde otro lugar. No prometer reproducción íntegra por verificar un manifiesto.

**Fallos operativos evitables.** Matrices simultáneas agotaron el margen de disco; el control de conexión no manejaba el primer timeout; la copia de respaldo tenía un límite de 180 segundos y un apagado podía interrumpirla. Separar estados de cálculo, empaquetado, copia, verificación y apagado. Copia reanudable y respaldo duradero antes de declarar éxito; límite de costo independiente. La continuación en memoria resolvió octubre, pero no reemplaza un sistema mensual probado.

**Documentación histórica confundida con estado actual.** Hay textos que decían v6 sin ejecutar cuando sí existen cierres; comentarios antiguos que decían octubre pendiente en v4; y manifiestos parciales. Crear un índice único por corrida con estado, fecha, commit y ubicación de evidencias. Preservar los originales con su fecha, sin usarlos como resumen actual.

## Controles ejecutados en esta auditoría

- Reejecutado el extractor de v4–v6: 23 brazos y 345 ajustes verificados en selección Optuna, columnas, métricas, cortes y aciertos compatibles con la fórmula económica.
- V4: 53 archivos originales del manifiesto y protocolo completo de columnas verifican. No se verificaron archivos privados de modelos ni se reentrenó.
- V6: verificador de octubre aprobó 55 políticas por semilla, 11 ensembles y 18 comparaciones.
- V7: 100 trials, 100 ganancias individuales de ambos meses y 20 ensembles; diferencias pareadas y configuración congelada coinciden. Las cifras no se regeneraron desde predicciones privadas en esta auditoría.
- Manifiestos: v5 59/59; v7 código 26/26 y resultados 153/153. V6: 19/20; el README cambió después del manifiesto, coherente con el commit que documentó octubre. Se conserva el manifiesto histórico y se informa la discrepancia, no se silencia regenerándolo. Estos conteos no implican que cada archivo existente esté cubierto por esos manifiestos parciales.

`verificar.py` y `VERIFICACION.json` permiten repetir las verificaciones agregadas de v7 y de los manifiestos. Los verificadores originales de las otras versiones se mantienen en sus carpetas. No se inspeccionaron en vivo VM, bucket, facturación ni backups remotos.

## Qué aprovechar de Ezequiel

Del análisis histórico disponible, aprovechar comparación pareada, calendario equivalente entre control y candidato, reporte en varios meses, control de configuración y revisión de presupuesto de contactos. No copiar cifras ni decir que su paquete es mejor sin igualar datos, pesos, calendario y política económica. Su evaluación exploratoria que incluye octubre no equivale a test independiente. El peso extra de BAJA+2 modifica otra dimensión; Clara no lo quiere incorporar, y no es necesario para la propuesta siguiente. V7 ya incorporó un híbrido con relativos simétricos y evaluación más explícita de incertidumbre; esa unión no demostró superioridad sobre R4.

## Mejor camino para cumplir la entrega

Separar el entregable experimental del operativo. Para el primero, contar una secuencia corta: historia básica; representaciones; profundidad; combinaciones; qué se sostuvo y qué no. Las conclusiones negativas también responden la hipótesis. No es requisito conseguir una mejora del 5%: fue una referencia de magnitud interesante en la tutoría, no una garantía.

Para el operativo, mi recomendación es B0 como referencia oficial conservadora y R3 como alternativa histórica exploratoria. R3 requiere menos historia que W4 y su familia muestra señal favorable repetida. No afirmar que es exactamente el mismo modelo de F3/v6: cambian listas y ajuste. T4 queda como candidato en observación si el costo lo permite, no como elección automática porque obtuvo el máximo de octubre. H_S es un candidato adicional, pero no hace falta llevar cuatro estrategias si solo se necesitan dos.

La elección B0/R3 es una recomendación posterior al análisis; no reescribirla como una selección independiente fijada antes de octubre. Si se decide otra estrategia oficial por criterio de negocio, documentar esa nueva decisión y su evaluación futura.

1. Cerrar respaldo y comprobar restauración de modelos, configuración, columnas y predicciones de referencia; confirmar estado de VM. Es prioridad operativa inmediata.
2. Congelar el alcance de la entrega y el catálogo B0/R3. Reutilizar funciones ejecutadas, sin cambiar silenciosamente ratios, ventanas o reglas de faltantes. Probar equivalencia lote histórico frente a cálculo mensual.
3. Verificar la reconstrucción de etiquetas contra `clase_ternaria` solo donde haya horizonte completo. Diferenciar baja, ausencia de archivo y cobertura incompleta. No tratar todos los desaparecidos como baja sin esa validación.
4. Construir entrada mensual, contrato de esquema y claves, orden de meses, estado persistente, escritura atómica, reintentos idempotentes, ranking estable por ID y salida requerida. El nombre `probabilidad`, si la consigna lo exige, debe documentarse como score no calibrado.
5. Fijar presupuesto común de B0 en 2019. Si se mantienen modelos congelados, usar su política congelada. Si se reentrenan hasta octubre, ambos deben tener el mismo calendario y un contrato nuevo: esos modelos no heredan la validación independiente del modelo viejo ni la optimalidad de su corte.
6. Puntuar y registrar alternativas sin afectar envíos oficiales. Evaluar al madurar etiquetas; no fabricar ganancias para los últimos meses sin clase. Monitorear cobertura, ceros, nulos, distribución de scores y tiempos; alertar sin imputar automáticamente.
7. Cronometrar el flujo completo en los archivos y máquina exigidos. Los 197 segundos de inferencia de octubre v7 son un antecedente favorable, pero no certifican un pipeline mensual dentro de 15 minutos. Si la consigna requiere 202001–202006, usarlo como recorrido operativo prospectivo con receta congelada, no para volver a elegir variables. Aclarar el régimen excepcional de 2020.
8. Dejar reentrenamiento mensual como extensión opcional después de tener el flujo fijo funcionando. Si existe, al final, con tiempo acotado y activación al mes siguiente.

Cerrar octubre de v5 es útil para completar el informe de sus siete brazos sin nuevos ajustes, pero no debería bloquear la entrega operativa. No lanzar v8, canaritos, otra batería de rankings o un híbrido más grande por inercia. Si queda una pregunta que cambia la decisión de producción, formular un único contraste específico y declarar de antemano qué decisión tomará cada resultado.

## Preguntas concretas para Ale

- ¿Abril–junio como adaptación común de W4 queda aceptado y se presenta separado de marzo–junio de referencia?
- ¿Para el sistema mensual se esperan modelos fijos evaluados o un ajuste final con toda la información disponible? ¿Se evalúa la exploración de una alternativa aunque no sea confirmatoriamente superior?
- ¿El presupuesto de contactos puede fijarse como proporción del control, y cuál es la regla exacta de maduración de clase?
- ¿El recorrido 202001–202006 y los 15 minutos incluyen carga, features, puntuación, reporte y eventual reentrenamiento? ¿Qué archivos y columnas son obligatorios?

No es necesario reabrir decisiones ya aclaradas, como la clase positiva de AUC, ni pedir permiso para cada acción reversible. Estas preguntas precisan el contrato de entrega, no condicionan que se avance ahora con respaldo y esqueleto mensual.

## Anexo: inventario numérico de los 33 brazos recientes

Deltas contra el control de la misma versión. Agosto v4–v6 suavizado/política propia; v7 puntual/presupuesto común. Octubre siempre puntual, con distintas políticas según versión. No son cifras directamente intercambiables.

| Versión | Brazo | Δ agosto M | Δ octubre M | Semillas favorables octubre |
|---|---|---:|---:|---:|
| v4 | B0 | +0.0000 | +0.0000 | — |
| v4 | F1 | +3.1975 | +12.1550 | 2/5 |
| v4 | F3 | +2.7326 | +7.1500 | 4/5 |
| v4 | F4a | -7.5050 | +10.2575 | 5/5 |
| v4 | F4b | -11.1762 | -7.8925 | 0/5 |
| v5 | B0 | +0.0000 | Pendiente | — |
| v5 | L | -1.6601 | Pendiente | — |
| v5 | P | +3.9866 | Pendiente | — |
| v5 | MIN | +5.1097 | Pendiente | — |
| v5 | MAX | +2.5144 | Pendiente | — |
| v5 | RANGO | +4.1824 | Pendiente | — |
| v5 | F1 | +1.4774 | Pendiente | — |
| v6 | B0_J | +0.0000 | +0.0000 | — |
| v6 | L4 | +0.1131 | +4.3175 | 2/5 |
| v6 | L6 | +2.1808 | +6.3525 | 3/5 |
| v6 | S3 | +0.6774 | +6.9300 | 4/5 |
| v6 | S4 | -2.9781 | +6.5175 | 2/5 |
| v6 | S6 | -7.0824 | +6.7925 | 2/5 |
| v6 | T4 | +6.2295 | +6.8200 | 5/5 |
| v6 | T6 | -4.7444 | +1.8975 | 4/5 |
| v6 | R3 | +5.4535 | +11.6875 | 5/5 |
| v6 | R4 | +4.7587 | +15.1250 | 5/5 |
| v6 | R6 | -3.5055 | +16.0600 | 4/5 |
| v7 | B0 | +0.0000 | +0.0000 | — |
| v7 | RK | +0.0000 | +3.3000 | 4/5 |
| v7 | P3 | -2.2000 | +9.9000 | 5/5 |
| v7 | MIN3 | -6.6000 | +2.2000 | 2/5 |
| v7 | RAN3 | -6.6000 | +0.0000 | 4/5 |
| v7 | R3 | +3.3000 | +7.7000 | 4/5 |
| v7 | R4 | -3.3000 | +9.9000 | 5/5 |
| v7 | T4 | -1.1000 | +11.0000 | 5/5 |
| v7 | H_T | -1.1000 | +3.3000 | 4/5 |
| v7 | H_S | +6.6000 | +4.4000 | 5/5 |
