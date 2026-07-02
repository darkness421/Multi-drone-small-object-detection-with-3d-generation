#!/usr/bin/env bash
set -euo pipefail

WAIT_FOR=${WAIT_FOR:-server-proposed-ablation}
POLL_SECONDS=${POLL_SECONDS:-300}
SESSION=${SESSION:-server-large-comparison}
RUN_ID=${RUN_ID:-large_$(date +%Y%m%d_%H%M%S)}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
DATASET_TAG=${DATASET_TAG:-visdrone_large}
EPOCHS=${EPOCHS:-100}
IMGSZ=${IMGSZ:-1280}
SEEDS=${SEEDS:-42,123,2026}
GPUS=${GPUS:-0}
WORKERS=${WORKERS:-4}
CHECK_MODELS=${CHECK_MODELS:-1}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}

# L-size anchors for paper defense. Batch is conservative for 1280px training.
# Keep RT-DETR-L here too because the current baseline only has partial seed coverage.
# YOLOv9-c is the largest YOLOv9 anchor kept in the fair paper-facing sweep.
MODEL_SPECS=${MODEL_SPECS:-yolov5lu.pt:2,yolov8l.pt:2,yolov9c.pt:2,yolov10l.pt:2,yolo11l.pt:2,yolo12l.pt:2,yolo26l.pt:2,rtdetr-l.pt:2}

STOP_EXISTING=${STOP_EXISTING:-0}
RESOURCE_GUARD=${RESOURCE_GUARD:-1}
MIN_FREE_GB=${MIN_FREE_GB:-100}
MAX_DISK_USE_PERCENT=${MAX_DISK_USE_PERCENT:-92}
MIN_RAM_GB=${MIN_RAM_GB:-16}
MIN_GPU_FREE_GB=${MIN_GPU_FREE_GB:-8}
GUARD_WAIT_SECONDS=${GUARD_WAIT_SECONDS:-120}

cd "$(dirname "$0")/../.."

wait_for_session() {
  local session=$1
  [[ -z "$session" ]] && return
  while tmux has-session -t "$session" 2>/dev/null; do
    echo "Waiting for tmux session to finish before large comparison: $session at $(date -Is)"
    sleep "$POLL_SECONDS"
  done
}

wait_for_session "$WAIT_FOR"

RUN_ID="$RUN_ID" \
SESSION="$SESSION" \
CONDA_ENV="$CONDA_ENV" \
DATA_YAML="$DATA_YAML" \
DATASET_TAG="$DATASET_TAG" \
EPOCHS="$EPOCHS" \
IMGSZ="$IMGSZ" \
SEEDS="$SEEDS" \
GPUS="$GPUS" \
WORKERS="$WORKERS" \
MODEL_SPECS="$MODEL_SPECS" \
CHECK_MODELS="$CHECK_MODELS" \
RUN_EVAL="$RUN_EVAL" \
ROC_AUC="$ROC_AUC" \
STOP_EXISTING="$STOP_EXISTING" \
RESOURCE_GUARD="$RESOURCE_GUARD" \
MIN_FREE_GB="$MIN_FREE_GB" \
MAX_DISK_USE_PERCENT="$MAX_DISK_USE_PERCENT" \
MIN_RAM_GB="$MIN_RAM_GB" \
MIN_GPU_FREE_GB="$MIN_GPU_FREE_GB" \
GUARD_WAIT_SECONDS="$GUARD_WAIT_SECONDS" \
bash scripts/ubuntu/restart_fresh_server_queue.sh
