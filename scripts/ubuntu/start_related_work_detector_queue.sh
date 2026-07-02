#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-related-work-detector-queue}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

mkdir -p outputs/logs/related_work_detectors outputs/experiments

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' SEEDS='${SEEDS:-42,123,2026}' EPOCHS='${EPOCHS:-100}' PATIENCE='${PATIENCE:-5}' IMGSZ='${IMGSZ:-1280}' BATCH='${BATCH:-4}' DATA_YAML='${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}' WAIT_FOR_SESSION='${WAIT_FOR_SESSION:-}' WAIT_FOR_SESSIONS='${WAIT_FOR_SESSIONS:-}' RELATED_WORK_GPU='${RELATED_WORK_GPU:-0}' CSFPR_IMGSZ='${CSFPR_IMGSZ:-1280}' LEAF_IMGSZ='${LEAF_IMGSZ:-1280}' CSFPR_BATCH='${CSFPR_BATCH:-1}' LEAF_BATCH='${LEAF_BATCH:-4}' RUN_TRAINING='${RUN_TRAINING:-1}' bash scripts/ubuntu/run_related_work_detector_queue.sh; exec bash"

echo "Started related-work detector queue: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: outputs/logs/related_work_detectors/queue.log"
echo "Queue CSV: outputs/experiments/related_work_detector_queue.csv"
