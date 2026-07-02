#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
BASE_SESSION=${BASE_SESSION:-server-nms-sweep}

mkdir -p outputs/logs/nms_sweep

start_worker() {
  local gpu="$1"
  local model_set="$2"
  local session="${BASE_SESSION}-gpu${gpu}-${model_set}"

  if tmux has-session -t "$session" 2>/dev/null; then
    echo "tmux session already exists: $session"
    echo "Attach with: tmux attach -t $session"
    return 0
  fi

  tmux new-session -d -s "$session" -n nms \
    "cd '$PWD' && GPU='$gpu' MODEL_SET='$model_set' CONDA_ENV='$CONDA_ENV' bash scripts/ubuntu/run_best_detector_nms_sweep_worker.sh; exec bash"
  echo "Started $session"
  echo "Attach: tmux attach -t $session"
}

start_worker 0 efficient
start_worker 1 accuracy

echo
echo "Logs:"
echo "  outputs/logs/nms_sweep/efficient_gpu0.log"
echo "  outputs/logs/nms_sweep/accuracy_gpu1.log"
