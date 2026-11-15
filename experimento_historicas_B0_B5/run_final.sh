#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sha256sum -c data.sha256
.venv/bin/python -m unittest discover -s src -p 'test_*.py'
.venv/bin/python src/entrenar.py --prep preparado --out resultados --config config.json --mode train
.venv/bin/python src/entrenar.py --prep preparado --out resultados --config config.json --mode evaluate
