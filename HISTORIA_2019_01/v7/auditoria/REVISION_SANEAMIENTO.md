# Revisión previa al entrenamiento

Auditoría real `v7_audit_20261114_015940`: retorno 0; VM apagada al finalizar. El informe completo se recuperó en Cloud Shell y queda identificado por SHA256 `430abb720b73f5ca225d6eeb5c131354766c5ca2be8f2853cd2a6ebf93d40401`. Los archivos RESUMEN_REAL y CONTROL_REAL transcriben los JSON de la salida suministrada por Clara, uniendo saltos de línea del terminal. No reemplazan el informe completo.

El dataset coincide con el original. Entrenamiento abril–junio: 381.596 filas; agosto: 131.887; octubre: 135.754. No hubo entrenamiento ni acceso a etiquetas de octubre durante esta auditoría.

Se conservan las nueve máscaras originales. Se agregan las catorce variables de octubre identificadas en el resumen: todas tienen 100 % de ceros, mientras en septiembre presentan valores heterogéneos. Se aplica NA antes de construir historia, igual para todos los brazos. Es una decisión de calidad basada en evidencia, no una confirmación oficial del origen de la rotura.

Para Visa_fultimo_cierre y Master_fultimo_cierre en julio, el diccionario define días desde el cierre; cero individualmente puede ser válido. La sospecha es la concentración abrupta de toda la información observada en cero. El controlador debe comprobar en el informe completo que todos los valores son cero o faltantes, sin otros valores finitos, y que junio tenía variación. Solo si se cumple aplica NA a estos dos campos en julio. Si no, bloquea antes de encender la VM. Esta hipótesis conservadora queda explícita y no se eligió mirando ganancia.

Las máscaras nuevas cambian las condiciones respecto de corridas anteriores: no atribuir diferencias entre versiones exclusivamente a las variables históricas. Los diez brazos de v7 comparten el mismo saneamiento. Las matrices y su cobertura todavía deben pasar el control del ejecutor antes del primer ajuste.
