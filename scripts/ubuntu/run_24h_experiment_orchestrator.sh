#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-24h-orchestrator}
START_IN_TMUX=${START_IN_TMUX:-0}
POLL_SECONDS=${POLL_SECONDS:-300}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
RUN_ID=${RUN_ID:-$(date +%Y%m%d_%H%M%S)}
LOG_DIR=${LOG_DIR:-outputs/logs/orchestrator/$RUN_ID}
LOG_FILE=${LOG_FILE:-$LOG_DIR/orchestrator.log}

ENABLE_TOP3=${ENABLE_TOP3:-1}
ENABLE_UAVDT=${ENABLE_UAVDT:-0}
ENABLE_3D=${ENABLE_3D:-0}
ENABLE_NOTION=${ENABLE_NOTION:-0}
ENABLE_PUBLISH=${ENABLE_PUBLISH:-0}
ENABLE_AUTO_RESEARCH=${ENABLE_AUTO_RESEARCH:-0}
CONTINUE_ON_OPTIONAL_FAILURE=${CONTINUE_ON_OPTIONAL_FAILURE:-1}

LARGE_SESSION=${LARGE_SESSION:-server-large-comparison}
BASELINE_WAIT_SESSIONS=${BASELINE_WAIT_SESSIONS:-$LARGE_SESSION}
TOP3_PENDING_SESSION=${TOP3_PENDING_SESSION:-server-top3-proposed-pending}
TOP3_SESSION=${TOP3_SESSION:-server-top3-proposed-screening}
UAVDT_PENDING_SESSION=${UAVDT_PENDING_SESSION:-server-uavdt-comparisons-pending}
UAVDT_YOLO_SESSION=${UAVDT_YOLO_SESSION:-server-uavdt-yolo-comparison}
UAVDT_RTDETR_SESSION=${UAVDT_RTDETR_SESSION:-server-uavdt-rtdetr-comparison}
GEN3D_SESSION=${GEN3D_SESSION:-marinecity-3d-generators}

LARGE_DETECTOR_ROOT=${LARGE_DETECTOR_ROOT:-outputs/detectors/server_fresh_baselines/large_20260524_140922}
EXTRA_BASELINE_ROOTS=${EXTRA_BASELINE_ROOTS:-}
ALL_BASELINE_ROOTS="$LARGE_DETECTOR_ROOT"
if [[ -n "$EXTRA_BASELINE_ROOTS" ]]; then
  ALL_BASELINE_ROOTS="$ALL_BASELINE_ROOTS,$EXTRA_BASELINE_ROOTS"
fi
LARGE_EXPERIMENT_ROOT=${LARGE_EXPERIMENT_ROOT:-outputs/experiments/server_fresh/large_20260524_140922}
LARGE_REPORT_DIR=${LARGE_REPORT_DIR:-outputs/reports/server_fresh_baselines/large_20260524_140922}

TOP3_CONFIG=${TOP3_CONFIG:-configs/experiments/top3_proposed_detector_screening.yaml}
TOP3_DETECTOR_ROOT=${TOP3_DETECTOR_ROOT:-outputs/detectors/server_top3_proposed_ablation}
TOP3_MAIN_DETECTOR_ROOT=${TOP3_MAIN_DETECTOR_ROOT:-outputs/detectors/server_top3_proposed_main}
LEGACY_PROPOSED_ROOT=${LEGACY_PROPOSED_ROOT:-outputs/detectors/server_proposed_ablation}
COMBINED_DETECTOR_ROOTS=${COMBINED_DETECTOR_ROOTS:-$ALL_BASELINE_ROOTS,$TOP3_DETECTOR_ROOT,$TOP3_MAIN_DETECTOR_ROOT,$LEGACY_PROPOSED_ROOT}
COMBINED_EXPERIMENT_ROOT=${COMBINED_EXPERIMENT_ROOT:-outputs/experiments/server_with_proposed}
COMBINED_REPORT_DIR=${COMBINED_REPORT_DIR:-outputs/reports/server_with_proposed}
DEDUPE_KEY=${DEDUPE_KEY:-dataset,model,seed,ablation,proposed_module}
STAGE_GATE_DATASET=${STAGE_GATE_DATASET:-VisDrone2019-DET}

UAVDT_DETECTOR_ROOT=${UAVDT_DETECTOR_ROOT:-outputs/detectors/server_uavdt_baselines}
UAVDT_EXPERIMENT_ROOT=${UAVDT_EXPERIMENT_ROOT:-outputs/experiments/uavdt}
UAVDT_REPORT_DIR=${UAVDT_REPORT_DIR:-outputs/reports/uavdt}

GEN3D_BENCHMARK=${GEN3D_BENCHMARK:-outputs/experiments/marinecity_multiview_benchmark.json}
GEN3D_RESULTS_DIR=${GEN3D_RESULTS_DIR:-outputs/experiments/3d_generation}
GEN3D_COMPARISON_CSV=${GEN3D_COMPARISON_CSV:-outputs/experiments/3d_generation_comparison.csv}

mkdir -p "$LOG_DIR"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG_FILE"
}

session_exists() {
  local session=$1
  [[ -n "$session" ]] && tmux has-session -t "$session" 2>/dev/null
}

wait_for_session() {
  local session=$1
  session=${session//[[:space:]]/}
  [[ -z "$session" ]] && return
  while session_exists "$session"; do
    log "Waiting for tmux session: $session"
    sleep "$POLL_SECONDS"
  done
}

wait_for_sessions_csv() {
  local sessions=$1
  local session
  IFS=',' read -r -a session_list <<< "$sessions"
  for session in "${session_list[@]}"; do
    wait_for_session "$session"
  done
}

run_logged() {
  local stage=$1
  shift
  log "START $stage"
  "$@" 2>&1 | tee -a "$LOG_DIR/${stage}.log"
  log "DONE $stage"
}

run_optional() {
  local stage=$1
  shift
  if run_logged "$stage" "$@"; then
    return 0
  fi
  log "OPTIONAL STAGE FAILED $stage"
  if [[ "$CONTINUE_ON_OPTIONAL_FAILURE" == "1" ]]; then
    return 0
  fi
  return 1
}

start_self_in_tmux_if_requested() {
  if [[ "$START_IN_TMUX" != "1" || -n "${TMUX:-}" ]]; then
    return
  fi
  if session_exists "$SESSION"; then
    echo "tmux session already exists: $SESSION"
    echo "Attach with: tmux attach -t $SESSION"
    exit 0
  fi
  START_IN_TMUX=0
  export SESSION START_IN_TMUX POLL_SECONDS CONDA_ENV RUN_ID LOG_DIR LOG_FILE
  export ENABLE_TOP3 ENABLE_UAVDT ENABLE_3D ENABLE_NOTION ENABLE_PUBLISH ENABLE_AUTO_RESEARCH CONTINUE_ON_OPTIONAL_FAILURE
  export LARGE_SESSION BASELINE_WAIT_SESSIONS TOP3_PENDING_SESSION TOP3_SESSION UAVDT_PENDING_SESSION UAVDT_YOLO_SESSION UAVDT_RTDETR_SESSION GEN3D_SESSION
  export LARGE_DETECTOR_ROOT EXTRA_BASELINE_ROOTS LARGE_EXPERIMENT_ROOT LARGE_REPORT_DIR
  export TOP3_CONFIG TOP3_DETECTOR_ROOT TOP3_MAIN_DETECTOR_ROOT LEGACY_PROPOSED_ROOT COMBINED_DETECTOR_ROOTS COMBINED_EXPERIMENT_ROOT COMBINED_REPORT_DIR
  export TOP3_GPUS TOP3_SKIP_COMPLETED
  export DEDUPE_KEY STAGE_GATE_DATASET UAVDT_DETECTOR_ROOT UAVDT_EXPERIMENT_ROOT UAVDT_REPORT_DIR
  export GEN3D_BENCHMARK GEN3D_RESULTS_DIR GEN3D_COMPARISON_CSV
  export GPUS METHODS RESOURCE_GUARD MIN_FREE_GB MAX_DISK_USE_PERCENT MIN_RAM_GB MIN_GPU_FREE_GB GUARD_WAIT_SECONDS
  export OVERLEAF_REPO COMMIT_MESSAGE OVERLEAF_COMMIT_MESSAGE DO_MAIN_COMMIT DO_MAIN_PUSH DO_OVERLEAF_SYNC DO_OVERLEAF_COMMIT DO_OVERLEAF_PUSH UPDATE_RESULTS_SECTION TOP_K PUBLISH_PATHS
  export NOTION_TOKEN NOTION_PAGE_ID NOTION_TARGET NOTION_FOCUS
  tmux new-session -d -s "$SESSION" "$PWD/scripts/ubuntu/run_24h_experiment_orchestrator.sh"
  echo "Started tmux session: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  echo "Log: $LOG_FILE"
  exit 0
}

collect_large_results() {
  mkdir -p "$LARGE_EXPERIMENT_ROOT" "$LARGE_REPORT_DIR"
  DETECTOR_ROOTS="$ALL_BASELINE_ROOTS" \
    DEDUPE_KEY="$DEDUPE_KEY" \
    RESULTS_CSV="$LARGE_EXPERIMENT_ROOT/server_baseline_results.csv" \
    SUMMARY_CSV="$LARGE_EXPERIMENT_ROOT/server_baseline_summary.csv" \
    PVALUES_CSV="$LARGE_EXPERIMENT_ROOT/server_baseline_pvalues.csv" \
    DASHBOARD="$LARGE_REPORT_DIR/figures/server_baseline_dashboard.png" \
    REPORT_DIR="$LARGE_REPORT_DIR" \
    STAGE_GATE_JSON="$LARGE_EXPERIMENT_ROOT/server_baseline_stage_gate.json" \
    STAGE_GATE_MD="$LARGE_EXPERIMENT_ROOT/server_baseline_stage_gate.md" \
    PROPOSED_GATE_JSON="$LARGE_EXPERIMENT_ROOT/proposed_overwhelm_gate.json" \
    PROPOSED_GATE_MD="$LARGE_EXPERIMENT_ROOT/proposed_overwhelm_gate.md" \
    STAGE_GATE_DATASET="$STAGE_GATE_DATASET" \
    CONDA_ENV="$CONDA_ENV" \
    NOTION_UPDATE="$ENABLE_NOTION" \
    bash scripts/ubuntu/collect_server_results.sh "$LARGE_DETECTOR_ROOT"
}

collect_combined_results() {
  mkdir -p "$COMBINED_EXPERIMENT_ROOT" "$COMBINED_REPORT_DIR"
  DETECTOR_ROOTS="$COMBINED_DETECTOR_ROOTS" \
    DEDUPE_KEY="$DEDUPE_KEY" \
    RESULTS_CSV="$COMBINED_EXPERIMENT_ROOT/server_with_proposed_results.csv" \
    SUMMARY_CSV="$COMBINED_EXPERIMENT_ROOT/server_with_proposed_summary.csv" \
    PVALUES_CSV="$COMBINED_EXPERIMENT_ROOT/server_with_proposed_pvalues.csv" \
    DASHBOARD="$COMBINED_REPORT_DIR/figures/server_with_proposed_dashboard.png" \
    REPORT_DIR="$COMBINED_REPORT_DIR" \
    STAGE_GATE_JSON="$COMBINED_EXPERIMENT_ROOT/server_with_proposed_stage_gate.json" \
    STAGE_GATE_MD="$COMBINED_EXPERIMENT_ROOT/server_with_proposed_stage_gate.md" \
    PROPOSED_GATE_JSON="$COMBINED_EXPERIMENT_ROOT/proposed_overwhelm_gate.json" \
    PROPOSED_GATE_MD="$COMBINED_EXPERIMENT_ROOT/proposed_overwhelm_gate.md" \
    STAGE_GATE_DATASET="$STAGE_GATE_DATASET" \
    CONDA_ENV="$CONDA_ENV" \
    NOTION_UPDATE="$ENABLE_NOTION" \
    bash scripts/ubuntu/collect_server_results.sh "$LARGE_DETECTOR_ROOT"
}

start_or_wait_top3() {
  if session_exists "$TOP3_PENDING_SESSION"; then
    log "Top-3 pending session already exists: $TOP3_PENDING_SESSION"
    wait_for_session "$TOP3_PENDING_SESSION"
  fi
  if ! session_exists "$TOP3_SESSION"; then
    WAIT_FOR="" \
      SESSION="$TOP3_SESSION" \
      CONFIG="$TOP3_CONFIG" \
      GPUS="${TOP3_GPUS:-0}" \
      SKIP_COMPLETED="${TOP3_SKIP_COMPLETED:-1}" \
      WAIT_AFTER_START=0 \
      CONDA_ENV="$CONDA_ENV" \
      bash scripts/ubuntu/train_proposed_ablation_after_session.sh
  else
    log "Top-3 session already running: $TOP3_SESSION"
  fi
  wait_for_session "$TOP3_SESSION"
}

run_uavdt_sweep() {
  if session_exists "$UAVDT_PENDING_SESSION"; then
    log "UAVDT pending session already exists: $UAVDT_PENDING_SESSION"
    wait_for_session "$UAVDT_PENDING_SESSION"
  else
    WAIT_FOR="" CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/train_uavdt_comparisons_after_session.sh
  fi
  wait_for_sessions_csv "$UAVDT_YOLO_SESSION,$UAVDT_RTDETR_SESSION"
}

collect_uavdt_results() {
  mkdir -p "$UAVDT_EXPERIMENT_ROOT" "$UAVDT_REPORT_DIR"
  DETECTOR_ROOTS="$UAVDT_DETECTOR_ROOT" \
    RESULTS_CSV="$UAVDT_EXPERIMENT_ROOT/uavdt_baseline_results.csv" \
    SUMMARY_CSV="$UAVDT_EXPERIMENT_ROOT/uavdt_baseline_summary.csv" \
    PVALUES_CSV="$UAVDT_EXPERIMENT_ROOT/uavdt_baseline_pvalues.csv" \
    DASHBOARD="$UAVDT_REPORT_DIR/uavdt_baseline_dashboard.png" \
    STAGE_GATE_JSON="$UAVDT_EXPERIMENT_ROOT/uavdt_stage_gate.json" \
    STAGE_GATE_MD="$UAVDT_EXPERIMENT_ROOT/uavdt_stage_gate.md" \
    STAGE_GATE_DATASET="UAVDT" \
    CONDA_ENV="$CONDA_ENV" \
    bash scripts/ubuntu/collect_server_results.sh "$UAVDT_DETECTOR_ROOT"
}

run_3d_sweep() {
  if session_exists "$GEN3D_SESSION"; then
    log "3D session already running: $GEN3D_SESSION"
  else
    SESSION="$GEN3D_SESSION" \
      RESULTS_DIR="$GEN3D_RESULTS_DIR" \
      CONDA_ENV="$CONDA_ENV" \
      bash scripts/ubuntu/train_3d_generators_tmux.sh "$GEN3D_SESSION" "$GEN3D_BENCHMARK"
  fi
  wait_for_session "$GEN3D_SESSION"
}

collect_3d_results() {
  CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/collect_3d_generation_results.sh "$GEN3D_RESULTS_DIR" "$GEN3D_COMPARISON_CSV"
}

run_auto_research() {
  CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/run_auto_research_loop.sh
}

publish_update() {
  bash scripts/ubuntu/publish_experiment_update.sh
}

start_self_in_tmux_if_requested

log "24h orchestrator started"
log "Options: ENABLE_TOP3=$ENABLE_TOP3 ENABLE_UAVDT=$ENABLE_UAVDT ENABLE_3D=$ENABLE_3D ENABLE_NOTION=$ENABLE_NOTION ENABLE_AUTO_RESEARCH=$ENABLE_AUTO_RESEARCH ENABLE_PUBLISH=$ENABLE_PUBLISH"
log "Log directory: $LOG_DIR"
log "Baseline wait sessions: $BASELINE_WAIT_SESSIONS"
log "Baseline detector roots: $ALL_BASELINE_ROOTS"

wait_for_sessions_csv "$BASELINE_WAIT_SESSIONS"
run_logged collect_large_results collect_large_results

if [[ "$ENABLE_TOP3" == "1" ]]; then
  run_logged top3_proposed_sweep start_or_wait_top3
  run_logged collect_combined_results collect_combined_results
else
  log "Skipping top-3 proposed sweep because ENABLE_TOP3=$ENABLE_TOP3"
fi

if [[ "$ENABLE_UAVDT" == "1" ]]; then
  run_optional uavdt_sweep run_uavdt_sweep
  run_optional collect_uavdt_results collect_uavdt_results
else
  log "Skipping UAVDT sweep because ENABLE_UAVDT=$ENABLE_UAVDT"
fi

if [[ "$ENABLE_3D" == "1" ]]; then
  run_optional gen3d_sweep run_3d_sweep
  run_optional collect_3d_results collect_3d_results
else
  log "Skipping 3D sweep because ENABLE_3D=$ENABLE_3D"
fi

if [[ "$ENABLE_AUTO_RESEARCH" == "1" ]]; then
  run_logged auto_research run_auto_research
else
  log "Skipping auto research because ENABLE_AUTO_RESEARCH=$ENABLE_AUTO_RESEARCH"
fi

if [[ "$ENABLE_PUBLISH" == "1" ]]; then
  run_logged publish_update publish_update
else
  log "Skipping publish step because ENABLE_PUBLISH=$ENABLE_PUBLISH"
fi

log "24h orchestrator complete"
