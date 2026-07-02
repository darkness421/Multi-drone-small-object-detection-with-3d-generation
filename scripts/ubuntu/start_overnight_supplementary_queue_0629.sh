#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-accv-overnight-supp-0629}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}

mkdir -p outputs/logs/overnight_supplementary_0629 outputs/experiments/overnight_supplementary_0629

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$PWD' && GPU='$GPU' CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_overnight_supplementary_queue_0629.sh; exec bash"

echo "Started overnight supplementary queue: $SESSION"
echo "Attach with: tmux attach -t $SESSION"
echo "Log: outputs/logs/overnight_supplementary_0629/queue.log"
echo "Plan: outputs/experiments/overnight_supplementary_0629/plan.csv"
