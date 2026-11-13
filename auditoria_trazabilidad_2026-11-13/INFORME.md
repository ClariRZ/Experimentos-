# Auditoría de trazabilidad — 13/11/2026

## Alcance

Se clonó el repositorio vacío `ClariRZ/Experimentos-` y se copió el experimento preservando los archivos originales. El manifiesto de 53 archivos coincide. Se ejecutaron diez pruebas originales y tres pruebas adicionales: 13 aprobadas. No se entrenaron modelos ni se encendió la VM.

## Revisión de los cinco huecos

| Punto | Evidencia y conclusión | Pendiente |
|---|---|---|
| `calibrar.py` | Se recuperó `/home/clarirz/calibrar.py` de Cloud Shell: SHA256 `0e95de37f1d6f2fb0e6831399919ebac6f82dd50527baf52e022a7791cec9110`, idéntico al registrado en `code_identity.json`. Guardado como `calibrar_original_vm.py`; no se ejecutó. | Cerrado: archivo original recuperado y verificado. |
| Modelos | La afirmación «modelos sin hash» no es correcta: el protocolo resumido guarda los 25 SHA256. Se extrajeron sin alterarlos a `modelos_sha256.json`. | Recuperar/comprobar los archivos y disponer de un respaldo privado; un hash no permite restaurar un modelo perdido. |
| Columnas de octubre | Cloud Shell confirmó la existencia del archivo agregado y del miembro `octubre_20261113_01/protocolo_congelado.json`. Se leyó su hash completo: `aa1ca2cf7eb7c7c5cfaf9c15c06d627ed60e23ce07c164da06d030677b26d479`. | Cerrado: recuperado en `protocolo_congelado_completo.json`, con igualdad exacta del hash del archivo original y verificación de las cinco listas ordenadas. |
| Entorno original | Están registradas las cuatro librerías principales; el entorno probado localmente no equivale al de la corrida original. | Recuperar evidencias históricas de Python/scikit-learn si existen. Un `pip freeze` actual solo describe el entorno actual. |
| Runner portable | Las pruebas sintéticas y la comparación AST pasan. | Ejecutar con el dataset real en otro entorno y contrastar todos los resultados. `full_dataset_rerun` sigue siendo false. |

## Archivo remoto localizado

Cloud Shell: `/home/clarirz/v4_octubre_20261113/octubre_20261113_01_agregados.tar.gz`.

Contenido observado: `protocolo_congelado.json`, `FINAL.json`, `verificaciones.json`, bajo `octubre_20261113_01/`. El protocolo completo se recuperó localmente. Se transfirieron las listas mediante índices comprimidos y se restauró la serialización original; el SHA256 final coincide exactamente con el observado en Cloud Shell.

## Qué puede afirmarse

Los archivos publicados identifican datos, configuración, código y resultados por semilla. Los modelos también están identificados por hashes. La carpeta fue copiada sin modificar sus 53 archivos verificados. Todavía no se ha demostrado reproducción independiente del entrenamiento ni respaldo local completo de los artefactos privados.

## Orden para cerrar los pendientes

1. Completado: protocolo completo recuperado y verificado.
2. Recuperar los modelos en almacenamiento privado y verificar los 25 hashes. Respaldar también el dataset autorizado y las predicciones si corresponde, sin publicarlos en Git.
3. Calibrador exacto recuperado; sigue pendiente evidencia histórica adicional del entorno.
4. Preparar entorno independiente y ejecutar la reproducción completa. Registrar identidad de máquina, sistema, Python, dependencias, semilla, comandos, tiempo y resultados de los verificadores.
5. Publicar el informe de reproducción con éxito o discrepancias. No declarar cierre por el solo hecho de tener instrucciones ejecutables.
