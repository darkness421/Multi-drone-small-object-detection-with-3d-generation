#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-tinyperson-eval-imgsz-sweep-gpu0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_eval_imgsz_sweep}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n eval-sweep \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' GPU='$GPU' bash scripts/ubuntu/run_tinyperson_eval_imgsz_sweep.sh; exec bash"

echo "Started TinyPerson eval-only input-size sweep: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
