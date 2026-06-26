#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-final-detector-input-resolution-gpu0}
LOG_DIR=${LOG_DIR:-outputs/logs/final_input_resolution_sweep}
mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session already running: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" \
  "GPU=${GPU:-0} CONDA_ENV=${CONDA_ENV:-com3d-ace} bash scripts/ubuntu/run_final_detector_input_resolution_sweep.sh"

echo "Started final detector input-resolution eval-only sweep in tmux session: $SESSION"
echo "Attach with: tmux attach -t $SESSION"
echo "Log: outputs/logs/final_input_resolution_sweep/queue.log"
echo "Plan: outputs/experiments/final_input_resolution_sweep/plan.csv"
echo "Status: outputs/experiments/final_input_resolution_sweep/status.csv"
