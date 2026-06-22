#!/usr/bin/env bash
set -euo pipefail

IMAGES_DIR=${1:-data/processed/visdrone_yolo/images/val}
shift || true
WEIGHTS=("$@")

cd "$(dirname "$0")/../.."

if [[ ${#WEIGHTS[@]} -eq 0 ]]; then
  echo "Usage: $0 <images-dir> <weight1.pt> [weight2.pt ...]"
  exit 2
fi

python -m evaluation.qualitative_examples \
  --images-dir "$IMAGES_DIR" \
  --weights "${WEIGHTS[@]}" \
  --out-dir outputs/qualitative/detection_examples \
  --max-images "${MAX_IMAGES:-12}" \
  --imgsz "${IMGSZ:-1280}" \
  --device "${DEVICE:-0}"
