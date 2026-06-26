#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
SEEDS=${SEEDS:-42,123,2026}
IMGSZ_LIST=${IMGSZ_LIST:-640,960,1280}
WORKERS=${WORKERS:-4}
DATA_YAML=${DATA_YAML:-configs/detector/tinyperson_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/tinyperson_eval_imgsz_sweep}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_eval_imgsz_sweep}
STATE_DIR=${STATE_DIR:-outputs/experiments/tinyperson_eval_imgsz_sweep}
WEIGHT_LINK_DIR=${WEIGHT_LINK_DIR:-outputs/experiments/tinyperson_eval_imgsz_sweep/weights}

mkdir -p "$PROJECT" "$LOG_DIR" "$STATE_DIR" "$WEIGHT_LINK_DIR"
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

latest_weight() {
  local pattern="$1"
  find outputs/detectors -type f -path "$pattern" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

weight_for() {
  local method="$1"
  local seed="$2"
  case "$method" in
    tinyperson_safr)
      latest_weight "*/tinyperson_640/*p2p4_selfattnfr_tinyperson640_seed${seed}/ultralytics/weights/best.pt"
      ;;
    tinyperson_safr_transfer)
      latest_weight "*/tinyperson_640_transfer/*p2p4_selfattnfr_visdrone_transfer_tinyperson640_seed${seed}/ultralytics/weights/best.pt"
      ;;
    tinyperson_yolov9m)
      latest_weight "*/tinyperson_640/*yolov9m_tinyperson640_seed${seed}/ultralytics/weights/best.pt"
      ;;
    *)
      return 1
      ;;
  esac
}

eval_summary_for() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 3 -path "*_${run_name}/metrics/eval_summary.json" -print -quit 2>/dev/null
}

eval_one() {
  local method="$1"
  local seed="$2"
  local imgsz="$3"
  local src_weight
  local link_weight
  local run_name="${method}_img${imgsz}_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"

  if [[ -n "$(eval_summary_for "$run_name")" ]]; then
    log "Skipping completed eval: $run_name"
    record_plan "$run_name" "skipped_completed" "$PROJECT"
    return 0
  fi

  src_weight=$(weight_for "$method" "$seed")
  if [[ -z "$src_weight" || ! -f "$src_weight" ]]; then
    log "WARN: missing checkpoint for method=$method seed=$seed"
    record_plan "$run_name" "blocked" "missing_checkpoint"
    return 0
  fi

  link_weight="$WEIGHT_LINK_DIR/${run_name}.pt"
  ln -sf "$(realpath "$src_weight")" "$link_weight"

  log "START TinyPerson eval sweep method=$method seed=$seed imgsz=$imgsz gpu=$GPU"
  record_plan "$run_name" "running" "weight=$src_weight"

  bash scripts/ubuntu/check_resource_margin.sh \
    --path "$PWD" \
    --gpu "$GPU" \
    --min-free-gb "${MIN_FREE_GB:-35}" \
    --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-95}" \
    --min-ram-gb "${MIN_RAM_GB:-10}" \
    --min-gpu-free-gb "${MIN_GPU_FREE_GB:-6}" \
    --wait-seconds "${GUARD_WAIT_SECONDS:-120}" 2>&1 | tee -a "$log_file"

  CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
    --model "$link_weight" \
    --data-yaml "$DATA_YAML" \
    --imgsz "$imgsz" \
    --workers "$WORKERS" \
    --device "$GPU" \
    --project "$PROJECT" \
    --name "$run_name" \
    --method "TinyPersonEvalSweep-${method}" \
    --ablation "eval_imgsz_${imgsz}" \
    --base-model "$method" \
    --proposed-module "eval_only_input_size_sweep" \
    --implementation-status "eval_only" 2>&1 | tee -a "$log_file"

  conda run --no-capture-output -n "$CONDA_ENV" python scripts/collect_tinyperson_eval_imgsz_sweep.py 2>&1 | tee -a "$QUEUE_LOG" || true
  record_plan "$run_name" "complete" "imgsz=$imgsz"
  log "FINISH TinyPerson eval sweep method=$method seed=$seed imgsz=$imgsz"
}

main() {
  log "TinyPerson eval-only input-size sweep requested"
  log "Methods: tinyperson_yolov9m,tinyperson_safr,tinyperson_safr_transfer"
  log "Seeds: $SEEDS; eval image sizes: $IMGSZ_LIST; GPU: $GPU"
  record_plan "queue" "requested" "gpu=$GPU seeds=$SEEDS imgsz=$IMGSZ_LIST"

  IFS=',' read -r -a seeds <<< "$SEEDS"
  IFS=',' read -r -a sizes <<< "$IMGSZ_LIST"
  local methods=(tinyperson_yolov9m tinyperson_safr tinyperson_safr_transfer)

  for method in "${methods[@]}"; do
    for seed in "${seeds[@]}"; do
      seed=${seed//[[:space:]]/}
      [[ -z "$seed" ]] && continue
      for imgsz in "${sizes[@]}"; do
        imgsz=${imgsz//[[:space:]]/}
        [[ -z "$imgsz" ]] && continue
        eval_one "$method" "$seed" "$imgsz"
      done
    done
  done

  conda run --no-capture-output -n "$CONDA_ENV" python scripts/collect_tinyperson_eval_imgsz_sweep.py 2>&1 | tee -a "$QUEUE_LOG"
  record_plan "queue" "complete" "TinyPerson eval-only input-size sweep finished"
  log "QUEUE_FINISHED TinyPerson eval-only input-size sweep"
}

main "$@"
