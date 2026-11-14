# Informe de prompts modelos e hipótesis de historia 2019

Informe de 24 páginas sobre v4, v5 y v6, con 23 fichas de modelos, ganancias de agosto y octubre disponibles y base propuesta para el siguiente experimento.

- [Informe editable en Word](Informe_prompts_modelos_hipotesis_2019.docx)
- [Informe para leer en GitHub](INFORME.md)
- [Resumen numérico por modelo](modelos_resumen.csv)
- [Métricas individuales por semilla](semillas.csv)
- [Evidencia completa y listas ordenadas de columnas](evidencia.json)
- [Prompts y contratos originales copiados sin cambios](prompts_originales/)
- [Verificación de esta entrega](VERIFICACION.json)

## Alcance y lectura

AUC elige los hiperparámetros. La regla de promoción de v4 fue AUC; en v5/v6 fue económica. Agosto reporta máximo suavizado y octubre ganancia puntual al corte congelado. El informe separa esas métricas, medias individuales y ensemble. V5 tiene pendiente octubre. Todas las nuevas hipótesis sobre meses ya explorados son exploratorias.

Se proponen seis brazos con controles explícitos, 90 ajustes máximos bajo diez trials y cinco semillas por brazo. Es una base de diseño, no una corrida autorizada ni una promesa de mejora. Canaritos, ranking previo, máscaras mínimas y otras ramas tienen protocolos separados.

## Corrección de la trazabilidad de v4

La auditoría complementaria sí recuperó el calibrador original y las listas completas de columnas, y confirmó los 25 hashes de modelos. Se incorporan esas evidencias. Siguen pendientes la recuperación privada verificable, información histórica del entorno y reproducción independiente del entrenamiento.

## Reconstruir las tablas y el documento sin entrenar

Desde la raíz de este repositorio, usando Python con `python-docx` instalado:

```bash
python informes/prompts_modelos_2019_2026-11-13/scripts/extraer.py --repo . --output /tmp/evidencia_historia
python informes/prompts_modelos_2019_2026-11-13/scripts/redactar.py --work /tmp/evidencia_historia --output /tmp/informe_historia
```

El extractor lee resultados ya guardados y comprueba trials, columnas, diferencias, cortes y aciertos; no accede al dataset ni entrena. El constructor genera Word, Markdown, CSV y JSON. El commit documental puede cambiar al reconstruir sobre otra revisión; los hashes de las fuentes permiten identificar las entradas originales. Las copias de prompts y el manifiesto de esta entrega se conservan en sus archivos independientes.

Los archivos incluyen parámetros y métricas agregadas, no datos de clientes ni predicciones individuales. `fuentes_sha256.json` identifica las entradas; `MANIFIESTO_SHA256.json` identifica la entrega. La reproducción del informe no reemplaza la reproducción del entrenamiento.
