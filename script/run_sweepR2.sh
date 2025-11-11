#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TSV_PATH="R2_sweep.tsv"
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <params.json or inline JSON>" >&2
  exit 1
fi

JSON_ARG="$1"
BCS_PNG="rr_bcs.png"
SWEEP_PNG="rr_sweep.png"

"$REPO_ROOT/cmake-build-release/main_SweepR2" --params "$JSON_ARG" --out "$TSV_PATH"

UV_PYTHON_DIR="$SCRIPT_DIR/.venv"
uv venv "$UV_PYTHON_DIR"
uv pip install --python "$UV_PYTHON_DIR/bin/python" -r "$SCRIPT_DIR/requirements.txt"
source "$UV_PYTHON_DIR/bin/activate"

python "$SCRIPT_DIR/plot_rr_sweep_bcs.py" --in "$TSV_PATH" --out "$BCS_PNG"
python "$SCRIPT_DIR/plot_rr_sweep.py" --in "$TSV_PATH" --out "$SWEEP_PNG"
