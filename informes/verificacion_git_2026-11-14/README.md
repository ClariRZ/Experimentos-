# Verificación de Git local y GitHub — 14/11/2026

## Resultado

Se consultaron los remotos y se compararon con los repositorios locales originales. Se clonaron de nuevo Segunda_competencia y Experimentos-cloud. Se verificaron sus objetos con `git fsck --full`, se comprobó cada archivo versionado contra su blob Git y se leyeron todos los JSON del árbol principal. No hubo errores de integridad, cambios locales pendientes ni JSON ilegibles en esos árboles.

| Repositorio | Commit auditado | Archivos comprobados | Estado |
|---|---|---:|---|
| ClariRZ/Experimentos- | fcaa8dfd719582d8b6b8b44ae79effa6f4a21459 | 553 | Local y remoto coinciden |
| ClariRZ/Segunda_competencia | c89185ae9ecaba061cd859cdf23c8ba3c5200c22 | 902 | Local y remoto coinciden |
| ClariRZ/Experimentos-cloud | 1d88507e875c62c0f872a922f0c92ab6d2666b0a | 261 | Local y remoto coinciden |

Total: 1.716 archivos (incluye copias entre repositorios; no son 1.716 artefactos únicos). La publicación de este informe añade un commit posterior en Experimentos-. Se crearon y verificaron bundles locales de los tres repositorios; el de Experimentos- ya tenía una restauración de prueba. Los bundles nuevos incluyen las referencias remotas descargadas, no solo main. La comprobación archivo a archivo corresponde a main, no a cada árbol histórico de cada rama.

## Dónde está cada experimento

| Material | Repositorio y carpeta principal |
|---|---|
| Antecedentes C1/C3 y otros diseños históricos | Experimentos-cloud; también auditorías C3 en Segunda_competencia |
| Históricas B0–B5, 7/11 | Segunda_competencia/experimento_historicas_B0_B5 |
| Ale + C3 en 2019, A/B/C/D | Segunda_competencia/experimento_Ale_C3_2019 |
| C3/B6 intrames | Segunda_competencia/experimentos_c3/02_intrames_C3_B6 |
| Historia v1, evidencia parcial | Segunda_competencia/HISTORIA_2019_01 y fuentes_vm de v2 |
| Historia v2 y v3 | Segunda_competencia/HISTORIA_2019_01/v2 y v3 |
| Historia v4 | Experimentos-/experimento_2026-11-13, con copia en Segunda_competencia |
| Historia v5–v7, cierres recientes | Experimentos-/HISTORIA_2019_01; Segunda_competencia conserva estados anteriores |

No confundir v6 propuesto en Segunda_competencia con la ejecución y octubre de v6 publicados en Experimentos-.

## Manifiestos: diferencias concretas

- **B0–B5:** los 98 archivos del manifiesto de entrega coinciden. Existen seis archivos de modelos LightGBM reales en Git, incluidos en ese manifiesto. Por lo tanto, la afirmación general de que ningún modelo anterior está en Git era incorrecta.
- **V4:** los 53 archivos del manifiesto coinciden en ambos repositorios.
- **V5:** coincide su manifiesto en cada repositorio (28 archivos en el estado anterior, 59 en el posterior). Son alcances diferentes; esos números no incluyen necesariamente todos los resultados agregados añadidos después.
- **V6:** manifiesto de tres archivos de la propuesta en Segunda_competencia sin diferencias. En Experimentos-, 19/20: el README cambió al incorporar el cierre de octubre. Se conserva el manifiesto histórico; el inventario nuevo registra el SHA256 del README actual.
- **V7:** los 153 archivos del manifiesto de resultados coinciden. La verificación previa también comprobó los 26 del manifiesto de código.
- **V2:** 41 archivos coinciden; `.gitignore` y `ESTADO_EJECUCION.txt` difieren del manifiesto inicial. Tres archivos empaquetados citados no están en el árbol publicado: `fuentes_vm.tar.gz`, `paquete_continuacion.tar.gz`, `paquete_v2_inicio.tar.gz`. Existen fuentes y resultados descomprimidos, pero no se afirma equivalencia byte a byte de esos tres archivos ausentes.
- **Ale+C3:** el manifiesto explícitamente llamado `manifest_codigo_previo.json` tiene siete diferencias posteriores. La firma efectiva `resultados/RUN_SIGNATURE.json` coincide con los tres scripts que identifica: `comun.py`, `ejecutar.py`, `preparar.py`. La diferencia de un protocolo previo no se silencia regenerando su manifiesto.
- **C3/B6:** los diez archivos del manifiesto de código coinciden.

El inventario distingue rutas inicialmente no localizadas de archivos encontrados por el mismo hash en otra carpeta/repositorio. Los hashes de modelos/predicciones privados que no están en Git no se clasifican automáticamente como pérdida: requieren comprobar el almacenamiento privado, fuera del alcance de la comprobación remota de Git.

## Respaldo privado v7: verificado adicionalmente

En archivos locales recuperados desde Cloud Shell:

- Agosto: archivo de 111 miembros legibles; 50 modelos y 50 predicciones individuales por semilla coinciden con los hashes de la política congelada. Los 11 miembros adicionales son legibles, pero no se afirma una comparación individual de hash contra aquella política.
- Octubre: los 61 miembros coinciden con `private_manifest.json` publicado; cero faltantes, extras o diferencias.
- SHA256 archivo agosto: `c7e6093d6d1228e93e666cdd269af6a432157217d68fad4108ed3d04db668d4f`.
- SHA256 archivo octubre: `bc98d361ecc938c5ef93025abe556f63b24f4655bbcfb872c92bbefd5a7e0cad`.
- Cloud Shell mostró `RESPALDO PRIVADO VERIFICADO` y la detención completada de la VM. Es evidencia de ese momento, no monitoreo permanente.

Los archivos privados se conservaron fuera de Git. La copia local adicional está en la misma computadora: no sustituye almacenamiento privado en otro dispositivo o servicio.

## Conclusión operativa

Los archivos versionados de los tres repositorios auditados están respaldados localmente y publicados en GitHub, con identidad comprobada. Eso no prueba que todo archivo de la VM forme parte de Git, que todos los modelos privados antiguos estén respaldados o que se haya reentrenado cada experimento independientemente. No se borró nada de la VM durante esta revisión.

Para limpieza, v7 tiene sus modelos y predicciones identificados y recuperados; todavía hay que verificar cada candidato regenerable contra su manifiesto y que no lo use ningún proceso. No autoriza borrar en bloque las matrices de C1/C3 ni datasets. El reporte evita pedir más inspecciones manuales de Git al usuario: el mapa y las diferencias ya están registrados aquí.
