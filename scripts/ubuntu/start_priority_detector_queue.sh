#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SESSION=${SESSION:-priority-detector-queue}

mkdir -p outputs/logs/priority_detector_queue outputs/experiments/priority_detector_queue

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_priority_detector_queue.sh; exec bash"

echo "Started priority detector queue: $SESSION"
echo "Attach with: tmux attach -t $SESSION"
echo "Log: outputs/logs/priority_detector_queue/queue.log"
echo "Decisions: outputs/experiments/priority_detector_queue/decisions.tsv"
