#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$PWD/.cache/ultralytics}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"

python -m scripts.check_env --paths-config configs/paths.ubuntu.yaml
