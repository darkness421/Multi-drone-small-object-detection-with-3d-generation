#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
SEEDS=${SEEDS:-42}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-8}
WORKERS=${WORKERS:-4}
IMG_SIZE=${IMG_SIZE:-1280}
DATA_YAML=${DATA_YAML:-configs/detector/tinyperson_corner_original_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/tinyperson_corner_original}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_corner_original}
STATE_DIR=${STATE_DIR:-outputs/experiments/tinyperson_corner_original}
REPORT_DIR=${REPORT_DIR:-outputs/reports/tinyperson_corner_original}

RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/tinyperson_corner_original/results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/tinyperson_corner_original/summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/tinyperson_corner_original/pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/tinyperson_corner_original_generic_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/tinyperson_corner_original/stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/tinyperson_corner_original/stage_gate.md}
PROPOSED_GATE_JSON=${PROPOSED_GATE_JSON:-outputs/experiments/tinyperson_corner_original/proposed_overwhelm_gate.json}
PROPOSED_GATE_MD=${PROPOSED_GATE_MD:-outputs/experiments/tinyperson_corner_original/proposed_overwhelm_gate.md}

mkdir -p "$PROJECT" "$LOG_DIR" "$STATE_DIR" "$REPORT_DIR" "$(dirname "$DASHBOARD")"
QUEUE_LOG="$LOG_DIR/queue.log"
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

latest_completed_weight() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 \
    -path "*_${run_name}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

prepare_data() {
  log "Preparing TinyPerson corner/original-window YOLO dataset."
  record_plan "prepare_data" "running" "$DATA_YAML"
  conda run --no-capture-output -n "$CONDA_ENV" python scripts/prepare_tinyperson_corner_yolo.py 2>&1 | tee -a "$QUEUE_LOG"
  record_plan "prepare_data" "complete" "$DATA_YAML"
}

collect_results() {
  log "Collecting TinyPerson corner/original-window results."
  DETECTOR_ROOTS="$PROJECT" \
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
  # Summary rows use dataset=TinyPerson; the corner/original-window protocol is
  # encoded in method/ablation names and the generated reports.
  STAGE_GATE_DATASET="TinyPerson" \
  bash scripts/ubuntu/collect_server_results.sh "$PROJECT" 2>&1 | tee -a "$QUEUE_LOG" || \
    log "WARN: TinyPerson corner/original result collection returned non-zero"
}

run_train_eval() {
  local job_key="$1"
  local method="$2"
  local ablation="$3"
  local model="$4"
  local init_weights="$5"
  local module="$6"
  local patches="$7"
  local seed="$8"

  local run_name="${job_key}_tinyperson_corner_original_img${IMG_SIZE}_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"

  if [[ -n "$(latest_completed_weight "$run_name")" ]]; then
    log "Skipping completed TinyPerson corner/original job: $run_name"
    record_plan "$job_key" "skipped_completed" "seed=$seed"
    return 0
  fi

  log "START TinyPerson corner/original job=$job_key seed=$seed gpu=$GPU imgsz=$IMG_SIZE"
  record_plan "$job_key" "running" "seed=$seed gpu=$GPU imgsz=$IMG_SIZE"

  bash scripts/ubuntu/check_resource_margin.sh \
    --path "$PWD" \
    --gpu "$GPU" \
    --min-free-gb "${MIN_FREE_GB:-35}" \
    --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-96}" \
    --min-ram-gb "${MIN_RAM_GB:-12}" \
    --min-gpu-free-gb "${MIN_GPU_FREE_GB:-8}" \
    --wait-seconds "${GUARD_WAIT_SECONDS:-120}" 2>&1 | tee -a "$log_file"

  local args=(
    train
    --model "$model"
    --data-yaml "$DATA_YAML"
    --epochs "$EPOCHS"
    --patience "$PATIENCE"
    --imgsz "$IMG_SIZE"
    --batch "$BATCH"
    --workers "$WORKERS"
    --device "$GPU"
    --seed "$seed"
    --project "$PROJECT"
    --name "$run_name"
    --method "$method"
    --ablation "$ablation"
    --base-model yolo11l.pt
    --proposed-module "$module"
    --implementation-status implemented
  )
  if [[ -n "$init_weights" ]]; then
    args+=(--init-weights "$init_weights")
  fi
  if [[ -n "$patches" ]]; then
    args+=(--model-patches "$patches")
  fi

  CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo "${args[@]}" 2>&1 | tee -a "$log_file"

  local weight
  weight=$(latest_completed_weight "$run_name")
  if [[ -n "$weight" && -f "$weight" ]]; then
    CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
      --model "$weight" \
      --data-yaml "$DATA_YAML" \
      --imgsz "$IMG_SIZE" \
      --workers "$WORKERS" \
      --device "$GPU" \
      --project "$PROJECT" \
      --name "eval_${run_name}" \
      --method "$method" \
      --ablation "$ablation" \
      --base-model yolo11l.pt \
      --proposed-module "$module" \
      --implementation-status implemented \
      --roc-auc 2>&1 | tee -a "$log_file" || log "WARN: eval failed for $run_name"
  fi

  record_plan "$job_key" "complete" "seed=$seed"
  log "FINISH TinyPerson corner/original job=$job_key seed=$seed"
}

main() {
  log "TinyPerson corner/original-window queue requested"
  log "Purpose: fix prior TinyPerson diagnostic by materializing corner crops and collapsing all categories to one person class."
  record_plan "queue" "requested" "gpu=$GPU seeds=$SEEDS imgsz=$IMG_SIZE"

  prepare_data

  IFS=',' read -r -a seeds <<< "$SEEDS"
  for seed in "${seeds[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue

    run_train_eval \
      yolov9m \
      YOLOv9m-TinyPersonCornerOriginal \
      tinyperson_corner_original_yolov9m_baseline \
      yolov9m.pt \
      "" \
      strong_tinyperson_baseline \
      "" \
      "$seed"

    run_train_eval \
      ours \
      Ours-TinyPersonCornerOriginal \
      tinyperson_corner_original_ours \
      configs/detector/yolo11l-p2p4-balanced-v1.yaml \
      yolo11l.pt \
      p2p4_balanced_head+lite_self_attention_neck+tiny_frelu_neck \
      lite_self_attention_neck,tiny_frelu_neck \
      "$seed"

    collect_results
  done

  collect_results
  record_plan "queue" "complete" "TinyPerson corner/original-window queue finished"
  log "QUEUE_FINISHED TinyPerson corner/original-window queue"
  log "Summary: $SUMMARY_CSV"
  log "Dashboard: $DASHBOARD"
}

main "$@"
