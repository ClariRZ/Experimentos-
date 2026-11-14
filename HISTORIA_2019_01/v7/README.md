# Historia 2019 v7

[Prompt maestro completo](prompts/PROMPT_MAESTRO_HISTORIA_2019_v7.md): diez brazos, entrenamiento abril–junio y ganancia a igual presupuesto de contactos.

## Estado

**No se ha entrenado v7 con datos reales.** El ejecutor pasó nueve pruebas y una ejecución sintética de los diez brazos (150 ajustes, hasta tres árboles por ajuste), con reproducción exacta de las 50 predicciones de agosto. Esto valida el circuito, no la auditoría real ni la calidad predictiva.

La autorización de Clara es ejecutar y apagar la VM al terminar. La auditoría real ya terminó; el contrato de lanzamiento incorpora el hash del informe y la revisión del saneamiento. La comprobación del informe completo y de las matrices sigue siendo obligatoria antes del primer ajuste.

## Auditoría remota

`scripts/control_auditoria.py` se ejecuta desde Cloud Shell. Requiere VM apagada, verifica límite GCE STOP de 45 minutos, programa apagado del sistema, ejecuta solamente estadísticas sin etiquetas de octubre, recupera agregados y detiene la VM. No entrena ni borra discos.

## Ejecutor

`scripts/ejecutar_v7.py` reconstruye matrices, optimiza diez brazos, entrena cinco semillas por brazo, congela el presupuesto común desde B0 en agosto y evalúa octubre después de regenerar exactamente agosto. Incluye comparaciones pareadas y bootstrap de contribuciones fijas.

`scripts/worker_vm.py` supervisa el proceso con guardas de tiempo, memoria y disco, genera archivos de recuperación y solicita apagado tras éxito o error. Antes de lanzarlo debe verificarse además el límite GCE de seis horas. **Ese límite se configurará y verificará automáticamente al ejecutar el controlador de entrenamiento.**

Presupuesto inicial: 100 trials y 50 entrenamientos por semilla. Reproducción independiente completa: presupuesto separado, no ejecutada.

Datos y modelos individuales se mantienen privados. Los manifiestos documentales y de código no certifican una corrida real.

## Actualización posterior a la auditoría real

La auditoría real finalizó con retorno 0, dataset identificado y VM `TERMINATED`. [Revisión de saneamiento](auditoria/REVISION_SANEAMIENTO.md) y [contrato de lanzamiento](configuraciones/contrato_v7.json). El contrato propuesto anterior se conserva como antecedente. **Todavía no hay entrenamiento real confirmado de v7.**

El controlador `scripts/control_entrenamiento.py` requiere el informe completo recuperado en Cloud Shell, verifica su hash y los criterios de saneamiento, y comprueba el manifiesto de código antes de encender. Configura y verifica STOP de GCE a seis horas, más apagado del sistema y supervisor independiente. No interfiere con una VM que ya esté encendida. El límite previo de auditoría era 45 minutos; solo cambia al ejecutar este controlador.

Presupuesto: 150 ajustes como máximo. Las doce pruebas locales pasaron; la prueba sintética anterior valida el circuito, no resultados reales. El supervisor limita el trabajo a 5 h 50 min desde el arranque para dejar margen de respaldo antes de las seis horas. No se garantiza completar los 150 ajustes dentro del límite.

En Cloud Shell, ejecutar desde un checkout fijado del commit publicado:

```bash
python3 HISTORIA_2019_01/v7/scripts/control_entrenamiento.py \
  --output "$HOME/v7_lanzamiento_$(date +%Y%m%d_%H%M%S)"
```

Mantener Cloud Shell abierto favorece la recuperación de archivos. Si se desconecta, el supervisor continúa y el apagado sigue protegido por GCE. El controlador recupera `aggregates.tar.gz` y `private_recovery.tar.gz` a la carpeta de salida, comprueba hashes y lectura del archivo, y detiene la VM. La recuperación es un respaldo privado en Cloud Shell, no una reproducción independiente. Si la conexión falla, quedan archivos en el disco persistente de la VM y hay que recuperarlos después; no reiniciar ni relanzar a ciegas.

El archivo privado incluye modelos y predicciones individuales: **no subirlo a GitHub**. Los agregados todavía requieren publicación al terminar; el controlador no hace push ni afirma que estén publicados. El dataset original permanece en su ubicación privada; no se crea otra copia del dataset en esta etapa. Una nueva máquina necesita ese dataset exacto y el entorno registrado para intentar una reproducción completa.
