#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python_bin=.venv/bin/python
"$python_bin" -m unittest discover -s src -p 'test_*.py'
sha256sum -c data.sha256
.venv/bin/pip freeze > requirements_vm.txt
"$python_bin" src/auditar.py --data data/competencia_02_crudo.parquet --out auditoria
"$python_bin" src/preparar.py --data data/competencia_02_crudo.parquet --out preparado
"$python_bin" src/entrenar.py --prep preparado --out piloto --config config_piloto.json --mode pilot
