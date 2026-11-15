# Consolidación de Segunda_competencia en Experimentos-

Repositorio central: **ClariRZ/Experimentos-**. No se modificó ni eliminó el origen.

Origen fijado: `ClariRZ/Segunda_competencia`, commit `c89185ae9ecaba061cd859cdf23c8ba3c5200c22`. Destino previo: `3d07e0c4931d5bc1be757f65d3f8dca93ad11e27`.

| Acción | Archivos |
|---|---:|
| Incorporados en sus rutas originales | 824 |
| Ya presentes e idénticos | 67 |
| Versiones diferentes conservadas en `fuentes/Segunda_competencia_c89185ae/` | 4 |
| Conservados sólo en respaldo privado local | 7 |
| Total de archivos del origen revisados | 902 |

Los siete privados son seis archivos `model.txt` de `experimento_historicas_B0_B5` y su `studies.sqlite`. No se republicaron aunque ya estuvieran en el repositorio de origen. Los archivos de curva contienen cantidades de contactos y ganancia, no identificadores de clientes. No se incluyeron dataset ni predicciones individuales nuevas.

Cada fila de `INVENTARIO.json` registra ruta y blob Git de origen, SHA256, tamaño, decisión y destino. Se verificó la igualdad byte a byte mediante SHA256. Los documentos copiados conservan su contenido histórico: las afirmaciones antiguas de «pendiente» no describen necesariamente el estado actual. Ver [índice central](../../INDICE_EXPERIMENTOS.md).

## Conflictos resueltos sin sobrescribir

- `README.md`: se conserva el del origen como antecedente; el destino mantiene su propia documentación.
- `HISTORIA_2019_01/v6/README.md`: el origen describía un protocolo sin correr. El destino documenta la ejecución y octubre; se conserva como principal.
- Manifiestos v5 y v6: se conservan ambas versiones. El manifiesto antiguo no debe reemplazar al que corresponde a resultados posteriores. El inventario nuevo documenta la copia completa sin reescribir los manifiestos históricos.

## Respaldo local adicional

En el workspace, `work/consolidacion_repos_20261115/Segunda_competencia_main_completo.tar.gz` conserva los 902 archivos, incluidos los siete privados. Se leyó y verificó cada miembro contra el inventario. `Segunda_competencia_historial.bundle` conserva las referencias Git disponibles de origen. Estos archivos no se suben a GitHub. El repositorio original permanece como otra ubicación; el respaldo local no implica disponibilidad permanente de los artefactos fuera de este equipo.

## Alcance y límites

Esta operación consolida contenido versionado y verifica integridad. **No reentrena ni demuestra reproducción numérica independiente.** No enciende la VM, no borra datos, no cambia recetas ni contratos ejecutados.

V1 cuenta con documentación histórica y evidencia de respaldo privado. No se inventa una carpeta v1 ejecutable completa a partir de una bitácora. V8 cuenta con código, contrato y pruebas; la salida compartida en la conversación confirma 144 ajustes y evaluación terminados, pero los resultados reales y el comprobante de recuperación aún no están disponibles aquí para publicarlos. Por eso no se declara que v8 esté completamente respaldada en este repositorio.

Verificar desde la raíz: `python3 herramientas/verificar_consolidacion.py`.
