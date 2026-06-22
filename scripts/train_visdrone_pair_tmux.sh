#!/usr/bin/env bash
set -euo pipefail

EPOCHS=${1:-100}
BATCH=${2:-8}
IMGSZ=${3:-1280}
SESSION=${4:-visdrone-baselines}

cd "$(dirname "$0")/.."

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Open two terminals and run scripts/train_yolo_visdrone.sh manually."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 1
fi

COMMON_PREFIX="cd '$PWD' && export MPLCONFIGDIR='$PWD/.cache/matplotlib' YOLO_CONFIG_DIR='$PWD/.cache/ultralytics'"
YOLO11_CMD="$COMMON_PREFIX && CUDA_VISIBLE_DEVICES=0 conda run --no-capture-output -n com3d-ace ./scripts/train_yolo_visdrone.sh '$EPOCHS' yolo11n.pt 0 '$BATCH' '$IMGSZ'"
YOLOV8_CMD="$COMMON_PREFIX && CUDA_VISIBLE_DEVICES=1 conda run --no-capture-output -n com3d-ace ./scripts/train_yolo_visdrone.sh '$EPOCHS' yolov8n.pt 0 '$BATCH' '$IMGSZ'"

tmux new-session -d -s "$SESSION" -n yolo11n "$YOLO11_CMD"
tmux new-window -t "$SESSION" -n yolov8n "$YOLOV8_CMD"

echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Windows: yolo11n on physical GPU 0, yolov8n on physical GPU 1"
