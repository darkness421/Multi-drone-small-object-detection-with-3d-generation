#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Run ambiguity evaluation with config: ${CONFIG}"
echo "TODO: load object hypotheses and compute AUROC/AUPRC/ECE/Brier."

