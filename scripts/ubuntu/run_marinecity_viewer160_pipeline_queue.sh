#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
CONTAINER_NAME=${CONTAINER_NAME:-isaac-sim-gui-uav-marinecity}
CONTAINER_USER=${CONTAINER_USER:-1234:1234}
HOST_UAV_ROOT=${HOST_UAV_ROOT:-/home/oem/UAV/uav_marinecity}
CONTAINER_UAV_ROOT=${CONTAINER_UAV_ROOT:-/workspace/uav_marinecity}
# Container-local GPU ordinal. The host may launch the Isaac container with
# `--gpus device=1`, but inside that container the visible GPU is usually `0`.
ISAAC_GPU=${ISAAC_GPU:-0}
CAPTURE_WIDTH=${CAPTURE_WIDTH:-1280}
CAPTURE_HEIGHT=${CAPTURE_HEIGHT:-720}
CAPTURE_OPEN_WARMUP=${CAPTURE_OPEN_WARMUP:-600}
CAPTURE_RENDER_WARMUP=${CAPTURE_RENDER_WARMUP:-120}
CAPTURE_HEADLESS=${CAPTURE_HEADLESS:-1}
CAPTURE_USE_ACTOR_SESSION=${CAPTURE_USE_ACTOR_SESSION:-1}
CAPTURE_BASE_STAGE=${CAPTURE_BASE_STAGE:-uavmarine.usd}
CAPTURE_CAMERA_PROFILE=${CAPTURE_CAMERA_PROFILE:-viewer160}
FORCE_RECAPTURE=${FORCE_RECAPTURE:-0}
FORCE_DETECTOR=${FORCE_DETECTOR:-0}
FORCE_REASONER=${FORCE_REASONER:-0}
DETECTOR_DEVICE=${DETECTOR_DEVICE:-cpu}
DETECTOR_CONF=${DETECTOR_CONF:-0.01}
DETECTOR_CONF_SLUG=${DETECTOR_CONF_SLUG:-conf001}
DETECTOR_IMGSZ=${DETECTOR_IMGSZ:-1280}
AEROGRAPH_COMMAND=${AEROGRAPH_COMMAND:-}
REASONER_PROVIDER=${REASONER_PROVIDER:-}
LOG_DIR=${LOG_DIR:-outputs/logs/marinecity_viewer160_pipeline}
STATE_DIR=${STATE_DIR:-outputs/experiments}
LIVE_DIR=${LIVE_DIR:-outputs/reports/live}
STATUS_MD="$STATE_DIR/marinecity_viewer160_pipeline_status.md"
STATUS_CSV="$STATE_DIR/marinecity_viewer160_pipeline_status.csv"
QUEUE_LOG="$LOG_DIR/queue.log"
WEIGHTS=${WEIGHTS:-outputs/detectors/server_yolov11_p2p4_balanced/20260610_073629_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt}

if [[ -z "$REASONER_PROVIDER" ]]; then
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    REASONER_PROVIDER=openai
  elif [[ -n "$AEROGRAPH_COMMAND" ]]; then
    REASONER_PROVIDER=command
  else
    REASONER_PROVIDER=mock
  fi
fi

mkdir -p "$LOG_DIR" "$STATE_DIR" "$LIVE_DIR"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

write_status_header() {
  if [[ ! -f "$STATUS_CSV" ]]; then
    echo "updated_at,scenario,step,status,artifact,note" > "$STATUS_CSV"
  fi
}

record_status() {
  local scenario="$1"
  local step="$2"
  local status="$3"
  local artifact="$4"
  local note="$5"
  printf '"%s","%s","%s","%s","%s","%s"\n' \
    "$(date -Is)" "$scenario" "$step" "$status" "$artifact" "$note" >> "$STATUS_CSV"
}

update_status_md() {
  local phase="$1"
  {
    echo "# MarineCity Viewer160 Pipeline Status"
    echo
    echo "- Updated: $(date -Is)"
    echo "- Phase: $phase"
    echo "- Isaac container: \`$CONTAINER_NAME\`"
    echo "- Capture profile: \`$CAPTURE_CAMERA_PROFILE\`"
    echo "- Detector: \`P2P4-SelfAttnFR\` checkpoint \`$WEIGHTS\`"
    echo "- Detector device: \`$DETECTOR_DEVICE\`"
    echo "- Reasoner provider: \`$REASONER_PROVIDER\`"
    if [[ "$REASONER_PROVIDER" == "openai" ]]; then
      echo "- External API reasoner: configured through \`OPENAI_API_KEY\`"
    elif [[ "$REASONER_PROVIDER" == "command" ]]; then
      echo "- Local/command LLM reasoner: configured through \`AEROGRAPH_COMMAND\`"
    else
      echo "- External/local reasoner: not configured; using rule-based verifier until \`OPENAI_API_KEY\` or \`AEROGRAPH_COMMAND\` is set"
    fi
    echo
    echo "## Scenario Queue"
    echo
    echo "| Scenario | Overlay USD | Capture | Detector | Reasoner |"
    echo "| --- | --- | --- | --- | --- |"
    local status_row status_scenario status_stage status_out_name
    for status_row in "${SCENARIOS[@]}"; do
      IFS='|' read -r status_scenario _ status_stage status_out_name <<< "$status_row"
      local host_out="$HOST_UAV_ROOT/outputs/isaac_exports/$status_out_name"
      local evidence_out="outputs/evidence/${status_out_name}_detector_smoke_${DETECTOR_CONF_SLUG}"
      local reasoner_slug="${REASONER_PROVIDER//-/_}"
      local reasoner_out="outputs/reasoning/${status_out_name}_from_detector_${DETECTOR_CONF_SLUG}_${reasoner_slug}"
      local cap="pending"
      local det="pending"
      local rea="pending"
      [[ -f "$host_out/real_cesium_capture_summary.json" ]] && cap="done"
      [[ -f "$evidence_out/detector_smoke_summary.json" ]] && det="done"
      [[ -f "$reasoner_out/summary.json" ]] && rea="done"
      echo "| $status_scenario | \`$status_stage\` | $cap | $det | $rea |"
    done
    echo
    echo "## Latest Queue Log"
    echo
    echo '```text'
    tail -n 35 "$QUEUE_LOG" 2>/dev/null || true
    echo '```'
  } > "$STATUS_MD"
}

refresh_dashboards() {
  update_status_md "${1:-running}"
  python scripts/build_marinecity_simulation_dashboard.py 2>&1 | tee -a "$QUEUE_LOG" || log "WARN marinecity dashboard update failed"
  PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png 2>&1 | tee -a "$QUEUE_LOG" || log "WARN training dashboard update failed"
}

container_running() {
  docker ps --format '{{.Names}}' | grep -Fx "$CONTAINER_NAME" >/dev/null 2>&1
}

deploy_capture_script() {
  mkdir -p "$HOST_UAV_ROOT/scripts"
  cp simulation/isaac/capture_realcities_multiuav.py "$HOST_UAV_ROOT/scripts/capture_realcities_multiuav.py"
  log "Deployed latest capture helper to $HOST_UAV_ROOT/scripts/capture_realcities_multiuav.py"
}

run_capture() {
  local scenario="$1"
  local stage_name="$2"
  local out_name="$3"
  local host_out="$HOST_UAV_ROOT/outputs/isaac_exports/$out_name"
  local container_stage="$CONTAINER_UAV_ROOT/$stage_name"
  local container_base_stage="$CONTAINER_UAV_ROOT/$CAPTURE_BASE_STAGE"
  local container_out="$CONTAINER_UAV_ROOT/outputs/isaac_exports/$out_name"
  local summary="$host_out/real_cesium_capture_summary.json"

  if [[ "$FORCE_RECAPTURE" != "1" && -f "$summary" ]]; then
    log "SKIP capture scenario=$scenario existing=$summary"
    record_status "$scenario" "capture" "skipped_existing" "$summary" "FORCE_RECAPTURE=1 to regenerate"
    return 0
  fi

  if ! container_running; then
    log "FAIL capture scenario=$scenario container_not_running=$CONTAINER_NAME"
    record_status "$scenario" "capture" "failed" "$container_stage" "Isaac GUI container is not running"
    return 1
  fi

  log "START capture scenario=$scenario stage=$container_stage out=$container_out actor_session=$CAPTURE_USE_ACTOR_SESSION camera_profile=$CAPTURE_CAMERA_PROFILE"
  record_status "$scenario" "capture" "started" "$container_out" "$CAPTURE_CAMERA_PROFILE real Cesium capture"
  local headless_args=()
  if [[ "$CAPTURE_HEADLESS" == "1" ]]; then
    headless_args+=(--headless)
  fi
  local stage_args=(--stage "$container_stage")
  if [[ "$CAPTURE_USE_ACTOR_SESSION" == "1" ]]; then
    stage_args=(--stage "$container_base_stage" --base-stage "$container_base_stage" --actor-layer "$container_stage")
  fi

  if docker exec -u "$CONTAINER_USER" -e ISAAC_ACTIVE_GPU="$ISAAC_GPU" "$CONTAINER_NAME" \
    /bin/bash -lc "cd '$CONTAINER_UAV_ROOT' && /isaac-sim/python.sh scripts/capture_realcities_multiuav.py ${stage_args[*]} --out-dir '$container_out' --width '$CAPTURE_WIDTH' --height '$CAPTURE_HEIGHT' --camera-profile '$CAPTURE_CAMERA_PROFILE' --open-warmup '$CAPTURE_OPEN_WARMUP' --render-warmup '$CAPTURE_RENDER_WARMUP' --active-gpu '$ISAAC_GPU' ${headless_args[*]}" \
    2>&1 | tee -a "$QUEUE_LOG"; then
    if [[ -f "$summary" ]]; then
      log "CAPTURE_OK scenario=$scenario summary=$summary"
      record_status "$scenario" "capture" "ok" "$summary" "real Cesium viewer160 capture complete"
      return 0
    fi
    log "FAIL capture scenario=$scenario summary_missing=$summary"
    record_status "$scenario" "capture" "failed" "$summary" "Capture command ended but summary is missing"
    return 1
  fi

  log "FAIL capture scenario=$scenario docker_exec_failed"
  record_status "$scenario" "capture" "failed" "$container_stage" "Docker/Isaac capture command failed"
  return 1
}

run_detector() {
  local scenario="$1"
  local out_name="$2"
  local host_out="$HOST_UAV_ROOT/outputs/isaac_exports/$out_name"
  local summary="$host_out/real_cesium_capture_summary.json"
  local capture_plan="$host_out/capture_plan.json"
  local evidence_out="outputs/evidence/${out_name}_detector_smoke_${DETECTOR_CONF_SLUG}"

  if [[ ! -f "$summary" || ! -f "$capture_plan" ]]; then
    log "SKIP detector scenario=$scenario capture_artifacts_missing"
    record_status "$scenario" "detector" "skipped_missing_capture" "$evidence_out" "Need real_cesium_capture_summary.json and capture_plan.json"
    return 1
  fi
  if [[ ! -f "$WEIGHTS" ]]; then
    log "FAIL detector scenario=$scenario weights_missing=$WEIGHTS"
    record_status "$scenario" "detector" "failed" "$WEIGHTS" "Selected detector checkpoint missing"
    return 1
  fi
  if [[ "$FORCE_DETECTOR" != "1" && -f "$evidence_out/detector_smoke_summary.json" ]]; then
    log "SKIP detector scenario=$scenario existing=$evidence_out/detector_smoke_summary.json"
    record_status "$scenario" "detector" "skipped_existing" "$evidence_out" "FORCE_DETECTOR=1 to regenerate"
    return 0
  fi

  log "START detector scenario=$scenario out=$evidence_out"
  record_status "$scenario" "detector" "started" "$evidence_out" "P2P4-SelfAttnFR EvidenceToken extraction"
  if PYTHONPATH=. conda run --no-capture-output -n "$CONDA_ENV" python scripts/run_marinecity_detector_smoke.py \
    --summary "$summary" \
    --capture-plan "$capture_plan" \
    --weights "$WEIGHTS" \
    --out-dir "$evidence_out" \
    --device "$DETECTOR_DEVICE" \
    --imgsz "$DETECTOR_IMGSZ" \
    --conf "$DETECTOR_CONF" 2>&1 | tee -a "$QUEUE_LOG"; then
    log "DETECTOR_OK scenario=$scenario out=$evidence_out"
    record_status "$scenario" "detector" "ok" "$evidence_out/detector_smoke_summary.json" "EvidenceTokens generated"
    return 0
  fi

  log "FAIL detector scenario=$scenario"
  record_status "$scenario" "detector" "failed" "$evidence_out" "Detector smoke script failed"
  return 1
}

run_reasoner() {
  local scenario="$1"
  local reasoner_scenario="$2"
  local out_name="$3"
  local evidence_out="outputs/evidence/${out_name}_detector_smoke_${DETECTOR_CONF_SLUG}"
  local tokens="$evidence_out/evidence_tokens.jsonl"
  local reasoner_slug="${REASONER_PROVIDER//-/_}"
  local reasoner_out="outputs/reasoning/${out_name}_from_detector_${DETECTOR_CONF_SLUG}_${reasoner_slug}"

  if [[ ! -f "$tokens" ]]; then
    log "SKIP reasoner scenario=$scenario tokens_missing=$tokens"
    record_status "$scenario" "reasoner" "skipped_missing_tokens" "$tokens" "Need detector EvidenceTokens"
    return 1
  fi
  if [[ "$FORCE_REASONER" != "1" && -f "$reasoner_out/summary.json" ]]; then
    log "SKIP reasoner scenario=$scenario existing=$reasoner_out/summary.json"
    record_status "$scenario" "reasoner" "skipped_existing" "$reasoner_out" "FORCE_REASONER=1 to regenerate"
    return 0
  fi

  local provider_args=(--provider "$REASONER_PROVIDER")
  if [[ "$REASONER_PROVIDER" == "command" ]]; then
    provider_args+=(--command "$AEROGRAPH_COMMAND")
  fi

  log "START reasoner scenario=$scenario provider=$REASONER_PROVIDER out=$reasoner_out"
  record_status "$scenario" "reasoner" "started" "$reasoner_out" "3D evidence graph + AeroGraph Reasoner"
  if PYTHONPATH=. conda run --no-capture-output -n "$CONDA_ENV" python scripts/run_marinecity_3d_reasoner_smoke.py \
    --scenario "$reasoner_scenario" \
    --tokens "$tokens" \
    "${provider_args[@]}" \
    --out-dir "$reasoner_out" 2>&1 | tee -a "$QUEUE_LOG"; then
    log "REASONER_OK scenario=$scenario out=$reasoner_out"
    record_status "$scenario" "reasoner" "ok" "$reasoner_out/summary.json" "Reasoner output generated"
    return 0
  fi

  log "FAIL reasoner scenario=$scenario"
  record_status "$scenario" "reasoner" "failed" "$reasoner_out" "Reasoner script failed"
  return 1
}

SCENARIOS=(
  "S0|s0_locked_roi|uavmarine_multiuav_actor_overlay_s0_locked_roi.usda|uavmarine_s0_viewer160_session_recapture"
  "S1|s1_adjacent_overlap|uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda|uavmarine_s1_viewer160_session_recapture"
  "S2|s2_coastline_multiview|uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda|uavmarine_s2_viewer160_session_recapture"
)

main() {
  write_status_header
  log "MarineCity viewer160 pipeline queue started"
  log "Policy: no fake city, no placeholder/proxy geometry, no USD overwrite"
  log "Container=$CONTAINER_NAME host_uav_root=$HOST_UAV_ROOT reasoner=$REASONER_PROVIDER"
  deploy_capture_script
  refresh_dashboards "started"

  local completed=0
  local failed=0
  for row in "${SCENARIOS[@]}"; do
    IFS='|' read -r scenario reasoner_scenario stage out_name <<< "$row"
    log "SCENARIO_BEGIN $scenario reasoner_scenario=$reasoner_scenario"
    if run_capture "$scenario" "$stage" "$out_name"; then
      refresh_dashboards "capture-ok-$scenario"
    else
      failed=$((failed + 1))
      refresh_dashboards "capture-failed-$scenario"
      continue
    fi

    if run_detector "$scenario" "$out_name"; then
      refresh_dashboards "detector-ok-$scenario"
    else
      failed=$((failed + 1))
      refresh_dashboards "detector-failed-$scenario"
      continue
    fi

    if run_reasoner "$scenario" "$reasoner_scenario" "$out_name"; then
      completed=$((completed + 1))
      refresh_dashboards "reasoner-ok-$scenario"
    else
      failed=$((failed + 1))
      refresh_dashboards "reasoner-failed-$scenario"
      continue
    fi
    log "SCENARIO_DONE $scenario"
  done

  log "QUEUE_FINISHED marinecity_viewer160 completed=$completed failed=$failed"
  refresh_dashboards "finished completed=$completed failed=$failed"
  if [[ "$completed" -eq 0 ]]; then
    exit 1
  fi
}

main "$@"
