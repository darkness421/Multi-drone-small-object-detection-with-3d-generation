#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/../.."

LOG_DIR=${LOG_DIR:-outputs/logs/accv_remaining_booster_0629}
STATE_DIR=${STATE_DIR:-outputs/experiments/accv_remaining_booster_0629}
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
  if "$@"; then
    record_plan "$stage" "done" "$detail"
    log "DONE $stage"
  else
    local code=$?
    record_plan "$stage" "failed" "$detail exit=$code"
    log "FAILED $stage exit=$code"
    return "$code"
  fi
}

main() {
  : > "$QUEUE_LOG"
  log "QUEUE_STARTED ACCV remaining booster 0629"
  record_plan "queue" "started" "paper-safe remaining booster checks"

  run_stage "viewer160_crossview_graph_refresh" \
    python scripts/build_marinecity_viewer160_combined_evidence_graph.py

  run_stage "marinecity_system_efficiency_refresh" \
    python scripts/build_marinecity_system_efficiency_report.py

  run_stage "marinecity_reobservation_policy_ablation" \
    python scripts/build_marinecity_reobservation_policy_ablation.py

  run_stage "marinecity_3d_table_refresh" \
    python scripts/build_marinecity_3d_results_table.py

  run_stage "marinecity_nerfacto_sweep_refresh" \
    python scripts/build_marinecity_nerfacto_sweep_artifacts.py

  run_stage "marinecity_3d_readiness_check" \
    python scripts/check_marinecity_3d_completion_readiness.py

  run_stage "aerograph_reasoner_table_refresh" \
    python scripts/build_aerograph_reasoner_table.py

  run_stage "aerograph_readiness_check" \
    python scripts/check_aerograph_nonmock_readiness.py

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

  run_stage "accv_snapshot_refresh" \
    python scripts/build_accv_status_snapshot.py

  record_plan "queue" "complete" "remaining booster checks finished"
  log "QUEUE_FINISHED ACCV remaining booster 0629"
  log "Plan: $PLAN_CSV"
  log "Log: $QUEUE_LOG"
}

main "$@"
