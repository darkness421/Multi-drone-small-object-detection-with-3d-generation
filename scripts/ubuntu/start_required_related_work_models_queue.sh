#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-required-related-work-models-gpu0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/required_related_work_models}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n gpu0 \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' GPU='${GPU:-0}' SEEDS='${SEEDS:-42,123,2026}' EPOCHS='${EPOCHS:-100}' PATIENCE='${PATIENCE:-5}' BATCH='${BATCH:-4}' IMG_SIZE='${IMG_SIZE:-1280}' bash scripts/ubuntu/run_required_related_work_models_queue.sh; exec bash"

echo "Started required related-work model queue: $SESSION"
echo "Required set: CSFPR-RTDETR, MFFSODNet, SFFEF-YOLO, BPD-YOLO, UAVDet, HF-D-FINE"
echo "GPU: ${GPU:-0}"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
