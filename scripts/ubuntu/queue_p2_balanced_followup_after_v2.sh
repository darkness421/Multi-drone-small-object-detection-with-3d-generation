#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

WAIT_SESSIONS=${WAIT_SESSIONS:-server-p2-balanced-v2-gpu0,server-p2-balanced-v2-gpu1}
POLL_SECONDS=${POLL_SECONDS:-60}
PROJECT=${PROJECT:-outputs/detectors/server_yolov11_p2_balanced_followup}
LOG_DIR=${LOG_DIR:-outputs/logs/server_yolov11_p2_balanced_followup}

echo "P2 balanced follow-up queue started at $(date -Is)"
echo "Waiting for sessions: $WAIT_SESSIONS"
echo "Poll interval: ${POLL_SECONDS}s"

while true; do
  active=0
  IFS=',' read -r -a sessions <<< "$WAIT_SESSIONS"
  for session in "${sessions[@]}"; do
    session=${session//[[:space:]]/}
    if [[ -n "$session" ]] && tmux has-session -t "$session" 2>/dev/null; then
      active=1
      break
    fi
  done
  [[ "$active" == "0" ]] && break
  echo "Still waiting at $(date -Is)"
  sleep "$POLL_SECONDS"
done

echo "Launching follow-up experiments at $(date -Is)"

tmux new-session -d -s server-p2-balanced-followup-gpu0 \
  "TARGET_GPU=0 SEED=2026 ABLATION=p2_balanced_tiny_frelu MODEL_YAML=configs/detector/yolo11l-p2-balanced.yaml PROJECT=$PROJECT LOG_DIR=$LOG_DIR bash scripts/ubuntu/start_yolov11_p2_balanced_search.sh"

tmux new-session -d -s server-p2-balanced-followup-gpu1 \
  "TARGET_GPU=1 SEED=42 ABLATION=p2_balanced_wavelet_tiny_frelu MODEL_YAML=configs/detector/yolo11l-p2-balanced.yaml PROJECT=$PROJECT LOG_DIR=$LOG_DIR bash scripts/ubuntu/start_yolov11_p2_balanced_search.sh"

echo "Queued jobs:"
echo "  GPU0: P2Balanced-FR seed2026"
echo "  GPU1: P2Balanced-WaveFR seed42"
