# Respaldo local y limpieza efectivos — v1 y v6

14/11/2026. Esta ejecución sustituye el estado «respaldo privado no encontrado / limpieza pendiente» de los informes anteriores para las carpetas aquí identificadas.

## Resultado comprobado

- Respaldo privado de **2.329.383.991 bytes**, guardado directamente en la computadora de Clara.
- **827 archivos** verificados individualmente contra el inventario previo a la transferencia, además del hash del archivo completo y sus 70 partes.
- **298 referencias publicadas** de v6 coinciden con los archivos recuperados, incluido dataset, metadatos, código de entrenamiento, modelos y predicciones identificados.
- V1: recuperados 120 modelos de la corrida principal, 120 archivos NPZ y 12 CSV de predicciones. También fuentes, configuración, resultados, piloto y revisiones existentes. Las dos exportaciones finales de octubre coinciden con los hashes de su FINAL.json.
- V6: recuperados los 55 modelos individuales; los archivos privados de la carpeta incluyen 133 NPZ y siete parquet conservados (no todos son matrices prescindibles).
- Restauración real de cinco archivos en otra carpeta local. Se abrieron dos modelos con LightGBM y sus NPZ con NumPy: v1, 304 árboles/760 features; v6, 320 árboles/634 features. Esto verifica recuperación y lectura, **no** reentrenamiento independiente ni regeneración de predicciones.

El archivo está fuera de Git por contener información privada. Los originales de modelos, predicciones, código, metadatos y dataset siguen en la VM. Las carpetas de entorno y caché no se incluyeron en el paquete y tampoco se borraron. El respaldo de v1 no convierte su test económico pendiente en una evaluación terminada: su FINAL conserva el estado histórico MODELOS_CONGELADOS_TEST_EXTERNO_PENDIENTE.

## Limpieza ejecutada

| Concepto | Archivos | Bytes retirados |
|---|---:|---:|
| Matrices derivadas de v6: once de entrenamiento y once de octubre | 22 | 7.633.068.007 |
| Copias temporales creadas para esta transferencia: archivo y partes | 71 | 4.658.767.982 |
| Total de esta ejecución | 93 | 12.291.835.989 |

Espacio libre final medido antes de apagar: **18.259.726.336 bytes (18,26 GB / 17,01 GiB)**. No sumar este total al espacio libre previo a crear el respaldo: los temporales se habían creado en esta misma operación. No se borró ningún archivo de v1 ni se intervino en C1/C3, v2–v5 o v7 durante esta limpieza.

El borrado de matrices se hizo después de comprobar todos los miembros del respaldo local y volver a validar los originales. Para los temporales se verificó nuevamente el hash de cada archivo. Se registraron rutas, hashes, tamaños y acciones. Los inventarios y diarios completos permanecen junto al respaldo privado local; este informe publica solo evidencia agregada.

## Apagado y acceso

Se retiró exactamente la clave SSH temporal habilitada para este rescate. El comando de apagado del sistema devolvió código 0, al igual que la sesión SSH. Se eliminó la clave privada temporal local. No se consultó el estado administrativo TERMINATED mediante la API de Google Cloud; no se presenta el cierre SSH como esa consulta. La instancia también tenía límite independiente de una hora con acción STOP.

## Ubicación y límites

Carpeta local: `work/respaldo_local_v1_v6_20261114/` dentro del workspace de esta tarea. Archivo: `respaldo_v1_v6.tar.gz`. El hash SHA256 está en COMPROBACION.json. Se preservaron el inventario, comprobante, restauración de prueba y diarios.

Esto certifica la captura de las carpetas identificadas y los archivos encontrados, no la existencia de cualquier archivo histórico perdido antes del inventario ni un respaldo completo de toda la VM. Tampoco convierte copias del mismo disco local en protección ante pérdida de ese dispositivo. Los originales conservados en la VM son otra ubicación para los artefactos esenciales; las matrices borradas son derivadas.
