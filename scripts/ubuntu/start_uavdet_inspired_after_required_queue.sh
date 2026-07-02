#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-uavdet-inspired-after-required-gpu0}
GPU=${GPU:-0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
SEEDS=${SEEDS:-42,123,2026}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-4}
IMG_SIZE=${IMG_SIZE:-1280}

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  tmux capture-pane -pt "$SESSION" -S -20 || true
  exit 0
fi

tmux new-session -d -s "$SESSION" \
  "GPU=$GPU CONDA_ENV=$CONDA_ENV SEEDS=$SEEDS EPOCHS=$EPOCHS PATIENCE=$PATIENCE BATCH=$BATCH IMG_SIZE=$IMG_SIZE bash scripts/ubuntu/run_uavdet_inspired_after_required_queue.sh"

echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
