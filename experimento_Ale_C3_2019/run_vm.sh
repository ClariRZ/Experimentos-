#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PARENT=/home/clara-m-rodr-guez/experimento_historicas_20261107
PY="$PARENT/.venv/bin/python"
"$PY" -m pip freeze > requirements_vm.txt
"$PY" src/test_reglas.py
"$PY" src/preparar.py --parent "$PARENT" --data "$PARENT/data/competencia_02_crudo.parquet"
"$PY" src/ejecutar.py --parent "$PARENT" --mode train
"$PY" src/ejecutar.py --parent "$PARENT" --mode evaluate
date -Is > COMPLETADO.txt
