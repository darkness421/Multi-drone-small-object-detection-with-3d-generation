#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/oem/projects/multi-uav-marine-city}"
cd "$ROOT"

CONDA_ENV="${CONDA_ENV:-com3d-ace}"
PHYSICAL_GPU="${PHYSICAL_GPU:-1}"
ULTRALYTICS_DEVICE="${ULTRALYTICS_DEVICE:-0}"
IMG="${IMG:-1280}"
WORKERS="${WORKERS:-4}"
RTDETR_BATCH="${RTDETR_BATCH:-2}"
EPOCHS="${EPOCHS:-100}"
RECOVERY_ID="${RECOVERY_ID:-$(date +%Y%m%d_%H%M%S)}"

DATA_YAML="${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}"
PROJECT="${PROJECT:-outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713}"
LOG_DIR="${LOG_DIR:-outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713}"
Y12_RUN="${Y12_RUN:-outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713/20260523_080841_yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_resume_20260522_190713}"

export CUDA_DEVICE_ORDER="${CUDA_DEVICE_ORDER:-PCI_BUS_ID}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-$PHYSICAL_GPU}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

mkdir -p "$LOG_DIR"

echo "GPU1 recovery start at $(date --iso-8601=seconds)"
echo "RECOVERY_ID=$RECOVERY_ID PHYSICAL_GPU=$PHYSICAL_GPU ULTRALYTICS_DEVICE=$ULTRALYTICS_DEVICE IMG=$IMG WORKERS=$WORKERS RTDETR_BATCH=$RTDETR_BATCH"

check_margin() {
  bash scripts/ubuntu/check_resource_margin.sh \
    --path . \
    --gpu "$PHYSICAL_GPU" \
    --min-free-gb "${MIN_FREE_GB:-100}" \
    --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-92}" \
    --min-ram-gb "${MIN_RAM_GB:-16}" \
    --min-gpu-free-gb "${MIN_GPU_FREE_GB:-6}" \
    --max-retries 1
}

run_eval() {
  local model_path="$1"
  local eval_name="$2"
  local log_name="$3"

  if [[ ! -f "$model_path" ]]; then
    echo "SKIP_EVAL missing model: $model_path"
    return 0
  fi

  check_margin
  echo "EVAL_START name=$eval_name model=$model_path at $(date --iso-8601=seconds)"
  if conda run --no-capture-output -n "$CONDA_ENV" \
    python -m detectors.train_yolo eval \
      --model "$model_path" \
      --data-yaml "$DATA_YAML" \
      --imgsz "$IMG" \
      --workers "$WORKERS" \
      --device "$ULTRALYTICS_DEVICE" \
      --project "$PROJECT" \
      --name "$eval_name" \
      --roc-auc 2>&1 | tee "$LOG_DIR/$log_name"; then
    echo "EVAL_OK name=$eval_name at $(date --iso-8601=seconds)"
  else
    echo "EVAL_FAILED name=$eval_name at $(date --iso-8601=seconds)"
  fi
}

run_rtdetr_seed() {
  local seed="$1"
  local run_name="rtdetr-l_visdrone_fresh_fresh_20260519_131739_seed${seed}_batch2_retry_${RECOVERY_ID}"
  local train_log="rtdetr-l_seed${seed}_batch2_retry_${RECOVERY_ID}.log"

  check_margin
  echo "TRAIN_START model=rtdetr-l.pt seed=$seed batch=$RTDETR_BATCH gpu=$PHYSICAL_GPU ultralytics_device=$ULTRALYTICS_DEVICE at $(date --iso-8601=seconds)"
  if conda run --no-capture-output -n "$CONDA_ENV" \
    python -m detectors.train_yolo train \
      --model rtdetr-l.pt \
      --data-yaml "$DATA_YAML" \
      --epochs "$EPOCHS" \
      --imgsz "$IMG" \
      --batch "$RTDETR_BATCH" \
      --workers "$WORKERS" \
      --device "$ULTRALYTICS_DEVICE" \
      --seed "$seed" \
      --project "$PROJECT" \
      --name "$run_name" 2>&1 | tee "$LOG_DIR/$train_log"; then
    echo "TRAIN_OK model=rtdetr-l.pt seed=$seed batch=$RTDETR_BATCH gpu=$PHYSICAL_GPU ultralytics_device=$ULTRALYTICS_DEVICE at $(date --iso-8601=seconds)"
  else
    echo "TRAIN_FAILED model=rtdetr-l.pt seed=$seed batch=$RTDETR_BATCH gpu=$PHYSICAL_GPU ultralytics_device=$ULTRALYTICS_DEVICE at $(date --iso-8601=seconds)"
    return 0
  fi

  local run_dir
  run_dir="$(find "$PROJECT" -maxdepth 1 -type d -name "*${run_name}" | sort | tail -1)"
  if [[ -n "$run_dir" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    run_eval "$run_dir/ultralytics/weights/best.pt" "eval_${run_name}" "rtdetr-l_seed${seed}_batch2_eval_${RECOVERY_ID}.log"
  else
    echo "SKIP_EVAL best.pt not found for $run_name"
  fi
}

run_eval \
  "$Y12_RUN/ultralytics/weights/best.pt" \
  "eval_yolo12m_visdrone_fresh_fresh_20260519_131739_seed123_rerun_${RECOVERY_ID}" \
  "yolo12m_seed123_eval_rerun_${RECOVERY_ID}.log"

for seed in ${RTDETR_SEEDS:-42 123}; do
  run_rtdetr_seed "$seed"
done

echo "GPU1 recovery done at $(date --iso-8601=seconds)"
