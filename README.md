# Repositorio central de experimentos

**Entrada principal:** [índice de Historia v1–v8, C3 y antecedentes](INDICE_EXPERIMENTOS.md).

Se consolidó el material publicable de `ClariRZ/Segunda_competencia`, preservando las versiones discrepantes y documentando los artefactos privados. [Alcance y comprobación](informes/consolidacion_repos_2026-11-15/README.md). Los apartados que siguen conservan documentación histórica y no sustituyen el índice actual.

# Experimentos — Historia 2019

Repositorio de evidencias y reproducción del experimento `experimento_2026-11-13`, originalmente conservado en `ClariRZ/Segunda_competencia`.

## Estado verificable

- Copia exacta de los 53 archivos enumerados en el manifiesto original, con commit de procedencia registrado.
- 25 modelos identificados por SHA256: los hashes ya estaban en el protocolo de octubre. No confundir identificación con respaldo de los archivos de modelo.
- Calibrador original recuperado, con SHA256 idéntico al registrado en la corrida.
- Protocolo completo de octubre recuperado, incluidas las cinco listas de columnas; SHA256 idéntico al original de Cloud Shell.
- 14 pruebas locales aprobadas: diez originales y cuatro controles adicionales.
- **No se ha completado una reproducción independiente con el dataset real. No se garantiza igualdad de resultados entre entornos sin verificarla.**

[Experimento e instrucciones originales](experimento_2026-11-13/README.md) · [Auditoría y pendientes](auditoria_trazabilidad_2026-11-13/INFORME.md)

## Verificar evidencias

```bash
python herramientas/verificar_trazabilidad.py
```

Para comprobar archivos privados recuperados, sin publicarlos ni entrenar:

```bash
python herramientas/verificar_trazabilidad.py \
  --modelos /ruta/completa_20261111_03/private \
  --protocolo /ruta/protocolo_congelado.json \
  --dataset /ruta/analistasr_competencia_2026.csv.gz
```

El verificador falla ante archivos ausentes, modelos distintos, columnas distintas o un dataset diferente. La salida declara por separado cada comprobación. El dataset, las matrices, las predicciones individuales y los modelos permanecen fuera de Git.

## Reproducción independiente

Usar otra carpeta o máquina, el dataset con el hash esperado y el entorno fijado. Seguir las etapas `entrenar`, `verificar-agosto`, `octubre` y `verificar-octubre` documentadas en el experimento. Conservar la salida completa y el entorno real de la reproducción. Si difiere, registrar el fallo: no cambiar tolerancias ni recetas para hacer coincidir resultados.

Una reproducción numérica no exige necesariamente archivos de modelo idénticos byte a byte. Para restaurar los modelos originales, en cambio, verificar sus hashes. No atribuir al entorno original versiones observadas hoy que no se registraron durante la corrida.

La preparación v5 es un experimento distinto y no se ejecuta desde este repositorio como parte de la auditoría v4.

## Cierre v1–v7 y propuesta siguiente (14/11/2026)

- [Inventario, fallas, fortalezas y comparación actual con Ezequiel](informes/cierre_v1_v7_2026-11-14/INFORME.md).
- [Prompt v8: cuatro recetas y tres ventanas, todavía sin ejecutar](HISTORIA_2019_01/v8/prompts/PROMPT_MAESTRO_V8.md).
- [Limpieza acotada y verificada de matrices v7](herramientas/limpiar_matrices_v7.py): ejecutar en Cloud Shell con `--apply`; no elimina modelos, predicciones ni archivos de v1–v6. Comprueba los dos respaldos conocidos antes de encender la VM, limita la sesión y apaga al terminar. Sus ocho pruebas son sintéticas; la limpieza real sigue pendiente.
