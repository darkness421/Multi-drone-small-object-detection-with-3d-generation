#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-gpu1-isaac-smoke-20260622}
GPU=${GPU:-1}
ISAAC_TIMEOUT=${ISAAC_TIMEOUT:-180}
ISAAC_ROOT=${ISAAC_ROOT:-/home/oem/UAV/isaac/isaacsim_source_code/isaacsim_4.5}
ISAAC_PYTHON=${ISAAC_PYTHON:-$ISAAC_ROOT/python.sh}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu1_isaac_smoke}
CONFIG=${CONFIG:-configs/sim/marinecity_windows_export.yaml}
SMOKE_PLAN=${SMOKE_PLAN:-outputs/experiments/marinecity_isaac_gpu1_smoke_capture_plan.json}
SMOKE_TEMPLATE=${SMOKE_TEMPLATE:-outputs/experiments/marinecity_isaac_gpu1_smoke_replicator_template.py}
MARKER=${MARKER:-outputs/logs/gpu1_isaac_smoke/isaac_smoke.done}

mkdir -p "$LOG_DIR" "$(dirname "$SMOKE_PLAN")" "$(dirname "$SMOKE_TEMPLATE")" "$(dirname "$MARKER")"

if [[ ! -x "$ISAAC_PYTHON" ]]; then
  echo "Isaac Python was not found or is not executable: $ISAAC_PYTHON" >&2
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

log_file="$LOG_DIR/smoke.log"

tmux new-session -d -s "$SESSION" -n isaac-smoke \
  "set -o pipefail; cd '$PWD' && \
   echo '[GPU1 Isaac smoke] started at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   echo 'Isaac root: $ISAAC_ROOT' 2>&1 | tee -a '$log_file'; \
   echo 'Isaac active GPU=$GPU' 2>&1 | tee -a '$log_file'; \
   nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>&1 | tee -a '$log_file'; \
   bash scripts/ubuntu/check_resource_margin.sh --path '$PWD' --gpu '$GPU' --min-free-gb 30 --max-disk-use-percent 94 --min-ram-gb 12 --min-gpu-free-gb 8 --wait-seconds 30 2>&1 | tee -a '$log_file'; \
   echo 'Running Isaac Replicator import smoke with timeout ${ISAAC_TIMEOUT}s...' 2>&1 | tee -a '$log_file'; \
   timeout '${ISAAC_TIMEOUT}s' env -u CONDA_PREFIX -u CONDA_DEFAULT_ENV ISAAC_ACTIVE_GPU='$GPU' PYTHONPATH='$PWD':\${PYTHONPATH:-} \
     '$ISAAC_PYTHON' simulation/isaac/export_rgb_depth_pose.py \
       --config '$CONFIG' \
       --plan-out '$SMOKE_PLAN' \
       --template-out '$SMOKE_TEMPLATE' \
       --active-gpu '$GPU' \
       --isaac-smoke 2>&1 | tee -a '$log_file'; \
   rc=\${PIPESTATUS[0]}; \
   if [[ \$rc -ne 0 ]]; then \
     echo '[GPU1 Isaac smoke] failed rc='\$rc' at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
     exec bash; \
   fi; \
   touch '$MARKER'; \
   echo '[GPU1 Isaac smoke] complete at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   exec bash"

echo "Started GPU1 Isaac smoke: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
