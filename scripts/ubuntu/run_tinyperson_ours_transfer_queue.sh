#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
SEEDS=${SEEDS:-42,123,2026}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-16}
WORKERS=${WORKERS:-4}
IMG_SIZE=${IMG_SIZE:-640}
DATA_YAML=${DATA_YAML:-configs/detector/tinyperson_yolo_data.yaml}
MODEL_YAML=${MODEL_YAML:-configs/detector/yolo11l-p2p4-balanced-v1.yaml}
PROJECT=${PROJECT:-outputs/detectors/tinyperson_640_transfer}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_640_transfer}
STATE_DIR=${STATE_DIR:-outputs/experiments/tinyperson_640_transfer}
REPORT_DIR=${REPORT_DIR:-outputs/reports/tinyperson_640_transfer}

RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/tinyperson_640_transfer/results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/tinyperson_640_transfer/summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/tinyperson_640_transfer/pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/tinyperson_640_transfer_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/tinyperson_640_transfer/stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/tinyperson_640_transfer/stage_gate.md}
PROPOSED_GATE_JSON=${PROPOSED_GATE_JSON:-outputs/experiments/tinyperson_640_transfer/proposed_overwhelm_gate.json}
PROPOSED_GATE_MD=${PROPOSED_GATE_MD:-outputs/experiments/tinyperson_640_transfer/proposed_overwhelm_gate.md}

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

data_ready() {
  local root train val
  root=$(awk '/^path:/ {print $2; exit}' "$DATA_YAML")
  train=$(awk '/^train:/ {print $2; exit}' "$DATA_YAML")
  val=$(awk '/^val:/ {print $2; exit}' "$DATA_YAML")
  [[ -n "${root:-}" && -n "${train:-}" && -n "${val:-}" ]] || return 1
  [[ -d "$root/$train" && -d "$root/$val" ]] || return 1
  find "$root/$train" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print -quit | grep -q .
  find "$root/$val" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print -quit | grep -q .
}

latest_completed_weight() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 \
    -path "*_${run_name}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

visdrone_ours_weight_for_seed() {
  local seed="$1"
  find outputs/detectors/server_yolov11_p2p4_balanced -type f \
    -path "*proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone*seed${seed}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

collect_results() {
  log "Collecting TinyPerson transfer results."
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
  STAGE_GATE_DATASET="TinyPerson" \
  bash scripts/ubuntu/collect_server_results.sh "$PROJECT" 2>&1 | tee -a "$QUEUE_LOG" || \
    log "WARN: TinyPerson transfer result collection returned non-zero"
}

run_seed() {
  local seed="$1"
  local init_weight
  local run_name="p2p4_selfattnfr_visdrone_transfer_tinyperson640_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"

  if [[ -n "$(latest_completed_weight "$run_name")" ]]; then
    log "Skipping completed TinyPerson transfer job: $run_name"
    record_plan "transfer_seed_${seed}" "skipped_completed" "$run_name"
    return 0
  fi

  init_weight=$(visdrone_ours_weight_for_seed "$seed")
  if [[ -z "$init_weight" || ! -f "$init_weight" ]]; then
    log "WARN: no same-seed VisDrone Ours weight found for seed=$seed; falling back to newest seed123 Ours weight."
    init_weight=$(visdrone_ours_weight_for_seed 123)
  fi
  if [[ -z "$init_weight" || ! -f "$init_weight" ]]; then
    log "ERROR: no VisDrone-trained Ours weight found; cannot run transfer fine-tune."
    record_plan "transfer_seed_${seed}" "blocked" "missing_visdrone_ours_weight"
    return 1
  fi

  log "START TinyPerson transfer seed=$seed gpu=$GPU init=$init_weight"
  record_plan "transfer_seed_${seed}" "running" "gpu=$GPU init=$init_weight"

  bash scripts/ubuntu/check_resource_margin.sh \
    --path "$PWD" \
    --gpu "$GPU" \
    --min-free-gb "${MIN_FREE_GB:-40}" \
    --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-94}" \
    --min-ram-gb "${MIN_RAM_GB:-12}" \
    --min-gpu-free-gb "${MIN_GPU_FREE_GB:-8}" \
    --wait-seconds "${GUARD_WAIT_SECONDS:-120}" 2>&1 | tee -a "$log_file"

  CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo train \
    --model "$MODEL_YAML" \
    --init-weights "$init_weight" \
    --data-yaml "$DATA_YAML" \
    --epochs "$EPOCHS" \
    --patience "$PATIENCE" \
    --imgsz "$IMG_SIZE" \
    --batch "$BATCH" \
    --workers "$WORKERS" \
    --device "$GPU" \
    --seed "$seed" \
    --project "$PROJECT" \
    --name "$run_name" \
    --method ProposedTransfer-P2P4SelfAttnFR-yolo11l-TinyPerson640 \
    --ablation tinyperson_transfer_from_visdrone_ours \
    --base-model yolo11l.pt \
    --proposed-module p2p4_balanced_head+lite_self_attention_neck+tiny_frelu_neck \
    --implementation-status implemented \
    --model-patches lite_self_attention_neck,tiny_frelu_neck 2>&1 | tee -a "$log_file"

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
      --method ProposedTransfer-P2P4SelfAttnFR-yolo11l-TinyPerson640 \
      --ablation tinyperson_transfer_from_visdrone_ours \
      --base-model yolo11l.pt \
      --proposed-module p2p4_balanced_head+lite_self_attention_neck+tiny_frelu_neck \
      --implementation-status implemented \
      --model-patches lite_self_attention_neck,tiny_frelu_neck \
      --roc-auc 2>&1 | tee -a "$log_file" || log "WARN: eval failed for $run_name"
  fi

  log "FINISH TinyPerson transfer seed=$seed"
  record_plan "transfer_seed_${seed}" "complete" "$run_name"
}

main() {
  log "TinyPerson Ours transfer fine-tune queue requested"
  log "Purpose: supplement the prior TinyPerson640 stress test with VisDrone-trained Ours initialization."
  if ! data_ready; then
    log "ERROR: TinyPerson data is not ready at $DATA_YAML"
    record_plan "data_ready" "blocked" "$DATA_YAML"
    exit 1
  fi
  record_plan "queue" "requested" "gpu=$GPU seeds=$SEEDS imgsz=$IMG_SIZE"

  IFS=',' read -r -a seeds <<< "$SEEDS"
  for seed in "${seeds[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue
    run_seed "$seed"
    collect_results
  done

  collect_results
  record_plan "queue" "complete" "TinyPerson Ours transfer fine-tune finished"
  log "QUEUE_FINISHED TinyPerson Ours transfer fine-tune"
  log "Summary: $SUMMARY_CSV"
  log "Dashboard: $DASHBOARD"
}

main "$@"
