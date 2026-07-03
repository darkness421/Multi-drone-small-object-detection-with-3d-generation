#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-marinecity-targeted-reobs}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/marinecity_targeted_reobservation}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Log: $LOG_DIR/queue.log"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n targeted-reobs \
  "cd '$PWD' && \
   SESSION='$SESSION' \
   CONDA_ENV='$CONDA_ENV' \
   CONTAINER_NAME='${CONTAINER_NAME:-isaac-sim-gui-uav-marinecity}' \
   CONTAINER_USER='${CONTAINER_USER:-1234:1234}' \
   HOST_UAV_ROOT='${HOST_UAV_ROOT:-/home/oem/UAV/uav_marinecity}' \
   CONTAINER_UAV_ROOT='${CONTAINER_UAV_ROOT:-/workspace/uav_marinecity}' \
   ISAAC_GPU='${ISAAC_GPU:-0}' \
   CAPTURE_WIDTH='${CAPTURE_WIDTH:-1280}' \
   CAPTURE_HEIGHT='${CAPTURE_HEIGHT:-720}' \
   CAPTURE_OPEN_WARMUP='${CAPTURE_OPEN_WARMUP:-600}' \
   CAPTURE_RENDER_WARMUP='${CAPTURE_RENDER_WARMUP:-120}' \
   CAPTURE_HEADLESS='${CAPTURE_HEADLESS:-1}' \
   CAPTURE_BASE_STAGE='${CAPTURE_BASE_STAGE:-uavmarine.usd}' \
   CAPTURE_CAMERA_PROFILE='${CAPTURE_CAMERA_PROFILE:-viewer160}' \
   DETECTOR_DEVICE='${DETECTOR_DEVICE:-cpu}' \
   DETECTOR_CONF='${DETECTOR_CONF:-0.01}' \
   DETECTOR_CONF_SLUG='${DETECTOR_CONF_SLUG:-conf001}' \
   DETECTOR_IMGSZ='${DETECTOR_IMGSZ:-1280}' \
   FORCE_RECAPTURE='${FORCE_RECAPTURE:-0}' \
   FORCE_DETECTOR='${FORCE_DETECTOR:-0}' \
   WEIGHTS='${WEIGHTS:-outputs/detectors/server_yolov11_p2p4_balanced/20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt}' \
   LOG_DIR='$LOG_DIR' \
   bash scripts/ubuntu/run_marinecity_targeted_reobservation_queue.sh; exec bash"

echo "Started MarineCity targeted re-observation queue: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $LOG_DIR/queue.log"
echo "Status: outputs/experiments/marinecity_targeted_reobservation_status.md"
