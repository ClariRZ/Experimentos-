# v8 — Resultados originales incorporados y verificados

Corrida `v8_20261115_021908_c48e9d`, commit ejecutado `64ac6ed4c21aacf21feaad216c0069d800195518`. **144 ajustes terminados; evaluación económica completa.**

Cuatro brazos, búsqueda propia de hiperparámetros y diez semillas finales por brazo. La cantidad de contactos es común, fijada con B0 en agosto: 3.665 / 131.887. Septiembre usa 3.710 contactos; octubre, 3.772. Las cifras de la tabla son ganancias del ensemble, no promedios de ganancias por semilla.

## Resultados económicos

Importes en millones de unidades monetarias de la regla del concurso.

| Brazo | Ganancia septiembre | Diferencia vs B0 | Ganancia octubre | Diferencia vs B0 | Octubre: semillas favorables | IC ajustado de la diferencia de octubre |
|---|---:|---:|---:|---:|---:|---|
| B0 | 248.875 | +0.000 | 279.070 | +0.000 | — | — |
| R3 | 244.475 | -4.400 | 281.270 | +2.200 | 9/10 | -10.560 a +15.052 |
| T4 | 252.175 | +3.300 | 290.070 | +11.000 | 10/10 | -0.376 a +23.183 |
| RR4 | 248.875 | +0.000 | 281.270 | +2.200 | 4/10 | -7.590 a +12.348 |

## Lectura del resultado

**T4 presenta la señal más consistente en esta corrida:** +3,30 M en septiembre y +11 M (+3,94%) en octubre; gana en 9/10 y 10/10 semillas, respectivamente. Su intervalo de octubre sin ajuste excluye cero, pero el ajustado por tres comparaciones va de −0,376 M a +23,183 M: no satisface el criterio preestablecido de promoción.

R3 gana +2,20 M en octubre pero pierde −4,40 M en septiembre. RR4 gana +2,20 M como ensemble en octubre, empata septiembre y su diferencia media por semilla de octubre es −1,10 M. Ninguno demuestra superioridad según la regla congelada. Los tres conservan `PROMETEDOR_INCONCLUSO`; no se cambia la regla después de observarlos. Octubre ya había sido observado: estos resultados no constituyen una prueba nueva independiente.

## Qué se verificó

- Hash y tamaño del archivo público y de todos sus miembros contra el manifiesto original.
- Contrato exacto e identidad del código contra el commit ejecutado.
- Ganancias desde aciertos y contactos, diferencias contra B0, medias y victorias por semilla, y cortes derivados de la política congelada.
- Coherencia del recibo `RESTORED.json` con los hashes de ambos archivos. El recibo acredita la recuperación verificada en Cloud Shell; **el archivo privado no está incluido en este ZIP y no se volvió a verificar localmente**.
- El control de recuperación registra `recovered: true` y `vm_status: TERMINATED`. No se consultó ni encendió la VM para esta incorporación.

El informe original de reproducción de agosto registra 40 predicciones regeneradas con error máximo cero. Aquí se verificó ese informe, no se recalcularon las predicciones ni se reentrenó. La integridad documental no equivale a reproducción independiente del experimento.

## Archivos

- `originales/`: todos los archivos del paquete público, sin modificar.
- `respaldo/`: paquete público original, manifiesto, control y recibo de recuperación.
- `VERIFICACION_LOCAL.json`: alcance de las comprobaciones de esta incorporación.

Los indicadores `backup_verified: false` y `vm_shutdown_verified: false` del FINAL original describen el momento anterior a la recuperación. Se preservan intactos y se complementan con el recibo y el control posteriores. No se publicaron modelos, datasets ni predicciones individuales.
