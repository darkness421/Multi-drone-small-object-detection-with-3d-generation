#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
WAIT_FOR=${WAIT_FOR:-priority-detector-queue,priority-detector-queue-rerun,remaining-experiments-queue,server-extra-comparison-medium,server-extra-comparison-large}
POLL_SECONDS=${POLL_SECONDS:-300}
GPU_LIST=${GPU_LIST:-0,1}
SEEDS=${SEEDS:-42,123,2026}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-4}
IMG_SIZE=${IMG_SIZE:-1280}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
MODEL_YAML=${MODEL_YAML:-configs/detector/yolo11l-p2p4-balanced-v1.yaml}
INIT_WEIGHTS=${INIT_WEIGHTS:-yolo11l.pt}
PROJECT=${PROJECT:-outputs/detectors/server_yolov11_p2p4_balanced}
LOG_DIR=${LOG_DIR:-outputs/logs/server_yolov11_p2p4_balanced}
QUEUE_LOG_DIR=${QUEUE_LOG_DIR:-outputs/logs/final_p2p4_selfattnfr_ablation_queue}
STATE_DIR=${STATE_DIR:-outputs/experiments/final_p2p4_selfattnfr_ablation_queue}
REPORT_DIR=${REPORT_DIR:-outputs/reports/final_p2p4_selfattnfr_ablation_queue}
RUN_NMS_EVAL=${RUN_NMS_EVAL:-1}
NMS_CONF=${NMS_CONF:-0.001}
NMS_IOUS=${NMS_IOUS:-0.45,0.55,0.65}
RUN_SUPPLEMENTARY=${RUN_SUPPLEMENTARY:-0}

RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/final_p2p4_selfattnfr_ablation_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/final_p2p4_selfattnfr_ablation_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/final_p2p4_selfattnfr_ablation_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/final_p2p4_selfattnfr_ablation_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/final_p2p4_selfattnfr_ablation_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/final_p2p4_selfattnfr_ablation_stage_gate.md}

mkdir -p "$QUEUE_LOG_DIR" "$STATE_DIR" "$REPORT_DIR" "$(dirname "$DASHBOARD")" "$LOG_DIR" "$PROJECT"
QUEUE_LOG="$QUEUE_LOG_DIR/queue.log"
PLAN_TSV="$STATE_DIR/plan.tsv"

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

wait_for_sessions() {
  local sessions=$1
  [[ -z "$sessions" ]] && return 0
  while true; do
    local active=()
    IFS=',' read -r -a session_list <<< "$sessions"
    for session in "${session_list[@]}"; do
      session=${session//[[:space:]]/}
      [[ -z "$session" ]] && continue
      if session_exists "$session"; then
        active+=("$session")
      fi
    done
    if [[ "${#active[@]}" -eq 0 ]]; then
      return 0
    fi
    log "Waiting for active sessions before final ablation queue: ${active[*]}"
    record_plan "wait" "running" "${active[*]}"
    sleep "$POLL_SECONDS"
  done
}

completed_best_exists() {
  local ablation="$1"
  local seed="$2"
  find "$PROJECT" -maxdepth 4 \
    -path "*proposed_${ablation}_yolo11l*seed${seed}/ultralytics/weights/best.pt" \
    -type f -print -quit | grep -q .
}

latest_weight() {
  local ablation="$1"
  local seed="$2"
  find "$PROJECT" -maxdepth 4 \
    -path "*proposed_${ablation}_yolo11l*seed${seed}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-
}

start_train_session() {
  local session="$1"
  local gpu="$2"
  local ablation="$3"
  local seed="$4"

  if completed_best_exists "$ablation" "$seed"; then
    log "Skipping completed train job: $ablation seed=$seed"
    record_plan "$ablation" "skipped_completed" "seed=$seed"
    return 1
  fi

  if session_exists "$session"; then
    log "Session already exists, waiting instead of starting duplicate: $session"
    record_plan "$ablation" "already_running" "$session seed=$seed"
    return 0
  fi

  log "Starting final ablation train session=$session gpu=$gpu ablation=$ablation seed=$seed"
  record_plan "$ablation" "started" "session=$session gpu=$gpu seed=$seed"
  tmux new-session -d -s "$session" -n train \
    "cd '$PWD' && TARGET_GPU='$gpu' SEED='$seed' ABLATION='$ablation' MODEL_YAML='$MODEL_YAML' P2P4_MODEL_YAML='$MODEL_YAML' INIT_WEIGHTS='$INIT_WEIGHTS' DATA_YAML='$DATA_YAML' PROJECT='$PROJECT' LOG_DIR='$LOG_DIR' CONDA_ENV='$CONDA_ENV' EPOCHS='$EPOCHS' PATIENCE='$PATIENCE' BATCH='$BATCH' IMG_SIZE='$IMG_SIZE' GUARD_WAIT_SECONDS=120 MIN_GPU_FREE_GB=8 LOCK_PROPOSED_TO_GPU0=0 bash scripts/ubuntu/start_yolov11_p2_balanced_search.sh"
  return 0
}

run_train_jobs() {
  local ablations=(
    p2p4_balanced_head_only
    p2p4_balanced_tiny_frelu
    p2p4_balanced_selfattn_only
    p2p4_balanced_selfattn_tiny_frelu
  )
  if [[ "$RUN_SUPPLEMENTARY" == "1" ]]; then
    ablations+=(
      p2p4_balanced_se_tiny_frelu
      p2p4_balanced_dynfreq_p2_tiny_frelu
      p2p4_balanced_dynfreq_small_tiny_frelu
    )
  fi

  IFS=',' read -r -a gpus <<< "$GPU_LIST"
  IFS=',' read -r -a seeds <<< "$SEEDS"
  local batch_sessions=()
  local job_index=0

  for ablation in "${ablations[@]}"; do
    for seed in "${seeds[@]}"; do
      seed=${seed//[[:space:]]/}
      [[ -z "$seed" ]] && continue
      local gpu="${gpus[$((job_index % ${#gpus[@]}))]}"
      gpu=${gpu//[[:space:]]/}
      local session="final-ablation-${ablation//_/-}-s${seed}"
      if start_train_session "$session" "$gpu" "$ablation" "$seed"; then
        batch_sessions+=("$session")
      fi
      job_index=$((job_index + 1))

      if [[ "${#batch_sessions[@]}" -ge "${#gpus[@]}" ]]; then
        local IFS=,
        wait_for_sessions "${batch_sessions[*]}"
        batch_sessions=()
      fi
    done
  done

  if [[ "${#batch_sessions[@]}" -gt 0 ]]; then
    local IFS=,
    wait_for_sessions "${batch_sessions[*]}"
  fi
}

run_nms_eval_for_seed() {
  local gpu="$1"
  local seed="$2"
  local iou="$3"
  local weight
  weight=$(latest_weight p2p4_balanced_selfattn_tiny_frelu "$seed")
  if [[ -z "$weight" || ! -f "$weight" ]]; then
    log "Skipping NMS eval: missing final weight for seed=$seed"
    record_plan "nms_iou_$iou" "missing_weight" "seed=$seed"
    return 0
  fi

  local iou_slug=${iou/./}
  local name="eval_p2p4_selfattnfr_nms${iou_slug}_seed${seed}"
  local log_file="$QUEUE_LOG_DIR/${name}.log"
  log "Running NMS eval seed=$seed iou=$iou gpu=$gpu weight=$weight"
  record_plan "nms_iou_$iou" "running" "seed=$seed gpu=$gpu"
  conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
    --model "$weight" \
    --data-yaml "$DATA_YAML" \
    --imgsz "$IMG_SIZE" \
    --device "$gpu" \
    --conf "$NMS_CONF" \
    --iou "$iou" \
    --project "$PROJECT" \
    --name "$name" \
    --method "Ours: P2P4-SelfAttnFR + NMS@${iou}" \
    --ablation "p2p4_balanced_selfattn_tiny_frelu+nms${iou_slug}" \
    --base-model yolo11l.pt \
    --proposed-module "p2p4_balanced_head+lite_self_attention_neck+tiny_frelu_neck+class_aware_nms_iou_${iou_slug}" \
    --model-patches "lite_self_attention_neck,tiny_frelu_neck" \
    --implementation-status eval_only \
    --roc-auc 2>&1 | tee "$log_file" || {
      log "WARN: NMS eval failed seed=$seed iou=$iou"
      record_plan "nms_iou_$iou" "failed" "seed=$seed"
    }
}

run_nms_evals() {
  [[ "$RUN_NMS_EVAL" == "1" ]] || {
    log "NMS eval disabled by RUN_NMS_EVAL=$RUN_NMS_EVAL"
    record_plan "nms_eval" "skipped" "disabled"
    return 0
  }

  IFS=',' read -r -a gpus <<< "$GPU_LIST"
  IFS=',' read -r -a seeds <<< "$SEEDS"
  IFS=',' read -r -a ious <<< "$NMS_IOUS"
  local job_index=0
  for iou in "${ious[@]}"; do
    iou=${iou//[[:space:]]/}
    [[ -z "$iou" ]] && continue
    for seed in "${seeds[@]}"; do
      seed=${seed//[[:space:]]/}
      [[ -z "$seed" ]] && continue
      local gpu="${gpus[$((job_index % ${#gpus[@]}))]}"
      gpu=${gpu//[[:space:]]/}
      run_nms_eval_for_seed "$gpu" "$seed" "$iou"
      job_index=$((job_index + 1))
    done
  done
}

collect_results() {
  local roots="outputs/detectors/server_baselines,$PROJECT"
  log "Collecting final P2P4-SelfAttnFR ablation results from: $roots"
  DETECTOR_ROOTS="$roots" \
  RESULTS_CSV="$RESULTS_CSV" \
  SUMMARY_CSV="$SUMMARY_CSV" \
  PVALUES_CSV="$PVALUES_CSV" \
  DASHBOARD="$DASHBOARD" \
  STAGE_GATE_JSON="$STAGE_GATE_JSON" \
  STAGE_GATE_MD="$STAGE_GATE_MD" \
  REPORT_DIR="$REPORT_DIR" \
  CONDA_ENV="$CONDA_ENV" \
  bash scripts/ubuntu/collect_server_results.sh "$roots" 2>&1 | tee -a "$QUEUE_LOG" || \
    log "WARN: final ablation result collection returned non-zero"
}

main() {
  log "Final P2P4-SelfAttnFR ablation queue requested"
  record_plan "queue" "requested" "wait_for=$WAIT_FOR"
  wait_for_sessions "$WAIT_FOR"
  record_plan "queue" "started" "training ablations"
  run_train_jobs
  collect_results
  run_nms_evals
  collect_results
  record_plan "queue" "complete" "final P2P4-SelfAttnFR ablation queue finished"
  log "QUEUE_FINISHED final P2P4-SelfAttnFR ablation"
  log "Plan TSV: $PLAN_TSV"
  log "Results CSV: $RESULTS_CSV"
  log "Dashboard: $DASHBOARD"
}

main "$@"
