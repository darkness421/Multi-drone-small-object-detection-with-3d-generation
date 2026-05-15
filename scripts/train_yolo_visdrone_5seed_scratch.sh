#!/usr/bin/env bash
set -euo pipefail

EPOCHS=${1:-100}
DEVICE=${2:-0}
BATCH=${3:-8}
IMGSZ=${4:-1280}

cd "$(dirname "$0")/.."

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$PWD/.cache/ultralytics}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"

python -m scripts.check_training_readiness --data-yaml configs/detector/visdrone_yolo_data.yaml --strict

python -m detectors.train_yolo_multiseed \
  --model yolo11n.pt \
  --method YOLOv11n \
  --dataset VisDrone2019-DET \
  --dataset-slug visdrone \
  --data-yaml configs/detector/visdrone_yolo_data.yaml \
  --epochs "$EPOCHS" \
  --imgsz "$IMGSZ" \
  --batch "$BATCH" \
  --device "$DEVICE" \
  --seeds 0,1,2,3,4 \
  --roc-auc \
  --project outputs/detectors \
  --out-dir outputs/experiments/multiseed
