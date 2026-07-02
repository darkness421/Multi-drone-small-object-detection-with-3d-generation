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
PROJECT=${PROJECT:-outputs/detectors/related_work_module_reproductions}
LOG_DIR=${LOG_DIR:-outputs/logs/related_work_module_reproductions}
STATE_DIR=${STATE_DIR:-outputs/experiments/related_work_module_reproductions}
REPORT_DIR=${REPORT_DIR:-outputs/reports/related_work_module_reproductions}

mkdir -p "$PROJECT" "$LOG_DIR" "$STATE_DIR" "$REPORT_DIR"
QUEUE_LOG="$LOG_DIR/queue.log"
PLAN_CSV="$STATE_DIR/queue.csv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record() {
  local method="$1"
  local seed="$2"
  local status="$3"
  local note="$4"
  if [[ ! -f "$PLAN_CSV" ]]; then
    echo "updated_at,method,seed,status,note" > "$PLAN_CSV"
  fi
  printf '"%s","%s","%s","%s","%s"\n' "$(date -Is)" "$method" "$seed" "$status" "$note" >> "$PLAN_CSV"
}

best_exists() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 -path "*_${run_name}/ultralytics/weights/best.pt" -type f -print -quit | grep -q .
}

latest_best() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 -path "*_${run_name}/ultralytics/weights/best.pt" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-
}

run_train_eval() {
  local key="$1"
  local method="$2"
  local patches="$3"
  local seed="$4"
  local run_name="${key}_visdrone_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"

  if best_exists "$run_name"; then
    log "Skipping completed module reproduction: $method seed=$seed"
    record "$method" "$seed" "SKIPPED_COMPLETED" "$run_name"
    return 0
  fi

  log "START module reproduction method=$method seed=$seed gpu=$GPU patches=$patches"
  record "$method" "$seed" "STARTED" "gpu=$GPU patches=$patches"
  CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo train \
    --model yolo11s.pt \
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
    --base-model yolo11s.pt \
    --proposed-module "module-level reproduction from public YOLO11s-UAV snippets" \
    --implementation-status "module_reproduction_not_official_full_model" \
    --model-patches "$patches" 2>&1 | tee "$log_file"

  local weight
  weight=$(latest_best "$run_name")
  if [[ -n "$weight" && -f "$weight" ]]; then
    log "EVAL module reproduction method=$method seed=$seed weight=$weight"
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
      --base-model yolo11s.pt \
      --proposed-module "module-level reproduction from public YOLO11s-UAV snippets" \
      --implementation-status "module_reproduction_not_official_full_model" \
      --model-patches "$patches" \
      --roc-auc 2>&1 | tee -a "$log_file" || log "WARN eval failed for $method seed=$seed"
  fi

  log "FINISH module reproduction method=$method seed=$seed"
  record "$method" "$seed" "FINISHED" "$run_name"
}

log "Related-work module reproduction queue started"
log "Policy: LEAF-YOLO is excluded. Full models without public code/weights remain Pending. This queue runs only transparent module-level reproductions."
log "Primary job: YOLO11s-UAV public-module reproduction using FlexSimAM/SimAM + DWR neck patches, not an official full-model reproduction."

IFS=',' read -r -a seed_items <<< "$SEEDS"
for seed in "${seed_items[@]}"; do
  seed=${seed//[[:space:]]/}
  [[ -z "$seed" ]] && continue
  run_train_eval \
    "yolo11s_uav_simam_dwr_repro" \
    "YOLO11s-UAV module reproduction" \
    "simam_neck,dwr_neck" \
    "$seed"
done

log "Collecting module reproduction results"
DETECTOR_ROOTS="$PROJECT" \
RESULTS_CSV="$STATE_DIR/results.csv" \
SUMMARY_CSV="$STATE_DIR/summary.csv" \
PVALUES_CSV="$STATE_DIR/pvalues.csv" \
DASHBOARD="$REPORT_DIR/dashboard.png" \
STAGE_GATE_JSON="$STATE_DIR/stage_gate.json" \
STAGE_GATE_MD="$STATE_DIR/stage_gate.md" \
REPORT_DIR="$REPORT_DIR" \
CONDA_ENV="$CONDA_ENV" \
bash scripts/ubuntu/collect_server_results.sh "$PROJECT" 2>&1 | tee -a "$QUEUE_LOG" || log "WARN result collection failed"

log "QUEUE_FINISHED related-work module reproductions"
