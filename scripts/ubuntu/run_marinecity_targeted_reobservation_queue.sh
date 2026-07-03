#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
CONTAINER_NAME=${CONTAINER_NAME:-isaac-sim-gui-uav-marinecity}
CONTAINER_USER=${CONTAINER_USER:-1234:1234}
HOST_UAV_ROOT=${HOST_UAV_ROOT:-/home/oem/UAV/uav_marinecity}
CONTAINER_UAV_ROOT=${CONTAINER_UAV_ROOT:-/workspace/uav_marinecity}
ISAAC_GPU=${ISAAC_GPU:-0}
CAPTURE_WIDTH=${CAPTURE_WIDTH:-1280}
CAPTURE_HEIGHT=${CAPTURE_HEIGHT:-720}
CAPTURE_OPEN_WARMUP=${CAPTURE_OPEN_WARMUP:-600}
CAPTURE_RENDER_WARMUP=${CAPTURE_RENDER_WARMUP:-120}
CAPTURE_HEADLESS=${CAPTURE_HEADLESS:-1}
CAPTURE_BASE_STAGE=${CAPTURE_BASE_STAGE:-uavmarine.usd}
CAPTURE_CAMERA_PROFILE=${CAPTURE_CAMERA_PROFILE:-viewer160}
DETECTOR_DEVICE=${DETECTOR_DEVICE:-cpu}
DETECTOR_CONF=${DETECTOR_CONF:-0.01}
DETECTOR_CONF_SLUG=${DETECTOR_CONF_SLUG:-conf001}
DETECTOR_IMGSZ=${DETECTOR_IMGSZ:-1280}
FORCE_RECAPTURE=${FORCE_RECAPTURE:-0}
FORCE_DETECTOR=${FORCE_DETECTOR:-0}
SKIP_DEPLOY=${SKIP_DEPLOY:-0}
LOG_DIR=${LOG_DIR:-outputs/logs/marinecity_targeted_reobservation}
STATE_DIR=${STATE_DIR:-outputs/experiments}
LIVE_DIR=${LIVE_DIR:-outputs/reports/live}
PLAN_JSON=${PLAN_JSON:-outputs/experiments/marinecity_targeted_reobservation_plan_20260703.json}
PLAN_SPLIT_DIR=${PLAN_SPLIT_DIR:-outputs/experiments/marinecity_targeted_reobservation_plan_20260703}
FRESH_TOKEN_DIR=${FRESH_TOKEN_DIR:-outputs/evidence/marinecity_targeted_reobservation_fresh_20260703}
FRESH_REPORT_DIR=${FRESH_REPORT_DIR:-outputs/reports/live/closed_loop_reobservation_fresh_20260703}
STATUS_MD="$STATE_DIR/marinecity_targeted_reobservation_status.md"
STATUS_CSV="$STATE_DIR/marinecity_targeted_reobservation_status.csv"
QUEUE_LOG="$LOG_DIR/queue.log"
WEIGHTS=${WEIGHTS:-outputs/detectors/server_yolov11_p2p4_balanced/20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt}

mkdir -p "$LOG_DIR" "$STATE_DIR" "$LIVE_DIR" "$FRESH_TOKEN_DIR"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record_status() {
  if [[ ! -f "$STATUS_CSV" ]]; then
    echo "updated_at,scenario,step,status,artifact,note" > "$STATUS_CSV"
  fi
  printf '"%s","%s","%s","%s","%s","%s"\n' \
    "$(date -Is)" "$1" "$2" "$3" "$4" "$5" >> "$STATUS_CSV"
}

update_status_md() {
  local phase="$1"
  {
    echo "# MarineCity Targeted Re-observation Status"
    echo
    echo "- Updated: $(date -Is)"
    echo "- Phase: $phase"
    echo "- Isaac container: \`$CONTAINER_NAME\`"
    echo "- Plan: \`$PLAN_JSON\`"
    echo "- Fresh token dir: \`$FRESH_TOKEN_DIR\`"
    echo "- Fresh report dir: \`$FRESH_REPORT_DIR\`"
    echo "- Detector device: \`$DETECTOR_DEVICE\`"
    echo
    echo "## How to Watch"
    echo
    echo "- Attach: \`tmux attach -t ${SESSION:-marinecity-targeted-reobs}\`"
    echo "- Log: \`tail -f $QUEUE_LOG\`"
    echo
    echo "## Latest Log"
    echo
    echo '```text'
    tail -n 45 "$QUEUE_LOG" 2>/dev/null || true
    echo '```'
  } > "$STATUS_MD"
}

container_running() {
  docker ps --format '{{.Names}}' | grep -Fx "$CONTAINER_NAME" >/dev/null 2>&1
}

deploy_inputs() {
  if [[ "$SKIP_DEPLOY" == "1" ]]; then
    log "SKIP deploy_inputs SKIP_DEPLOY=1"
    return 0
  fi
  mkdir -p "$HOST_UAV_ROOT/scripts" "$HOST_UAV_ROOT/outputs/experiments"
  cp simulation/isaac/capture_realcities_multiuav.py "$HOST_UAV_ROOT/scripts/capture_realcities_multiuav.py"
  cp -a "$PLAN_SPLIT_DIR" "$HOST_UAV_ROOT/outputs/experiments/"
  log "Deployed capture helper and camera plans to $HOST_UAV_ROOT"
}

build_plan() {
  log "START build targeted re-observation plan"
  PYTHONPATH=. python scripts/build_marinecity_targeted_reobservation_plan.py \
    --out "$PLAN_JSON" \
    --split-dir "$PLAN_SPLIT_DIR" 2>&1 | tee -a "$QUEUE_LOG"
  record_status "ALL" "plan" "ok" "$PLAN_JSON" "9 targeted re-observation frames expected"
}

run_capture() {
  local scenario="$1"
  local stage_name="$2"
  local out_name="$3"
  local plan_name="$4"
  local host_out="$HOST_UAV_ROOT/outputs/isaac_exports/$out_name"
  local summary="$host_out/real_cesium_capture_summary.json"
  local container_stage="$CONTAINER_UAV_ROOT/$stage_name"
  local container_base_stage="$CONTAINER_UAV_ROOT/$CAPTURE_BASE_STAGE"
  local container_out="$CONTAINER_UAV_ROOT/outputs/isaac_exports/$out_name"
  local container_plan="$CONTAINER_UAV_ROOT/outputs/experiments/$(basename "$PLAN_SPLIT_DIR")/$plan_name"

  if [[ "$FORCE_RECAPTURE" != "1" && -f "$summary" ]]; then
    log "SKIP capture scenario=$scenario existing=$summary"
    record_status "$scenario" "capture" "skipped_existing" "$summary" "FORCE_RECAPTURE=1 to regenerate"
    return 0
  fi
  if ! container_running; then
    log "FAIL capture scenario=$scenario container_not_running=$CONTAINER_NAME"
    record_status "$scenario" "capture" "failed" "$CONTAINER_NAME" "Start Isaac GUI container first"
    return 1
  fi

  local headless_args=()
  if [[ "$CAPTURE_HEADLESS" == "1" ]]; then
    headless_args+=(--headless)
  fi
  log "START targeted capture scenario=$scenario plan=$container_plan out=$container_out"
  record_status "$scenario" "capture" "started" "$container_out" "$container_plan"
  if docker exec -u "$CONTAINER_USER" -e ISAAC_ACTIVE_GPU="$ISAAC_GPU" "$CONTAINER_NAME" \
    /bin/bash -lc "cd '$CONTAINER_UAV_ROOT' && /isaac-sim/python.sh scripts/capture_realcities_multiuav.py --stage '$container_base_stage' --base-stage '$container_base_stage' --actor-layer '$container_stage' --camera-plan '$container_plan' --out-dir '$container_out' --width '$CAPTURE_WIDTH' --height '$CAPTURE_HEIGHT' --camera-profile '$CAPTURE_CAMERA_PROFILE' --open-warmup '$CAPTURE_OPEN_WARMUP' --render-warmup '$CAPTURE_RENDER_WARMUP' --active-gpu '$ISAAC_GPU' ${headless_args[*]}" \
    2>&1 | tee -a "$QUEUE_LOG"; then
    if [[ -f "$summary" ]]; then
      log "CAPTURE_OK scenario=$scenario summary=$summary"
      record_status "$scenario" "capture" "ok" "$summary" "fresh targeted recapture complete"
      return 0
    fi
  fi
  log "FAIL capture scenario=$scenario"
  record_status "$scenario" "capture" "failed" "$summary" "capture command failed or summary missing"
  return 1
}

run_detector() {
  local scenario="$1"
  local out_name="$2"
  local host_out="$HOST_UAV_ROOT/outputs/isaac_exports/$out_name"
  local summary="$host_out/real_cesium_capture_summary.json"
  local capture_plan="$host_out/capture_plan.json"
  local evidence_out="outputs/evidence/${out_name}_detector_smoke_${DETECTOR_CONF_SLUG}"

  if [[ "$FORCE_DETECTOR" != "1" && -f "$evidence_out/detector_smoke_summary.json" ]]; then
    log "SKIP detector scenario=$scenario existing=$evidence_out"
    record_status "$scenario" "detector" "skipped_existing" "$evidence_out" "FORCE_DETECTOR=1 to regenerate"
    return 0
  fi
  if [[ ! -f "$summary" || ! -f "$capture_plan" ]]; then
    log "FAIL detector scenario=$scenario capture_missing"
    record_status "$scenario" "detector" "failed" "$summary" "missing capture summary or plan"
    return 1
  fi
  if [[ ! -f "$WEIGHTS" ]]; then
    log "FAIL detector scenario=$scenario weights_missing=$WEIGHTS"
    record_status "$scenario" "detector" "failed" "$WEIGHTS" "weights missing"
    return 1
  fi

  log "START detector scenario=$scenario evidence_out=$evidence_out"
  record_status "$scenario" "detector" "started" "$evidence_out" "fresh targeted EvidenceTokens"
  if PYTHONPATH=. conda run --no-capture-output -n "$CONDA_ENV" python scripts/run_marinecity_detector_smoke.py \
    --summary "$summary" \
    --capture-plan "$capture_plan" \
    --weights "$WEIGHTS" \
    --out-dir "$evidence_out" \
    --device "$DETECTOR_DEVICE" \
    --imgsz "$DETECTOR_IMGSZ" \
    --conf "$DETECTOR_CONF" 2>&1 | tee -a "$QUEUE_LOG"; then
    log "DETECTOR_OK scenario=$scenario evidence=$evidence_out"
    record_status "$scenario" "detector" "ok" "$evidence_out/evidence_tokens.jsonl" "fresh tokens generated"
    return 0
  fi
  log "FAIL detector scenario=$scenario"
  record_status "$scenario" "detector" "failed" "$evidence_out" "detector failed"
  return 1
}

merge_tokens() {
  local token_file="$FRESH_TOKEN_DIR/evidence_tokens.jsonl"
  : > "$token_file"
  for row in "${SCENARIOS[@]}"; do
    IFS='|' read -r _ _ out_name _ <<< "$row"
    local source="outputs/evidence/${out_name}_detector_smoke_${DETECTOR_CONF_SLUG}/evidence_tokens.jsonl"
    if [[ -f "$source" ]]; then
      cat "$source" >> "$token_file"
    fi
  done
  local count
  count=$(wc -l < "$token_file" | tr -d ' ')
  log "MERGE_TOKENS count=$count out=$token_file"
  record_status "ALL" "merge_tokens" "ok" "$token_file" "token_count=$count"
}

build_fresh_report() {
  log "START closed-loop fresh report"
  PYTHONPATH=. python scripts/build_marinecity_closed_loop_reobservation.py \
    --reobserve-tokens "$FRESH_TOKEN_DIR/evidence_tokens.jsonl" \
    --out-dir "$FRESH_REPORT_DIR" 2>&1 | tee -a "$QUEUE_LOG"
  record_status "ALL" "closed_loop_report" "ok" "$FRESH_REPORT_DIR" "fresh targeted report generated"
}

SCENARIOS=(
  "S0|uavmarine_multiuav_actor_overlay_s0_locked_roi.usda|uavmarine_s0_targeted_reobservation_20260703|targeted_reobservation_plan_S0.json"
  "S1|uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda|uavmarine_s1_targeted_reobservation_20260703|targeted_reobservation_plan_S1.json"
  "S2|uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda|uavmarine_s2_targeted_reobservation_20260703|targeted_reobservation_plan_S2.json"
)

main() {
  log "MarineCity targeted re-observation queue started"
  update_status_md "started"
  build_plan
  deploy_inputs

  local completed=0
  local failed=0
  for row in "${SCENARIOS[@]}"; do
    IFS='|' read -r scenario stage out_name plan_name <<< "$row"
    log "SCENARIO_BEGIN $scenario"
    if run_capture "$scenario" "$stage" "$out_name" "$plan_name"; then
      update_status_md "capture-ok-$scenario"
    else
      failed=$((failed + 1))
      update_status_md "capture-failed-$scenario"
      continue
    fi
    if run_detector "$scenario" "$out_name"; then
      completed=$((completed + 1))
      update_status_md "detector-ok-$scenario"
    else
      failed=$((failed + 1))
      update_status_md "detector-failed-$scenario"
    fi
  done

  merge_tokens
  build_fresh_report
  log "QUEUE_FINISHED targeted_reobservation completed=$completed failed=$failed"
  update_status_md "finished completed=$completed failed=$failed"
}

main "$@"
