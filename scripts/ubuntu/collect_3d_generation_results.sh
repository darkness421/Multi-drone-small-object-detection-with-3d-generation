#!/usr/bin/env bash
set -euo pipefail

RESULTS_DIR=${1:-outputs/experiments/3d_generation}
OUT=${2:-outputs/experiments/3d_generation_comparison.csv}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

cd "$(dirname "$0")/../.."

conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.generative3d_compare --results-dir "$RESULTS_DIR" --out "$OUT"
echo "3D generation comparison: $OUT"
