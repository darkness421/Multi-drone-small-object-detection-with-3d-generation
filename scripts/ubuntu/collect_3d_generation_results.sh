#!/usr/bin/env bash
set -euo pipefail

RESULTS_DIR=${1:-outputs/experiments/3d_generation}
OUT=${2:-outputs/experiments/3d_generation_comparison.csv}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

cd "$(dirname "$0")/../.."

conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.generative3d_compare --results-dir "$RESULTS_DIR" --out "$OUT"
python scripts/build_marinecity_3d_results_table.py
python scripts/check_marinecity_3d_completion_readiness.py
python scripts/check_external_gate_capabilities.py
python scripts/check_paper_artifact_readiness.py
python scripts/build_accv_remaining_gates_queue.py
echo "3D generation comparison: $OUT"
