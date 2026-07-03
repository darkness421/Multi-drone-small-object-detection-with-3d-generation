#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONTAINER_NAME=${CONTAINER_NAME:-isaac-sim-gui-uav-marinecity}
IMAGE=${IMAGE:-nvcr.io/nvidia/isaac-sim:5.1.0}
GPU=${GPU:-1}
UAV_PROJECT=${UAV_PROJECT:-/home/oem/UAV/uav_marinecity}
CONTAINER_USER=${CONTAINER_USER:-0:0}
LOG_DIR=${LOG_DIR:-outputs/logs/uav_marinecity_isaac_idle}
DOCKER_IPC_ARGS=${DOCKER_IPC_ARGS:---ipc=host}
DISPLAY_ID=${DISPLAY_ID:-${DISPLAY:-:1}}
if [[ -f "/run/user/$(id -u)/gdm/Xauthority" ]]; then
  XAUTHORITY_PATH=${XAUTHORITY_PATH:-/run/user/$(id -u)/gdm/Xauthority}
else
  XAUTHORITY_PATH=${XAUTHORITY_PATH:-$HOME/.Xauthority}
fi
XAUTHORITY_MOUNT=${XAUTHORITY_MOUNT:-/tmp/${CONTAINER_NAME}.idle.Xauthority}

mkdir -p "$LOG_DIR"

if [[ ! -d "$UAV_PROJECT" ]]; then
  echo "UAV project was not found: $UAV_PROJECT" >&2
  exit 1
fi

if docker ps --format '{{.Names}}' | grep -Fx "$CONTAINER_NAME" >/dev/null 2>&1; then
  echo "Container already running: $CONTAINER_NAME"
  exit 0
fi

if [[ -f "$XAUTHORITY_PATH" ]]; then
  cp "$XAUTHORITY_PATH" "$XAUTHORITY_MOUNT"
  chmod 0644 "$XAUTHORITY_MOUNT"
fi

log_file="$LOG_DIR/${CONTAINER_NAME}_idle.log"
{
  echo "[Isaac idle container] starting at $(date -Is)"
  echo "Container: $CONTAINER_NAME"
  echo "Image: $IMAGE"
  echo "GPU: $GPU"
  echo "User: $CONTAINER_USER"
} | tee -a "$log_file"

xhost +local: 2>&1 | tee -a "$log_file" || true
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run --name "$CONTAINER_NAME" \
  --entrypoint bash \
  -d \
  --gpus "\"device=$GPU\"" \
  --network=host \
  $DOCKER_IPC_ARGS \
  --rm \
  -e ACCEPT_EULA=Y \
  -e PRIVACY_CONSENT=Y \
  -e OMNI_ENV_PRIVACY_CONSENT=Y \
  -e DISPLAY="$DISPLAY_ID" \
  -e XAUTHORITY=/isaac-sim/.Xauthority \
  -v "$XAUTHORITY_MOUNT":/isaac-sim/.Xauthority:ro \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /home/oem/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
  -v /home/oem/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
  -v /home/oem/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
  -v /home/oem/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
  -v /home/oem/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
  -v /home/oem/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
  -v "$UAV_PROJECT":/workspace/uav_marinecity:rw \
  -u "$CONTAINER_USER" \
  "$IMAGE" \
  -lc "sleep infinity" 2>&1 | tee -a "$log_file"

echo "Started Isaac idle container: $CONTAINER_NAME"
echo "Log: $log_file"
