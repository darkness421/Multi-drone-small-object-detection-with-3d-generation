#!/usr/bin/env bash
set -euo pipefail

WAIT_FOR=${WAIT_FOR:-server-additional-comparisons-pending}
POLL_SECONDS=${POLL_SECONDS:-300}
SESSION=${SESSION:-server-paper-yolo-comparison}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
EPOCHS=${EPOCHS:-100}
IMGSZ=${IMGSZ:-1280}
SEEDS=${SEEDS:-42,123,2026}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/server_baselines}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}
RESTART_VIEWER=${RESTART_VIEWER:-1}
VIEWER_SESSION=${VIEWER_SESSION:-server-live-viewer}
VIEWER_PORT=${VIEWER_PORT:-8766}
CHECK_MODELS=${CHECK_MODELS:-1}

YOLOV10_ADDITIONS=${YOLOV10_ADDITIONS:-yolov10n.pt}
LRDS_MODELS=${LRDS_MODELS:-weights/lrds-yolo.pt,lrds-yolo.pt}
MODELS=${MODELS:-$YOLOV10_ADDITIONS,$LRDS_MODELS}
BATCH=${BATCH:-8}

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
    print(f"Checking paper comparison model availability: {model}", file=sys.stderr, flush=True)
    try:
        YOLO(model)
    except Exception as exc:
        print(f"Skipping unavailable paper comparison model {model}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    else:
        available.append(model)
print(",".join(available))
PY
}

wait_for_session "$WAIT_FOR"

available_models=$(filter_available_models "$MODELS" | tail -n 1)
if [[ -z "$available_models" ]]; then
  echo "No paper comparison models are available to run."
  echo "Requested: $MODELS"
  echo "For LRDS-YOLO, place a loadable checkpoint at weights/lrds-yolo.pt or set LRDS_MODELS=/path/to/checkpoint.pt."
  exit 0
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
else
  echo "Starting $SESSION with models=$available_models seeds=$SEEDS batch=$BATCH at $(date -Is)"
  MODELS="$available_models" SEEDS="$SEEDS" DATA_YAML="$DATA_YAML" PROJECT="$PROJECT" LOG_DIR="$LOG_DIR" \
    CONDA_ENV="$CONDA_ENV" RUN_EVAL="$RUN_EVAL" ROC_AUC="$ROC_AUC" DATASET_TAG=visdrone \
    bash scripts/ubuntu/train_visdrone_baselines_tmux.sh "$SESSION" "$EPOCHS" "$BATCH" "$IMGSZ"
fi

restart_viewer "$SESSION"
wait_for_session "$SESSION"

echo "Paper comparison additions complete at $(date -Is)"
echo "Collect results with: bash scripts/ubuntu/collect_server_results.sh"
