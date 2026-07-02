#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-remaining-experiments-queue}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

mkdir -p outputs/logs/remaining_experiments_queue outputs/experiments/remaining_experiments_queue

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_remaining_experiments_queue.sh; exec bash"

echo "Started remaining experiments queue: $SESSION"
echo "Attach with: tmux attach -t $SESSION"
echo "Log: outputs/logs/remaining_experiments_queue/queue.log"
echo "Plan: outputs/experiments/remaining_experiments_queue/remaining_queue_plan.tsv"
