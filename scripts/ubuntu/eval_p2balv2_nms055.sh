#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
IMGSZ=${IMGSZ:-1280}
WORKERS=${WORKERS:-4}
SOURCE_PROJECT=${SOURCE_PROJECT:-outputs/detectors/server_yolov11_p2_balanced_v2}
PROJECT=${PROJECT:-outputs/detectors/nms_confirm_p2balv2}
LOG_DIR=${LOG_DIR:-outputs/logs/nms_confirm_p2balv2}

mkdir -p "$PROJECT" "$LOG_DIR"
log_file="$LOG_DIR/eval_p2balv2_nms055_gpu${GPU}.log"

echo "[P2BalV2 NMS0.55 eval] started at $(date -Is)" | tee -a "$log_file"
echo "GPU=$GPU SOURCE_PROJECT=$SOURCE_PROJECT PROJECT=$PROJECT" | tee -a "$log_file"

for seed in 42 123 2026; do
  run_dir=$(find "$SOURCE_PROJECT" -maxdepth 1 -type d -name "*p2_balanced_v2_tiny_frelu*seed${seed}" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  weight="${run_dir:-}/ultralytics/weights/best.pt"
  if [[ -z "${run_dir:-}" || ! -f "$weight" ]]; then
    echo "[skip] missing P2BalV2 seed${seed} weight under $SOURCE_PROJECT" | tee -a "$log_file"
    continue
  fi

  echo "[eval] seed=${seed} weight=$weight" | tee -a "$log_file"
  conda run --no-capture-output -n "$CONDA_ENV" \
    python -m detectors.train_yolo eval \
    --model "$weight" \
    --data-yaml "$DATA_YAML" \
    --imgsz "$IMGSZ" \
    --workers "$WORKERS" \
    --device "$GPU" \
    --conf 0.001 \
    --iou 0.55 \
    --method "P2BalV2-FR-s${seed}+nms055" \
    --ablation "p2_balanced_v2_tiny_frelu+nms055" \
    --base-model yolo11l.pt \
    --proposed-module "p2_balanced_v2_head+tiny_frelu_neck+nms055" \
    --implementation-status implemented \
    --project "$PROJECT" \
    --name "eval_p2balv2_seed${seed}_nms055" 2>&1 | tee -a "$log_file"
done

echo "[P2BalV2 NMS0.55 eval] finished at $(date -Is)" | tee -a "$log_file"
