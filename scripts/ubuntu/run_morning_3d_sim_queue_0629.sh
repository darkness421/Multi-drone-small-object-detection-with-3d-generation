#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-0}
ENV_NAME=${ENV_NAME:-marinecity-nerfstudio}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
MAX_ITERS=${MAX_ITERS:-64000}
CAMERA_SCALE=${CAMERA_SCALE:-1.0}
TRAIN_SPLIT_FRACTION=${TRAIN_SPLIT_FRACTION:-0.67}
EXPERIMENT=${EXPERIMENT:-marinecity_nerfacto_fullres64k_20260629_morning}
TIMESTAMP=${TIMESTAMP:-$(date +%Y%m%d_%H%M%S)_fullres64k}

LOG_DIR=${LOG_DIR:-outputs/logs/morning_3d_sim_queue_0629}
STATE_DIR=${STATE_DIR:-outputs/experiments/morning_3d_sim_queue_0629}
mkdir -p "$LOG_DIR" "$STATE_DIR"

QUEUE_LOG="$LOG_DIR/queue.log"
PLAN_CSV="$STATE_DIR/plan.csv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record_plan() {
  local stage="$1"
  local status="$2"
  local detail="$3"
  if [[ ! -f "$PLAN_CSV" ]]; then
    printf "updated_at,stage,status,detail\n" > "$PLAN_CSV"
  fi
  printf '"%s","%s","%s","%s"\n' "$(date -Is)" "$stage" "$status" "$detail" >> "$PLAN_CSV"
}

run_stage() {
  local stage="$1"
  shift
  local detail="$*"
  log "START $stage"
  record_plan "$stage" "running" "$detail"
  "$@"
  record_plan "$stage" "done" "$detail"
  log "DONE $stage"
}

main() {
  log "QUEUE_STARTED morning 3D/simulation continuation"
  record_plan "queue" "started" "gpu=$GPU max_iters=$MAX_ITERS"

  run_stage "marinecity_nerfacto_fullres_extended" \
    env GPU="$GPU" ENV_NAME="$ENV_NAME" MAX_ITERS="$MAX_ITERS" CAMERA_SCALE="$CAMERA_SCALE" \
      TRAIN_SPLIT_FRACTION="$TRAIN_SPLIT_FRACTION" IMPORT_AFTER=1 \
      EXPERIMENT="$EXPERIMENT" TIMESTAMP="$TIMESTAMP" \
      bash scripts/ubuntu/run_marinecity_nerfstudio_nerfacto_torch_smoke.sh

  run_stage "marinecity_nerfacto_sweep_refresh" \
    python scripts/build_marinecity_nerfacto_sweep_artifacts.py

  run_stage "marinecity_3d_table_refresh" \
    python scripts/build_marinecity_3d_results_table.py

  run_stage "marinecity_system_efficiency_refresh" \
    python scripts/build_marinecity_system_efficiency_report.py

  run_stage "marinecity_integration_check" \
    python scripts/check_marinecity_system_integration.py

  run_stage "marinecity_3d_readiness_check" \
    python scripts/check_marinecity_3d_completion_readiness.py

  run_stage "paper_artifact_readiness_check" \
    python scripts/check_paper_artifact_readiness.py

  run_stage "latex_patch_integrity_check" \
    python scripts/check_latex_patch_integrity.py

  run_stage "remaining_gates_refresh" \
    python scripts/build_accv_remaining_gates_queue.py

  run_stage "marinecity_dashboard_refresh" \
    python scripts/build_marinecity_simulation_dashboard.py

  run_stage "training_dashboard_refresh" \
    env PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png

  run_stage "current_work_status_refresh" \
    python scripts/build_current_work_status.py

  record_plan "queue" "complete" "morning 3D/simulation continuation finished"
  log "QUEUE_FINISHED morning 3D/simulation continuation"
  log "Plan: $PLAN_CSV"
  log "Log: $QUEUE_LOG"
}

main "$@"
