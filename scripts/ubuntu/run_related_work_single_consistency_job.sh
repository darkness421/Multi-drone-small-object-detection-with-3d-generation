#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

MODEL=${MODEL:-}
SEED=${SEED:-42}
GPU=${GPU:-0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
IMGSZ=${IMGSZ:-1280}
WORKERS=${WORKERS:-4}
CSFPR_BATCH=${CSFPR_BATCH:-1}
MFFSOD_BATCH=${MFFSOD_BATCH:-2}
LOG_DIR=${LOG_DIR:-outputs/logs/related_work_consistency}
PROJECT=${PROJECT:-outputs/detectors/related_work_consistency}
QUEUE_CSV=${QUEUE_CSV:-outputs/experiments/related_work_1280_consistency_queue.csv}

mkdir -p "$LOG_DIR" "$PROJECT" "$(dirname "$QUEUE_CSV")"

queue_log="$LOG_DIR/queue.log"

log() {
  echo "[$(date -Is)] $*" | tee -a "$queue_log"
}

record() {
  local model="$1"
  local seed="$2"
  local protocol="$3"
  local status="$4"
  local note="$5"
  if [[ ! -f "$QUEUE_CSV" ]]; then
    echo "created_at,model,seed,protocol,status,note" > "$QUEUE_CSV"
  fi
  printf '"%s","%s","%s","%s","%s","%s"\n' \
    "$(date -Is)" "$model" "$seed" "$protocol" "$status" "$note" >> "$QUEUE_CSV"
}

is_complete() {
  local run_dir="$1"
  [[ -f "$run_dir/weights/best.pt" ]] || [[ -s "$run_dir/results.csv" ]] || [[ -s "$run_dir/results.txt" ]]
}

finish_or_fail() {
  local status="$1"
  local model_label="$2"
  local seed="$3"
  local protocol="$4"
  local output_path="$5"
  if [[ "$status" -eq 0 ]]; then
    log "FINISH $model_label consistency retrain seed=$seed"
    record "$model_label" "$seed" "$protocol" "FINISHED" "$output_path"
  elif is_complete "$output_path"; then
    log "FINISH $model_label consistency retrain seed=$seed with checkpoint postprocess warning rc=$status"
    record "$model_label" "$seed" "$protocol" "FINISHED_POSTPROCESS_WARNING" "rc=$status after best.pt/results output; $output_path"
  else
    log "FAILED $model_label consistency retrain seed=$seed rc=$status"
    record "$model_label" "$seed" "$protocol" "FAILED" "rc=$status; see $LOG_DIR"
    exit "$status"
  fi
}

run_csfpr() {
  local name="csfpr_rtdetr_img${IMGSZ}_seed${SEED}"
  local run_dir="$PROJECT/csfpr_rtdetr/$name"
  local log_file="$LOG_DIR/${name}_gpu${GPU}.log"
  local protocol="VisDrone 1280 train/val, scratch, ${EPOCHS}e, patience=$PATIENCE"

  if [[ ! -f external/CSFPR-RTDETR/ultralytics/cfg/modelY/CSFPR-RTDETR.yaml ]]; then
    log "SKIP $name missing CSFPR config."
    record "CSFPR-RTDETR" "$SEED" "$protocol" "SKIPPED" "missing config"
    return 0
  fi
  if is_complete "$run_dir"; then
    log "SKIP $name already has output at $run_dir"
    record "CSFPR-RTDETR" "$SEED" "$protocol" "SKIPPED" "existing output"
    return 0
  fi

  log "START CSFPR-RTDETR consistency retrain seed=$SEED img=$IMGSZ gpu=$GPU"
  record "CSFPR-RTDETR" "$SEED" "$protocol" "STARTED" "single GPU split job"
  set +e
  MPLCONFIGDIR="$PWD/.cache/matplotlib" \
  YOLO_CONFIG_DIR="$PWD/.cache/ultralytics" \
  PYTHONHASHSEED="$SEED" \
  CUDA_DEVICE_ORDER=PCI_BUS_ID \
  TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.train_csfpr_rtdetr_consistency \
    --device "$GPU" \
    --imgsz "$IMGSZ" \
    --epochs "$EPOCHS" \
    --batch "$CSFPR_BATCH" \
    --workers "$WORKERS" \
    --patience "$PATIENCE" \
    --seed "$SEED" \
    --project "$PROJECT/csfpr_rtdetr" \
    --name "$name" 2>&1 | tee "$log_file"
  local status=${PIPESTATUS[0]}
  set -e
  finish_or_fail "$status" "CSFPR-RTDETR" "$SEED" "$protocol" "$run_dir"
}

run_mffsodnet() {
  local name="mffsodnet_img${IMGSZ}_seed${SEED}"
  local run_dir="$PROJECT/mffsodnet/$name"
  local log_file="$LOG_DIR/${name}_gpu${GPU}.log"
  local protocol="VisDrone 1280 train/val, scratch, ${EPOCHS}e, patience=$PATIENCE"

  if [[ ! -f external/MFFSODNet/tph-yolov5/train.py ]] || [[ ! -f external/MFFSODNet/tph-yolov5/models/MFFSODNet_3head_MS_Module_BDFPN.yaml ]]; then
    log "SKIP $name missing MFFSODNet extracted code/config."
    record "MFFSODNet" "$SEED" "$protocol" "SKIPPED" "missing extracted code/config"
    return 0
  fi
  if is_complete "$run_dir"; then
    log "SKIP $name already has output at $run_dir"
    record "MFFSODNet" "$SEED" "$protocol" "SKIPPED" "existing output"
    return 0
  fi

  log "START MFFSODNet consistency retrain seed=$SEED img=$IMGSZ gpu=$GPU"
  record "MFFSODNet" "$SEED" "$protocol" "STARTED" "single GPU split job"
  set +e
  (
    cd external/MFFSODNet/tph-yolov5
    MPLCONFIGDIR="/home/oem/projects/multi-uav-marine-city/.cache/matplotlib" \
    YOLO_CONFIG_DIR="/home/oem/projects/multi-uav-marine-city/.cache/ultralytics" \
    PYTHONHASHSEED="$SEED" \
    CUDA_DEVICE_ORDER=PCI_BUS_ID \
    TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
    conda run --no-capture-output -n "$CONDA_ENV" python train.py \
      --device "$GPU" \
      --imgsz "$IMGSZ" \
      --epochs "$EPOCHS" \
      --batch-size "$MFFSOD_BATCH" \
      --workers "$WORKERS" \
      --patience "$PATIENCE" \
      --seed "$SEED" \
      --data data/visdrone_local.yaml \
      --cfg models/MFFSODNet_3head_MS_Module_BDFPN.yaml \
      --weights '' \
      --hyp data/hyps/hyp.VisDrone.yaml \
      --project "../../../$PROJECT/mffsodnet" \
      --name "$name" \
      --exist-ok
  ) 2>&1 | tee "$log_file"
  local status=${PIPESTATUS[0]}
  set -e
  finish_or_fail "$status" "MFFSODNet" "$SEED" "$protocol" "$run_dir"
}

case "${MODEL,,}" in
  csfpr|csfpr-rtdetr|csfpr_rtdetr)
    run_csfpr
    ;;
  mffsod|mffsodnet)
    run_mffsodnet
    ;;
  *)
    echo "Usage: MODEL=csfpr|mffsod SEED=42 GPU=0 bash $0" >&2
    exit 2
    ;;
esac
