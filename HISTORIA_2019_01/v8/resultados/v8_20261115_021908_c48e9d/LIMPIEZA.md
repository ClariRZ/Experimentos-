# Limpieza limitada a duplicados de transferencia

Preparada, **todavía no ejecutada en la VM**.

El manifiesto identifica 14 partes de transferencia que suman 414.007.271 bytes (~395 MiB). Duplican exactamente los archivos completos `public.tar.gz` y `private.tar.gz`. No hay que borrar modelos, checkpoints, predicciones, resultados, código ni dataset para liberar esas partes.

`python3 herramientas/limpiar_partes_v8.py --apply` se ejecuta en Cloud Shell. Antes de encender la VM comprueba por hash y tamaño ambos archivos recuperados y el recibo en `~/v8_lanzamiento_20261115_021905/recovery/`. Rechaza una VM activa. Establece y verifica un límite de 20 minutos; arranca, toma los bloqueos del experimento y exige evaluación completa. Verifica el manifiesto congelado y los archivos completos en la VM antes de borrar únicamente las partes coincidentes. Conserva un informe con cada archivo eliminado, bytes candidatos y espacio libre antes/después. Finalmente apaga la VM, también ante fallos de comprobación. Sin `--apply`, sólo verifica y prepara el informe, sin borrar.

La copia privada en Cloud Shell se vuelve a comprobar para esta operación, pero no equivale a tenerla descargada en la computadora personal. El ZIP público entregado no contiene modelos ni predicciones.

Cuatro pruebas sintéticas verifican conservación de originales, idempotencia, rechazo de archivo corrupto, rechazo de enlace simbólico y modo sin borrado. Esta documentación no acredita ejecución ni espacio ya liberado. El encendido temporal para la operación consume cómputo de Google Cloud.
