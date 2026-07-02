#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-paper-artifacts-after-2d}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/paper_artifacts_after_2d}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n artifacts \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' WAIT_FOR_FINAL_2D='${WAIT_FOR_FINAL_2D:-1}' WAIT_FOR_RELATED_WORK='${WAIT_FOR_RELATED_WORK:-1}' bash scripts/ubuntu/run_paper_artifacts_after_2d.sh; exec bash"

echo "Started paper artifact refresh queue: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
