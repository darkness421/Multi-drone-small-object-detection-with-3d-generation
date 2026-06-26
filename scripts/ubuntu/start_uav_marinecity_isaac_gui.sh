#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-uav-marinecity-isaac-gui}
CONTAINER_NAME=${CONTAINER_NAME:-isaac-sim-gui-uav-marinecity}
IMAGE=${IMAGE:-nvcr.io/nvidia/isaac-sim:5.1.0}
GPU=${GPU:-1}
DISPLAY_ID=${DISPLAY_ID:-${DISPLAY:-:1}}
if [[ -f "/run/user/$(id -u)/gdm/Xauthority" ]]; then
  XAUTHORITY_PATH=${XAUTHORITY_PATH:-/run/user/$(id -u)/gdm/Xauthority}
else
  XAUTHORITY_PATH=${XAUTHORITY_PATH:-$HOME/.Xauthority}
fi
UAV_PROJECT=${UAV_PROJECT:-/home/oem/UAV/uav_marinecity}
LOG_DIR=${LOG_DIR:-outputs/logs/uav_marinecity_isaac_gui}
RUN_MODE=${RUN_MODE:-main}
MAIN_ARGS=${MAIN_ARGS:-}
RUNAPP_STAGE_PATH=${RUNAPP_STAGE_PATH-/isaac-sim/.local/share/ov/data/haeundae_marinecity_roi_prep.usd}
RUNAPP_BASE_ARGS=${RUNAPP_BASE_ARGS:---/exts/omni.kit.pipapi/envPath=/isaac-sim/.cache/pip3-envs/no_space}
RUNAPP_EXTRA_ARGS=${RUNAPP_EXTRA_ARGS:-}
CONTAINER_USER=${CONTAINER_USER:-1234:1234}
DOCKER_IPC_ARGS=${DOCKER_IPC_ARGS:---ipc=host}
XAUTHORITY_MOUNT=${XAUTHORITY_MOUNT:-/tmp/${SESSION}.Xauthority}
MARINECITY_PROFILE=${MARINECITY_PROFILE:-viewer160}
MARINECITY_USD=${MARINECITY_USD:-/isaac-sim/.local/share/ov/data/haeundae_marinecity_roi_prep.usd}
MARINECITY_OUTPUT_ROOT=${MARINECITY_OUTPUT_ROOT:-/workspace/uav_marinecity/outputs/debug}
COM3D_UAVMARINE_STAGE=${COM3D_UAVMARINE_STAGE:-}
COM3D_UAVMARINE_STATUS=${COM3D_UAVMARINE_STATUS:-}
COM3D_UAVMARINE_CAPTURE_DIR=${COM3D_UAVMARINE_CAPTURE_DIR:-}
COM3D_UAVMARINE_CAPTURE=${COM3D_UAVMARINE_CAPTURE:-}
COM3D_UAVMARINE_BASE_STAGE=${COM3D_UAVMARINE_BASE_STAGE:-}
COM3D_UAVMARINE_ACTOR_LAYER=${COM3D_UAVMARINE_ACTOR_LAYER:-}
COM3D_UAVMARINE_SESSION_STATUS=${COM3D_UAVMARINE_SESSION_STATUS:-}
COM3D_KEEP_USER_CAMERA=${COM3D_KEEP_USER_CAMERA:-}
COM3D_VIEWER_PROFILE=${COM3D_VIEWER_PROFILE:-viewer160}
COM3D_GEOREF_HEIGHT=${COM3D_GEOREF_HEIGHT:-160.0}

mkdir -p "$LOG_DIR"

if [[ ! -d "$UAV_PROJECT" ]]; then
  echo "UAV project was not found: $UAV_PROJECT" >&2
  exit 1
fi

if [[ ! -f "$XAUTHORITY_PATH" ]]; then
  echo "Xauthority file was not found: $XAUTHORITY_PATH" >&2
  exit 1
fi

cp "$XAUTHORITY_PATH" "$XAUTHORITY_MOUNT"
chmod 0644 "$XAUTHORITY_MOUNT"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  exit 0
fi

log_file="$LOG_DIR/${SESSION}.log"

if [[ "$RUN_MODE" == "runapp" ]]; then
  if [[ -n "$RUNAPP_STAGE_PATH" ]]; then
    container_cmd="cd /isaac-sim && ./runapp.sh $RUNAPP_BASE_ARGS $RUNAPP_EXTRA_ARGS '$RUNAPP_STAGE_PATH'"
  else
    container_cmd="cd /isaac-sim && ./runapp.sh $RUNAPP_BASE_ARGS $RUNAPP_EXTRA_ARGS"
  fi
else
  container_cmd="cd /isaac-sim && /isaac-sim/python.sh /workspace/uav_marinecity/scripts/main.py $MAIN_ARGS"
fi

tmux new-session -d -s "$SESSION" -n isaac-gui \
  "set -o pipefail; cd '$PWD' && \
   echo '[UAV MarineCity Isaac GUI] started at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   echo 'Container: $CONTAINER_NAME' 2>&1 | tee -a '$log_file'; \
   echo 'Image: $IMAGE' 2>&1 | tee -a '$log_file'; \
   echo 'GPU: $GPU' 2>&1 | tee -a '$log_file'; \
   echo 'DISPLAY: $DISPLAY_ID' 2>&1 | tee -a '$log_file'; \
   echo 'XAUTHORITY: $XAUTHORITY_PATH' 2>&1 | tee -a '$log_file'; \
   echo 'XAUTHORITY mount: $XAUTHORITY_MOUNT' 2>&1 | tee -a '$log_file'; \
   echo 'UAV project: $UAV_PROJECT' 2>&1 | tee -a '$log_file'; \
   echo 'Run mode: $RUN_MODE' 2>&1 | tee -a '$log_file'; \
   echo 'Container user: $CONTAINER_USER' 2>&1 | tee -a '$log_file'; \
   echo 'Docker IPC args: $DOCKER_IPC_ARGS' 2>&1 | tee -a '$log_file'; \
   echo 'Container command: $container_cmd' 2>&1 | tee -a '$log_file'; \
   xhost +local: 2>&1 | tee -a '$log_file'; \
   docker rm -f '$CONTAINER_NAME' >/dev/null 2>&1 || true; \
   docker run --name '$CONTAINER_NAME' \
     --entrypoint bash \
     -it \
     --gpus '\"device=$GPU\"' \
     --network=host \
     $DOCKER_IPC_ARGS \
     --rm \
     -e ACCEPT_EULA=Y \
     -e PRIVACY_CONSENT=Y \
     -e DISPLAY='$DISPLAY_ID' \
     -e XAUTHORITY=/isaac-sim/.Xauthority \
     -e MARINECITY_PROFILE='$MARINECITY_PROFILE' \
     -e MARINECITY_USD='$MARINECITY_USD' \
     -e MARINECITY_OUTPUT_ROOT='$MARINECITY_OUTPUT_ROOT' \
     -e COM3D_UAVMARINE_STAGE='$COM3D_UAVMARINE_STAGE' \
     -e COM3D_UAVMARINE_STATUS='$COM3D_UAVMARINE_STATUS' \
     -e COM3D_UAVMARINE_CAPTURE_DIR='$COM3D_UAVMARINE_CAPTURE_DIR' \
     -e COM3D_UAVMARINE_CAPTURE='$COM3D_UAVMARINE_CAPTURE' \
     -e COM3D_UAVMARINE_BASE_STAGE='$COM3D_UAVMARINE_BASE_STAGE' \
     -e COM3D_UAVMARINE_ACTOR_LAYER='$COM3D_UAVMARINE_ACTOR_LAYER' \
     -e COM3D_UAVMARINE_SESSION_STATUS='$COM3D_UAVMARINE_SESSION_STATUS' \
     -e COM3D_KEEP_USER_CAMERA='$COM3D_KEEP_USER_CAMERA' \
     -e COM3D_VIEWER_PROFILE='$COM3D_VIEWER_PROFILE' \
     -e COM3D_GEOREF_HEIGHT='$COM3D_GEOREF_HEIGHT' \
     -v '$XAUTHORITY_MOUNT':/isaac-sim/.Xauthority:ro \
     -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
     -v /home/oem/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
     -v /home/oem/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
     -v /home/oem/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
     -v /home/oem/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
     -v /home/oem/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
     -v /home/oem/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
     -v '$UAV_PROJECT':/workspace/uav_marinecity:rw \
     -u '$CONTAINER_USER' \
     '$IMAGE' \
     -lc '$container_cmd' \
     2>&1 | tee -a '$log_file'; \
   rc=\${PIPESTATUS[0]}; \
   echo '[UAV MarineCity Isaac GUI] exited rc='\$rc' at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   exec bash"

echo "Started UAV MarineCity Isaac GUI session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
