#!/usr/bin/env bash
set -euo pipefail

STRICT=${1:-}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

cd "$(dirname "$0")/../.."

ARGS=(--paths-config configs/paths.ubuntu.yaml)
if [[ "$STRICT" == "--strict" || "$STRICT" == "strict" ]]; then
  ARGS+=(--strict)
fi

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready "${ARGS[@]}"
