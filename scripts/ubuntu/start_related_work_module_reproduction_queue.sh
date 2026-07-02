#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-related-work-module-repro-gpu0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/related_work_module_reproductions}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n gpu0 \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_related_work_module_reproduction_queue.sh; exec bash"

echo "Started related-work module reproduction queue: $SESSION"
echo "Policy: LEAF-YOLO excluded; YOLO11s-UAV public snippets are run as module reproduction only."
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
