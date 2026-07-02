#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-gpu1-isaac51-streaming-marinecity-20260623}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu1_isaac51_streaming}
GPU=${GPU:-1}
ACTIVE_GPU=${ACTIVE_GPU:-0}
STAGE_PATH=${STAGE_PATH:-outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/marinecity_proxy_stage.usda}
OPEN_SCRIPT=${OPEN_SCRIPT:-simulation/isaac/open_marinecity_stage_gui.py}
OPEN_MARKER=${OPEN_MARKER:-outputs/logs/gpu1_isaac51_streaming/marinecity_stage_opened.json}
VIEW_CAMERA=${VIEW_CAMERA:-/World/UAVs/uav_01/Camera}
LIVESTREAM_PORT=${LIVESTREAM_PORT:-49100}
CORE_STREAM_PORT=${CORE_STREAM_PORT:-48010}
MOUNT_ISAAC_DATA=${MOUNT_ISAAC_DATA:-0}
EXTRA_KIT_ARGS=${EXTRA_KIT_ARGS:-}
mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n isaac51-streaming \
  "cd '$PWD' && \
   GPU='$GPU' \
   ACTIVE_GPU='$ACTIVE_GPU' \
   STAGE_PATH='$STAGE_PATH' \
   OPEN_SCRIPT='$OPEN_SCRIPT' \
   OPEN_MARKER='$OPEN_MARKER' \
   VIEW_CAMERA='$VIEW_CAMERA' \
   LOG_DIR='$LOG_DIR' \
   LIVESTREAM_PORT='$LIVESTREAM_PORT' \
   CORE_STREAM_PORT='$CORE_STREAM_PORT' \
   MOUNT_ISAAC_DATA='$MOUNT_ISAAC_DATA' \
   EXTRA_KIT_ARGS='$EXTRA_KIT_ARGS' \
   bash scripts/ubuntu/run_gpu1_isaac51_streaming_marinecity.sh; exec bash"

echo "Started Isaac 5.1 GPU1 MarineCity streaming session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Logs: $LOG_DIR"
