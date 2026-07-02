#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

TARGET_GPU=${TARGET_GPU:-0}
ABLATIONS=${ABLATIONS:-"p2_wavelet_frelu"}
LOG_DIR=${LOG_DIR:-outputs/logs/server_yolov11_p2_module_search}
mkdir -p "$LOG_DIR"

lane_log="$LOG_DIR/lane_gpu${TARGET_GPU}.log"

echo "[$(date -Is)] P2-FR module lane started on GPU${TARGET_GPU}: $ABLATIONS" | tee -a "$lane_log"
for ablation in $ABLATIONS; do
  echo "[$(date -Is)] Starting $ablation on GPU${TARGET_GPU}" | tee -a "$lane_log"
  if TARGET_GPU="$TARGET_GPU" ABLATION="$ablation" bash scripts/ubuntu/run_p2fr_module_worker.sh; then
    echo "[$(date -Is)] Finished $ablation on GPU${TARGET_GPU}" | tee -a "$lane_log"
  else
    echo "[$(date -Is)] FAILED $ablation on GPU${TARGET_GPU}; continuing lane" | tee -a "$lane_log"
  fi
done
echo "[$(date -Is)] P2-FR module lane finished on GPU${TARGET_GPU}" | tee -a "$lane_log"
