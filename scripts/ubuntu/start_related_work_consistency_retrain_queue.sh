#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-related-work-consistency-1280}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/related_work_consistency}

mkdir -p "$LOG_DIR" outputs/experiments

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' SEEDS='${SEEDS:-42,123,2026}' EPOCHS='${EPOCHS:-100}' PATIENCE='${PATIENCE:-5}' IMGSZ='${IMGSZ:-1280}' CSFPR_GPU='${CSFPR_GPU:-1}' CSFPR_BATCH='${CSFPR_BATCH:-1}' MFFSOD_GPU='${MFFSOD_GPU:-1}' MFFSOD_BATCH='${MFFSOD_BATCH:-2}' WAIT_FOR_FINAL_2D='${WAIT_FOR_FINAL_2D:-1}' bash scripts/ubuntu/run_related_work_consistency_retrain_queue.sh; exec bash"

echo "Started strict Sec. 2.1 related-work consistency queue: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
echo "Queue CSV: outputs/experiments/related_work_1280_consistency_queue.csv"
