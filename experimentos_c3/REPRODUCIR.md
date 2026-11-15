# Reproducir la auditoría

Desde la raíz del repositorio, con Python 3 y acceso autorizado al bucket:

```bash
mkdir -p /tmp/c3_auditoria_modelos
gcloud storage cp 'gs://clarirz_buckito2026/experimentos_clara/corridas/c1c3final04b/modelos/modelo_*.txt' /tmp/c3_auditoria_modelos/
python3 experimentos_c3/scripts/auditar_hiperparametros.py --models /tmp/c3_auditoria_modelos
```

El script usa sólo biblioteca estándar. Coteja plan contra los veinte boosters, verifica semillas y número de árboles, registra hashes y compara con los modelos de la carpeta hermana `experimento_historicas_B0_B5`. Para validar los hashes descargados, compararlos con el archivo versionado `00_auditoria/verificacion_20_modelos.csv` antes de reemplazarlo; se puede pasar `--output /tmp/c3_auditoria_resultados` para conservarlo.

La auditoría anterior de importancias y reconstrucción del envío conserva su código en `00_auditoria/auditar.py` y su disposición original de insumos documentada en `00_auditoria/REPRODUCIR.txt`. Admite `--root`; requiere LightGBM 4.7.0, NumPy 2.5.4 y pandas 3.1.1. Su generador HTML se conserva como fuente del informe. Los insumos con IDs se recuperan en almacenamiento privado y nunca se agregan a Git.

No hay todavía un ejecutor de entrenamiento de los experimentos E01–E05. Son diseños pendientes. El plan original identifica código, datos y versiones C3; no confundir esta auditoría reproducible con haber reproducido el entrenamiento completo desde datos originales.
