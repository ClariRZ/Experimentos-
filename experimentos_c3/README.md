# Experimentos derivados de C3

Estado: **auditoría y ensayo C3/B6 intrames completados; resultados verificados**. Control: C3_HIST_MAS_TARJETAS, corrida `c1c3final04b`. Esta carpeta reúne evidencia, configuraciones y diseños sin modificar el modelo original.

## Entradas

- [Radiografía de punta a punta](00_auditoria/informe.html) (descargar y abrir en navegador).
- [Hiperparámetros: comparación e interpretación](00_auditoria/HIPERPARAMETROS.md).
- [Parámetros extraídos de C3 y B0–B5](00_auditoria/hiperparametros_comparados.csv).
- [Diseño de los próximos experimentos](01_diseno/PROTOCOLO.md).
- [Plan original de C3](config/c3_plan_original.json).
- [Reproducir y límites de alcance](REPRODUCIR.md).

## Qué está verificado

Se leyeron los 20 boosters y sus checkpoints; se cotejaron 2.062 nombres y su orden, 300 árboles por modelo, hashes e identidad del plan. El promedio de las predicciones reconstruyó byte a byte el CSV enviado de 11.000 IDs. Los parámetros declarados en el plan coinciden con los guardados en los veinte modelos; sólo varían parámetros de semillas.

La ganancia pública/privada de C3 es evidencia documental, no un recálculo con etiquetas privadas. La auditoría no reconstruyó las matrices desde el parquet ni reentrenó C3. Los análisis a nuevos cortes de B0–B5 son posteriores al test original.

## Estructura

- `00_auditoria/`: resultados agregados, scripts originales y comparación de parámetros.
- `01_diseno/`: hipótesis, controles y criterios de evaluación pendientes.
- `config/`: receta original congelada y diseños propuestos.
- `scripts/`: extracción verificable de parámetros desde los boosters.

No contiene IDs, predicciones individuales, datos bancarios ni credenciales. Los insumos privados se recuperan del bucket autorizado; sus hashes permiten verificar identidad. Las importancias internas no equivalen a contribuciones causales a la ganancia.

## Ensayo completado

[Comparación de tres brazos para C3 y B6 con ratios intrames](02_intrames_C3_B6/README.md).
