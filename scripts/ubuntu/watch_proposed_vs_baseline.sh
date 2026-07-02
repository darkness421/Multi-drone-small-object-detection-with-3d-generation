#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

INTERVAL=${INTERVAL:-15}
PROJECT_DIR=${PROJECT_DIR:-outputs/detectors/server_yolov11_p2_next_step,outputs/detectors/server_yolov11_p2_confirm}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/server_with_proposed/server_with_proposed_summary.csv}
BASELINE_METHOD=${BASELINE_METHOD:-YOLOv11l}
TARGET_REL_IMPROVEMENT=${TARGET_REL_IMPROVEMENT:-0.015}
OVERPASS_REL_IMPROVEMENT=${OVERPASS_REL_IMPROVEMENT:-0.001}
SAME_PARAMS_TOLERANCE=${SAME_PARAMS_TOLERANCE:-0.01}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

while true; do
  clear || true
  date -Is
  echo ""
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits \
      | awk -F, '{gsub(/^ +| +$/, "", $1); gsub(/^ +| +$/, "", $2); gsub(/^ +| +$/, "", $3); gsub(/^ +| +$/, "", $4); gsub(/^ +| +$/, "", $5); printf "GPU%s  %s  mem=%s/%s MiB  util=%s%%\n", $1, $2, $3, $4, $5}'
    echo ""
  fi
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.watch_proposed_vs_baseline \
    --project-dir "$PROJECT_DIR" \
    --summary-csv "$SUMMARY_CSV" \
    --baseline-method "$BASELINE_METHOD" \
    --target-rel-improvement "$TARGET_REL_IMPROVEMENT" \
    --overpass-rel-improvement "$OVERPASS_REL_IMPROVEMENT" \
    --same-params-tolerance "$SAME_PARAMS_TOLERANCE"
  echo ""
  echo "Refresh interval: ${INTERVAL}s"
  sleep "$INTERVAL"
done
