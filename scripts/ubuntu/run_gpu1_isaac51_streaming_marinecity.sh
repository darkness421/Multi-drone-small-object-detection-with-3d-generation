#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-1}
ACTIVE_GPU=${ACTIVE_GPU:-0}
IMAGE=${IMAGE:-nvcr.io/nvidia/isaac-sim:5.1.0}
CONTAINER_NAME=${CONTAINER_NAME:-isaac-gpu1-marinecity-streaming-$(date +%Y%m%d-%H%M%S)}
STAGE_PATH=${STAGE_PATH:-outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/marinecity_proxy_stage.usda}
OPEN_SCRIPT=${OPEN_SCRIPT:-simulation/isaac/open_marinecity_stage_gui.py}
OPEN_MARKER=${OPEN_MARKER:-outputs/logs/gpu1_isaac51_streaming/marinecity_stage_opened.json}
VIEW_CAMERA=${VIEW_CAMERA:-/World/UAVs/uav_01/Camera}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu1_isaac51_streaming}
LIVESTREAM_PORT=${LIVESTREAM_PORT:-49100}
CORE_STREAM_PORT=${CORE_STREAM_PORT:-48010}
EXTRA_KIT_ARGS=${EXTRA_KIT_ARGS:-}
MOUNT_ISAAC_DATA=${MOUNT_ISAAC_DATA:-0}

mkdir -p "$LOG_DIR" "$(dirname "$OPEN_MARKER")"
chmod 777 "$(dirname "$OPEN_MARKER")" 2>/dev/null || true
rm -f "$OPEN_MARKER"

if [[ "$STAGE_PATH" != /isaac-sim/* && ! -f "$STAGE_PATH" ]]; then
  echo "MarineCity USD stage was not found: $STAGE_PATH" >&2
  exit 1
fi

if [[ ! -f "$OPEN_SCRIPT" ]]; then
  echo "MarineCity GUI open script was not found: $OPEN_SCRIPT" >&2
  exit 1
fi

log_file="$LOG_DIR/${CONTAINER_NAME}.log"
if [[ "$STAGE_PATH" == /isaac-sim/* ]]; then
  stage_container="$STAGE_PATH"
else
  stage_container="/workspace/$STAGE_PATH"
fi
open_script_container="/workspace/$OPEN_SCRIPT"
open_marker_container="/workspace/$OPEN_MARKER"

echo "[Isaac 5.1 GPU${GPU} MarineCity streaming] started at $(date -Is)" | tee -a "$log_file"
echo "Image: $IMAGE" | tee -a "$log_file"
echo "Host GPU: $GPU" | tee -a "$log_file"
echo "Container active GPU: $ACTIVE_GPU" | tee -a "$log_file"
echo "Stage: $stage_container" | tee -a "$log_file"
echo "Open script: $open_script_container" | tee -a "$log_file"
echo "Open marker: $OPEN_MARKER" | tee -a "$log_file"
echo "View camera: $VIEW_CAMERA" | tee -a "$log_file"
echo "WebRTC livestream port: $LIVESTREAM_PORT" | tee -a "$log_file"
echo "Livestream core port: $CORE_STREAM_PORT" | tee -a "$log_file"
echo "Mount Isaac data: $MOUNT_ISAAC_DATA" | tee -a "$log_file"
echo "Extra Kit args: ${EXTRA_KIT_ARGS:-<none>}" | tee -a "$log_file"

nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>&1 | tee -a "$log_file"

docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

extra_mounts=()
if [[ "$MOUNT_ISAAC_DATA" == "1" ]]; then
  extra_mounts=(
    -v /home/oem/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw
    -v /home/oem/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw
    -v /home/oem/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw
    -v /home/oem/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw
    -v /home/oem/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw
    -v /home/oem/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw
  )
fi

docker run \
  --name "$CONTAINER_NAME" \
  --gpus "\"device=${GPU}\"" \
  --network host \
  --ipc host \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  -e ACCEPT_EULA=Y \
  -e PRIVACY_CONSENT=Y \
  -e PRIVACY_USERID=oem@local \
  -e PYTHONPATH=/workspace \
  -e COM3D_MARINECITY_STAGE="$stage_container" \
  -e COM3D_MARINECITY_OPEN_MARKER="$open_marker_container" \
  -e COM3D_MARINECITY_CAMERA="$VIEW_CAMERA" \
  "${extra_mounts[@]}" \
  -v "$PWD:/workspace:rw" \
  -w /workspace \
  "$IMAGE" \
  /isaac-sim/isaac-sim.streaming.sh \
    --/renderer/activeGpu="$ACTIVE_GPU" \
    --/physics/cudaDevice="$ACTIVE_GPU" \
    --/renderer/multiGpu/enabled=false \
    --/renderer/multiGpu/maxGpuCount=1 \
    --/app/livestream/port="$LIVESTREAM_PORT" \
    --/app/livestream/core/port="$CORE_STREAM_PORT" \
    $EXTRA_KIT_ARGS \
    --exec "$open_script_container" \
  2>&1 | tee -a "$log_file"

rc=${PIPESTATUS[0]}
echo "[Isaac 5.1 GPU${GPU} MarineCity streaming] exited rc=$rc at $(date -Is)" | tee -a "$log_file"
exit "$rc"
