#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Train detector baseline with config: ${CONFIG}"
echo "TODO: wire to Ultralytics/MMDetection training once dataset paths are fixed."

