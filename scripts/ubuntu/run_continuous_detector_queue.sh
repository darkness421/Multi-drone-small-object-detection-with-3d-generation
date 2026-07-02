#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/continuous_detector_queue}
GPU_CONFIRM=${GPU_CONFIRM:-0}
GPU_EVAL=${GPU_EVAL:-0}
mkdir -p "$LOG_DIR"

queue_log="$LOG_DIR/queue.log"

log() {
  echo "[$(date -Is)] $*" | tee -a "$queue_log"
}

wait_for_marker() {
  local label="$1"
  local file="$2"
  local marker="$3"
  local fail_marker="${4:-TRAIN_FAILED}"

  log "Waiting for $label marker: $marker"
  while true; do
    if [[ -f "$file" ]] && grep -q "$fail_marker" "$file"; then
      log "$label failed marker found in $file"
      return 1
    fi
    if [[ -f "$file" ]] && grep -q "$marker" "$file"; then
      log "$label completed"
      return 0
    fi
    sleep 60
  done
}

compression_log_a="outputs/logs/server_yolov11_p2_compression/proposed_p2_compress_v3_tiny_frelu_yolo11l_visdrone_yolov11_p2_compression_seed123.log"
compression_log_b="outputs/logs/server_yolov11_p2_compression/proposed_p2_efficient_v3_tiny_frelu_yolo11l_visdrone_yolov11_p2_compression_seed123.log"

log "Continuous detector queue started"
log "Stage 0: wait for current compression experiments"
wait_for_marker "P2CompV3-FR-s123" "$compression_log_a" "P2 compression job finished"
wait_for_marker "P2EffV3-FR-s123" "$compression_log_b" "P2 compression job finished"

log "Stage 1: train P2BalV2-FR seed2026 confirmation on GPU${GPU_CONFIRM}"
TARGET_GPU="$GPU_CONFIRM" \
ABLATION="p2_balanced_v2_tiny_frelu" \
SEED="2026" \
CONDA_ENV="$CONDA_ENV" \
PROJECT="outputs/detectors/server_yolov11_p2_balanced_v2" \
LOG_DIR="outputs/logs/server_yolov11_p2_balanced_v2" \
MODEL_YAML="configs/detector/yolo11l-p2-balanced-v2.yaml" \
bash scripts/ubuntu/start_yolov11_p2_balanced_search.sh

log "Stage 2: eval P2BalV2 seeds with class-aware NMS iou=0.55"
GPU="$GPU_EVAL" CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/eval_p2balv2_nms055.sh

log "Stage 3: collect reports, supplementary artifacts, qualitative examples, and MarineCity readiness"
CONDA_ENV="$CONDA_ENV" GPU="$GPU_EVAL" bash scripts/ubuntu/run_detector_poststage_artifacts.sh

log "Stage 4: queue finished. Next manual decision: lock detector or launch real 3D generator integration."
