#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
RAW_ROOT=${RAW_ROOT:-data/raw/TinyPerson}
YOLO_OUT=${YOLO_OUT:-data/processed/tinyperson_yolo}
SUMMARY=${SUMMARY:-outputs/experiments/tinyperson_prepare_summary.json}

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.prepare_tinyperson_dataset \
  --raw-root "$RAW_ROOT" \
  --yolo-out "$YOLO_OUT" \
  --summary "$SUMMARY"

echo "TinyPerson YOLO data prepared at $YOLO_OUT"
echo "Summary: $SUMMARY"
