#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT=${REPO_ROOT:-/home/oem/projects/multi-uav-marine-city}
SESSION=${SESSION:-accv-morning-3d-sim-0629}
GPU=${GPU:-0}
ENV_NAME=${ENV_NAME:-marinecity-nerfstudio}
CONDA_ENV=${CONDA_ENV:-com3d-ace}

cd "$REPO_ROOT"

mkdir -p outputs/logs/morning_3d_sim_queue_0629 outputs/experiments/morning_3d_sim_queue_0629

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n queue \
  "cd '$REPO_ROOT' && GPU='$GPU' ENV_NAME='$ENV_NAME' CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_morning_3d_sim_queue_0629.sh; exec bash"

echo "Started morning 3D/simulation queue: $SESSION"
echo "Attach with: tmux attach -t $SESSION"
echo "Log: outputs/logs/morning_3d_sim_queue_0629/queue.log"
echo "Plan: outputs/experiments/morning_3d_sim_queue_0629/plan.csv"
