#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
SEEDS=${SEEDS:-42,123,2026}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-4}
WORKERS=${WORKERS:-4}
IMG_SIZE=${IMG_SIZE:-1280}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/required_related_work_reimplementations}
LOG_DIR=${LOG_DIR:-outputs/logs/required_related_work_models}
STATE_DIR=${STATE_DIR:-outputs/experiments/required_related_work_models}
QUEUE_LOG="$LOG_DIR/uavdet_inspired_after_required.log"
PLAN_CSV="$STATE_DIR/queue.csv"
REQUIRED_LOG="$LOG_DIR/queue.log"
REQUIRED_DONE_MARKER="QUEUE_FINISHED required related-work model queue"

mkdir -p "$PROJECT" "$LOG_DIR" "$STATE_DIR"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record_plan() {
  local model="$1"
  local ref="$2"
  local protocol="$3"
  local status="$4"
  local note="$5"
  if [[ ! -f "$PLAN_CSV" ]]; then
    echo "updated_at,model,reference,protocol,status,note" > "$PLAN_CSV"
  fi
  printf '"%s","%s","%s","%s","%s","%s"\n' \
    "$(date -Is)" "$model" "$ref" "$protocol" "$status" "$note" >> "$PLAN_CSV"
}

latest_completed_weight() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 \
    -path "*_${run_name}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

wait_for_required_queue() {
  log "Waiting for required related-work queue marker: $REQUIRED_DONE_MARKER"
  while true; do
    if [[ -f "$REQUIRED_LOG" ]] && grep -q "$REQUIRED_DONE_MARKER" "$REQUIRED_LOG"; then
      log "Detected required related-work queue completion marker."
      return 0
    fi
    sleep "${WAIT_SECONDS:-300}"
  done
}

run_one_seed() {
  local seed="$1"
  local key="uavdet_inspired_reimpl"
  local method="UAVDet [16] inspired reproduction"
  local ref="[16]"
  local model="configs/detector/yolo11l-p2p4-balanced-v1.yaml"
  local init_weights="yolo11l.pt"
  local patches="uavdet_mamba_neck,dwr_neck"
  local module_note="P2/P3/P4 high-resolution heads + lightweight SSM-style context + DWR local refinement"
  local run_name="${key}_visdrone_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"
  local existing

  existing=$(latest_completed_weight "$run_name")
  if [[ -n "$existing" && -f "$existing" ]]; then
    log "Skipping completed $method seed=$seed"
    record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "skipped_completed" "$existing"
    return 0
  fi

  log "START $method seed=$seed gpu=$GPU patches=$patches"
  record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "started" "$module_note"

  bash scripts/ubuntu/check_resource_margin.sh \
    --path "$PWD" \
    --gpu "$GPU" \
    --min-free-gb "${MIN_FREE_GB:-40}" \
    --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-94}" \
    --min-ram-gb "${MIN_RAM_GB:-12}" \
    --min-gpu-free-gb "${MIN_GPU_FREE_GB:-8}" \
    --wait-seconds "${GUARD_WAIT_SECONDS:-120}" 2>&1 | tee -a "$log_file"

  CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo train \
    --model "$model" \
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
    --method "$method" \
    --ablation "$key" \
    --base-model "$model" \
    --proposed-module "$module_note" \
    --implementation-status "uavdet_inspired_reproduction_not_official_checkpoint" \
    --model-patches "$patches" \
    --init-weights "$init_weights" 2>&1 | tee -a "$log_file"

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
      --ablation "$key" \
      --base-model "$model" \
      --proposed-module "$module_note" \
      --implementation-status "uavdet_inspired_reproduction_not_official_checkpoint" \
      --model-patches "$patches" \
      --roc-auc 2>&1 | tee -a "$log_file" || log "WARN eval failed for $method seed=$seed"
  fi

  log "FINISH $method seed=$seed"
  record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "finished" "$module_note"
}

main() {
  wait_for_required_queue
  IFS=',' read -r -a seed_items <<< "$SEEDS"
  for seed in "${seed_items[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue
    run_one_seed "$seed"
  done
  log "QUEUE_FINISHED UAVDet inspired reproduction queue"
}

main "$@"
