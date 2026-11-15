# Hiperparámetros efectivamente guardados

Se extrajeron del bloque `parameters` de los 20 archivos de modelo, no sólo de la configuración. Los valores decimales del formato de LightGBM pueden estar redondeados; para reproducir B0–B5 usar sus `complete.json`, no copiar valores redondeados de esta tabla.

| Parámetro | C3 | B0 | B2 | B4 |
|---|---:|---:|---:|---:|
| learning_rate | 0,03 | 0,0238691 | 0,0239092 | 0,0239092 |
| num_leaves | 64 | 77 | 72 | 72 |
| min_data_in_leaf | **100** | **2276** | **2355** | **2355** |
| feature_fraction | 0,8 | 0,969724 | 0,969996 | 0,969996 |
| bagging_fraction | 0,8 | 0,763414 | 0,764297 | 0,764297 |
| bagging_freq | 1 | 1 | 1 | 1 |
| Árboles guardados | 300 | 204 | 298 | 250 |
| max_bin | 255 | 255 | 255 | 255 |
| feature_pre_filter | true | false | false | false |
| Métrica registrada | binary_logloss | auc | auc | auc |

En todos: objetivo binary, max_depth=-1, lambda_l1=lambda_l2=0, min_gain_to_split=0, min_sum_hessian_in_leaf=0,001, scale_pos_weight=1, is_unbalance=false, zero_as_missing=false. C3 usa seis hilos y los nuestros ocho. C3 no declara categorías nativas en los boosters; nuestros modelos sí usan la codificación categórica del pipeline.

## Qué cambia la interpretación

1. **Regularización por tamaño mínimo de hoja:** C3 admite regiones mucho menores. No implica que sus hojas observadas tengan exactamente 100 filas ni prueba sobreajuste; su mínimo está lejos del de nuestros modelos. Puede ayudar con subgrupos pequeños y también aumentar variabilidad.
2. **Nuestra búsqueda no incluía C3:** min_data_in_leaf se exploró entre 200 y 5000; el valor 100 estaba fuera. Comparar ganancia no es aislar las transformaciones si además cambian estas condiciones.
3. **Cantidad de árboles y parada:** C3 fija 300 sin early stopping en S3; nuestros árboles dependen de validación AUC. Que B2 tenga 298 no hace equivalentes las recetas.
4. **Métrica versus objetivo:** ambos entrenan un objetivo binario. Registrar AUC o logloss no significa por sí solo cambiar la función que construye los árboles; aquí AUC sí gobierna BO y early stopping de B0–B5. Targets y datasets también difieren.
5. **Muestreo de columnas:** conservar feature_fraction al quitar/agregar variables mantiene la fracción, no las columnas muestreadas ni su número. Una ablación mide el cambio completo del procedimiento.
6. **Prefiltrado:** C3 guarda feature_pre_filter=true. Si se busca min_data_in_leaf sobre un Dataset reutilizado, hay que reconstruir el Dataset por prueba o desactivar prefiltrado coherentemente en todos los brazos. No mezclar este cambio con el supuesto efecto de una familia.
7. **Ensemble:** C3 promedia veinte modelos; B0–B5 no. La reducción de variabilidad es otra diferencia a controlar.

## Verificación

`verificacion_20_modelos.csv` enumera semillas, árboles y hashes. `parametros_efectivos_20_modelos.json` conserva todos los parámetros. Sólo varían seed, bagging_seed, feature_fraction_seed, extra_seed, drop_seed, data_random_seed y objective_seed. Los parámetros de algoritmos no activos que LightGBM serializa no son evidencia de que esos algoritmos se hayan utilizado.

Primera pregunta experimental: ¿qué cambia al aumentar min_data_in_leaf de C3 manteniendo sus variables, target, datos y rondas? Segunda pregunta, separada: ¿qué cambia al incorporar una familia con los hiperparámetros de C3 congelados?
