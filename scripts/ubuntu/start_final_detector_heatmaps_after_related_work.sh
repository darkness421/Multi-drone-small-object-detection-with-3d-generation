#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-final-detector-heatmaps-after-related-work}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/final_detector_heatmaps}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n heatmaps \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' WAIT_FOR_2D='${WAIT_FOR_2D:-1}' WAIT_FOR_RELATED_WORK='${WAIT_FOR_RELATED_WORK:-1}' bash scripts/ubuntu/run_final_detector_heatmaps_after_related_work.sh; exec bash"

echo "Started final detector heatmap queue: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
