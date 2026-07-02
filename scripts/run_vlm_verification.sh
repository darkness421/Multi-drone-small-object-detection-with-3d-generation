#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Run selective AeroGraph VLM verification with config: ${CONFIG}"
python -m evaluation.vlm_ablation --out paper/tables/selective_vlm_ablation.csv
echo "TODO: replace template rows with measured no-VLM, always-on, random, uncertainty-triggered, and AeroGraph-triggered VLM results."
