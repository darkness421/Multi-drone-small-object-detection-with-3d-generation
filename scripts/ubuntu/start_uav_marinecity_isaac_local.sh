#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-uav-marinecity-isaac-local}
ISAAC_ROOT=${ISAAC_ROOT:-/home/oem/UAV/isaac/isaacsim_source_code/isaacsim_4.5}
USD_PATH=${USD_PATH:-/home/oem/docker/isaac-sim/data/haeundae_marinecity_roi_prep.usd}
GPU=${GPU:-1}
DISPLAY_ID=${DISPLAY_ID:-${DISPLAY:-:1}}
LOG_DIR=${LOG_DIR:-outputs/logs/uav_marinecity_isaac_local}
GPU_MODE=${GPU_MODE:-direct}
XDG_RUNTIME_DIR_PATH=${XDG_RUNTIME_DIR_PATH:-/run/user/$(id -u)}
DBUS_SESSION_BUS_ADDRESS_VALUE=${DBUS_SESSION_BUS_ADDRESS_VALUE:-unix:path=${XDG_RUNTIME_DIR_PATH}/bus}
if [[ -f "${XDG_RUNTIME_DIR_PATH}/gdm/Xauthority" ]]; then
  XAUTHORITY_PATH=${XAUTHORITY_PATH:-${XDG_RUNTIME_DIR_PATH}/gdm/Xauthority}
else
  XAUTHORITY_PATH=${XAUTHORITY_PATH:-$HOME/.Xauthority}
fi

mkdir -p "$LOG_DIR"

if [[ ! -x "$ISAAC_ROOT/isaac-sim.sh" ]]; then
  echo "Isaac local launcher was not found: $ISAAC_ROOT/isaac-sim.sh" >&2
  exit 1
fi

if [[ ! -f "$USD_PATH" ]]; then
  echo "USD stage was not found: $USD_PATH" >&2
  exit 1
fi

if [[ ! -f "$XAUTHORITY_PATH" ]]; then
  echo "Xauthority file was not found: $XAUTHORITY_PATH" >&2
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  exit 0
fi

log_file="$LOG_DIR/${SESSION}.log"

if [[ "$GPU_MODE" == "remap" ]]; then
  gpu_env="CUDA_VISIBLE_DEVICES='$GPU'"
  active_gpu=0
  cuda_device=0
else
  gpu_env=""
  active_gpu="$GPU"
  cuda_device="$GPU"
fi

tmux new-session -d -s "$SESSION" -n isaac-local \
  "set -o pipefail; cd '$ISAAC_ROOT' && \
   echo '[UAV MarineCity Isaac Local] started at '\$(date -Is) 2>&1 | tee -a '$PWD/$log_file'; \
   echo 'Isaac root: $ISAAC_ROOT' 2>&1 | tee -a '$PWD/$log_file'; \
   echo 'USD: $USD_PATH' 2>&1 | tee -a '$PWD/$log_file'; \
   echo 'GPU: $GPU' 2>&1 | tee -a '$PWD/$log_file'; \
   echo 'GPU mode: $GPU_MODE' 2>&1 | tee -a '$PWD/$log_file'; \
   echo 'DISPLAY: $DISPLAY_ID' 2>&1 | tee -a '$PWD/$log_file'; \
   echo 'XAUTHORITY: $XAUTHORITY_PATH' 2>&1 | tee -a '$PWD/$log_file'; \
   DISPLAY='$DISPLAY_ID' \
   XAUTHORITY='$XAUTHORITY_PATH' \
   XDG_RUNTIME_DIR='$XDG_RUNTIME_DIR_PATH' \
   DBUS_SESSION_BUS_ADDRESS='$DBUS_SESSION_BUS_ADDRESS_VALUE' \
   $gpu_env \
   ./isaac-sim.sh '$USD_PATH' \
     --/renderer/activeGpu=$active_gpu \
     --/physics/cudaDevice=$cuda_device \
     --/renderer/multiGpu/enabled=False \
     --/renderer/multiGpu/maxGpuCount=1 \
     2>&1 | tee -a '$PWD/$log_file'; \
   rc=\${PIPESTATUS[0]}; \
   echo '[UAV MarineCity Isaac Local] exited rc='\$rc' at '\$(date -Is) 2>&1 | tee -a '$PWD/$log_file'; \
   exec bash"

echo "Started UAV MarineCity Isaac local session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
