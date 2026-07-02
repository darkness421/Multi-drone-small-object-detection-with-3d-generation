#!/usr/bin/env bash
set -euo pipefail

WAIT_FOR=${WAIT_FOR:-server-top3-seed5}
POLL_SECONDS=${POLL_SECONDS:-300}
EPOCHS=${EPOCHS:-100}
IMGSZ=${IMGSZ:-1280}
SEEDS=${SEEDS:-42,123,2026}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}
RESTART_VIEWER=${RESTART_VIEWER:-1}
VIEWER_SESSION=${VIEWER_SESSION:-server-live-viewer}
VIEWER_PORT=${VIEWER_PORT:-8766}

NANO_SESSION=${NANO_SESSION:-server-extra-comparison-nano}
# Reviewer-facing YOLO scale coverage. Ultralytics does not expose identical
# n/s/m/l names for every generation, so CHECK_MODELS filters unavailable
# checkpoints before launch. For YOLOv9, t/s/m/c are the practical scale
# anchors kept for the fair sweep when n/l are not loadable.
NANO_MODELS=${NANO_MODELS:-yolov5nu.pt,yolov8n.pt,yolov9t.pt,yolov10n.pt,yolo11n.pt,yolo12n.pt,yolo26n.pt}
NANO_BATCH=${NANO_BATCH:-8}

SMALL_SESSION=${SMALL_SESSION:-server-extra-comparison-small}
SMALL_MODELS=${SMALL_MODELS:-yolov5su.pt,yolov8s.pt,yolov9s.pt,yolov10s.pt,yolo11s.pt,yolo12s.pt,yolo26s.pt}
OPTIONAL_LEGACY_MODELS=${OPTIONAL_LEGACY_MODELS:-yolov6s.pt,yolov7.pt}
SMALL_BATCH=${SMALL_BATCH:-8}
CHECK_MODELS=${CHECK_MODELS:-1}

MEDIUM_SESSION=${MEDIUM_SESSION:-server-extra-comparison-medium}
MEDIUM_MODELS=${MEDIUM_MODELS:-yolov5mu.pt,yolov8m.pt,yolov9m.pt,yolov10m.pt,yolo11m.pt,yolo12m.pt,yolo26m.pt}
MEDIUM_BATCH=${MEDIUM_BATCH:-4}

LARGE_SESSION=${LARGE_SESSION:-server-extra-comparison-large}
LARGE_MODELS=${LARGE_MODELS:-yolov5lu.pt,yolov8l.pt,yolov9c.pt,yolov10l.pt,yolo11l.pt,yolo12l.pt,yolo26l.pt,rtdetr-l.pt}
LARGE_BATCH=${LARGE_BATCH:-2}

cd "$(dirname "$0")/../.."
ROOT=$PWD

wait_for_session() {
  local session=$1
  if [[ -z "$session" ]]; then
    return
  fi
  while tmux has-session -t "$session" 2>/dev/null; do
    echo "Waiting for tmux session to finish: $session at $(date -Is)"
    sleep "$POLL_SECONDS"
  done
}

restart_viewer() {
  local training_session=$1
  if [[ "$RESTART_VIEWER" != "1" ]]; then
    return
  fi
  tmux kill-session -t "$VIEWER_SESSION" 2>/dev/null || true
  tmux new-session -d -s "$VIEWER_SESSION" \
    "cd '$ROOT' && python scripts/ubuntu/live_training_viewer.py --host 0.0.0.0 --port '$VIEWER_PORT' --training-session '$training_session'"
}

filter_available_models() {
  local models=$1
  if [[ "$CHECK_MODELS" != "1" || -z "$models" ]]; then
    echo "$models"
    return
  fi
  MODELS_TO_CHECK="$models" conda run --no-capture-output -n "$CONDA_ENV" python - <<'PY'
import os
import sys

from ultralytics import YOLO

models = [item.strip() for item in os.environ["MODELS_TO_CHECK"].split(",") if item.strip()]
available = []
for model in models:
    print(f"Checking model availability: {model}", file=sys.stderr, flush=True)
    try:
        YOLO(model)
    except Exception as exc:
        print(f"Skipping unavailable model {model}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    else:
        available.append(model)
print(",".join(available))
PY
}

start_and_wait() {
  local session=$1
  local models=$2
  local batch=$3
  models=$(filter_available_models "$models" | tail -n 1)
  if [[ -z "$models" ]]; then
    echo "No available models for session: $session"
    return
  fi
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "tmux session already exists: $session"
    echo "Attach with: tmux attach -t $session"
  else
    echo "Starting $session with models=$models seeds=$SEEDS batch=$batch at $(date -Is)"
    MODELS="$models" SEEDS="$SEEDS" CONDA_ENV="$CONDA_ENV" RUN_EVAL="$RUN_EVAL" ROC_AUC="$ROC_AUC" GPU_LIST="${GPU_LIST:-0,1}" \
      bash scripts/ubuntu/train_visdrone_baselines_tmux.sh "$session" "$EPOCHS" "$batch" "$IMGSZ"
  fi
  restart_viewer "$session"
  wait_for_session "$session"
}

wait_for_session "$WAIT_FOR"
start_and_wait "$NANO_SESSION" "$NANO_MODELS" "$NANO_BATCH"
start_and_wait "$SMALL_SESSION" "$SMALL_MODELS,$OPTIONAL_LEGACY_MODELS" "$SMALL_BATCH"
start_and_wait "$MEDIUM_SESSION" "$MEDIUM_MODELS" "$MEDIUM_BATCH"
start_and_wait "$LARGE_SESSION" "$LARGE_MODELS" "$LARGE_BATCH"

echo "Expanded comparison sweep complete at $(date -Is)"
echo "Collect results with: bash scripts/ubuntu/collect_server_results.sh"
