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
| Cobertura real por mes B0/R3/T4/RR4 | PARCIAL | Disponibilidad por columna B0/R3/T4 y atribución RR4 ejecutadas en seis meses; falta atribución completa de causas de B0/R3/T4 |
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
