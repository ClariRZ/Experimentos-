#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PARENT=/home/clara-m-rodr-guez/experimento_historicas_20261107
PY="$PARENT/.venv/bin/python"
"$PY" src/ratios_intrames.py
"$PY" -m pip freeze > requirements_vm.txt
"$PY" src/preparar.py --c1 "$PARENT/data/c1_bucket.parquet" --c2 "$PARENT/data/competencia_02_crudo.parquet" --parent-prep "$PARENT/preparado" --out preparado
"$PY" src/entrenar.py --mode b6 --prep preparado --out resultados --parent "$PARENT"
"$PY" src/entrenar.py --mode c3 --prep preparado --out resultados --parent "$PARENT"
date -Is > COMPLETADO.txt
