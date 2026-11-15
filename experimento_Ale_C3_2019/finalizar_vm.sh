#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PARENT=/home/clara-m-rodr-guez/experimento_historicas_20261107
PY="$PARENT/.venv/bin/python"
while [ ! -f COMPLETADO.txt ]; do
  if grep -q '^Traceback' corrida.log; then
    echo 'Entrenamiento falló; revisar corrida.log. No generar informe.'
    exit 1
  fi
  sleep 20
done
"$PY" src/verificar.py --root . --parent "$PARENT"
MPLCONFIGDIR=/tmp/ale-c3-mpl "$PY" src/informe.py --root .
"$PY" src/exportar.py --root .
date -Is > ENTREGA_VERIFICADA.txt
