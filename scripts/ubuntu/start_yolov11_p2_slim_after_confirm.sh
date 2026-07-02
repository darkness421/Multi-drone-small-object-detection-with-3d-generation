#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

TARGET_GPU=${TARGET_GPU:-0}
ABLATION=${ABLATION:-p2_slim_tiny_frelu}
SEED=${SEED:-42}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
CONFIRM_SESSION=${CONFIRM_SESSION:-server-yolov11-p2-confirm-gpu${TARGET_GPU}}
PROJECT=${PROJECT:-outputs/detectors/server_yolov11_p2_slim}
LOG_DIR=${LOG_DIR:-outputs/logs/server_yolov11_p2_slim}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
MODEL_YAML=${MODEL_YAML:-configs/detector/yolo11l-p2-slim.yaml}
INIT_WEIGHTS=${INIT_WEIGHTS:-yolo11l.pt}
IMG_SIZE=${IMG_SIZE:-1280}
BATCH=${BATCH:-4}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}

mkdir -p "$LOG_DIR"

case "$ABLATION" in
  p2_slim_tiny_frelu)
    METHOD="ProposedSize-P2SlimTinyFReLU-yolo11l"
    MODULE="p2_slim_head+tiny_frelu_neck"
    PATCHES="tiny_frelu_neck"
    ;;
  p2_slim_wavelet_tiny_frelu)
    METHOD="ProposedSize-P2SlimWaveTinyFReLU-yolo11l"
    MODULE="p2_slim_head+wavelet_stem+tiny_frelu_neck"
    PATCHES="wavelet_stem,tiny_frelu_neck"
    ;;
  *)
    echo "Unknown ABLATION=$ABLATION" >&2
    exit 2
    ;;
esac

RUN_NAME="proposed_${ABLATION}_yolo11l_visdrone_yolov11_p2_slim_seed${SEED}"
LOG_FILE="$LOG_DIR/${RUN_NAME}.log"

echo "Slim P2 job waiting at $(date -Is)"
echo "Target GPU: $TARGET_GPU"
echo "Ablation: $ABLATION"
echo "Wait-for session: $CONFIRM_SESSION"
while tmux has-session -t "$CONFIRM_SESSION" 2>/dev/null; do
  echo "Still waiting for $CONFIRM_SESSION at $(date -Is)"
  sleep 60
done

echo "Starting slim P2 job at $(date -Is)" | tee -a "$LOG_FILE"
echo "Method: $METHOD" | tee -a "$LOG_FILE"
echo "Goal: keep P2/TinyFReLU while reducing Params below YOLOv11l." | tee -a "$LOG_FILE"

bash scripts/ubuntu/check_resource_margin.sh \
  --path "$PWD" \
  --gpu "$TARGET_GPU" \
  --min-free-gb "${MIN_FREE_GB:-80}" \
  --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-94}" \
  --min-ram-gb "${MIN_RAM_GB:-12}" \
  --min-gpu-free-gb "${MIN_GPU_FREE_GB:-8}" \
  --wait-seconds "${GUARD_WAIT_SECONDS:-120}" 2>&1 | tee -a "$LOG_FILE"

if CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo train \
  --model "$MODEL_YAML" \
  --data-yaml "$DATA_YAML" \
  --epochs "$EPOCHS" \
  --imgsz "$IMG_SIZE" \
  --batch "$BATCH" \
  --device "$TARGET_GPU" \
  --seed "$SEED" \
  --project "$PROJECT" \
  --name "$RUN_NAME" \
  --method "$METHOD" \
  --ablation "$ABLATION" \
  --base-model yolo11l.pt \
  --proposed-module "$MODULE" \
  --model-patches "$PATCHES" \
  --implementation-status implemented \
  --patience "$PATIENCE" \
  --init-weights "$INIT_WEIGHTS" 2>&1 | tee -a "$LOG_FILE"; then
  echo "TRAIN_OK $ABLATION seed=$SEED gpu=$TARGET_GPU at $(date -Is)" | tee -a "$LOG_FILE"
else
  echo "TRAIN_FAILED $ABLATION seed=$SEED gpu=$TARGET_GPU at $(date -Is)" | tee -a "$LOG_FILE"
  exit 1
fi

run_dir=$(find "$PROJECT" -maxdepth 1 -type d -name "*_${RUN_NAME}" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
  conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
    --model "$run_dir/ultralytics/weights/best.pt" \
    --data-yaml "$DATA_YAML" \
    --imgsz "$IMG_SIZE" \
    --device "$TARGET_GPU" \
    --project "$PROJECT" \
    --name "eval_${RUN_NAME}" \
    --method "$METHOD" \
    --ablation "$ABLATION" \
    --base-model yolo11l.pt \
    --proposed-module "$MODULE" \
    --implementation-status implemented \
    --roc-auc 2>&1 | tee -a "$LOG_FILE" || echo "EVAL_FAILED $ABLATION seed=$SEED at $(date -Is)" | tee -a "$LOG_FILE"
fi

echo "Slim P2 job finished at $(date -Is)" | tee -a "$LOG_FILE"
