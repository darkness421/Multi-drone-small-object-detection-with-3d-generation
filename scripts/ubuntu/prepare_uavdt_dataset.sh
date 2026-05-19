#!/usr/bin/env bash
set -euo pipefail

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SOURCE=${SOURCE:-}
RAW_ROOT=${RAW_ROOT:-data/raw/UAVDT}
COCO_OUT=${COCO_OUT:-data/processed/uavdt_coco.json}
YOLO_OUT=${YOLO_OUT:-data/processed/uavdt_yolo}
SUMMARY=${SUMMARY:-outputs/experiments/uavdt_prepare_summary.json}
COPY_IMAGES=${COPY_IMAGES:-1}
STRICT=${STRICT:-0}

cd "$(dirname "$0")/../.."

args=(
  --raw-root "$RAW_ROOT"
  --coco-out "$COCO_OUT"
  --yolo-out "$YOLO_OUT"
  --summary "$SUMMARY"
)

if [[ -n "$SOURCE" ]]; then
  args+=(--source "$SOURCE")
fi
if [[ "$COPY_IMAGES" == "1" ]]; then
  args+=(--copy-images)
fi
if [[ "$STRICT" == "1" ]]; then
  args+=(--strict)
fi

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.prepare_uavdt_dataset "${args[@]}"

echo "== UAVDT readiness =="
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready \
  --paths-config configs/paths.ubuntu.yaml \
  --data-yaml configs/detector/uavdt_yolo_data.yaml
