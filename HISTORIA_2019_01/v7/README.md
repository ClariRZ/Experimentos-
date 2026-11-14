# Historia 2019 v7

[Prompt maestro completo](prompts/PROMPT_MAESTRO_HISTORIA_2019_v7.md): diez brazos, entrenamiento abril–junio y ganancia a igual presupuesto de contactos.

## Estado

**No se ha entrenado v7 con datos reales.** El ejecutor pasó nueve pruebas y una ejecución sintética de los diez brazos (150 ajustes, hasta tres árboles por ajuste), con reproducción exacta de las 50 predicciones de agosto. Esto valida el circuito, no la auditoría real ni la calidad predictiva.

La autorización de Clara es ejecutar y apagar la VM al terminar. Primero debe completarse la auditoría real y congelarse el saneamiento. El contrato propuesto no habilita el ejecutor hasta incorporar el hash del informe real y una revisión resuelta.

## Auditoría remota

`scripts/control_auditoria.py` se ejecuta desde Cloud Shell. Requiere VM apagada, verifica límite GCE STOP de 45 minutos, programa apagado del sistema, ejecuta solamente estadísticas sin etiquetas de octubre, recupera agregados y detiene la VM. No entrena ni borra discos.

## Ejecutor

`scripts/ejecutar_v7.py` reconstruye matrices, optimiza diez brazos, entrena cinco semillas por brazo, congela el presupuesto común desde B0 en agosto y evalúa octubre después de regenerar exactamente agosto. Incluye comparaciones pareadas y bootstrap de contribuciones fijas.

`scripts/worker_vm.py` supervisa el proceso con guardas de tiempo, memoria y disco, genera archivos de recuperación y solicita apagado tras éxito o error. Antes de lanzarlo debe verificarse además el límite GCE de seis horas. **Ese límite aún no se ha configurado en la VM.**

Presupuesto inicial: 100 trials y 50 entrenamientos por semilla. Reproducción independiente completa: presupuesto separado, no ejecutada.

Datos y modelos individuales se mantienen privados. Los manifiestos documentales y de código no certifican una corrida real.
