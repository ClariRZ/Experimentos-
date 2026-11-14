# Historia 2019 v7

## Estado vigente — 14 de noviembre de 2026

**Preparado para lanzamiento con controles previos obligatorios; entrenamiento real todavía no confirmado.** Esta revisión sustituye el bloqueo de `0079bf5` tras la decisión expresa de Clara: tratar octubre como en v4/v6, documentar las anomalías y seguir adelante.

- Se mantienen las nueve máscaras históricas de abril–mayo. Su continuidad es una decisión del experimento, no una confirmación oficial nueva.
- **No se aplican máscaras en julio ni octubre.** Se conservan ceros y faltantes originales. Las 14 anomalías de octubre quedan documentadas sin tratamiento.
- No se modifica el dataset original. No se decide saneamiento por AUC o ganancias.
- Diez brazos, entrenamiento abril–junio, selección por AUC de agosto, cinco semillas diferentes de la búsqueda, presupuesto común de contactos, evaluación congelada en octubre.
- Comparaciones pareadas por semilla, dispersión y peor resultado; bootstrap condicional por cliente; tres contrastes principales con ajuste Bonferroni. Son resultados exploratorios, no una garantía temporal ni de ganancia futura.

[Prompt](prompts/PROMPT_MAESTRO_HISTORIA_2019_v7.md) y [contrato ejecutable](configuraciones/contrato_v7.json). El prompt incluye la resolución posterior del saneamiento. Los documentos históricos de auditoría se conservan; su estado queda actualizado por [CIERRE_REVISION.json](auditoria/CIERRE_REVISION.json).

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
