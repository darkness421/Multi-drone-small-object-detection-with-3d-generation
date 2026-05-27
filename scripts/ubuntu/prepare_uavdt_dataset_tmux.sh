#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-uavdt-data-prep}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
SOURCE=${SOURCE:-}
RAW_ROOT=${RAW_ROOT:-data/raw/UAVDT}
COCO_OUT=${COCO_OUT:-data/processed/uavdt_coco.json}
YOLO_OUT=${YOLO_OUT:-data/processed/uavdt_yolo}
SUMMARY=${SUMMARY:-outputs/experiments/uavdt_prepare_summary.json}
COPY_IMAGES=${COPY_IMAGES:-0}
LINK_IMAGES=${LINK_IMAGES:-1}
STRICT=${STRICT:-0}

cd "$(dirname "$0")/../.."

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Run scripts/ubuntu/prepare_uavdt_dataset.sh directly."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 1
fi

mkdir -p "$LOG_DIR"
log_file="$LOG_DIR/${SESSION}.log"
tmux new-session -d -s "$SESSION" -n prepare \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' SOURCE='$SOURCE' RAW_ROOT='$RAW_ROOT' COCO_OUT='$COCO_OUT' YOLO_OUT='$YOLO_OUT' SUMMARY='$SUMMARY' COPY_IMAGES='$COPY_IMAGES' LINK_IMAGES='$LINK_IMAGES' STRICT='$STRICT' bash scripts/ubuntu/prepare_uavdt_dataset.sh 2>&1 | tee '$log_file'"

echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
