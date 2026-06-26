#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-marinecity-viewer160-pipeline}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/marinecity_viewer160_pipeline}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n viewer160 \
  "cd '$PWD' && \
   CONDA_ENV='$CONDA_ENV' \
   CONTAINER_NAME='${CONTAINER_NAME:-isaac-sim-gui-uav-marinecity}' \
   CONTAINER_USER='${CONTAINER_USER:-1234:1234}' \
   HOST_UAV_ROOT='${HOST_UAV_ROOT:-/home/oem/UAV/uav_marinecity}' \
   CONTAINER_UAV_ROOT='${CONTAINER_UAV_ROOT:-/workspace/uav_marinecity}' \
   ISAAC_GPU='${ISAAC_GPU:-0}' \
   CAPTURE_USE_ACTOR_SESSION='${CAPTURE_USE_ACTOR_SESSION:-1}' \
   CAPTURE_BASE_STAGE='${CAPTURE_BASE_STAGE:-uavmarine.usd}' \
   CAPTURE_WIDTH='${CAPTURE_WIDTH:-1280}' \
   CAPTURE_HEIGHT='${CAPTURE_HEIGHT:-720}' \
   CAPTURE_OPEN_WARMUP='${CAPTURE_OPEN_WARMUP:-600}' \
   CAPTURE_RENDER_WARMUP='${CAPTURE_RENDER_WARMUP:-120}' \
   CAPTURE_HEADLESS='${CAPTURE_HEADLESS:-1}' \
   CAPTURE_CAMERA_PROFILE='${CAPTURE_CAMERA_PROFILE:-viewer160}' \
   FORCE_RECAPTURE='${FORCE_RECAPTURE:-0}' \
   FORCE_DETECTOR='${FORCE_DETECTOR:-0}' \
   FORCE_REASONER='${FORCE_REASONER:-0}' \
   DETECTOR_DEVICE='${DETECTOR_DEVICE:-cpu}' \
   DETECTOR_CONF='${DETECTOR_CONF:-0.01}' \
   DETECTOR_CONF_SLUG='${DETECTOR_CONF_SLUG:-conf001}' \
   DETECTOR_IMGSZ='${DETECTOR_IMGSZ:-1280}' \
   AEROGRAPH_COMMAND='${AEROGRAPH_COMMAND:-}' \
   OPENAI_API_KEY='${OPENAI_API_KEY:-}' \
   REASONER_PROVIDER='${REASONER_PROVIDER:-}' \
   LOG_DIR='$LOG_DIR' \
   bash scripts/ubuntu/run_marinecity_viewer160_pipeline_queue.sh; exec bash"

echo "Started MarineCity viewer160 pipeline queue: $SESSION"
echo "Policy: real Cesium MarineCity only; no fake/proxy city fallback."
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
echo "Status: outputs/experiments/marinecity_viewer160_pipeline_status.md"
echo "Dashboard: outputs/reports/live/marinecity_simulation_dashboard.png"
