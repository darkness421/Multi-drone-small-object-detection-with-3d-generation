#!/usr/bin/env bash
set -euo pipefail

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SOURCE=${SOURCE:-}
DOWNLOAD_DIR=${DOWNLOAD_DIR:-data/raw/downloads}
RAW_ROOT=${RAW_ROOT:-data/raw/VisDrone2019-DET}
APPLY_STAGE=${APPLY_STAGE:-1}
SKIP_DOWNLOAD=${SKIP_DOWNLOAD:-0}
SKIP_EXTRACT=${SKIP_EXTRACT:-0}
SKIP_CONVERT=${SKIP_CONVERT:-0}

cd "$(dirname "$0")/../.."

echo "== CoM3D-ACE VisDrone dataset preparation =="
echo "CONDA_ENV=$CONDA_ENV"
echo "RAW_ROOT=$RAW_ROOT"
echo "DOWNLOAD_DIR=$DOWNLOAD_DIR"

if [[ -n "$SOURCE" ]]; then
  echo "== Stage from source: $SOURCE =="
  stage_args=(--source "$SOURCE" --raw-root "$RAW_ROOT")
  if [[ "$APPLY_STAGE" == "1" ]]; then
    stage_args+=(--apply)
  fi
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.stage_visdrone_dataset "${stage_args[@]}"
else
  echo "== No SOURCE provided; skipping local staging dry-run/copy =="
fi

download_args=(--download-dir "$DOWNLOAD_DIR" --raw-root "$RAW_ROOT")
if [[ "$SKIP_DOWNLOAD" == "1" ]]; then
  download_args+=(--skip-download)
fi
if [[ "$SKIP_EXTRACT" == "1" ]]; then
  download_args+=(--skip-extract)
fi

echo "== Download/extract check =="
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.download_visdrone "${download_args[@]}"

if [[ "$SKIP_CONVERT" != "1" ]]; then
  echo "== Convert configured datasets to COCO/YOLO =="
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.convert_datasets
fi

echo "== Training preflight =="
bash scripts/ubuntu/preflight_baseline.sh
