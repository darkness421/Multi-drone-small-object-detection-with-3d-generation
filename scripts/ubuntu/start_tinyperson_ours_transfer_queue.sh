#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-tinyperson-ours-transfer-gpu0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_640_transfer}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n transfer \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' GPU='$GPU' bash scripts/ubuntu/run_tinyperson_ours_transfer_queue.sh; exec bash"

echo "Started TinyPerson Ours transfer queue: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
