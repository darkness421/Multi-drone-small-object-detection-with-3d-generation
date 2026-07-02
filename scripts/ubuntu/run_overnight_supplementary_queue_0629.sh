#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
LOG_DIR=${LOG_DIR:-outputs/logs/overnight_supplementary_0629}
STATE_DIR=${STATE_DIR:-outputs/experiments/overnight_supplementary_0629}
LIVE_DIR=${LIVE_DIR:-outputs/reports/live}

mkdir -p "$LOG_DIR" "$STATE_DIR" "$LIVE_DIR"
QUEUE_LOG="$LOG_DIR/queue.log"
PLAN_CSV="$STATE_DIR/plan.csv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record() {
  local stage="$1"
  local status="$2"
  local detail="$3"
  if [[ ! -f "$PLAN_CSV" ]]; then
    echo "updated_at,stage,status,detail" > "$PLAN_CSV"
  fi
  printf '"%s","%s","%s","%s"\n' "$(date -Is)" "$stage" "$status" "$detail" >> "$PLAN_CSV"
}

run_step() {
  local stage="$1"
  shift
  log "START $stage"
  record "$stage" "running" "$*"
  if "$@" 2>&1 | tee -a "$QUEUE_LOG"; then
    log "DONE $stage"
    record "$stage" "done" "$*"
  else
    log "WARN $stage failed; continuing overnight queue"
    record "$stage" "warn_failed" "$*"
  fi
}

run_gpu_sweeps() {
  run_step "nms_conf001_extended" env GPU="$GPU" CONDA_ENV="$CONDA_ENV" CONF=0.01 IOUS="0.45 0.50 0.55 0.60 0.65 0.75" \
    bash scripts/ubuntu/run_final_detector_nms_robustness_sweep.sh
  run_step "nms_report_refresh" python scripts/build_final_nms_robustness_report.py

  run_step "input_resolution_extended" env GPU="$GPU" CONDA_ENV="$CONDA_ENV" IMGSZS="768 1152 1408 1600" CONF=0.001 IOU=0.55 \
    bash scripts/ubuntu/run_final_detector_input_resolution_sweep.sh
  run_step "input_resolution_report_refresh" python scripts/build_final_input_resolution_report.py
}

run_marinecity_supplement() {
  run_step "depth_consistency_target_uav01_stride2" python scripts/build_marinecity_depth_view_consistency_sanity.py \
    --target-uav uav_01 \
    --source-uavs uav_02,uav_03 \
    --stride 2 \
    --out-dir outputs/experiments/3d_generation/marinecity_depth_view_consistency_target_uav01_stride2 \
    --live-json outputs/reports/live/marinecity_depth_view_consistency_target_uav01_stride2.json \
    --live-md outputs/reports/live/marinecity_depth_view_consistency_target_uav01_stride2.md \
    --live-png outputs/reports/live/marinecity_depth_view_consistency_target_uav01_stride2.png

  run_step "depth_consistency_target_uav02_stride2" python scripts/build_marinecity_depth_view_consistency_sanity.py \
    --target-uav uav_02 \
    --source-uavs uav_01,uav_03 \
    --stride 2 \
    --out-dir outputs/experiments/3d_generation/marinecity_depth_view_consistency_target_uav02_stride2 \
    --live-json outputs/reports/live/marinecity_depth_view_consistency_target_uav02_stride2.json \
    --live-md outputs/reports/live/marinecity_depth_view_consistency_target_uav02_stride2.md \
    --live-png outputs/reports/live/marinecity_depth_view_consistency_target_uav02_stride2.png

  run_step "depth_consistency_target_uav03_stride1" python scripts/build_marinecity_depth_view_consistency_sanity.py \
    --target-uav uav_03 \
    --source-uavs uav_01,uav_02 \
    --stride 1 \
    --out-dir outputs/experiments/3d_generation/marinecity_depth_view_consistency_target_uav03_stride1 \
    --live-json outputs/reports/live/marinecity_depth_view_consistency_target_uav03_stride1.json \
    --live-md outputs/reports/live/marinecity_depth_view_consistency_target_uav03_stride1.md \
    --live-png outputs/reports/live/marinecity_depth_view_consistency_target_uav03_stride1.png

  cp outputs/reports/live/marinecity_depth_view_consistency_target_uav01_stride2.png \
    paper/figures/results/marinecity_system/marinecity_depth_view_consistency_target_uav01_stride2.png 2>/dev/null || true
  cp outputs/reports/live/marinecity_depth_view_consistency_target_uav02_stride2.png \
    paper/figures/results/marinecity_system/marinecity_depth_view_consistency_target_uav02_stride2.png 2>/dev/null || true
  cp outputs/reports/live/marinecity_depth_view_consistency_target_uav03_stride1.png \
    paper/figures/results/marinecity_system/marinecity_depth_view_consistency_target_uav03_stride1.png 2>/dev/null || true

  run_step "marinecity_system_artifacts_refresh" python scripts/build_marinecity_system_test_artifacts.py
  cp outputs/reports/live/marinecity_system_test_10plus/contact_sheet_3_scenarios.png \
    paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png 2>/dev/null || true
  cp outputs/reports/live/marinecity_system_test_10plus/contact_sheet_token_tests.png \
    paper/figures/results/marinecity_system/contact_sheet_token_tests.png 2>/dev/null || true
  cp outputs/reports/live/marinecity_system_test_10plus/paper_system_scenario_table.tex \
    paper/tables/marinecity_system_scenario_table.tex 2>/dev/null || true
}

run_paper_refresh() {
  run_step "marinecity_integration_check" python scripts/check_marinecity_system_integration.py
  run_step "marinecity_3d_readiness" python scripts/check_marinecity_3d_completion_readiness.py
  run_step "paper_latex_integrity" python scripts/check_latex_patch_integrity.py
  run_step "paper_artifact_readiness" python scripts/check_paper_artifact_readiness.py
  run_step "training_dashboard_refresh" env PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png
  run_step "marinecity_dashboard_refresh" python scripts/build_marinecity_simulation_dashboard.py
  run_step "current_work_status_refresh" python scripts/build_current_work_status.py
  run_step "accv_snapshot_refresh" python scripts/build_accv_status_snapshot.py
  run_step "remaining_gates_refresh" python scripts/build_accv_remaining_gates_queue.py
}

main() {
  log "OVERNIGHT_SUPPLEMENTARY_QUEUE_START gpu=$GPU conda=$CONDA_ENV"
  record "queue" "started" "gpu=$GPU"
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1 | tee -a "$QUEUE_LOG" || true
  run_gpu_sweeps
  run_marinecity_supplement
  run_paper_refresh
  record "queue" "complete" "overnight supplementary queue finished"
  log "QUEUE_FINISHED overnight supplementary 0629"
  log "Plan: $PLAN_CSV"
  log "Log: $QUEUE_LOG"
}

main "$@"
