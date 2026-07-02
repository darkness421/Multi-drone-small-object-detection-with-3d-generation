#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

REFRESH=${REFRESH:-5}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.watch_live_training_scoreboard --refresh "$REFRESH"
