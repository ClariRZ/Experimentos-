> **Estado actualizado al 13/11/2026:** existen v1, v2, v3 y v4. El documento que sigue describe la **primera corrida**, no el estado global del proyecto. La etapa corta v4 terminó con 75 ajustes; octubre sigue pendiente.
>
> [Comparación de versiones y respaldo Git](v4/auditoria/comparacion_versiones_20261113/COMPARACION_Y_GIT.md) · [Resultados v4](v4/auditoria/completa_20261111_03/analisis/INFORME.md)
>
> GitHub estaba 13 commits detrás antes de esta auditoría; este guardado es local.

# HISTORIA_2019_01 — Bitácora metodológica y resultados

**Competencia:** Data Mining en Economía y Finanzas — Segunda Competencia  
**Tema:** Feature engineering histórico  
**Estado final:** `MODELOS_CONGELADOS_TEST_EXTERNO_PENDIENTE`  
**Fin de corrida:** 2026-11-05 05:52:52 (UTC−03:00)  
**VM:** `clari-c1-fundados`  
**Ruta de origen:** `/home/clarirz/HISTORIA_2019_01/`  

> **Alcance de la evidencia.** Este registro fue reconstruido el 2026-11-07 a partir de `RESUMEN_HISTORIA_2019.txt`, exportado desde la VM. Contiene el texto de `LEEME.txt`, `CAMBIOS.txt`, `VALIDACION.txt`, y métricas de `result.json` y `FINAL.json`. No equivale a haber auditado de nuevo el código o los datos originales. No se entrenó ningún modelo al redactarlo.

## 1. Pregunta e hipótesis

¿Las representaciones adicionales de la historia de cada cliente mejoran la discriminación de BAJA+2 en agosto de 2019, frente a un baseline con variables originales saneadas, lag1/lag2 y delta1/delta2?

La idea central fue evaluar **cambios relativos al comportamiento habitual del propio cliente**, no solo valores absolutos. Se plantearon hipótesis explícitas por familia de variables y comparaciones pareadas contra B0. Una familia que no superara la regla no debía promoverse por conveniencia.

## 2. Contrato temporal y objetivo

| Uso | Meses | Regla |
|---|---|---|
| Historia auxiliar | 201901–201902 | Solo para construir variables históricas |
| Entrenamiento | 201903–201906 | Sin undersampling; positivo: BAJA+1 o BAJA+2; negativo: CONTINUA |
| Validación | 201908 | AUC con BAJA+2 positiva y BAJA+1/CONTINUA negativas; selección y BO |
| Evaluación externa | 201910 | **Solo predicciones en este runner**; ganancia externa pendiente |

Julio y septiembre pueden aportar valores históricos anteriores a la fecha de predicción, sin convertirse en filas de entrenamiento. Noviembre y diciembre no participan en etiquetas, selección ni transformaciones. La etiqueta de octubre no interviene en la selección. El score se entrena con ambas bajas positivas y **no** debe interpretarse como probabilidad calibrada de BAJA+2.

## 3. Diseño de las iteraciones

| ID | Nombre | Transformación o etapa |
|---|---|---|
| 000 | B0_baseline | RAW saneado + lag/delta de órdenes 1 y 2 |
| 001 | resumen_3m | Media, mínimo, máximo y desviación de tres observaciones (ddof=0) |
| 002 | inactividad | Rachas de ceros observados; cero no equivale a faltante |
| 003 | ratios_personales | Valor actual / media propia de tres fotos; ventana completa no negativa; negativos a NA |
| 004 | rangos_monetarios | Paquete de rangos intrames y derivados históricos; no aísla cada componente |
| 005 | combinadas | Unión solo si se aceptan al menos dos familias; se evalúa de nuevo |
| 006 | canaritos | Poda heurística de variables nuevas del candidato aceptado; reentrenamiento posterior |
| 007 | BO_final | Reoptimización separada del candidato elegido; comparación contra padre y B0 |

En la salida final recuperada aparecen **000, 001, 002, 003, 004 y 007**. No aparecen resultados individuales de 005 y 006; el protocolo prevé omitir la unión si solo hay una familia aceptada. No atribuir resultados a etapas ausentes.

## 4. Regla de decisión fijada

- Veinte semillas por candidato en la corrida completa, con comparaciones pareadas.
- Para promover: mejora media de AUC **≥ 0,0001**, al menos **12/20** semillas favorables y AUC del ensamble no inferior a la referencia.
- Las iteraciones de poda y BO final deben superar **tanto B0 como su padre**.
- Se distinguen AUC medio por semilla y AUC del ensamble: no son la misma métrica.
- Para elegir entre candidatos elegibles, prevalece el AUC del ensamble; en empate, menos variables y luego iteración anterior.
- La ganancia de agosto y su meseta son **diagnósticas**; no son el evaluador oficial ni el criterio de BO.
- La regla es **operativa, no una prueba estadística de significación**. Veinte semillas sobre los mismos clientes no equivalen a veinte muestras independientes. Existe riesgo de sobreajustar agosto mediante exploración reiterada.

## 5. Bitácora operativa

**2026-11-04 — Preparación y validación técnica del paquete.** Se documentaron modos separados `preflight` (auditoría sin entrenamiento), `pilot` (solo B0, una semilla, hasta dos trials y 80 rondas) y `full`. El paquete registró 88 pruebas técnicas aprobadas sobre datos sintéticos: 25 de variables/calendario/lectura, 35 de métricas/selección, 17 de configuración/presupuesto y 11 de integración. Esta validación **no** certificaba eficacia bancaria ni ejecución real en la VM.

**Revisión de datos y piloto.** En la VM existen `revision_historia_01/`, `revision_historia_02/` y `piloto_historia_01/`, además de `datos/`. El resumen disponible no aporta el contenido íntegro de sus auditorías; por eso no se declara aquí qué defectos concretos fueron saneados. El protocolo exige que `sanitization_reviewed` sea una confirmación consciente, no una corrección automática.

**2026-11-05 — Corrida completa.** Se ejecutó `full` con 20 semillas por iteración y se guardaron `config_frozen.json`, `audit.json`, `resultados.json`, resultados por iteración, importancias, predicciones de agosto y octubre y `FINAL.json`. La carpeta de resultados ocupa ~533 MB; el directorio general ~1,9 GB, incluyendo datos y entorno virtual. La bitácora de consola se llama `full_historia_01.log`.

**2026-11-05 02:08–02:34 — Iteración 003.** `ratios_personales` completada y mantenida.

**2026-11-05 02:34–03:02 — Iteración 004.** `rangos_monetarios` completada y descartada.

**2026-11-05 05:01–05:52 — Iteración 007.** BO final completada, pero descartada: supera B0 bajo la regla, **no** supera a su padre 003.

**2026-11-05 05:52:52 — Congelamiento.** `FINAL.json` registra selección por AUC de agosto exclusivamente, baseline 000 y seleccionado 003; `test_gain=null`, `test_auc=null`.

## 6. Resultados de validación (agosto 2019)

| ID | Variables | AUC medio (20 semillas) | AUC ensamble | Δ AUC ensamble vs B0 | Decisión |
|---|---:|---:|---:|---:|---|
| 000 | 760 | 0,913171 | 0,914136 | — | Baseline |
| 001 | 784 | 0,912891 | 0,913923 | −0,000214 | Descartado |
| 002 | 763 | 0,912851 | 0,913935 | −0,000201 | Descartado |
| **003** | **764** | **0,914121** | **0,915105** | **+0,000969** | **Mantenido / seleccionado** |
| 004 | 796 | 0,912289 | 0,913303 | −0,000833 | Descartado |
| 007 | 764 | 0,913993 | 0,914407 | +0,000271 | Descartado vs 003 |

**Comparaciones pareadas de AUC medio respecto de B0:**

| Candidato | Δ media AUC | Victorias / 20 | ¿Supera regla vs B0? |
|---|---:|---:|---|
| 001 | −0,000281 | 7 | No |
| 002 | −0,000320 | 5 | No |
| **003** | **+0,000950** | **16** | **Sí** |
| 004 | −0,000883 | 5 | No |
| 007 | +0,000822 | 15 | Sí, pero no supera 003 |

La comparación **007 vs 003** arroja Δ AUC medio = −0,000128, 7 victorias y 13 derrotas, y Δ AUC del ensamble = −0,000699. Por eso no reemplaza a 003.

### Ganancia diagnóstica de agosto (no test)

| Modelo | N sugerido por meseta | Ganancia observada a N |
|---|---:|---:|
| B0 (000) | 3.565 | 205.562.500 |
| 003 | 4.482 | 210.045.000 |
| 007 | 3.680 | 207.900.000 |

La diferencia diagnóstica 003−B0 es **+4.482.500 (+2,18%)**, pero se calcula en **N diferentes** y en el período utilizado para seleccionar modelos. No demuestra mejora económica causal ni ganancia externa. La meseta usa media móvil centrada de 1.001 posiciones sobre ganancia acumulada, con ventana completa; no sustituye al evaluador oficial.

## 7. Selección congelada y test externo

`FINAL.json`:
- `status`: `MODELOS_CONGELADOS_TEST_EXTERNO_PENDIENTE`
- `chosen_on`: `AUC 201908, exclusivamente`
- Baseline: `iteraciones/000/pred_201910.csv`; SHA-256 `a4d12d3d0393b9ae75b17e55e5dba3100d54d28f804f4a40fa1f7634e9e6839d`
- Seleccionado: `iteraciones/003/pred_201910.csv`; SHA-256 `f0f212bd562013f8236672b802bc7c0bba146312739f64866f17ccda757869ca`
- `test_gain`: `null`; `test_auc`: `null`.

**Pendiente:** aplicar externamente la regla de ganancia oficial en 201910, sin modificar el modelo ni elegir cortes mirando ese test. El protocolo indica confirmar con el tutor las adaptaciones, la definición del target de validación y el contrato de ganancia.

## 8. Archivos originales en la VM

```text
/home/clarirz/HISTORIA_2019_01/
├── historia_2019_v1/
│   ├── LEEME.txt
│   ├── CAMBIOS.txt
│   ├── VALIDACION.txt
│   ├── config_historia.json
│   ├── config_historia_saneado_2019.json
│   ├── requirements.txt
│   └── tests/
├── revision_historia_01/
├── revision_historia_02/
├── piloto_historia_01/
├── resultados_historia_01/
│   ├── FINAL.json
│   ├── audit.json
│   ├── config_frozen.json
│   ├── families.json
│   ├── feature_manifest.json
│   ├── resultados.json
│   ├── bo_baseline/
│   ├── bo_final/
│   └── iteraciones/{000,001,002,003,004,007}/
├── full_historia_01.log
└── datos/
```

El registro de la VM es la **fuente de verdad** de las corridas. El texto `VALIDACION.txt` es anterior al entrenamiento real y describe solo las pruebas sintéticas; no debe leerse como negación de la corrida posterior.

## 9. Reproducibilidad, seguridad y tareas pendientes

1. Recuperar el código exacto, `requirements.txt`, `config_frozen.json`, `run_manifest.json`, `audit.json`, `feature_manifest.json` y `resultados.tsv` desde la VM, verificar que no contengan información sensible y versionarlos.
2. Conservar los CSV de predicción individual y el dataset bancario **fuera de GitHub**; referenciarlos solo mediante ruta, hash y esquema.
3. Revisar el saneamiento real a partir de `revision_historia_01/02` y registrar columnas/meses defectuosos sin inferirlos.
4. Evaluar la ganancia externa en octubre con contrato acordado; documentar resultado incluso si es nulo o negativo.
5. No reoptimizar ni volver a seleccionar usando octubre.

## 10. Procedencia de este documento

Fuente: resumen de 35,5 KB `RESUMEN_HISTORIA_2019.txt` generado en la VM el 2026-11-07 a partir de los tres documentos locales, los `result.json` de las iteraciones y `FINAL.json`. Los valores de las tablas se transcribieron de ese resumen; las diferencias porcentuales se calcularon a partir de las ganancias informadas.

**No confundir** con el experimento distinto de `Experimentos-cloud/segunda_competencia_experimento_variables_historicas`, que compara rezagos discretos con `tend6` sobre otro calendario.
