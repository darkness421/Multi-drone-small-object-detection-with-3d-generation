#!/usr/bin/env bash
set -euo pipefail

INPUT=${1:-datasets/converters/dummy_marinecity_input.json}
OUT=${2:-outputs/experiments/marinecity_multiview_benchmark.json}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

cd "$(dirname "$0")/../.."

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_marinecity_multiview_benchmark \
  --input "$INPUT" \
  --out "$OUT" \
  --val-angles "${VAL_ANGLES:-side_view}" \
  --test-angles "${TEST_ANGLES:-rear_oblique,right_oblique}"
