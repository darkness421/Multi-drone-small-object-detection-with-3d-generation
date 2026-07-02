#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-continuous-detector-queue}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

mkdir -p outputs/logs/continuous_detector_queue

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_continuous_detector_queue.sh; exec bash"

echo "Started continuous detector queue: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: outputs/logs/continuous_detector_queue/queue.log"
