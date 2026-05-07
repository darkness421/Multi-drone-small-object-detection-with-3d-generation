#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Run re-observation policy comparison with config: ${CONFIG}"
echo "TODO: compare no-reobserve, random, uncertainty-based, and CoM3D policy."

