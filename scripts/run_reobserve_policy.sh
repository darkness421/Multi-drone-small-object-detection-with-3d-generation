#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/com3d_ace_base.yaml}
echo "Run re-observation policy comparison with config: ${CONFIG}"
python -m evaluation.reobservation_ablation --out paper/tables/reobservation_policy_ablation.csv
echo "TODO: replace template rows with measured no-reobserve, random, density-crop, uncertainty, information-gain, and CoM3D policy results."
