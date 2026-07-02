#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
IMGSZ=${IMGSZ:-1280}
BATCH=${BATCH:-1}
WORKERS=${WORKERS:-4}
LOG_DIR=${LOG_DIR:-outputs/logs/related_work_detectors}
PROJECT=${PROJECT:-outputs/detectors/related_work_detectors}
NAME=${NAME:-csfpr_rtdetr_visdrone_eval_img${IMGSZ}}

mkdir -p "$LOG_DIR" "$PROJECT"
log_file="$LOG_DIR/${NAME}.log"

echo "[$(date -Is)] Starting CSFPR-RTDETR eval on GPU${GPU}" | tee "$log_file"
MPLCONFIGDIR="$PWD/.cache/matplotlib" \
YOLO_CONFIG_DIR="$PWD/.cache/ultralytics" \
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.eval_csfpr_rtdetr \
  --device "$GPU" \
  --imgsz "$IMGSZ" \
  --batch "$BATCH" \
  --workers "$WORKERS" \
  --project "../../$PROJECT" \
  --name "$NAME" 2>&1 | tee -a "$log_file"
echo "[$(date -Is)] Finished CSFPR-RTDETR eval" | tee -a "$log_file"
