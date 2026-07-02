#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

BASE_SESSION=${BASE_SESSION:-server-p2-compression}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
SEED=${SEED:-123}

start_worker() {
  local gpu="$1"
  local ablation="$2"
  local session="${BASE_SESSION}-gpu${gpu}-${ablation}"

  if tmux has-session -t "$session" 2>/dev/null; then
    echo "tmux session already exists: $session"
    echo "Attach: tmux attach -t $session"
    return 0
  fi

  tmux new-session -d -s "$session" -n train \
    "cd '$PWD' && TARGET_GPU='$gpu' ABLATION='$ablation' SEED='$SEED' CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_yolov11_p2_compression_worker.sh; exec bash"
  echo "Started $session"
  echo "Attach: tmux attach -t $session"
}

start_worker 0 p2_compress_v3_tiny_frelu
start_worker 1 p2_efficient_v3_tiny_frelu

echo
echo "Monitor:"
echo "  /home/oem/projects/multi-uav-marine-city/scripts/ubuntu/watch_live_training_scoreboard.sh"
echo "Logs:"
echo "  outputs/logs/server_yolov11_p2_compression/"
