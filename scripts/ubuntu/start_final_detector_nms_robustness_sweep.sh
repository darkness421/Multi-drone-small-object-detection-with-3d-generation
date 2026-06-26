#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-final-detector-nms-robustness-gpu0}
GPU=${GPU:-0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

mkdir -p outputs/logs/final_nms_robustness_sweep outputs/experiments/final_nms_robustness_sweep

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n nms \
  "cd '$PWD' && GPU='$GPU' CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_final_detector_nms_robustness_sweep.sh; exec bash"

echo "Started final detector NMS robustness sweep: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: outputs/logs/final_nms_robustness_sweep/queue.log"
echo "Plan: outputs/experiments/final_nms_robustness_sweep/plan.csv"
echo "Status: outputs/experiments/final_nms_robustness_sweep/status.csv"
