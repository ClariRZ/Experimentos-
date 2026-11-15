> **Cierre actualizado:** 144 ajustes y evaluación completados. [Resultados originales y verificación](../resultados/v8_20261115_021908_c48e9d/README.md): 33 archivos públicos contrastados, recibo de recuperación y apagado registrado. R3/T4/RR4 permanecen prometedores inconclusos. Las secciones siguientes conservan el historial de preparación.

# v8 — Preflight local del cierre consolidado

Estado: **PARCIAL; NO APROBADO PARA ENTRENAR**. No se entrenaron modelos ni se encendió la VM. El prompt vigente está en `../prompts/cierre_consolidado/PROMPT_MAESTRO_V8.md`.

## Resultados ejecutados

| Requisito | Estado | Evidencia |
|---|---|---|
| Esquemas originales B0/R3/T4 | PASÓ identidad de referencia | Contrato con listas completas de 652/1.024/776 columnas; identidad del código original verificada |
| Modelos v7 y predicciones de agosto por semilla | PASÓ | 50 modelos y sus predicciones contrastados con hashes de la política congelada; modelos cargados con LightGBM 4.7.0 |
| Archivos privados de octubre | PASÓ | 61 miembros verificados contra manifiesto |
| Importancias de las 14 fuentes señaladas | PASÓ extracción | `preflight/octubre/importancias.json`, gain/split y denominadores por modelo |
| Procedencia de las 14 fuentes | PASÓ identificación | `preflight/octubre/fuentes_octubre.json`; reglas de Ezequiel, no confirmación de la cátedra |
| Implementación RR4 y controles sintéticos v7 | PASÓ | 16 pruebas unitarias locales |
| Paridad con generador C3 real | PASÓ | 256 combinaciones, `preflight/c3_paridad.json`; se cargaron el generador original y sus funciones puras sin cambiar fórmulas |
| Dataset exacto | PASÓ | Recuperado del respaldo privado v1–v6; SHA256 completo coincide con v7. Copia local junto al prompt, excluida de Git |
| Inferencia intacta y perturbaciones | PASÓ ejecución | 50 predicciones por semilla y 10 ensembles intactos exactos; tres escenarios completos en `preflight/octubre_real/` |
| Cobertura real por mes B0/R3/T4/RR4 | PASÓ | Atribución de causas en seis meses: 14.712 registros B0/R3/T4 y 2.322 RR4; cero causas inesperadas |
| Esquema RR4 depurado en train | PASÓ | 956 columnas: 652 B0 + 304 nuevas; 83 excluidas; lista y aliases en `preflight/matrices_reales/rr4_schema.json` |
| Recursos de entrenamiento | PENDIENTE | Disco/RAM del host registrados; no se equiparan a pico de entrenamiento |
| Conteos 21/23 y 15/29 | PENDIENTE | No homologados; no se usan como evidencia confirmada |
| Porcentajes C3 0,8%/1,8% | PENDIENTE | No localizados en fuente de importancia suficiente; no se certifican |

## Dataset requerido

SHA256 obligatorio: `459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872`.

Se buscaron nombres de datasets en el espacio local de la usuaria y se verificaron los candidatos en la carpeta de base de competencia 2. Los dos CSV comprimidos crudos coinciden entre sí con hash `6c3ec2fb4d94521c0c3cc72988c4019c8b65a157d81e0f3b6d7e1b87e0c306f4`; el parquet tiene hash `84dffddadf9216be9460793ea3c28d87bff82b3c194a67a2e49fc7b4a7475a22`. Ninguno es el archivo congelado. Una diferencia de hash no demuestra que los valores sean diferentes, pero no autoriza sustituir el insumo ni inventar su clase. Recuperar el archivo exacto desde un respaldo disponible; si sólo está en VM, su recuperación requiere autorización para encenderla conforme al prompt.

## Hallazgo de importancia

Sumando gain de las cinco semillas y dividiendo por gain total de sus modelos, las 14 columnas contemporáneas más sus descendientes representan 2,649% en B0, 5,580% en R3 y 8,255% en T4. No demuestra dependencia económica ni causalidad. El denominador incluye todos los splits de entrenamiento, no sólo clientes de octubre. No se modifica saneamiento ni diseño por este dato.

## Reproducir los controles locales

Desde la raíz de este repositorio, con Python 3.12 y numpy 2.3.5, polars 2.1.0, lightgbm 4.7.0, optuna 5.0.0 y scikit-learn 1.8.0:

```bash
python -m unittest discover -s HISTORIA_2019_01/v8/cierre_consolidado/tests -v
python HISTORIA_2019_01/v8/cierre_consolidado/scripts/verificar_c3.py --c3-directory /ruta/al/generador/C3 --output /ruta/nueva/c3_paridad.json
python HISTORIA_2019_01/v8/cierre_consolidado/scripts/diagnostico_octubre.py --repo . --august-archive /ruta/privada/v7_modelos_y_predicciones_agosto.tar.gz --october-archive /ruta/privada/v7_octubre_predicciones.tar.gz --output /ruta/nueva/diagnostico
```

El último comando sin dataset ejecuta integridad e importancias, NO inferencia. Con `--dataset /ruta/al/archivo_exacto` exige su hash antes de puntuar. No entrenará. La ruta de salida debe ser nueva: no sobrescribir diagnósticos anteriores.

`auditar_rr4.py` acepta `--repo`, `--dataset` y `--output` para cobertura real RR4. Su implementación procesa una fuente por vez; no materializa todas las columnas históricas de la auditoría juntas. Necesita validación real una vez recuperado el insumo.

## Medición pendiente y continuación

La extracción de importancias alcanzó unos 167 MiB de RSS; es sólo ese proceso, no generación de matrices ni entrenamiento. Antes de aprobar: medir filas, dtype, RAM pico y disco con cada constructor real, reservar espacio para temporales y recuperación, fijar umbrales cuantitativos y comprobar viabilidad del techo propuesto de seis horas. No hay umbrales aprobados todavía.

El contrato permanece DRAFT y `training_authorized=false`. No está habilitado para ejecución. El pipeline de competencia 2 sigue como línea independiente definida en el prompt, no implementada en este preflight. El dataset exacto ya fue recuperado. Se completaron el diagnóstico real de octubre y la auditoría RR4; no corresponde pedir aprobación de entrenamiento todavía.

## Recuperación local del dataset

Se encontró dentro de `respaldo_v1_v6.tar.gz`, no en el historial Git. Se verificaron sus 740.919.315 bytes contra el SHA256 requerido y se copió a `../prompts/cierre_consolidado/datos_privados/`, excluido de Git. No fue necesario encender la VM. La búsqueda inicial había omitido el contenido de este respaldo; ese faltante queda resuelto.

## Ejecución real con la base recuperada

La población de train auditada contiene 381.596 filas. Se validaron claves únicas/no nulas y clases conocidas en enero–octubre. Se midió disponibilidad por columna para B0/R3/T4 en abril, mayo, junio, agosto, septiembre y octubre. RR4 tiene 2.322 registros de cobertura (129 fuentes × seis meses × tres operaciones), sin categoría inesperada. Esto no sustituye la atribución completa de causas todavía pendiente para B0/R3/T4.

Se preservaron las nueve máscaras y los ceros de julio/octubre. `anomalias_sin_tratamiento.json` documenta las 14 fuentes en enero–octubre. Ninguna de las perturbaciones alimentó entrenamiento.

| Escenario de octubre v7, K=3.583 | B0 | R3 − B0 | T4 − B0 |
|---|---:|---:|---:|
| Intacto | 272.167.500 | +7.700.000 | +11.000.000 |
| Sólo contemporáneas en NA | 272.167.500 | +9.900.000 | +9.900.000 |
| Fuentes de octubre en NA y derivadas recalculadas | 276.567.500 | +1.100.000 | 0 |

Son unidades económicas del concurso y ensembles de v7. Las ventajas son sensibles a estas entradas; esto no demuestra error en los ceros ni causalidad. No cambia brazos, saneamiento ni regla de cierre de v8.

El diagnóstico tardó 209,4 segundos y alcanzó 3,09 GiB RSS. La auditoría de matrices tardó 44,0 segundos y alcanzó 5,84 GiB RSS; la matriz RR4 de entrenamiento float32 equivale a 1.459.223.104 bytes sin contar otras estructuras. No son mediciones de entrenamiento ni garantizan el plazo de 144 ajustes.

Estado al cierre de esta ejecución local: **DRAFT, entrenamiento no iniciado**. Quedan atribución completa de causas B0/R3/T4, comprobaciones históricas no homologadas, límites operativos y validación del ejecutor de entrenamiento. No se encendió la VM. No se presenta esta ejecución parcial como preflight aprobado.

## Ejecutor de v8 — avance de implementación

`ejecutar_v8.py` implementa las 20 búsquedas, confirmación de tres configuraciones con dos semillas y diez semillas finales por brazo. Reproduce el estado del sampler mediante ask/tell determinista al retomar; no vuelve a entrenar checkpoints completos. Un ajuste interrumpido queda bloqueado para revisión, no se repite silenciosamente. La identidad incluye contrato, dataset y código original importado. El contrato aprobado se copia byte a byte. Los modelos y predicciones quedan bajo `private/` en el directorio de ejecución elegido, fuera de los artefactos públicos.

`evaluar_v8.py` sólo puntúa modelos congelados en septiembre/octubre. Calcula presupuesto común exacto, bootstrap pareado con índices compartidos, intervalos por semilla, sensibilidad, blend descriptivo y diagnóstico RR4. No llama a entrenamiento. Termina en EVALUATED_BACKUP_PENDING: el análisis terminado no equivale a respaldo ni apagado verificados.

Pasaron 37 pruebas unitarias sin entrenar LightGBM, incluidas reanudación, corrupción, desempates, repetición del sampler, contribuciones económicas y reglas de cierre. **No es una validación integral del ejecutor.** La ejecución completa, supervisor independiente, respaldo externo reanudable y apagado siguen pendientes. El contrato continúa DRAFT; estas pruebas no autorizan la corrida.

`auditar_causas.py` está ejecutándose localmente para completar la atribución de faltantes B0/R3/T4 en seis meses. Hasta que cierre y se revise su salida, no se da ese requisito por aprobado.

### Cierre de auditoría de causas

La ejecución real de `auditar_causas.py` terminó correctamente: 14.712 registros de columna/mes/brazo para B0/R3/T4, seis meses completos y cero causas inesperadas. Las categorías exclusivas suman exactamente el denominador en todos los registros. Se guardan también los solapamientos y los faltantes nuevos atribuibles a las nueve máscaras, comparando contra la variante sin máscaras sólo para diagnóstico. Evidencia en `preflight/causas_reales/`. Esta actualización cierra el pendiente descrito arriba; los controles operativos e integración del ejecutor siguen abiertos.

## Validación operativa local — 45 pruebas aprobadas

El flujo real de búsqueda, confirmación y congelamiento recorrió los 144 ajustes con datos sintéticos y un sustituto de LightGBM. Al repetirlo, reutilizó los 144 checkpoints sin invocar nuevos ajustes. Esto comprueba la coordinación; no mide calidad, consumo ni duración de LightGBM real.

Se incorporaron supervisor independiente con límites de tiempo/disco/RAM, controlador de despliegue que exige VM detenida y contrato aprobado, y respaldo por partes con hashes de archivos y contenidos. Una transferencia interrumpida se retomó reutilizando partes verificadas. Se probaron corrupción, rutas inválidas y separación entre archivos privados y públicos. No se encendió ninguna VM.

Las nuevas protecciones todavía requieren validación en GCE. La integración completa de evaluación, el presupuesto operativo y el cierre del contrato siguen pendientes. El contrato permanece DRAFT y no se ejecutaron entrenamientos reales. La publicación del código no implica aprobación del lanzamiento.

## Evaluación integrada y recursos

La prueba sintética ahora cubre congelamiento, reproducción exacta de las 40 predicciones finales de agosto, evaluación de septiembre/octubre, repetición con archivos idénticos y restauración del respaldo. Invocar entrenamiento durante evaluación hace fallar la prueba. Alterar un modelo también la bloquea. Las 45 pruebas pasan; no se entrenó LightGBM real.

Consulta de consola del 14/11: VM detenida, e2-highmem-8, 8 vCPU, 64 GB de memoria, disco de 100 GB y límite vigente de una hora con acción Stop. El controlador configura y verifica seis horas antes de lanzar; ese cambio todavía no se aplicó. El espacio libre y las versiones instaladas no están verificados actualmente.

Los tiempos guardados de B0/R3/T4 en v7 dan una aproximación de 2,62 horas sólo para ajustes, usando el brazo conocido más lento como sustituto provisional de RR4. No incluye evaluación, preparación ni respaldo; RR4 no está medido y esto no garantiza el plazo. Detalle en `preflight/PLANIFICACION_RECURSOS.json`. Sigue pendiente cerrar presupuesto, comparabilidad histórica y contrato antes de ejecutar.

## Autorización de lanzamiento

La instrucción explícita «entrená ya» autoriza los 144 ajustes del contrato. El estado pasa a APPROVED. No cambia ninguna definición, semilla, calendario ni regla de decisión. Las cifras históricas no homologadas y los porcentajes de importancia de C3 no se utilizarán como evidencia ni como criterio de selección. El consumo de entrenamiento de v8 todavía no está medido: se aplican límites, sin presentarlos como mediciones.

El controlador exige 12 GiB libres al iniciar, conserva al menos 4 GiB durante los procesos y limita RSS a 48 GiB en una máquina con al menos 8 GiB adicionales. Compara Python y dependencias contra el contrato antes de despachar. Un fallo de preparación apaga la VM sin entrenar. El límite GCE de seis horas se configura y verifica antes del arranque. Estas comprobaciones remotas todavía no se han ejecutado.

Lanzar desde un checkout limpio con Python estándar: `python3 HISTORIA_2019_01/v8/cierre_consolidado/scripts/control_v8.py --repo . --config HISTORIA_2019_01/v8/cierre_consolidado/contrato_v8_consolidado.json --output RUTA_NUEVA_PRIVADA`. La terminal debe tener gcloud autenticado. No publicar el directorio privado de salida. Si se interrumpe la conexión, usar `--recover RUTA_NUEVA_PRIVADA`; no lanzar otra corrida.

## Recuperación después del apagado

`recuperar_v8.py --control-dir DIRECTORIO_ORIGINAL` consulta y recupera una corrida existente. Exige VM detenida; establece y verifica un límite de una hora para rescate, la enciende, guarda status/FINAL/supervisor y recupera el respaldo por partes con hashes. La apaga al terminar o ante un error de copia. No invoca entrenamiento ni evaluación, no modifica el contrato ejecutado ni extiende su plazo. Sin manifiesto completo conserva la inspección y se detiene sin borrar resultados. Se agregaron tres pruebas de apagado, rechazo de VM activa y fallo de transferencia.
