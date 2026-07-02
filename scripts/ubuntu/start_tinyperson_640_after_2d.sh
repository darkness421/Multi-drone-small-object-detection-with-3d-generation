#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-tinyperson-640-after-2d-gpu0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_640}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n gpu0 \
  "cd '$PWD' && CONDA_ENV='$CONDA_ENV' GPU='${GPU:-0}' SEEDS='${SEEDS:-42}' EPOCHS='${EPOCHS:-100}' PATIENCE='${PATIENCE:-5}' BATCH='${BATCH:-16}' IMG_SIZE='${IMG_SIZE:-640}' RUN_STRONG_YOLO_BASELINE='${RUN_STRONG_YOLO_BASELINE:-1}' RUN_EXTRA_TOP_BASELINES='${RUN_EXTRA_TOP_BASELINES:-1}' RUN_CORE_ABLATION='${RUN_CORE_ABLATION:-0}' WAIT_FOR_2D='${WAIT_FOR_2D:-1}' WAIT_FOR_RELATED_WORK='${WAIT_FOR_RELATED_WORK:-1}' WAIT_FOR_UAVDET='${WAIT_FOR_UAVDET:-1}' WAIT_FOR_HEATMAP='${WAIT_FOR_HEATMAP:-1}' bash scripts/ubuntu/run_tinyperson_640_after_2d.sh"

echo "Started TinyPerson 640 core-model queue: $SESSION"
echo "Policy: waits for final 2D ablation, related-work 1280, and final detector heatmaps before training."
echo "Core models: Ours, YOLOv11l, YOLOv9c, YOLOv8l, YOLOv9m."
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
