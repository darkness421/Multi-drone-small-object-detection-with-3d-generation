#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
LIMIT=${LIMIT:-5}

conda run --no-capture-output -n "$CONDA_ENV" \
  python -m scripts.watch_nms_sweep_scoreboard --limit "$LIMIT"
