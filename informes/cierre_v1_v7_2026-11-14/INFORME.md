# Cierre de v1–v7: evidencia, límites y siguiente experimento

14/11/2026. Actualiza el estado de respaldo del informe anterior y revisa la rama actual de Ezequiel. No es una nueva corrida. No se borró ningún archivo de la VM al redactarlo.

## 1. Respuesta sobre los respaldos

**Hay evidencia de las siete versiones; no hay siete archivos privados completos certificados.** Git local y GitHub coinciden para los tres repositorios auditados. V7 tiene además modelos y predicciones recuperados y verificados fuera de Git. V1 sigue siendo parcial. Las matrices antiguas no se pueden borrar en bloque con el argumento de que «todo está en Git».

| Versión | Ubicación pública principal | Qué se puede defender | Qué falta para certificar recuperación íntegra |
|---|---|---|---|
| v1 | Segunda_competencia/HISTORIA_2019_01; v2/auditoria/fuentes_vm | Código/configuración recuperados y evidencia de resultados | Inventario completo de originales y copia privada verificada; no reconstruir lo faltante a partir del relato |
| v2 | Segunda_competencia/HISTORIA_2019_01/v2 | Fuentes, resultados y cierre; manifiesto inicial parcialmente verificable | Tres archivos empaquetados citados no están en Git; existen fuentes expandidas, sin prueba de equivalencia de esos paquetes. Modelos privados no certificados en este cierre |
| v3 | Segunda_competencia/HISTORIA_2019_01/v3 | Código, protocolo y resultados de desarrollo | Octubre no figura cerrado en la evidencia revisada; archivo privado completo no certificado |
| v4 | Experimentos-/experimento_2026-11-13 | 53 archivos originales del manifiesto coinciden; agosto y octubre trazables | No hay reproducción independiente con dataset completo; persiste el hueco de versión de calibrar.py y del entorno original; no certificar modelos por tener hashes de predicciones |
| v5 | Experimentos-/HISTORIA_2019_01/v5 | Siete brazos, 105 ajustes y resultados de agosto | Octubre no publicado; modelos privados no certificados aquí |
| v6 | Experimentos-/HISTORIA_2019_01/v6 | Once brazos, 165 ajustes; agosto y octubre publicados | Modelos privados no certificados aquí; README posterior al manifiesto histórico (19/20 coinciden) |
| v7 | Experimentos-/HISTORIA_2019_01/v7 | Diez brazos, 150 ajustes; agosto y octubre; modelos y predicciones privados verificados | Falta reentrenamiento independiente integral; la copia local adicional usa el mismo dispositivo |

El mapa e inventario por archivo están en [verificación Git](../verificacion_git_2026-11-14/README.md). Se comprobaron 1.716 archivos de los árboles principales, integridad Git y JSON; incluye duplicados entre repositorios. Se guardaron bundles de los tres repositorios. No confundir esto con la recuperación de todos los archivos de la VM.

**Actualización respecto del informe anterior:** el respaldo privado de octubre v7 ya está completo. Sus 61 miembros coinciden con el manifiesto publicado. El archivo de agosto tiene 111 miembros legibles; sus 50 modelos y 50 predicciones individuales coinciden con la política congelada. Los otros 11 miembros son legibles, sin atribuirles una verificación individual que no se hizo. Cloud Shell mostró la detención de la VM después del rescate; no es una consulta de estado en tiempo real.

## 2. Qué aprendimos, sin sumar mejoras incompatibles

| Versión | Pregunta | Resultado útil | Principal límite |
|---|---|---|---|
| v1 | ¿Sirven transformaciones históricas? | Ratios: mejora de AUC, 16/20 comparaciones favorables | Evidencia parcial y sin cierre económico comparable |
| v2 | ¿La historia básica supera RAW? | B4: +4,913 M de ganancia suavizada media en agosto, 5/5 semillas | No equivale a ganarle al baseline histórico del curso |
| v3 | ¿Rankings, actividad y presencia agregan valor? | Conservó C0; una señal inicial no sobrevivió la ampliación de semillas | Parámetros heredados; no confundir sus fórmulas con rankings de otras versiones |
| v4 | ¿Qué familia agrega valor al baseline con ajuste propio? | Relativos favorables económicamente en ambos meses; resultados distintos por ensemble y por semilla | Ninguna pasó la regla original de AUC; cortes propios y semilla 101 compartida con búsqueda |
| v5 | ¿Qué componente de los resúmenes sirve? | Promedio, mínimo y rango favorables en agosto | Octubre pendiente; no declarar ganadores finales |
| v6 | ¿Sirven distintas profundidades con junio común? | R3, R4 y T4 favorables en agosto y octubre | Solo un mes de entrenamiento; no trasladar la magnitud a otro calendario |
| v7 | ¿Se sostienen con abril–junio y mejoran los híbridos? | R3 mantiene signo positivo; T4 mejor ensemble de octubre | Ninguno de los tres contrastes principales de híbridos fue concluyente |

Los [33 brazos de v4–v7 y sus tablas](../auditoria_integral_2026-11-14/INFORME.md#anexo-inventario-numérico-de-los-33-brazos-recientes) suman 495 ajustes registrados. No son 495 tests independientes. No volvimos a entrenarlos en esta auditoría.

### Señales económicas principales

Millones de la regla del concurso. Cada delta es contra el control **de esa versión**. Agosto v4–v6 usa ganancia suavizada y políticas propias; v7 usa ganancia puntual con contactos comunes. No hay clasificación numérica válida entre filas de distintas versiones.

| Receta | Δ agosto M | Δ octubre M | Semillas favorables octubre |
|---|---:|---:|---:|
| v4 F3, relativos | +2,733 | +7,150 | 4/5 |
| v4 F1, resúmenes juntos | +3,198 | +12,155 | 2/5 |
| v4 F4a, ranking actual | −7,505 | +10,258 | 5/5 |
| v4 F4b, historia del ranking | −11,176 | −7,893 | 0/5 |
| v5 promedio / mínimo / rango | +3,987 / +5,110 / +4,182 | Pendiente | — |
| v6 R3 | +5,453 | +11,688 | 5/5 |
| v6 R4 | +4,759 | +15,125 | 5/5 |
| v6 T4 | +6,229 | +6,820 | 5/5 |
| v7 R3 | +3,300 | +7,700 | 4/5 |
| v7 R4 | −3,300 | +9,900 | 5/5 |
| v7 T4 | −1,100 | +11,000 | 5/5 |
| v7 H_S | +6,600 | +4,400 | 5/5 |

En octubre v7: B0 = 272,1675 M; T4 = 283,1675 M; ambos con 3.583 contactos. El +4,04% es de ese mes y ese ensemble. No convierte a T4 en ganador universal. H_T y H_S no superaron a sus componentes en los contrastes principales. El bootstrap condicionado a predicciones fijas no incorpora incertidumbre de búsqueda ni variación entre épocas.

## 3. Comparación actual con Ezequiel

Se revisaron README, diseño, resultados y notebooks 22–24 en la rama **ezequiel/etapa-1**, commit **129e19a17638c7a3aee4cc30b6f504c68deea0bd**. Main está en 770abaa9cad412647211c255360cb6dfe364e697. No confundirlos. Esto es una revisión de evidencia publicada, no reproducción independiente de sus modelos.

Fuentes: [diseño inicial](https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/129e19a17638c7a3aee4cc30b6f504c68deea0bd/docs/diseno_experimental.md), [notebook 22](https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/129e19a17638c7a3aee4cc30b6f504c68deea0bd/notebooks/22_exploratorio.ipynb), [23](https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/129e19a17638c7a3aee4cc30b6f504c68deea0bd/notebooks/23_exploratorio.ipynb), [24](https://github.com/ezequielabregu/DMEyF-2026-experi-colab-feature_historico/blob/129e19a17638c7a3aee4cc30b6f504c68deea0bd/notebooks/24_exploratorio.ipynb).

| Aspecto | Nuestro trabajo | Ezequiel | Qué conservar / precaución |
|---|---|---|---|
| Historia | Familias separadas, W3/W4/W6; v7 híbridos | Historia curada, Visa/Master, relativos, pesos y paquetes | Separar mecanismos. Un paquete ganador no identifica qué ingrediente causó la mejora |
| Calendario | Controles comunes dentro de cada versión; calendario cambia entre versiones | Banco móvil hasta t−2, junio–octubre, desde notebook 15 | Adoptar repetición temporal y mismo calendario por contraste |
| Hiperparámetros | Propios por brazo desde v4; diez trials por brazo | Inicialmente comunes; notebook 23 reoptimiza paquete por ganancia | No decir que jamás reoptimizó. Tampoco que usar parámetros propios sea un error |
| Economía | v7 presupuesto común puntual | Banco reciente promedia ganancia en banda 3.000–6.000 | Banda útil como diagnóstico; no es la misma magnitud que nuestros contactos fijos |
| Pesos | Sin peso extra BAJA+2 | PAQ_P3 usa peso 3 | Su mejora frente a AC mezcla features y peso; Clara excluyó este cambio |
| Calidad | Nueve máscaras históricas abril–mayo; ceros de julio/octubre conservados | Diseño inicial: 23 pares a NA, 12 en octubre; luego declara otros dos no tratados | No trasladar máscaras. Concentración de ceros es evidencia de anomalía, no confirmación de error |
| Incertidumbre | Semillas, bootstrap y tres contrastes ajustados en v7 | Regla inicial Wilcoxon/Holm; banco reciente bootstrap por cliente y error de semilla | Son avances útiles, con alcances diferentes. La regla exploratoria reciente no exige IC positivo |
| Transparencia | Negativos, incidentes y hashes | Distingue regla inicial de análisis exploratorios posteriores | Ambos deben mantener esa separación |
| Reproducción | Hashes y predicción de agosto exacta antes de octubre | Pruebas manuales de features y comparaciones de predicción entre corridas | Reutilizar pruebas temporales y de equivalencia. Hash no equivale a reentrenar en otra máquina |

### Qué dicen sus resultados recientes

Media por mes y semilla de la **banda**, no nuestro ensemble puntual. Cifras de los CSV de la rama citada; copia mínima de evidencia y hashes en `EVIDENCIA_EZEQUIEL.json`.

| Contraste | Meses | Δ M/mes | IC 95% M | Lectura |
|---|---|---:|---|---|
| PAQ_P3 − ACH_4_P3 | junio–octubre | +2,2010 | [−0,1013; +4,5033] | Ganó su regla de magnitud; intervalo incluye cero |
| PAQ_C_P3 − PAQ_P3 (canaritos) | junio–octubre | −0,7867 | [−2,9151; +1,3418] | No demuestra mejora por selección |
| ACH_4_P3 − AC | junio–octubre | +6,7976 | [+3,3400; +10,2552] | Mejora del paquete con peso, no efecto aislado de features |
| Elegida Optuna − PAQ_P3 | septiembre–octubre | −0,9167 | [−5,1122; +3,2788] | La reoptimización no confirmó la mejora |
| PAQ2_P3 − PAQ_P3 | junio–octubre | −1,7638 | [−4,5025; +0,9750] | Agregar cinco bloques no mejoró |
| Locro de hiperparámetros − semillerío PAQ_P3 | septiembre–octubre | −0,9274 | [−3,2906; +1,4357] | Diversidad de configuraciones no garantizó ganancia |

**Octubre:** usarlo una vez para la regla predefinida es coherente con la consigna. Volver a usarlo en experimentos posteriores no es una infracción por sí sola, pero deja de ser prueba independiente. Él rotula esas fases como exploratorias. Llamar «confirmación» a septiembre–octubre en una búsqueda particular no borra su exposición en las fases previas; lo mismo aplica a nosotros.

**Canaritos:** son una selección posible, no una obligación ni un generador garantizado de ganancias. Se ajustan únicamente con entrenamiento. Sus resultados no justifican agregarlos automáticamente a nuestra última batería.

**Qué sería incorrecto afirmar:** que todos sus cambios funcionan; que su último paquete mejora; que los 9 M/mes comunicados son directamente comparables con nuestros 11 M de octubre; que la importancia de un bloque dentro de un modelo prueba ganancia incremental; que los meses reutilizados se volvieron independientes. No se infiere mala conducta de resultados exploratorios documentados.

## 4. Fallas y fortalezas propias: acciones concretas

| Hallazgo | Acción de cierre |
|---|---|
| Buena trazabilidad de v4–v7, definiciones y políticas | Preservar código ejecutado y manifiestos; copiar referencias inmutables a v8 |
| V1 parcial y privados antiguos no certificados | No borrar sus originales; inventariar y recuperar antes de futuras limpiezas |
| Octubre y agosto reutilizados | Rotular la nueva comparación como exploratoria temporal; no prometer significancia confirmatoria |
| Semillas no sustituyen meses | Tres calendarios móviles comunes; informar ambos tipos de variación por separado |
| Ratios y tendencias tienen señales pero cambian por contexto | Probar solo B0/R3/R4/T4; no otro catálogo de 27 brazos |
| Saneamiento discutido sin autoridad suficiente | Mantener decisiones históricas; registrar ceros y anomalías sin máscaras nuevas |
| Disco lleno tras entrenar v7 | Una matriz por vez; estimación de picos y margen antes de arrancar; checkpoints y cierre desacoplado |
| Copia interrumpida por timeout/apagado | Transferencia reanudable, verificación y estados de recuperación explícitos; apagado con límite independiente |
| Comunicación confundió «enviado», «entrenando» y «terminado» | Estado verificable: preparado, ajuste iniciado, ajustes completos, evaluación completa, respaldo verificado, VM detenida |

## 5. Limpieza: alcance autorizado y verificable

Conservar dataset, modelos, predicciones, fuentes, parámetros, métricas, logs, manifiestos y versiones de entorno. No borrar C1/C3 ni v1–v6 por tamaño. El `.tmp` de C1 que no coincidió con su supuesto original se conserva.

El limpiador preparado elimina únicamente matrices derivadas de la corrida v7 `120354`, después de verificar respaldos fuera de la VM, modelos originales y cierre de octubre. Registra hash/tamaño antes de eliminar, rechaza enlaces y actividad de entrenamiento, y apaga al terminar. **Es una limpieza acotada, no una declaración de que todos los demás archivos son necesarios o innecesarios.** Los archivos sin evidencia suficiente quedan protegidos.

La sesión local no tiene cuenta activa de gcloud y la herramienta de navegador disponible no permite escribir en la terminal. Por ello esta revisión no ejecutó el limpiador ni volvió a encender la VM. No atribuir ahorro de espacio a una acción todavía pendiente. El procedimiento completo está en `herramientas/limpiar_matrices_v7.py`.

## 6. Último experimento y segunda competencia

La pregunta útil pendiente es: **¿una receta histórica corta mantiene su ventaja cuando avanza el calendario, a igual presupuesto de contactos?** No necesitamos repetir la búsqueda de todas las familias. El [prompt v8](../../HISTORIA_2019_01/v8/prompts/PROMPT_MAESTRO_V8.md) propone cuatro recetas congeladas, tres meses y cinco semillas nuevas: 60 ajustes. Usa hiperparámetros propios ya elegidos en v7, con modelos nuevos; no mezcla modelos antiguos con nuevos.

Eso compara recetas completas transferidas en el tiempo, no efecto puro de variables con capacidad idéntica. Las recetas conservan sus fórmulas y su búsqueda previa; no se afirma que sean óptimas para cada ventana. El calendario móvil es una adaptación de la consigna, que se presenta separada del resultado oficial anterior. La ventaja práctica se evalúa con regla fija; ninguna significancia corrige retrospectivamente toda la exploración v1–v7.

Para la segunda competencia, el principal valor adicional es operativo: el mismo módulo de features en lote y mensual, etiquetas verificadas con horizonte completo, dos estrategias, salida atómica, reintentos, medición y monitoreo. El recorrido 202001–202006 sirve como prueba operativa con recetas congeladas si es exigido por la entrega; 2020 no se usa para elegir variables ni representa estabilidad económica general. El texto oficial completo de esa entrega aún debe cotejarse: los 15 minutos y las columnas provienen del diseño conversado, no del mensaje de Zulip reproducido.

**No se garantiza ganar.** Un resultado negativo bien medido cierra la pregunta y habilita B0 oficial más R3 exploratorio. No abrir automáticamente v9 para buscar otra victoria.
