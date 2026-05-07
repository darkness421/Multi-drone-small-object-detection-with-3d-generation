#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Evaluate detector baseline with config: ${CONFIG}"
echo "TODO: compute AP, AP50, AP75, APsmall, FPS, Params, GFLOPs."

