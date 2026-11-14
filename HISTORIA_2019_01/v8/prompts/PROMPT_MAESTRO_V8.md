# PROMPT MAESTRO — HISTORIA 2019 v8
## Cierre temporal de recetas históricas y preparación del sistema mensual

Estado: **protocolo propuesto, no ejecutado**. Fecha: 14/11/2026. Repositorio: `https://github.com/ClariRZ/Experimentos-`, carpeta `HISTORIA_2019_01/v8`. Este documento sustituye las propuestas conversadas de v8, no los contratos ejecutados de v1–v7.

Actuá como especialista en experimentación con LightGBM y evaluación económica. Ejecutá por etapas verificables, registrando fallos y resultados negativos. No prometas una mejora. No cambies fórmulas, tratamiento de ceros, cortes, semillas, brazos o calendario tras mirar resultados. No entrenes hasta que contrato, implementación, controles y presupuesto estén congelados y el plan de ejecución esté aprobado. Preparar y probar el código no equivale a autorizar horas de VM.

## 1. Pregunta única y alcance

¿Las recetas históricas R3, R4 o T4 sostienen una ventaja económica sobre B0 al desplazar el entrenamiento y evaluar agosto, septiembre y octubre de 2019, con igual proporción de contactos?

Se comparan **recetas completas congeladas**, cada una con sus hiperparámetros propios de v7. No se pretende aislar causalmente las variables con igual capacidad efectiva, ni medir el óptimo posible de cada ventana, ni demostrar mejora sobre el paquete de Ezequiel.

El experimento es exploratorio: agosto y octubre ya influyeron en el desarrollo; no se asegura que septiembre nunca se haya observado. Semillas nuevas y entrenamiento desde cero no borran esa exposición. No presentar los intervalos como confirmación independiente de toda la búsqueda histórica.

## 2. Relación con Ale y con lo aprendido

Mantener LightGBM, 2019, entrenamiento completo sin muestreo, BAJA+1 y BAJA+2 juntas, ganancia de BAJA+2, historia calendario exacta. La búsqueda previa de v7 fue por AUC de agosto y con igual presupuesto propio por brazo, como pidió Ale; aquí no se repite BO.

La consigna de referencia marzo–junio/agosto/octubre ya fue evaluada. El calendario móvil siguiente es una adaptación explícita para estudiar estabilidad temporal; no reemplaza ni reescribe aquella entrega. Tampoco cambia AUC por ganancia en una búsqueda que no se ejecutará.

Aprovechar de Ezequiel: ventanas equivalentes, repetición temporal, pruebas de features sin información futura, comprobación de predicciones, reporte de incertidumbre. No copiar automáticamente sus máscaras, pesos BAJA+2, banda de contactos, paquetes ni conclusiones.

No agregar canaritos, rankings, pesos, undersampling, híbridos, otras familias o búsqueda adicional en esta etapa. Sus resultados anteriores ya orientan la elección de estos tres contrastes; ampliar ahora cambia el experimento.

## 3. Datos, saneamiento y cobertura

Dataset de referencia SHA256 `459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872`. Comparar bytes antes de leer. Si falta o no coincide, detener sin sustituir por otro dataset. No publicar datos, identificadores ni predicciones individuales en Git.

Usar solo fotos 201901–201910 para features y evaluación de esta etapa. 201911/12 no son entrenamiento etiquetado. La etiqueta original se conserva; la prueba de reconstrucción desde presencia necesita su propia especificación y horizonte completo. No inventar clases para meses incompletos ni usar ausencia de archivo como baja.

Saneamiento idéntico a `referencias/config_frozen_v7.json`: nueve pares variable–mes de abril/mayo a NA, antes de construir historia; nulos conservados; no imputar ceros; infinitos a NA como en código original. Estas máscaras son decisiones históricas, no una nueva certificación oficial. **No agregar máscaras de julio u octubre**, ni reglas automáticas del 95%, ni ajustes por inflación/aguinaldo.

Ficha de anomalías por variable/mes: filas, nulos, ceros, no finitos, cardinalidad, cuantiles, definición del diccionario, comparación con meses vecinos y fuente; decisión explícita «documentar y conservar». No usar clase ni ganancia para decidir saneamiento.

Bloqueantes: claves duplicadas, mes ausente como archivo, esquema incompatible, etiqueta inválida, IDs desalineados, fuentes sin cobertura calendario exigida. Diferenciar ausencia de cliente y ausencia de mes completo. Una columna vacía en una ventana de entrenamiento se informa y conserva conforme al esquema congelado; no se depura por mirar evaluación. Si la matriz entera o un bloque completo carece de datos por un defecto de construcción, detener. Los faltantes legítimos por cliente no son un fallo ni se rellenan.

## 4. Calendario común y ausencia de futuro

| Mes puntuado | Entrenamiento etiquetado | Historia adicional disponible |
|---|---|---|
| 201908 | 201904, 201905, 201906 | Desde 201901 hasta el mes puntuado |
| 201909 | 201905, 201906, 201907 | Desde 201901 hasta el mes puntuado |
| 201910 | 201906, 201907, 201908 | Desde 201901 hasta el mes puntuado |

Todos los brazos usan exactamente las mismas claves ordenadas en cada ventana. El mes inmediatamente anterior queda fuera del entrenamiento etiquetado. Para features de una fila de mes t, solo usar fotos ≤t. Nunca calcular estadísticas históricas con fotos posteriores a esa fila.

El rezago máximo es 3, porque W4 incluye actual y tres anteriores; abril es el primer mes con cuatro fotos calendario potenciales desde enero. Esto no exige que cada cliente aparezca en las cuatro.

El esquema t−2 es una simulación condicionada a que esa clase esté disponible al puntuar t. Antes de llamarlo producción, verificar la definición y fecha real de maduración. Si la disponibilidad es posterior, bloquear esa afirmación y adaptar el protocolo **antes de ejecutar**, no mezclar calendarios durante la corrida.

## 5. Cuatro recetas, mismas definiciones ejecutadas

Listas exactas y orden de columnas: `referencias/recetas_v7.json`. Fuente de fórmulas: los scripts originales de v7 identificados por SHA256 en `referencias/PROCEDENCIA.json`. Reutilizar esas funciones o demostrar igualdad; no reescribirlas aproximadamente.

- **B0:** variables actuales y lag/delta 1 y 2 de las fuentes históricas admitidas por v7. No afirmar que son lags de todas las columnas crudas. Excluir ID, mes y clase de predictores según el contrato original.
- **R3:** B0 + relativos W3, para los pares fuente/fórmula que sobrevivieron la selección de entrenamiento de v7.
- **R4:** B0 + los mismos tipos de relativos W4, respetando la selección común R3/R4 de v7.
- **T4:** B0 + pendiente lineal W4, según las columnas congeladas de v7.

Lag j = valor del mismo cliente exactamente j meses antes. Delta j = actual − lag j. W_L = [t−L+1,…,t], orden cronológico. Ventana estricta: todas sus observaciones finitas y no nulas. Si falta una, la feature de ventana es NA.

Relativo = `(x_t − referencia) / abs(referencia)`. Las tres referencias son media de W_L, valor t−1 y primer valor de W_L. Referencia cero → NA; no agregar epsilon, no sustituir por relativo simétrico. Los negativos válidos permanecen. Pendiente = `sum((i−media(i))*x_i) / sum((i−media(i))²)`, i=0,…,L−1. Verificar unidades por mes.

Congelar el esquema heredado para estudiar transferencia de recetas: no volver a seleccionar columnas por cada mes. Explicitar que la selección original se basó en abril–junio de v7 y no representa una búsqueda nueva en cada ventana.

## 6. Modelos, hiperparámetros y 60 ajustes

Cada brazo mantiene exactamente su `best.json` y parámetros fijos de LightGBM de v7, incluido número de árboles. Guardarlos completos en el contrato, con semillas de LightGBM y número de hilos. No usar solo los cinco parámetros buscados olvidando defaults o parámetros fijos. `bagging_freq >= 1`. No ponderación extra ni sampling.

**No hay Optuna ni early stopping nuevos:** no observar etiquetas del mes puntuado para elegir árboles. V7 ya reoptimizó cada representación. Se estudia si esas recetas transferidas sirven al avanzar los meses, no si una nueva búsqueda puede rescatarlas.

Cinco semillas de evaluación comunes a todos los brazos y ventanas: 810001, 810007, 810019, 810031, 810043. Comprobar antes de congelar que no fueron usadas en los registros recuperados; si existe coincidencia, resolver y documentar antes de entrenar, jamás elegir por resultado. Derivar todas las semillas internas mediante una función fija y registrada.

Total: **4 brazos × 3 ventanas × 5 semillas = 60 ajustes nuevos**. Modelos nuevos desde cero, sin cargar modelos entrenados antiguos para producir métricas de esta etapa. Sí se reutilizan deliberadamente código, listas, configuración y conocimiento previo, con procedencia explícita. Un reajuste por recuperación con misma clave no cuenta como modelo adicional pero sí como costo consumido.

Ensemble = promedio aritmético de scores de las cinco semillas. Score no es probabilidad calibrada de BAJA+2. Preservar todos los modelos individuales. No mezcla de puestos, no stacking ni promedio de brazos.

## 7. Política económica congelada

Proporción común `p = 3481 / 131887`, tomada del control B0 de agosto v7. Calcular `k_t = (3481 * N_t) // 131887` con enteros. Misma población y k para todos los brazos y semillas. Orden: score descendente, ID ascendente para desempatar. No excluir clientes de forma diferente por brazo.

Ganancia = `1.100.000 * aciertos_BAJA+2 − 27.500 * contactos`. Equivale a +1.072.500 por BAJA+2 contactado y −27.500 por cualquier otro contactado, incluido BAJA+1. No sumar ambos costos dos veces. Son unidades monetarias nominales de la regla del concurso; no ROI real ni ganancia causal de una campaña sin experimento de intervención.

Métrica primaria de cada alternativa: media simple de sus tres diferencias mensuales de **ensemble** contra B0 con k común. Reportar también diferencia acumulada (3×media), ganancias absolutas y relativa = suma(diferencias)/suma(ganancias B0), si denominador positivo.

Diagnósticos sin selección: AUC contra BAJA+2; ganancias y deltas por semilla; positivos/empates/negativos; dispersión entre semillas; contactos y aciertos; captura y lift; coincidencia de envíos. Banda de sensibilidad k=80%,90%,100%,110%,120% del k común, redondeados hacia abajo, sin elegir el mejor corte. No confundir promedio de ganancias individuales con ganancia del ensemble.

## 8. Tres contrastes, incertidumbre y decisión

Contrastes únicos: R3−B0, R4−B0, T4−B0. No agregar comparaciones principales retrospectivamente.

Bootstrap pareado por cliente, manteniendo juntos todos sus meses. 20.000 réplicas, semilla 820001. Para cada cliente guardar contribución económica mensual bajo los envíos ya congelados; cada réplica remuestrea clientes con reemplazo y calcula la media de las tres diferencias agregadas. Intervalo percentil bilateral de **98,333333%** por contraste (colas 0,008333333 y 0,991666667; Bonferroni de tres). Informar el intervalo de 95% como secundario, con su rótulo.

Este bootstrap mantiene envíos y modelos fijos; no recalcula top-k de una nueva población, no reentrena, no repite selección y no estima generalización a otras épocas. El ajuste controla solo los tres contrastes de esta etapa, no todas las decisiones v1–v7. Con tres meses no afirmar estabilidad temporal universal. La variabilidad entre semillas se reporta aparte, sin sumar errores suponiendo independencia sin justificación.

Una candidata se clasifica «favorable según el protocolo exploratorio» solo si cumple todo:
1. diferencia primaria positiva y mejora relativa agregada ≥3%; B0 agregado positivo;
2. diferencia de ensemble positiva en al menos dos meses, **incluido septiembre**;
3. límite inferior ajustado >0;
4. al menos 4/5 semillas con diferencia media temporal positiva, sin convertir esta cuenta en un p-valor;
5. cumple el presupuesto operativo y todos los controles de integridad.

Si falla cualquiera, no se promueve por esta regla. Publicar resultados y causa. Si cumplen varias, elegir la de mayor límite inferior ajustado; empate exacto: menos columnas, luego menor tiempo mediano de puntuación, luego orden R3/R4/T4. Esta elección sigue siendo exploratoria y necesita evaluación futura.

Si ninguna cumple: mantener B0 como oficial y R3 como alternativa exploratoria predeclarada. No escoger retrospectivamente el mejor octubre ni abrir más pruebas. No exigir una mejora para dar el trabajo por concluido.

## 9. Pruebas antes de gastar VM

- Casos manuales: meses ausentes, cliente nuevo, ceros, negativos, NA, infinitos, fechas y orden calendario; relativos y pendiente calculados a mano.
- Igualdad del módulo nuevo contra funciones originales de v7 y orden de columnas; no modificar originales para hacer pasar la prueba.
- Invariancia de features de t al agregar o alterar meses posteriores a t.
- Mismas claves por brazo, sin ID/clase como predictor; impedir etiquetas de evaluación en ajuste.
- Ganancia con ejemplos manuales, igualdad de contactos, empate por ID y cálculo racional de k.
- Bootstrap con un cliente repetido entre meses: verificar que se remuestrea como bloque y respeta pareamiento.
- Recuperación interrumpida: resultado parcial no cuenta como completo; modelo y predicciones válidos no se sobrescriben.
- Restauración de un artefacto y reproducción de sus scores desde una ubicación distinta. Igual entorno: igualdad exacta esperada; otro entorno: tolerancias declaradas antes de medir, nunca ajustadas para ocultar un desvío.

## 10. Trazabilidad y respaldo

Antes del lanzamiento, guardar contrato legible y JSON; commit exacto; hash del dataset y de cada archivo mensual si se particiona; claves de entrenamiento/evaluación y sus hashes; lista ordenada de columnas; fuentes semánticas; fórmulas; saneamiento; configuración completa; semillas; biblioteca, sistema, CPU/hilos y dependencias fijadas; presupuesto; pruebas y exposición histórica de meses.

Por ajuste: clave única (run, brazo, mes, semilla), tiempos, modelo, hashes, predicciones con IDs, métricas, cantidad de filas/columnas y estado. Por cierre: tablas por mes y semilla, ensembles, contraste, bootstrap, incidentes, manifiesto de **todos** los artefactos. Manifiesto no incluye su propio hash; registrar el hash del manifiesto externamente.

Git público: prompts, código, configuración, dependencias, pruebas, reportes agregados, manifiestos sin datos individuales. Privado: dataset, modelos, predicciones, clases e IDs. Separar carpetas antes de `git add`; revisar lo que se publica. No asumir que `.gitignore` desversiona algo ya seguido.

Guardar copia privada fuera de la VM, verificar SHA256 del archivo y cada miembro, restaurar un modelo y sus predicciones, conservar registro de comprobación. Solo después las matrices regenerables pueden eliminarse mediante lista explícita. Una segunda carpeta en el mismo disco no es respaldo independiente. No marcar «reproducido» por comprobar hashes: distinguir integridad, restauración, reproducción de predicciones y reentrenamiento independiente.

## 11. Ejecución y límites

Una ventana y una matriz de brazo por vez; reutilizar memoria y liberar antes de la siguiente. No materializar los cuatro brazos para todos los meses simultáneamente. Dataset nunca se sobrescribe. Resultados anteriores y su entorno se preservan.

Preflight real: espacio libre, RAM, tamaño estimado de matrices, modelos, copias y archivos temporales; requerir margen superior a pico estimado más reserva operativa documentada. Medir tiempo con el primer ajuste programado, que queda como uno de los 60 si es válido. Si proyección excede seis horas, parar ordenadamente y entregar diagnóstico; no bajar semillas ni modificar receta silenciosamente.

Límite máximo inicial: seis horas de VM, con acción STOP independiente del proceso. Apagado al terminar o ante error, después de recuperación si cabe en el plazo. Si un respaldo no termina, preservar originales y registrar recuperación pendiente; no prolongar automáticamente el costo. Transferencia reanudable o por bloques, sin timeout fijo de 180 s para archivos grandes. El límite de seguridad puede detener la VM; la recuperación posterior no reentrena.

Estados separados: PREPARADO, ENTRENANDO, AJUSTES_COMPLETOS, EVALUACION_COMPLETA, RESPALDO_VERIFICADO, VM_DETENIDA. «Despachado» no significa entrenando. Chequeos de progreso cada 15 minutos si se configura monitor; avisar solo avance significativo, error, cierre o intervención necesaria. Nunca crear un monitor ficticio ni prometer supervisión sin programarla.

## 12. Puente a la segunda competencia, sin otra búsqueda

Construir en paralelo el esqueleto mensual con B0 y la segunda estrategia del catálogo. Confirmar el texto oficial antes de certificar cumplimiento: los archivos 202001–202006, dos estrategias y 15 minutos son requisitos conversados pendientes de cotejo documental.

Flujo: validar mes/esquema/claves → registrar entrada inmutable y hash → calcular features con el mismo módulo y solo pasado → puntuar modelos del catálogo → aplicar p congelada → escribir en staging → validar salida y reporte → publicar atómicamente y marcar mes terminado. Reintentar una ejecución interrumpida sin duplicar ni mezclar resultados. Si el mismo mes llega con otro hash, detener y registrar conflicto; no ignorarlo por estar «ya procesado».

La salida oficial, si la consigna lo exige, tendrá `numero_de_cliente`, `probabilidad`, `enviar`; documentar que `probabilidad` es score de ranking. Guardar predicciones de alternativas sin alterar envíos oficiales. Monitorear nulos, ceros, cobertura, scores y PSI como alertas; jamás modificar features automáticamente por esos indicadores.

Madurar etiquetas solo cuando el horizonte esté completo; contrastar la reconstrucción de 2019 con la clase conocida. Distinguir retraso de archivo, ausencia de cliente y baja. Ganancia/lift/captura solo donde exista clase válida; últimos meses pendientes.

Cronometrar carga, features, puntuación y reporte completos. Si se realiza recorrido 2020, recetas y reglas se congelan antes; no se seleccionan con ese resultado. Señalar pandemia y no extrapolar estabilidad de negocio. El entrenamiento final hasta octubre, si se decide para producción, exige un contrato separado común a ambas estrategias; no hereda evaluación independiente de modelos entrenados hasta junio. Reentrenamiento mensual queda fuera de esta etapa, no se agrega por defecto.

## 13. Entregables y cierre

1. Contrato y preflight reproducibles; diferencia explícita contra v7.
2. Código, pruebas y comando único de ejecución; modo de verificación sin entrenar.
3. 60 ajustes identificados o explicación precisa de interrupción; tabla completa de tres meses, semillas y ensembles.
4. Resultados de los tres contrastes, incertidumbre y decisión aplicando exactamente la regla.
5. Reporte de fallas y fortalezas actualizado, sin borrar resultados negativos.
6. Manifiesto público y respaldo privado comprobado; espacio liberado real, no estimado, y estado de VM verificado.
7. Guion corto para video: hipótesis, diseño, límites, resultados, conclusión y siguiente paso operativo; bibliografía de Ale y fuentes de código.
8. Prueba del módulo mensual y lista de puntos pendientes de la consigna operativa.

No iniciar una nueva batería si el resultado no es favorable. La finalidad es cerrar una pregunta útil, dejar evidencia recuperable y disponer de un proceso que pueda evaluarse hacia adelante.
