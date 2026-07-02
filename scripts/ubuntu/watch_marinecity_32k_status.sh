#!/usr/bin/env bash
set -euo pipefail

cd /home/oem/projects/multi-uav-marine-city

SESSION=${SESSION:-marinecity-nerfacto-fullres32k-gpu0-0629}
METRIC_JSON=${METRIC_JSON:-outputs/experiments/3d_generation/nerfstudio_native_runs/marinecity_nerfacto_fullres32k_20260629_0028_fullres32k_metric_row.json}
MANIFEST=${MANIFEST:-outputs/experiments/3d_generation/nerfstudio_native_runs/marinecity_nerfacto_fullres32k_20260629_0028_fullres32k_manifest.json}

while true; do
  clear
  date
  echo
  echo "=== GPU STATUS ==="
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits
  echo
  echo "=== MARINECITY 32K LOG: $SESSION ==="
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux capture-pane -pt "$SESSION" -S -36 | tail -36
  else
    echo "tmux session is no longer running."
  fi
  echo
  echo "=== RESULT FILES ==="
  if [[ -f "$METRIC_JSON" ]]; then
    cat "$METRIC_JSON"
  else
    echo "metric JSON pending: $METRIC_JSON"
  fi
  if [[ -f "$MANIFEST" ]]; then
    echo
    echo "manifest exists: $MANIFEST"
  fi
  sleep 30
done
