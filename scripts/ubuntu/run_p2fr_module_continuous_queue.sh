#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

LOG_DIR=${LOG_DIR:-outputs/logs/server_yolov11_p2_module_queue}
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
      log "$label failed marker found in $file; continuing queue anyway"
      return 0
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

log "P2-FR-s123 module queue started"
log "Stage 0: wait for current compression jobs so we do not fight for VRAM"
wait_for_marker "P2CompV3-FR-s123" "$compression_log_a" "P2 compression job finished"
wait_for_marker "P2EffV3-FR-s123" "$compression_log_b" "P2 compression job finished"

log "Stage 1: launch P2-FR-s123 family module search"
log "GPU0 queue: wavelet+FReLU, SE+FReLU, deformable+FReLU"
log "GPU1 queue: CBAM+FReLU, wavelet+CBAM+FReLU, DCT+FReLU"

TARGET_GPU=0 ABLATIONS="p2_wavelet_frelu p2_se_frelu p2_deform_frelu" bash scripts/ubuntu/run_p2fr_module_lane.sh &
pid0=$!
TARGET_GPU=1 ABLATIONS="p2_cbam_frelu p2_wavelet_cbam_frelu p2_dct_frelu" bash scripts/ubuntu/run_p2fr_module_lane.sh &
pid1=$!

wait "$pid0"
wait "$pid1"

log "Stage 2: module search finished. Rank with live scoreboard and NMS scoreboard."
