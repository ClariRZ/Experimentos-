# Experimento 13/11/2026 — Historia 2019 v4

**Estado: entrenamiento y evaluación de octubre completados.** Esta carpeta reúne una copia identificable del experimento y una entrada portable para reproducirlo desde el dataset. No es un nuevo entrenamiento: el desarrollo terminó en la corrida `completa_20261111_03`; octubre se evaluó el 13/11 en `octubre_20261113_01`.

## 1. Pregunta y diseño

¿Agregar nuevas representaciones de historia corta mejora un LightGBM que ya tiene rezagos y deltas?

- Datos de 2019. Enero y febrero aportan historia; entrenamiento marzo–junio completo; validación agosto; evaluación octubre.
- Entrenamiento: BAJA+1 y BAJA+2 positivas. AUC: BAJA+2 positiva. Ganancia: +1.072.500 por BAJA+2 contactada, −27.500 por cualquier otro contacto.
- Nueve pares variable-mes saneados antes de construir historia. Faltantes preservados; rezagos por mes calendario exacto.
- 129 fuentes históricas revisadas. Se eliminan vacías, constantes y duplicadas usando solo entrenamiento; se conservan 152 variables originales antes de esas exclusiones.
- W3 incluye mes actual y dos anteriores, con observaciones completas para los resúmenes/ratios.

| Brazo | Qué agrega al baseline | Columnas finales |
|---|---|---:|
| B0 | Variables actuales + rezagos 1/2 + deltas 1/2 | 652 |
| F1 | Promedio, mínimo, máximo y rango W3 | 1156 |
| F3 | (actual − referencia) / abs(referencia), contra promedio W3, lag1 y lag2 | 1030 |
| F4a | Ranking transversal dentro del mes | 778 |
| F4b | F4a + rezagos, deltas y resúmenes W3 de rankings | 1786 |

Cada brazo tiene 10 pruebas Optuna propias, elegidas por AUC de agosto, y luego cinco semillas (101, 211, 307, 401, 503) con sus parámetros y cantidad de árboles congelados. Total original: 50 ajustes Optuna + 25 modelos por semilla. No hubo canaritos, historia larga ni combinaciones en esta etapa.

En agosto ninguna variante cumplió la regla de promoción de AUC; se mantuvo B0. La evaluación posterior de los cinco brazos en octubre es descriptiva y no cambia retrospectivamente esa decisión.

## 2. Qué está guardado

- [Prompt y protocolo originales](prompts/README.md): carpeta separada con la propuesta, el plan adaptado y el contrato realmente ejecutado.

- `configuracion/contrato_original.json`: configuración ejecutada, fórmulas, meses, semillas, espacio Optuna y hash del dataset. Sus campos de autorización/presupuesto reflejan la etapa original; octubre tuvo autorización posterior.
- `scripts/`: generación de variables, entrenamiento portable, evaluación de octubre y controles de reproducción.
- `originales/ejecutar_completa_vm.py`: runner original sin cambios, que reutilizaba matrices de una corrida anterior.
- `resultados/agosto/`: parámetros ganadores, ensayos Optuna, métricas por semilla/ensemble y cierre original.
- `resultados/octubre/`: protocolo, métricas, verificaciones e informe. La lista completa de columnas del protocolo original permanece en el archivo agregado de Cloud Shell; aquí se conservan sus hashes y cantidades.
- `documentacion/`: antecedentes, análisis y comparación histórica con v1–v3. Son documentos fechados; sus pendientes de Git/octubre pueden ser anteriores a este cierre.
- `pruebas/`: casos sintéticos de calendario, faltantes, fórmulas, corte y selección solo con entrenamiento.
- `MANIFIESTO_SHA256.json`: integridad de los archivos de esta carpeta.

**Fuera de Git:** dataset, matrices, modelos y predicciones de clientes. Se reconstruyen en `ejecuciones/`, que está ignorada por Git. No se requiere la VM original para reconstruirlos, pero sí acceso autorizado al mismo dataset.

## 3. Preparar entorno y datos

Desde la raíz del repositorio:

```bash
cd experimento_2026-11-13
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-validado.txt
python scripts/reproducir.py verificar-archivos
python -m pytest pruebas -q
```

`requirements-validado.txt` fija el entorno completo usado para las pruebas sintéticas de esta carpeta; no pretende ser una captura retroactiva de toda la VM original. `requirements.txt` conserva las cuatro versiones originales conocidas y las dependencias adicionales.

Se fijaron las versiones registradas: LightGBM 4.7.0, Polars 2.1.0, NumPy 2.3.5 y Optuna 5.0.0. No se registraron las versiones originales de Python/scikit-learn ni todas las librerías del sistema: no se garantiza identidad binaria entre plataformas. Si el índice de paquetes no ofrece una versión, no sustituirla silenciosamente; recuperar ese entorno o documentar la diferencia y verificar los resultados. Los controles numéricos fallan ante discrepancias.

Dataset original: `analistasr_competencia_2026.csv.gz`, CSV separado por coma, con `numero_de_cliente`, `foto_mes`, `clase_ternaria` y variables originales. SHA256 requerido:

```text
459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872
```

El hash identifica el archivo exacto: recomprimir un contenido equivalente cambia el hash. Este pipeline no reconstruye la clase desde otro crudo ni descarga datos privados.

## 4. Reproducir preparación y entrenamiento

El comando siguiente **sí entrena**. Esta organización del repositorio no lo ejecuta automáticamente.

```bash
python scripts/reproducir.py entrenar \
  --dataset /ruta/analistasr_competencia_2026.csv.gz \
  --salida ejecuciones/replica_agosto \
  --horas 16
```

Reconstruye todas las matrices desde cero con las funciones originales, registra columnas y exclusiones, ejecuta las mismas 75 adaptaciones y verifica resultados contra agosto. La adaptación portable solo reemplaza la carga de matrices previas por su construcción; no cambia el diseño ni la búsqueda. Las carpetas de salida deben ser nuevas. El comando no administra ni apaga una VM: si se usa en Cloud, configurar su apagado por separado.

Referencia de recursos del entrenamiento original: aproximadamente 2 h 32 min y pico de 16,84 GiB para el trabajador con matrices ya preparadas; reconstruirlas agrega tiempo y memoria. Se recomienda margen de RAM y disco, sin prometer ese tiempo en otra máquina. El proceso exige al menos 10 GiB libres durante su ejecución.

```bash
python scripts/reproducir.py verificar-agosto --corrida ejecuciones/replica_agosto
```

Comprueba filas, orden de columnas, hiperparámetros, cantidad de árboles y métricas por semilla/ensemble. Excluye duración de la comparación; tolerancia numérica absoluta 1e-8. Una discrepancia detiene el flujo: no hay que ajustar resultados para hacerlos coincidir.

## 5. Evaluar octubre con los modelos congelados

```bash
python scripts/reproducir.py octubre \
  --dataset /ruta/analistasr_competencia_2026.csv.gz \
  --corrida ejecuciones/replica_agosto \
  --salida ejecuciones/replica_octubre
python scripts/reproducir.py verificar-octubre --corrida ejecuciones/replica_octubre
```

No entrena. Antes de puntuar octubre, reproduce las cinco matrices y 25 predicciones de agosto. Por brazo, usa `floor(proporción de contactos del ensemble de agosto × población de octubre)`, igual para sus semillas y ensemble. No busca otro corte en octubre. Evalúa 135.754 clientes; el baseline contacta 3.682. Las cantidades son distintas entre brazos porque sus proporciones se congelaron por separado.

## 6. Resultados y lectura correcta

| Brazo | Ganancia ensemble octubre M | Diferencia vs B0 M | Semillas favorables |
|---|---:|---:|---:|
| B0 | 277,1450 | — | — |
| F1 | 289,3000 | +12,1550 | 2/5 |
| F3 | 284,2950 | +7,1500 | 4/5 |
| F4a | 287,4025 | +10,2575 | 5/5 |
| F4b | 269,2525 | −7,8925 | 0/5 |

F1 obtuvo la mayor ganancia combinada; F4a fue más consistente entre semillas en octubre. B0 mantuvo el mayor AUC del ensemble. Cinco semillas no representan cinco períodos independientes. F4a había perdido ganancia en agosto. Ya se conocían resultados grupales sobre octubre: esta evaluación no se presenta como un test completamente independiente. No se compara directamente con PAQ_P3, cuya métrica, controles y calendario difieren.

[Informe completo de octubre](resultados/octubre/INFORME.md). [Análisis de agosto](documentacion/analisis_agosto.md).

## 7. Alcance de la verificación de esta carpeta

El historial ejecutado y las métricas provienen de corridas reales. La nueva entrada portable se valida con pruebas sintéticas y controles de archivos; no se volvió a entrenar el dataset completo al organizar esta carpeta. Por eso se entrega un procedimiento reproducible con resultados esperados, no una reproducción cruzada ya completada en otra máquina. Ver `documentacion/VALIDACION.json`.
