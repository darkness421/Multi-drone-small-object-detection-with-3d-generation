#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-gpu1-isaac-visible-20260622}
GPU=${GPU:-1}
RENDER_GPU=${RENDER_GPU:-0}
PHYSICS_GPU=${PHYSICS_GPU:-$GPU}
DISPLAY_ID=${DISPLAY_ID:-${DISPLAY:-:1}}
XAUTHORITY_PATH=${XAUTHORITY:-$HOME/.Xauthority}
XDG_RUNTIME_DIR_PATH=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
ISAAC_ROOT=${ISAAC_ROOT:-/home/oem/UAV/isaac/isaacsim_source_code/isaacsim_4.5}
ISAAC_SIM=${ISAAC_SIM:-$ISAAC_ROOT/isaac-sim.sh}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu1_isaac_visible}
CAPTURE_PLAN=${CAPTURE_PLAN:-outputs/experiments/marinecity_isaac_gpu1_smoke_capture_plan.json}
REPLICATOR_TEMPLATE=${REPLICATOR_TEMPLATE:-outputs/experiments/marinecity_isaac_gpu1_smoke_replicator_template.py}
STARTED_MARKER=${STARTED_MARKER:-outputs/logs/gpu1_isaac_visible/isaac_visible.started}
STAGE_PATH=${STAGE_PATH:-outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/marinecity_proxy_stage.usda}
OPEN_SCRIPT=${OPEN_SCRIPT:-simulation/isaac/open_marinecity_stage_gui.py}
OPEN_MARKER=${OPEN_MARKER:-outputs/logs/gpu1_isaac_visible/marinecity_stage_opened.json}
VIEW_CAMERA=${VIEW_CAMERA:-/World/UAVs/uav_01/Camera}

mkdir -p "$LOG_DIR" "$(dirname "$STARTED_MARKER")"

if [[ ! -x "$ISAAC_SIM" ]]; then
  echo "Isaac Sim launcher was not found or is not executable: $ISAAC_SIM" >&2
  exit 1
fi

if [[ ! -f "$STAGE_PATH" ]]; then
  echo "MarineCity USD stage was not found: $STAGE_PATH" >&2
  exit 1
fi

if [[ ! -f "$OPEN_SCRIPT" ]]; then
  echo "MarineCity GUI open script was not found: $OPEN_SCRIPT" >&2
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

log_file="$LOG_DIR/isaac_visible.log"
stage_abs="$(readlink -f "$STAGE_PATH")"
open_script_abs="$(readlink -f "$OPEN_SCRIPT")"
mkdir -p "$(dirname "$OPEN_MARKER")"
open_marker_abs="$(cd "$(dirname "$OPEN_MARKER")" && pwd)/$(basename "$OPEN_MARKER")"

tmux new-session -d -s "$SESSION" -n isaac-gui \
  "set -o pipefail; cd '$PWD' && \
   echo '[GPU1 Isaac visible] started at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   echo 'Isaac root: $ISAAC_ROOT' 2>&1 | tee -a '$log_file'; \
   echo 'Isaac launcher: $ISAAC_SIM' 2>&1 | tee -a '$log_file'; \
   echo 'Display: $DISPLAY_ID' 2>&1 | tee -a '$log_file'; \
   echo 'Xauthority: $XAUTHORITY_PATH' 2>&1 | tee -a '$log_file'; \
   echo 'XDG runtime dir: $XDG_RUNTIME_DIR_PATH' 2>&1 | tee -a '$log_file'; \
   echo 'Requested NVIDIA GPU: $GPU' 2>&1 | tee -a '$log_file'; \
   echo 'Isaac renderer activeGpu ordinal: $RENDER_GPU' 2>&1 | tee -a '$log_file'; \
   echo 'Isaac physics CUDA device: $PHYSICS_GPU' 2>&1 | tee -a '$log_file'; \
   echo 'MarineCity stage: $stage_abs' 2>&1 | tee -a '$log_file'; \
   echo 'MarineCity GUI open script: $open_script_abs' 2>&1 | tee -a '$log_file'; \
   echo 'MarineCity open marker: $open_marker_abs' 2>&1 | tee -a '$log_file'; \
   echo 'MarineCity view camera: $VIEW_CAMERA' 2>&1 | tee -a '$log_file'; \
   echo 'Capture plan: $CAPTURE_PLAN' 2>&1 | tee -a '$log_file'; \
   echo 'Replicator template: $REPLICATOR_TEMPLATE' 2>&1 | tee -a '$log_file'; \
   nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>&1 | tee -a '$log_file'; \
   bash scripts/ubuntu/check_resource_margin.sh --path '$PWD' --gpu '$GPU' --min-free-gb 30 --max-disk-use-percent 94 --min-ram-gb 12 --min-gpu-free-gb 8 --wait-seconds 30 2>&1 | tee -a '$log_file'; \
   touch '$STARTED_MARKER'; \
   env -u CONDA_PREFIX -u CONDA_DEFAULT_ENV \
     DISPLAY='$DISPLAY_ID' \
     XAUTHORITY='$XAUTHORITY_PATH' \
     XDG_RUNTIME_DIR='$XDG_RUNTIME_DIR_PATH' \
     COM3D_MARINECITY_STAGE='$stage_abs' \
     COM3D_MARINECITY_OPEN_MARKER='$open_marker_abs' \
     COM3D_MARINECITY_CAMERA='$VIEW_CAMERA' \
     '$ISAAC_SIM' \
       --/renderer/activeGpu='$RENDER_GPU' \
       --/physics/cudaDevice='$PHYSICS_GPU' \
       --/renderer/multiGpu/enabled=false \
       --/renderer/multiGpu/maxGpuCount=1 \
       --/app/window/hideUi=0 \
       --/app/window/width=1600 \
       --/app/window/height=900 \
       --exec '$open_script_abs' \
       2>&1 | tee -a '$log_file'; \
   rc=\${PIPESTATUS[0]}; \
   echo '[GPU1 Isaac visible] exited rc='\$rc' at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   exec bash"

echo "Started GPU1 Isaac visible session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
