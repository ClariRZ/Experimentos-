> **Actualización:** el paquete original ya fue incorporado y verificado. Consultar [resultados y recibo](../../resultados/v8_20261115_021908_c48e9d/README.md). El texto siguiente conserva el estado anterior a recibir los archivos.

# v8: cierre de ejecución reportado

Corrida `v8_20261115_021908_c48e9d`, commit ejecutado `64ac6ed4c21aacf21feaad216c0069d800195518`.

## Evidencia y alcance

La salida de `recuperar_v8.py` compartida por la usuaria registra **144 checkpoints completos**, entrenamiento y evaluación con código de salida 0, y evaluación económica terminada. Esta incorporación transcribe esos campos en [ESTADO_REPORTADO.json](ESTADO_REPORTADO.json). **No es una copia del FINAL original ni una verificación independiente de los archivos**: todavía no se dispone aquí del paquete recuperado ni de su recibo.

| Brazo | Clasificación reportada |
|---|---|
| B0 | Control; no se reportó clasificación |
| R3 | PROMETEDOR_INCONCLUSO |
| T4 | PROMETEDOR_INCONCLUSO |
| RR4 | PROMETEDOR_INCONCLUSO |

La clasificación no certifica superioridad ni permite inferir la ganancia o cuál condición falló. Las ganancias, intervalos y consistencia por semilla se incorporarán desde los JSON originales; no se sustituyen por cifras de v7. Octubre ya había sido observado, como reconoce `exposed_months: true`.

## Pendiente para cerrar la incorporación

Recuperar `public.tar.gz`, `manifest.json` y `RESTORED.json` desde `/home/clarirz/v8_lanzamiento_20261115_021905/recovery/` en Cloud Shell. Verificar hashes del archivo y de cada miembro, contrato e identidad de corrida; luego publicar exclusivamente métricas agregadas, trazabilidad y reporte. Los modelos y predicciones individuales permanecen privados. El respaldo privado requiere su propia comprobación local.

`backup_verified: false` y `vm_shutdown_verified: false` son valores del FINAL durante la inspección, no una consulta actual de la VM. La existencia de un manifiesto no prueba que la transferencia haya terminado. Esta actualización no encendió la VM ni ejecutó entrenamientos.
