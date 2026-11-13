# Historia 2019 v6 — profundidad histórica

Autorizada por Clara: «lanzá v6», 13/11/2026. Preparada para once brazos, 165 ajustes máximos y 18 contrastes preregistrados. Entrenamiento junio, validación agosto; historia enero–agosto. Ningún resultado de v5 decide los brazos.

## Alcance de este lanzamiento

B0_J, L4, L6, S3, S4, S6, T4, T6, R3, R4, R6. Cada brazo tiene 10 trials Optuna y cinco semillas propias de evaluación. La auditoría real construye y congela columnas, matrices y exclusiones antes del primer ajuste; cualquier error aborta. Las pruebas sintéticas no sustituyen esa auditoría.

Octubre queda fuera de esta corrida de desarrollo. Es una fase pendiente explícita, sin reentrenamiento y con proporciones de contacto congeladas. La ejecución de agosto no representa el cierre económico completo del prompt.

## Tiempo y protección

V5 midió 2 h 26 min para 105 ajustes. La extrapolación simple a 165 es 3 h 50 min; junio tiene menos filas y las representaciones cambian. Estimación prudente: 2–5 horas. Límite independiente v6: 6 horas de VM, supervisor de 5 h 50 min desde el lanzamiento, 48 GiB RAM y 10 GiB libres mínimos. Un ajuste a la vez, cuatro hilos.

Costo orientativo de cómputo: unos USD 0,40/h, máximo aproximado USD 2,40 en seis horas, además de disco, red e impuestos. Fuente regional consultada: https://www.devzero.dev/instances/gcp/e2-highmem-8 ; no es una cotización de facturación.

El trabajador se ejecuta separado de Cloud Shell, genera el archivo de agregados y apaga la VM tres minutos después de finalizar o fallar. GCE impone además el límite máximo. Si Cloud Shell pierde la conexión, los modelos, matrices y resultados quedan en el disco persistente para recuperación; no se consideran respaldados en Git hasta verificar el push.

## Reproducción

El contrato está en `configuraciones/contrato_v6.json`. `scripts/ejecutar_etapa1.py` verifica el SHA256 del dataset, construye matrices calendario exactas, depura exclusivamente con junio y ejecuta los once brazos identificables. `scripts/auditar_etapa1.py` permite construir las mismas matrices sin entrenar. Ambos requieren `--config`, `--dataset`, `--output` (nuevo) y `--deadline` (epoch futuro). Las dependencias exactas de la VM se registran en `entorno.json`.

Pruebas: `python -m pytest pruebas -q`. Control Cloud Shell: `python scripts/control_cloudshell.py --repo RUTA_REPO --commit SHA_COMPLETO --run v6_20261113_01`. El controlador exige VM apagada, valida hashes del código y confirma el apagado máximo antes de encenderla. Nunca relanzar un identificador ya existente.

## Artefactos

Se publican contratos, código, columnas, exclusiones, métricas agregadas, trials, semillas y hashes de modelos/predicciones. No se publican datos de clientes, modelos ni matrices. Ubicación privada: `/home/clarirz/HISTORIA_2019_01/v6/deployments/IDENTIFICADOR/resultados/entrenamiento/private/`.

El protocolo original está conservado en `prompts/`. El estado real y los registros de lanzamiento se incorporan en `auditoria/`; resultados en `resultados/`. Los resultados siguen siendo exploratorios por el uso previo de agosto y octubre.
