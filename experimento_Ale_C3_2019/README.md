# Ale + variables intrames de C3 en 2019: resultados A/B/C/D

**Terminado y verificado el 8 de noviembre de 2026.** 40 trials completados y 40 modelos finales: 20 semillas por representación. No hubo envío a la competencia.

[Informe completo](informe.html) (descargar y abrir en navegador) · [Conclusiones](conclusiones.txt) · [Resultados](resultados/resumen.csv) · [Guion del video](guion_video.txt).

| Brazo | Descripción | Contactos elegidos con agosto | Ganancia octubre | Ganancia con 5.042 contactos |
|---|---|---:|---:|---:|
| A | B2, una semilla | 5.042 | $282.645.000 | $282.645.000 |
| B | B2 + 43 variables, reoptimizado, una semilla | 4.762 | $284.845.000 | $285.945.000 |
| C | B2, promedio de 20 semillas | 3.561 | $277.172.500 | $283.745.000 |
| D | B2 + 43 variables, promedio de 20 semillas | 4.460 | $282.150.000 | $278.245.000 |

B gana $2,2 millones contra A con políticas propias y $3,3 millones al mismo presupuesto. Pero la representación enriquecida gana sólo 6 de las 20 comparaciones pareadas a 5.042 contactos y pierde $2,2 millones en promedio. No hay mejora consistente para adoptar el cambio automáticamente. Los ensembles tampoco mejoran a sus versiones individuales bajo sus políticas propias; a igual presupuesto, C mejora ligeramente y D empeora.

Octubre ya había sido observado: resultados exploratorios de un único mes. B/A y D/C comparan variables más reoptimización, no efecto puro de variables. No confundir estas ganancias con los resultados de C3 en 2021 ni con el privado de la competencia.

## Evidencia y reproducción

- [Protocolo previo](PROTOCOLO.md), [configuración](config_propuesta.json) y [43 variables](variables_propuestas.csv).
- [Verificación final](verificacion_final.json): 40 modelos, políticas y ganancias recalculadas. Nuevo A reproduce exactamente las predicciones de B2 en agosto y octubre.
- [Resultados por semilla](resultados/por_semilla.csv), [contrastes](resultados/contrastes.csv) y [cambios en la selección](resultados/seleccion.csv).
- [Reproducir](REPRODUCIR.txt), [versiones](requirements_vm.txt), [entorno](entorno.json), [hashes de modelos](modelos_sha256.json) y [firma del código ejecutado](resultados/RUN_SIGNATURE.json).
- [Incidentes y correcciones](IMPLEMENTACION.txt): categorías de validación antes del primer trial; lista inicial de 19 semillas corregida a 20 antes del congelamiento y del test, sin reemplazar semillas por desempeño. Se preservaron checkpoints válidos.

Datos y predicciones individuales permanecen privados. El protocolo/configuración conservan la descripción de su escritura previa; este README informa el estado final. El manifiesto de código previo corresponde a la versión inicial; la firma efectiva final está en RUN_SIGNATURE y FROZEN.
