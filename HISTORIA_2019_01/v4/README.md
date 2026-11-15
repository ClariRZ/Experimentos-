## Actualización: octubre evaluado — 13/11/2026

Evaluación de los 25 modelos v4 completada sin reentrenar ni buscar cortes en octubre. VM apagada. [Informe de octubre](auditoria/octubre_20261113_01/INFORME.md). F1: +12,155 M de ensemble; F4a: 5/5 semillas favorables. Se declara exposición previa a resultados grupales. Las referencias a octubre pendiente más abajo describen el estado anterior.

# Historia 2019 v4 — estado actualizado al 13/11/2026

La etapa corta exploratoria **terminó correctamente**: 5 alternativas, 50 pruebas Optuna y 25 reajustes con semillas. Control B0 conservado por la regla de AUC; señales económicas de F3 y del ensemble F1, aún sin confirmación. Octubre no evaluado.

- [Informe y resultados](auditoria/completa_20261111_03/analisis/INFORME.md)
- [Comparación con v1–v3 y auditoría Git](auditoria/comparacion_versiones_20261113/COMPARACION_Y_GIT.md)
- Contrato efectivamente ejecutado: `configuraciones/ejecucion_completa.json` y `scripts/ejecutar_completa.py`.
- El umbral del 90% del borrador se eliminó para esta corrida. No se entrenaron canaritos, historia larga ni combinaciones.
- Código y métricas están en Git local; publicación y respaldo externo completo pendientes según la auditoría.

## Documento histórico de preparación (no refleja el estado actual)

# Historia 2019 v4 — preparación de auditoría

Estado: auditoría real completada el 11 de noviembre de 2026; VM apagada. Sin entrenamientos v4. Ver `auditoria/INFORME_AUDITORIA_REAL.md`.

Se preserva la propuesta recibida en `prompts/propuesta_recibida.txt` como antecedente, no como instrucciones ejecutables. Este README y el código describen el alcance implementado.

## Correcciones implementadas

- Saneamiento obligatorio de los nueve pares variable-mes conocidos, antes de generar historia.
- Dataset identificado por SHA-256 y veinte semillas contrastadas con un artefacto previo explícito.
- Verificación de claves, etiquetas y todos los meses de enero a agosto.
- Rezagos por mes calendario exacto; ventanas completas; ratios con denominador cero o resultado no finito quedan nulos.
- Baseline contado con nombres reales: originales no vacías en entrenamiento más lag1, lag2, delta1 y delta2 de las fuentes propuestas/revisadas. No se presupone 588 ni 760 columnas.
- Cobertura finita medida por mes. Redundancias se informan por separado y no eliminan fuentes completas.
- Rama larga conserva pares fuente-fórmula comunes a W3/W4/W6. Esto reemplaza la exigencia del borrador de conservar ocho fórmulas para cada fuente. Los clientes no se eliminan por cobertura.
- La pendiente W3 queda solo como referencia homogénea en la rama larga; se excluye de la rama corta por equivalencia con delta2/2.
- Ranking mensual: rango promedio dividido por cantidad no nula, incluyendo ceros; distinto del ranking con signo de v3. Se auditan ranking actual y su historia, sin aprobar automáticamente todas sus columnas.
- No se importan LightGBM ni Optuna. No se entrenan canaritos.

## Validación local

21 pruebas sintéticas aprobadas el 11 de noviembre de 2026, incluyendo ejecución completa del auditor sobre un dataset artificial. Cubren huecos de mes, cambio de año, saneamiento, pendientes W3/W4/W6, ceros y desbordes, cobertura finita, duplicados, semillas, rankings, ganancia suavizada, desempate y corte congelado.

## Pendiente antes de entrenar

1. Revisión semántica completada con el diccionario: 129 fuentes candidatas, 23 excluidas de transformaciones genéricas. `sources_reviewed` es true. Falta contrastar el esquema y la cobertura con los datos reales; esto no es selección por performance.
2. Auditoría real completada. Revisar sus exclusiones por cobertura antes de congelar el 90 %. La detección de nuevas roturas requiere revisión adicional.
3. Cerrar los brazos y la política de redundancias, canaritos y promoción entre semillas antes de ejecutar modelos.
4. Medir presupuesto con autorización separada para cualquier benchmark que entrene. Las dimensiones por sí solas no dan una estimación fiable de horas.
5. Octubre se utilizará para evaluación final según la consigna de Ale. Este auditor solo carga enero–agosto para cálculos; el hash lee los bytes del archivo completo y un CSV requiere lectura para filtrar. No se usan resultados de octubre.

## Ejecución

Usar un entorno con `requirements-auditoria.txt`. Ejecutar primero `python -m pytest -q -p no:cacheprovider pruebas` desde esta carpeta.

El auditor requiere `--dataset`, `--prior-config` (JSON previo con las veinte semillas), y `--output` (directorio nuevo). Su configuración por defecto es `configuraciones/auditoria.json`; sus rutas internas no dependen del directorio de trabajo. No sobreescribe auditorías anteriores.

No hay autorización de entrenamiento ni publicación automática a GitHub incluida en este paquete.

## Revisión del diccionario incorporada

`configuraciones/revision_diccionario.json` registra las 152 variables originales, definición, unidad, celda de origen y motivo de inclusión/exclusión. Se contrastaron los nombres con la receta B0 guardada de v2; la verificación del esquema también se realizó en la VM, con conversión estricta de `cmobile_app_trx`.

- Candidatas: 73 montos y 56 conteos. No se excluye un conteo por tener solo dos valores observados.
- Fuera de las transformaciones genéricas: 10 indicadores binarios, 3 estados/categorías (incluye `tcuentas`), 2 variables de edad/antigüedad y 8 tiempos relativos de tarjetas. Se conservan como originales; otras hipótesis podrían estudiar sus transiciones.
- Alias explícito: el diccionario llama `mtarjeta_visa_debitos_automaticos` a la columna `mttarjeta_visa_debitos_automaticos` del dataset. No se renombra el dataset ni se pierde su máscara de abril.
- Los montos negativos no implican rotura: el diccionario menciona saldos negativos y devoluciones de consumos. No convertirlos en cero.
- Todos los montos están expresados en pesos según las consideraciones generales, incluso los nombres con dólares. Su variación histórica puede incluir efecto cambiario. No se aplica ninguna conversión adicional.
- Las fechas de tarjetas ya son días relativos, no enteros YYYYMMDD. No convertirlas como fechas absolutas. La descripción de vencimiento/mora usa expresiones de dirección inconsistentes con la fórmula general: cualquier futura transformación debe verificar el signo con datos.
- `ctrx_quarter` ya cubre 90 días y `mrentabilidad_annual` hasta un año. Sus ventanas de fotos se solapan; no se sumarán interpretándolas como flujos mensuales independientes.

La exclusión de estas 23 fuentes es una decisión metodológica de esta versión, no una prohibición del diccionario ni una selección basada en AUC. El baseline resultante debe documentarse como adaptación y no confundirse con B4 de v2. El umbral de cobertura 90 % sigue sujeto a revisar sus efectos antes del entrenamiento.
