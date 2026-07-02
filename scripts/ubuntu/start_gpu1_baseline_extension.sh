#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

RUN_ID=${RUN_ID:-gpu1_baseline_extension_$(date +%Y%m%d_%H%M%S)}
SESSION=${SESSION:-server-gpu1-baseline-extension}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPUS=${GPUS:-1}
SEEDS=${SEEDS:-7,3407}
EPOCHS=${EPOCHS:-100}
IMGSZ=${IMGSZ:-1280}
WORKERS=${WORKERS:-4}

# Extend the strongest large anchors beyond the official 3-seed baseline.
# These are baseline-only jobs, not proposed-module jobs.
MODEL_SPECS=${MODEL_SPECS:-yolo11l.pt:2,yolo12l.pt:2,yolov8l.pt:2}

PROJECT=${PROJECT:-outputs/detectors/server_fresh_baselines/$RUN_ID}
EXPERIMENT_ROOT=${EXPERIMENT_ROOT:-outputs/experiments/server_fresh/$RUN_ID}
LOG_DIR=${LOG_DIR:-outputs/logs/server_fresh_baselines/$RUN_ID}
REPORT_DIR=${REPORT_DIR:-outputs/reports/server_fresh_baselines/$RUN_ID}

STOP_EXISTING=${STOP_EXISTING:-0}
MONITOR_SESSION=${MONITOR_SESSION:-server-gpu1-baseline-monitor}
DUAL_VIEW_SESSION=${DUAL_VIEW_SESSION:-server-gpu1-baseline-view}
VIEWER_SESSION=${VIEWER_SESSION:-server-gpu1-baseline-live-viewer}
VIEWER_PORT=${VIEWER_PORT:-8777}

DATASET_TAG=${DATASET_TAG:-visdrone_large_gpu1}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}
CHECK_MODELS=${CHECK_MODELS:-1}
RESOURCE_GUARD=${RESOURCE_GUARD:-1}
USE_CUDA_VISIBLE_DEVICES=${USE_CUDA_VISIBLE_DEVICES:-0}
MIN_FREE_GB=${MIN_FREE_GB:-60}
MAX_DISK_USE_PERCENT=${MAX_DISK_USE_PERCENT:-94}
MIN_RAM_GB=${MIN_RAM_GB:-16}
MIN_GPU_FREE_GB=${MIN_GPU_FREE_GB:-8}
GUARD_WAIT_SECONDS=${GUARD_WAIT_SECONDS:-120}

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
PROJECT="$PROJECT" \
EXPERIMENT_ROOT="$EXPERIMENT_ROOT" \
LOG_DIR="$LOG_DIR" \
REPORT_DIR="$REPORT_DIR" \
STOP_EXISTING="$STOP_EXISTING" \
MONITOR_SESSION="$MONITOR_SESSION" \
DUAL_VIEW_SESSION="$DUAL_VIEW_SESSION" \
VIEWER_SESSION="$VIEWER_SESSION" \
VIEWER_PORT="$VIEWER_PORT" \
RUN_EVAL="$RUN_EVAL" \
ROC_AUC="$ROC_AUC" \
CHECK_MODELS="$CHECK_MODELS" \
RESOURCE_GUARD="$RESOURCE_GUARD" \
USE_CUDA_VISIBLE_DEVICES="$USE_CUDA_VISIBLE_DEVICES" \
MIN_FREE_GB="$MIN_FREE_GB" \
MAX_DISK_USE_PERCENT="$MAX_DISK_USE_PERCENT" \
MIN_RAM_GB="$MIN_RAM_GB" \
MIN_GPU_FREE_GB="$MIN_GPU_FREE_GB" \
GUARD_WAIT_SECONDS="$GUARD_WAIT_SECONDS" \
bash scripts/ubuntu/restart_fresh_server_queue.sh

cat <<EOF

GPU1 baseline extension started.

Session:       $SESSION
Detector root: $PROJECT
Experiment:    $EXPERIMENT_ROOT

To include this root in the 24h orchestrator collection:
  EXTRA_BASELINE_ROOTS=$PROJECT
  BASELINE_WAIT_SESSIONS=server-large-comparison,$SESSION
EOF
