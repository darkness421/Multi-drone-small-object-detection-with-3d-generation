#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-tinyperson-corner-original-gpu0}
GPU=${GPU:-0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_corner_original}
mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' GPU='$GPU' SEEDS='${SEEDS:-42}' EPOCHS='${EPOCHS:-100}' PATIENCE='${PATIENCE:-5}' BATCH='${BATCH:-8}' IMG_SIZE='${IMG_SIZE:-1280}' bash scripts/ubuntu/run_tinyperson_corner_original_queue.sh; exec bash"

echo "Started TinyPerson corner/original-window queue: $SESSION"
echo "Attach with: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
