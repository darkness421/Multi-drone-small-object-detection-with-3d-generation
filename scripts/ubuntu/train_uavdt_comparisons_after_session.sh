#!/usr/bin/env bash
set -euo pipefail

WAIT_FOR=${WAIT_FOR:-server-large-comparison,server-top3-proposed-pending}
POLL_SECONDS=${POLL_SECONDS:-300}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
EPOCHS=${EPOCHS:-100}
IMGSZ=${IMGSZ:-1280}
SEEDS=${SEEDS:-42,123,2026}
DATA_YAML=${DATA_YAML:-configs/detector/uavdt_yolo_data.yaml}
DATASET_TAG=${DATASET_TAG:-uavdt}
PROJECT=${PROJECT:-outputs/detectors/server_uavdt_baselines}
EXPERIMENT_ROOT=${EXPERIMENT_ROOT:-outputs/experiments/uavdt}
LOG_DIR=${LOG_DIR:-outputs/logs/server_uavdt_baselines}
CHECK_MODELS=${CHECK_MODELS:-1}

YOLO_SESSION=${YOLO_SESSION:-server-uavdt-yolo-comparison}
YOLO_MODELS=${YOLO_MODELS:-yolov8s.pt,yolo12s.pt,yolo11s.pt,yolov9s.pt,yolov10s.pt,yolo26s.pt}
YOLO_BATCH=${YOLO_BATCH:-8}

RTDETR_SESSION=${RTDETR_SESSION:-server-uavdt-rtdetr-comparison}
RTDETR_MODELS=${RTDETR_MODELS:-rtdetr-l.pt}
RTDETR_BATCH=${RTDETR_BATCH:-2}

cd "$(dirname "$0")/../.."

wait_for_session() {
  local session=$1
  session=${session//[[:space:]]/}
  if [[ -z "$session" ]]; then
    return
  fi
  while tmux has-session -t "$session" 2>/dev/null; do
    echo "Waiting for tmux session to finish: $session at $(date -Is)"
    sleep "$POLL_SECONDS"
  done
}

wait_for_sessions() {
  local sessions=$1
  local session
  IFS=',' read -r -a session_list <<< "$sessions"
  for session in "${session_list[@]}"; do
    wait_for_session "$session"
  done
}

check_uavdt_ready() {
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready \
    --paths-config configs/paths.ubuntu.yaml \
    --data-yaml "$DATA_YAML" \
    --strict
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
    echo "Starting $session on UAVDT with models=$models seeds=$SEEDS batch=$batch at $(date -Is)"
    MODELS="$models" SEEDS="$SEEDS" DATA_YAML="$DATA_YAML" DATASET_TAG="$DATASET_TAG" PROJECT="$PROJECT" EXPERIMENT_ROOT="$EXPERIMENT_ROOT" LOG_DIR="$LOG_DIR" CONDA_ENV="$CONDA_ENV" \
      bash scripts/ubuntu/train_visdrone_baselines_tmux.sh "$session" "$EPOCHS" "$batch" "$IMGSZ"
  fi
  wait_for_session "$session"
}

wait_for_sessions "$WAIT_FOR"

if ! check_uavdt_ready; then
  echo ""
  echo "UAVDT is not ready. Prepare it first, for example:"
  echo "  SOURCE=/path/to/UAVDT bash scripts/ubuntu/prepare_uavdt_dataset.sh"
  echo "Then rerun:"
  echo "  bash scripts/ubuntu/train_uavdt_comparisons_after_session.sh"
  exit 1
fi

start_and_wait "$YOLO_SESSION" "$YOLO_MODELS" "$YOLO_BATCH"
start_and_wait "$RTDETR_SESSION" "$RTDETR_MODELS" "$RTDETR_BATCH"

echo "UAVDT comparison sweep complete at $(date -Is)"
echo "Collect with a UAVDT-specific detector root, e.g.:"
  echo "  DETECTOR_ROOT=$PROJECT RESULTS_CSV=outputs/experiments/uavdt_baseline_results.csv SUMMARY_CSV=outputs/experiments/uavdt_baseline_summary.csv PVALUES_CSV=outputs/experiments/uavdt_baseline_pvalues.csv DASHBOARD=outputs/reports/uavdt_baseline_dashboard.png bash scripts/ubuntu/collect_server_results.sh"
