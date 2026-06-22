#!/usr/bin/env bash
set -euo pipefail

EPOCHS=${1:-100}
MODEL=${2:-yolo11n.pt}
DEVICE=${3:-0}
BATCH=${4:-8}
IMGSZ=${5:-1280}

cd "$(dirname "$0")/.."

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$PWD/.cache/ultralytics}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"

python -m scripts.check_training_readiness --data-yaml configs/detector/visdrone_yolo_data.yaml --strict

python -m detectors.train_yolo train \
  --model "$MODEL" \
  --data-yaml configs/detector/visdrone_yolo_data.yaml \
  --epochs "$EPOCHS" \
  --imgsz "$IMGSZ" \
  --batch "$BATCH" \
  --device "$DEVICE" \
  --project outputs/detectors \
  --name "${MODEL%.pt}_visdrone"
