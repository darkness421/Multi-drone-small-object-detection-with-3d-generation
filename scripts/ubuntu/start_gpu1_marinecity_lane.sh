#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-gpu1-marinecity-lane}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-1}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu1_marinecity}
MANIFEST=${MANIFEST:-outputs/experiments/marinecity_multiview_benchmark.json}
VALIDATION_MANIFEST=${VALIDATION_MANIFEST:-outputs/experiments/marinecity_multiview_benchmark_readiness.json}
MANIFEST_INPUT=${MANIFEST_INPUT:-outputs/experiments/marinecity_isaac_dry_run_manifest.json}
CAPTURE_PLAN=${CAPTURE_PLAN:-outputs/experiments/marinecity_isaac_capture_plan.json}
REPLICATOR_TEMPLATE=${REPLICATOR_TEMPLATE:-outputs/experiments/marinecity_isaac_replicator_template.py}
ALLOW_PLACEHOLDER_3D=${ALLOW_PLACEHOLDER_3D:-0}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

log_file="$LOG_DIR/lane.log"

tmux new-session -d -s "$SESSION" -n marinecity \
  "cd '$PWD' && \
   echo '[GPU1 MarineCity lane] started at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   echo 'GPU status:' 2>&1 | tee -a '$log_file'; \
   nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>&1 | tee -a '$log_file'; \
   echo 2>&1 | tee -a '$log_file'; \
   bash scripts/ubuntu/check_resource_margin.sh --path '$PWD' --gpu '$GPU' --min-free-gb 40 --max-disk-use-percent 92 --min-ram-gb 12 --min-gpu-free-gb 8 --wait-seconds 30 2>&1 | tee -a '$log_file'; \
   echo 2>&1 | tee -a '$log_file'; \
   echo 'Checking MarineCity files...' 2>&1 | tee -a '$log_file'; \
   ls -lh '$MANIFEST' '$CAPTURE_PLAN' '$REPLICATOR_TEMPLATE' 2>&1 | tee -a '$log_file'; \
   conda run --no-capture-output -n '$CONDA_ENV' python -m scripts.build_marinecity_multiview_benchmark --input '$MANIFEST_INPUT' --out '$VALIDATION_MANIFEST' 2>&1 | tee -a '$log_file'; \
   echo 'Readiness validation manifest: $VALIDATION_MANIFEST' 2>&1 | tee -a '$log_file'; \
   echo 2>&1 | tee -a '$log_file'; \
   if [[ '$ALLOW_PLACEHOLDER_3D' == '1' ]]; then \
     echo 'ALLOW_PLACEHOLDER_3D=1, running placeholder 3D command contract on GPU $GPU.' 2>&1 | tee -a '$log_file'; \
     GPUS='$GPU' bash scripts/ubuntu/train_3d_generators_tmux.sh 2>&1 | tee -a '$log_file'; \
   else \
     echo '3D training is intentionally not started: generative3d.external_runner is still a placeholder.' 2>&1 | tee -a '$log_file'; \
     echo 'Next real step: connect 3DGS/Instant-NGP/NeRF upstream runner, then rerun with a real command.' 2>&1 | tee -a '$log_file'; \
   fi; \
   echo '[GPU1 MarineCity lane] readiness complete at '\$(date -Is) 2>&1 | tee -a '$log_file'; \
   exec bash"

echo "Started GPU1 MarineCity lane: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
