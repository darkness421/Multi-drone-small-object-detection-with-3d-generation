#!/usr/bin/env bash
set -euo pipefail

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/server_baseline_summary.csv}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/detector_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/detector_stage_gate.md}

cd "$(dirname "$0")/../.."

conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.detector_stage_gate \
  --summary-csv "$SUMMARY_CSV" \
  --out-json "$STAGE_GATE_JSON" \
  --out-md "$STAGE_GATE_MD" \
  "$@"

echo "Stage gate JSON: $STAGE_GATE_JSON"
echo "Stage gate report: $STAGE_GATE_MD"
