#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SESSION_PRIORITY=${SESSION_PRIORITY:-priority-detector-queue-rerun}
LOG_DIR=${LOG_DIR:-outputs/logs/remaining_experiments_queue}
STATE_DIR=${STATE_DIR:-outputs/experiments/remaining_experiments_queue}
REPORT_DIR=${REPORT_DIR:-outputs/reports/remaining_experiments_queue}
POLL_SECONDS=${POLL_SECONDS:-300}

RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/remaining_experiments_queue/detector_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/remaining_experiments_queue/detector_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/remaining_experiments_queue/detector_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/remaining_experiments_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/remaining_experiments_queue/stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/remaining_experiments_queue/stage_gate.md}
PROPOSED_GATE_JSON=${PROPOSED_GATE_JSON:-outputs/experiments/remaining_experiments_queue/proposed_overwhelm_gate.json}
PROPOSED_GATE_MD=${PROPOSED_GATE_MD:-outputs/experiments/remaining_experiments_queue/proposed_overwhelm_gate.md}

RUN_PRIORITY_QUEUE=${RUN_PRIORITY_QUEUE:-1}
RUN_FINAL_COLLECTION=${RUN_FINAL_COLLECTION:-1}
RUN_PUBLISH_SNAPSHOT=${RUN_PUBLISH_SNAPSHOT:-0}
PRIORITY_FINISH_MARKER=${PRIORITY_FINISH_MARKER:-Priority detector queue finished}

mkdir -p "$LOG_DIR" "$STATE_DIR" "$REPORT_DIR" "$(dirname "$DASHBOARD")"
QUEUE_LOG="$LOG_DIR/queue.log"
PLAN_TSV="$STATE_DIR/remaining_queue_plan.tsv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record_plan() {
  local stage="$1"
  local status="$2"
  local detail="$3"
  if [[ ! -f "$PLAN_TSV" ]]; then
    printf "updated_at\tstage\tstatus\tdetail\n" > "$PLAN_TSV"
  fi
  printf "%s\t%s\t%s\t%s\n" "$(date -Is)" "$stage" "$status" "$detail" >> "$PLAN_TSV"
}

session_exists() {
  tmux has-session -t "$1" 2>/dev/null
}

session_text_has_marker() {
  local session="$1"
  local marker="$2"
  local text
  text=$(tmux capture-pane -pt "$session:0" -S -300 2>/dev/null || true)
  grep -Fq "$marker" <<< "$text"
}

log_has_marker() {
  local marker="$1"
  [[ -f "outputs/logs/priority_detector_queue/queue.log" ]] || return 1
  grep -Fq "$marker" outputs/logs/priority_detector_queue/queue.log
}

ensure_priority_queue() {
  if [[ "$RUN_PRIORITY_QUEUE" != "1" ]]; then
    log "Priority detector queue disabled by RUN_PRIORITY_QUEUE=$RUN_PRIORITY_QUEUE"
    record_plan "priority_detector_queue" "skipped" "disabled"
    return 0
  fi

  if log_has_marker "$PRIORITY_FINISH_MARKER"; then
    log "Priority detector queue already has finish marker."
    record_plan "priority_detector_queue" "already_finished" "$PRIORITY_FINISH_MARKER"
    return 0
  fi

  if session_exists "$SESSION_PRIORITY"; then
    log "Priority detector queue already running: $SESSION_PRIORITY"
    record_plan "priority_detector_queue" "running" "$SESSION_PRIORITY"
    return 0
  fi

  log "Starting priority detector queue: $SESSION_PRIORITY"
  SESSION="$SESSION_PRIORITY" CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/start_priority_detector_queue.sh
  record_plan "priority_detector_queue" "started" "$SESSION_PRIORITY"
}

wait_for_priority_queue() {
  if log_has_marker "$PRIORITY_FINISH_MARKER"; then
    log "Priority detector queue finish marker found in log."
    record_plan "priority_detector_queue" "complete" "log marker"
    return 0
  fi

  while true; do
    if session_exists "$SESSION_PRIORITY" && session_text_has_marker "$SESSION_PRIORITY" "$PRIORITY_FINISH_MARKER"; then
      log "Priority detector queue finish marker found in tmux session."
      record_plan "priority_detector_queue" "complete" "tmux marker"
      return 0
    fi
    if log_has_marker "$PRIORITY_FINISH_MARKER"; then
      log "Priority detector queue finish marker found in log."
      record_plan "priority_detector_queue" "complete" "log marker"
      return 0
    fi
    log "Waiting for priority detector queue to finish: $SESSION_PRIORITY"
    sleep "$POLL_SECONDS"
  done
}

existing_roots_csv() {
  local candidates=(
    "outputs/detectors/server_baselines"
    "outputs/detectors/server_fresh_baselines"
    "outputs/detectors/server_yolov11_p2p4_balanced"
    "outputs/detectors/server_yolov11_p2_module_search"
    "outputs/detectors/server_yolov11_p2_module_nms055"
    "outputs/detectors/server_yolov11_p2_compact_ideas"
    "outputs/detectors/server_yolov11_p2_balanced_v2"
    "outputs/detectors/server_yolov11_p2_balanced_v3"
    "outputs/detectors/server_yolov11_p2_compression"
    "outputs/detectors/nms_sweep_efficient"
    "outputs/detectors/nms_sweep_accuracy"
    "outputs/detectors/related_work_detectors"
  )
  local roots=()
  local root
  for root in "${candidates[@]}"; do
    [[ -d "$root" ]] && roots+=("$root")
  done
  local IFS=,
  echo "${roots[*]}"
}

collect_final_results() {
  if [[ "$RUN_FINAL_COLLECTION" != "1" ]]; then
    log "Final collection disabled by RUN_FINAL_COLLECTION=$RUN_FINAL_COLLECTION"
    record_plan "final_collection" "skipped" "disabled"
    return 0
  fi

  local roots
  roots=$(existing_roots_csv)
  log "Collecting final remaining-experiment results from: $roots"
  record_plan "final_collection" "running" "$roots"

  DETECTOR_ROOTS="$roots" \
  RESULTS_CSV="$RESULTS_CSV" \
  SUMMARY_CSV="$SUMMARY_CSV" \
  PVALUES_CSV="$PVALUES_CSV" \
  DASHBOARD="$DASHBOARD" \
  STAGE_GATE_JSON="$STAGE_GATE_JSON" \
  STAGE_GATE_MD="$STAGE_GATE_MD" \
  PROPOSED_GATE_JSON="$PROPOSED_GATE_JSON" \
  PROPOSED_GATE_MD="$PROPOSED_GATE_MD" \
  REPORT_DIR="$REPORT_DIR" \
  CONDA_ENV="$CONDA_ENV" \
  bash scripts/ubuntu/collect_server_results.sh "$roots"

  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.collect_related_work_detector_results || \
    log "WARN: related-work result collection returned non-zero"

  record_plan "final_collection" "complete" "$SUMMARY_CSV"
}

publish_snapshot() {
  if [[ "$RUN_PUBLISH_SNAPSHOT" != "1" ]]; then
    log "Publish snapshot disabled by RUN_PUBLISH_SNAPSHOT=$RUN_PUBLISH_SNAPSHOT"
    record_plan "publish_snapshot" "skipped" "disabled"
    return 0
  fi

  log "Publishing non-committing experiment snapshot."
  record_plan "publish_snapshot" "running" "no commit/push"
  DO_MAIN_COMMIT=0 \
  DO_MAIN_PUSH=0 \
  DO_OVERLEAF_COMMIT=0 \
  DO_OVERLEAF_PUSH=0 \
  DO_NOTION_UPDATE=0 \
  CONDA_ENV="$CONDA_ENV" \
  bash scripts/ubuntu/publish_experiment_update.sh
  record_plan "publish_snapshot" "complete" "snapshot generated"
}

main() {
  log "Remaining experiments queue started"
  record_plan "queue" "started" "priority -> final collection -> optional snapshot"
  ensure_priority_queue
  wait_for_priority_queue
  collect_final_results
  publish_snapshot
  record_plan "queue" "complete" "remaining experiments queue finished"
  log "QUEUE_FINISHED remaining experiments"
  log "Plan TSV: $PLAN_TSV"
  log "Dashboard: $DASHBOARD"
  log "Report: $REPORT_DIR/README.md"
}

main "$@"
