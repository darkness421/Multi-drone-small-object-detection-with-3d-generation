#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

while true; do
  clear
  echo "ACCV LIVE STATUS - $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo
  echo "== GPU =="
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader || true
  echo
  echo "== Current Work =="
  sed -n '1,80p' outputs/reports/live/current_work_status.md || true
  echo
  echo "== Remaining Gates =="
  sed -n '1,120p' outputs/reports/live/accv_remaining_gates_queue.md || true
  echo
  echo "== Overnight Supplementary Queue =="
  if [[ -f outputs/logs/overnight_supplementary_0629/queue.log ]]; then
    tail -n 24 outputs/logs/overnight_supplementary_0629/queue.log
  else
    echo "not started"
  fi
  echo
  echo "== Morning 3D/Simulation Queue =="
  if [[ -f outputs/logs/morning_3d_sim_queue_0629/queue.log ]]; then
    tail -n 32 outputs/logs/morning_3d_sim_queue_0629/queue.log
  else
    echo "not started"
  fi
  echo
  echo "== Live Figures =="
  echo "Detector dashboard: outputs/reports/live/training_dashboard.png"
  echo "MarineCity dashboard: outputs/reports/live/marinecity_simulation_dashboard.png"
  echo "3D sweep plot:      outputs/reports/live/marinecity_nerfacto_iteration_sweep.png"
  echo "Depth sanity plot:  outputs/reports/live/marinecity_depth_view_consistency_sanity.png"
  sleep 10
done
