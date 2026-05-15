#!/usr/bin/env bash
set -euo pipefail

STRICT=${1:-}

cd "$(dirname "$0")/../.."

ARGS=(--paths-config configs/paths.ubuntu.yaml)
if [[ "$STRICT" == "--strict" || "$STRICT" == "strict" ]]; then
  ARGS+=(--strict)
fi

python -m scripts.check_dataset_ready "${ARGS[@]}"
