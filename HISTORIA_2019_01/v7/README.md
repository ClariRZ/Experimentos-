# Historia 2019 v7

## Estado vigente — 14 de noviembre de 2026

**Entrenamiento real de 150 ajustes completado; evaluación de octubre completada sin reentrenar.** Esta revisión sustituye el bloqueo de `0079bf5` tras la decisión expresa de Clara: tratar octubre como en v4/v6, documentar las anomalías y seguir adelante.

- Se mantienen las nueve máscaras históricas de abril–mayo. Su continuidad es una decisión del experimento, no una confirmación oficial nueva.
- **No se aplican máscaras en julio ni octubre.** Se conservan ceros y faltantes originales. Las 14 anomalías de octubre quedan documentadas sin tratamiento.
- No se modifica el dataset original. No se decide saneamiento por AUC o ganancias.
- Diez brazos, entrenamiento abril–junio, selección por AUC de agosto, cinco semillas diferentes de la búsqueda, presupuesto común de contactos, evaluación congelada en octubre.
- Comparaciones pareadas por semilla, dispersión y peor resultado; bootstrap condicional por cliente; tres contrastes principales con ajuste Bonferroni. Son resultados exploratorios, no una garantía temporal ni de ganancia futura.

[Prompt](prompts/PROMPT_MAESTRO_HISTORIA_2019_v7.md) y [contrato ejecutable](configuraciones/contrato_v7.json). El prompt incluye la resolución posterior del saneamiento. Los documentos históricos de auditoría se conservan; su estado queda actualizado por [CIERRE_REVISION.json](auditoria/CIERRE_REVISION.json).

## Resultados reales publicados

Corrida original `v7_20261114_120354`: desarrollo congelado y luego interrupción por `DISK_CAP`. Continuación `octubre_20261114_182415`: `COMPLETE_EXPLORATORY`, supervisor con código de salida 0, cero ajustes nuevos y 50 predicciones de agosto reproducidas exactamente. Se preservan ambos estados originales en carpetas separadas; el fallo original no se presenta como una ejecución completa.

- [Agosto: búsqueda, hiperparámetros, resultados por semilla y auditorías](resultados/agosto/).
- [Octubre: resultados por semilla, contrastes e intervalos](resultados/octubre/).
- [Procedencia y hashes de los archivos descargados](resultados/PROCEDENCIA.json).
- [Resumen numérico verificado](resultados/RESUMEN_VERIFICADO.json).
- [Continuación sin entrenamiento](../../herramientas/continuar_octubre_v7.py) y [evaluador](../../herramientas/evaluar_octubre_v7.py).

Ganancias en millones; ensemble de cinco semillas. Presupuesto común: 3.481 contactos en agosto y 3.583 en octubre. La mejora se calcula frente a B0 del mismo mes. Las victorias por semilla son una medida distinta de la ganancia del ensemble.

| Brazo | Ganancia octubre | Diferencia octubre vs B0 | Semillas favorables octubre | Diferencia agosto vs B0 |
|---|---:|---:|---:|---:|
| B0 | 272.1675 | +0.00 | 0/5 | +0.00 |
| RK | 275.4675 | +3.30 | 4/5 | +0.00 |
| P3 | 282.0675 | +9.90 | 5/5 | -2.20 |
| MIN3 | 274.3675 | +2.20 | 2/5 | -6.60 |
| RAN3 | 272.1675 | +0.00 | 4/5 | -6.60 |
| R3 | 279.8675 | +7.70 | 4/5 | +3.30 |
| R4 | 282.0675 | +9.90 | 5/5 | -3.30 |
| T4 | 283.1675 | +11.00 | 5/5 | -1.10 |
| H_T | 275.4675 | +3.30 | 4/5 | -1.10 |
| H_S | 276.5675 | +4.40 | 5/5 | +6.60 |

T4 obtuvo la mayor ganancia en octubre (+11 M, aproximadamente +4,04%), pero había perdido 1,1 M en agosto. R3 y H_S mejoraron frente a B0 en ambos meses. Los tres contrastes principales (H_T vs R4, H_T vs T4, H_S vs R4) no excluyen cero con el ajuste previsto. T4 vs B0 tiene un intervalo nominal del 95% positivo en octubre, pero es secundario, sin ajuste por multiplicidad. No se declara ganador confirmatorio ni se modifica la selección mirando octubre.

**Alcance del respaldo:** se publican código, configuración, prompts, auditorías agregadas, parámetros, hashes, métricas y registros. No se publican dataset, modelos ni predicciones individuales. El respaldo privado de octubre sufrió una transferencia interrumpida: su recuperación completa y el estado actual de la VM siguen pendientes de verificación. Esto no es una reproducción independiente desde cero. Los hashes locales de los archivos descargados no sustituyen la comparación con los manifiestos externos de transferencia, no disponibles localmente.

## Verificaciones realizadas

20 pruebas locales aprobadas. Ejecución sintética completa: 150 ajustes pequeños, diez brazos, 50 predicciones de agosto regeneradas exactamente y evaluación de ambos meses. No equivale a una corrida sobre datos reales ni a reproducción independiente.

Se verifican antes de encender: aprobación del contrato, manifiesto y hash del informe real recuperado en Cloud Shell. Antes de entrenar: hash del dataset, entorno compatible, matrices, claves, columnas y cobertura. El informe distingue ausencia del cliente-mes, faltantes originales, saneamiento y valores no finitos; los reportes de fórmulas separan inputs incompletos de faltantes producidos con inputs completos. Las causas de una ventana incompleta pueden superponerse.

El entorno exige Python 3.12 y las cinco versiones centrales ya usadas en v6 y validadas localmente; se registra el inventario completo de distribuciones antes del primer ajuste. No instala ni actualiza paquetes automáticamente. Capturar el entorno no prueba por sí solo reproducción idéntica en otra máquina.

## Lanzamiento y apagado

Desde un checkout fijado de esta revisión en Cloud Shell:

```bash
python3 HISTORIA_2019_01/v7/scripts/control_entrenamiento.py \
  --output "$HOME/v7_lanzamiento_$(date +%Y%m%d_%H%M%S)"
```

El controlador exige VM apagada. Configura y verifica STOP de GCE a seis horas, programa apagado del sistema y lanza un supervisor independiente. El trabajo tiene un plazo de 5 h 50 min desde el arranque, dejando margen de respaldo. La duración no garantiza completar los 150 ajustes. El controlador no modifica una VM ya encendida.

El supervisor solicita apagado al terminar o fallar, también ante fallos de inicialización si obtuvo el bloqueo de ejecución. Un conflicto de bloqueo no autoriza apagar otro proceso. Ante fallos de SSH, permisos o cierre de Cloud Shell, el límite GCE sigue siendo el respaldo, no una garantía de apagado inmediato.

Mantener Cloud Shell abierto permite recuperar `aggregates.tar.gz` y `private_recovery.tar.gz`, verificar sus hashes y detener la VM. Una interrupción o el vencimiento del plazo puede impedir el respaldo externo; quedan archivos en disco persistente y hay que verificar su recuperación antes de afirmar que están respaldados. No se reinicia ni se reentrena automáticamente.

**No subir el archivo privado a GitHub:** contiene modelos y predicciones por cliente. El controlador no publica resultados automáticamente. Dataset original privado; no se realiza una copia adicional en esta etapa. Una reproducción independiente completa requiere ese dataset exacto, entorno y presupuesto separado.
