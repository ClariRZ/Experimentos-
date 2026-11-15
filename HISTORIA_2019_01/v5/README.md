# Historia 2019 v5 — preparación de la etapa 1

Estado: auditoría real aprobada; lanzamiento de entrenamiento autorizado el 13/11/2026. El prompt del usuario está en [prompts/PROMPT_MAESTRO_HISTORIA_2019_v5.md](prompts/PROMPT_MAESTRO_HISTORIA_2019_v5.md).

## Alcance implementado

Siete brazos: B0, L (sin deltas), P (promedio), MIN, MAX, RANGO y F1 completo. Entrenamiento marzo–junio, validación agosto, sin cargar octubre en desarrollo. La construcción de B0/F1 se contrasta con v4 mediante datos sintéticos. L es un subconjunto exacto de B0: no restaura alias eliminados por la depuración del control.

Diez ensayos Optuna propios por brazo (semilla de modelo 101); cinco reajustes con semillas 211, 307, 401, 503 y 601. Total: 105 ajustes nuevos si no hay reutilización verificada. Se preservan el espacio, 1.500 árboles máximos y early stopping de 100 rondas. La promoción se basa en ganancia del ensemble y estabilidad individual de agosto; el AUC continúa como objetivo de Optuna.

## Plan operativo propuesto

- Una corrida a la vez, cuatro hilos.
- Límite propuesto: seis horas de VM, incluyendo preparación; no es una duración garantizada ni un precio monetario.
- Verificar primero hash del dataset, entorno, memoria, disco y manifiestos de columnas reales. La auditoría real se completó en la VM del propietario y se guardó en `auditoria/real_20261113_01`.
- Mínimo 10 GiB libres; guardia de memoria 48 GiB en el trabajador. Esta guardia es un chequeo periódico, no una cuota del sistema operativo.
- Antes de lanzar, adaptar/verificar supervisor externo y apagado de VM ante éxito, error o timeout. El runner por sí solo NO apaga la VM ni garantiza interrumpir una operación nativa bloqueada.
- No entrenar hasta habilitar explícitamente el contrato y verificar el supervisor. `training_authorized=false` bloquea la ejecución antes de crear resultados.
- Si el límite se alcanza, conservar resultados parciales y no declarar terminada la comparación.

## Verificación

Desde esta carpeta, con el entorno de `requirements-validado.txt`:

```bash
python -m pytest pruebas -q
```

Trece pruebas aprobadas durante la preparación (incluyen el supervisor): fórmulas/calendario/nulos/ganancia, selección solo en entrenamiento, filas alineadas, familias separadas, paridad sintética B0/F1 con v4 y bloqueo previo a autorización. No constituyen reproducción con el dataset completo ni un entrenamiento real.

## Pendientes explícitos

Completar los 105 ajustes dentro del límite y analizar sus resultados. Evaluador de octubre adaptado a siete brazos, rama larga, tendencias, cambios relativos alternativos, combinaciones, canaritos y confirmaciones no forman parte de esta implementación. Los resultados de octubre ya conocidos hacen exploratoria la continuación.

Código adaptado de `experimento_2026-11-13/scripts/entrenar_desde_cero.py`. Motor de fórmulas y auditoría copiados sin cambios. No se modifican v4 ni resultados anteriores.

## Auditoría real y lanzamiento autorizado

La auditoría terminó sin errores: 507.328 filas de entrenamiento, 131.887 de agosto; siete matrices construidas en 114,74 segundos; pico de RAM 18,13 GiB. Se recuperaron agregados en Cloud Shell y el controlador confirmó la VM apagada (`TERMINATED`). Cero modelos entrenados durante esa auditoría.

| Brazo | Variables |
|---|---:|
| B0 | 652 |
| L, sin deltas | 400 |
| P, promedio | 778 |
| MIN | 778 |
| MAX | 778 |
| RANGO | 778 |
| F1, cuatro resúmenes | 1.156 |

Las claves de las filas y las listas ordenadas de columnas B0/F1 coinciden con v4. La igualdad de valores con v4 se probó en sintético; no se afirma una comparación completa entre matrices reales v4/v5.

Contrato de ejecución: `configuraciones/etapa1_autorizada_20261113.json`. Conserva 10 ensayos Optuna por brazo y cinco reajustes, máximo 105 ajustes. Antes del primer ajuste se comprueban los hashes de las siete matrices reconstruidas contra la auditoría. Se guardan versiones del entorno y hashes de modelos y predicciones privadas.

Controlador: `scripts/control_entrenamiento_cloudshell.py`. Límite GCE de 21.600 segundos (seis horas); supervisor del trabajador con 21.000 segundos desde antes del encendido, dejando margen para recuperación y apagado. Apaga ante éxito, error o límite. Una ejecución incompleta debe reportarse como parcial. No se evalúa octubre. Los datos, matrices, modelos y predicciones individuales permanecen privados en la VM.

El contrato original de propuesta sigue con entrenamiento bloqueado como registro de la etapa previa. La auditoría aprobada no implica que el entrenamiento haya terminado; consultar los registros de la corrida.
