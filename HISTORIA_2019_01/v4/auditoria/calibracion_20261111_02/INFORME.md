# Calibración corregida v4

Completada: cinco modelos de 200 árboles. Octubre excluido. VM apagada, estado TERMINATED.

| Alternativa | Variables | Preparación LightGBM (s) | Entrenamiento 200 árboles (s) |
|---|---:|---:|---:|
| B0 | 652 | 8.97 | 45.89 |
| F1 | 1156 | 17.30 | 76.07 |
| F3 | 1030 | 15.09 | 69.12 |
| F4a | 778 | 12.15 | 54.83 |
| F4b | 1786 | 37.79 | 146.84 |

Proyección de 75 ajustes a 1500 árboles: 15.26 horas, con 20% de margen. Usa velocidad por alternativa y costo separado de construcción. No descuenta early stopping y solo mide los hiperparámetros del piloto: no es un tiempo garantizado ni prueba de que el tiempo real sea exactamente ese.

El límite autorizado sigue siendo dos horas. No se ejecutó Optuna ni comparación de semillas. Estos resultados miden costo computacional, no calidad predictiva. La comparación completa requiere un presupuesto revisado o un alcance diferente aprobado.

Controlador desde encendido hasta apagado: 11.24 minutos. Registros originales recuperados por transferencia comprimida desde Cloud Shell. Código local: dd91501. No se realizó push.
