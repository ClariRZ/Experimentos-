# Primera ejecución v4 — pausa por presupuesto

Se ejecutó la preparación completa y dos pilotos reales de LightGBM. Las 25 pruebas pasaron localmente y en la VM. La optimización y comparación entre semillas no comenzaron. No hay ganador ni resultados comparativos de AUC o ganancia.

| Piloto | Variables | Árboles | Tiempo de entrenamiento |
|---|---:|---:|---:|
| B0 | 652 | 100 | 27,46 s |
| F4b | 1786 | 100 | 102,35 s |

Se crearon las cinco matrices. Pico de memoria del proceso: 26,34 GiB. El controlador tardó 400 segundos desde la orden de encendido hasta verificar el apagado. Estado final de la VM: TERMINATED. Octubre no fue evaluado.

## Motivo de pausa

El plan aprobado exige pausar si la proyección no cabe en dos horas. La regla implementada extrapola el piloto más lento a 75 ajustes de 1500 árboles con 20% de margen: 38,38 horas frente a 1,87 horas restantes. Es una proyección deliberadamente conservadora, NO un pronóstico preciso ni una cota matemática: incluye el costo de construir datasets en cada piloto, supone que todos los ajustes usan el brazo más pesado, no descuenta early stopping y tampoco mide los extremos del espacio de hiperparámetros. No corresponde pedir 38 horas basándose únicamente en esta cifra.

El siguiente paso requiere revisar el presupuesto y calibrar por separado el costo de preparación de LightGBM y el costo incremental de árboles. Cualquier cambio en el límite de tiempo o en el número de alternativas debe quedar explícito; no reducir silenciosamente el presupuesto de algunas alternativas.

## Respaldo

Código y configuración aprobada: commit d1f8cd7. Los registros originales agregados están en Cloud Shell, /home/clarirz/inicial_20261111_01_agregados.tar.gz, y en la VM apagada. Los datos individuales, matrices y modelos permanecen en la VM y están excluidos de Git.

Este informe y cierre_observado.json transcriben la evidencia visible de Cloud Shell. El navegador informó descarga exitosa, pero no se localizó el paquete en el sistema de archivos local: la incorporación del manifiesto completo a Git sigue pendiente. No se realizó push a GitHub.
