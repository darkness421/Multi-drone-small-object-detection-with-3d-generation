#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
TARGET_GPU=${TARGET_GPU:-0}
SEED=${SEED:-123}
ABLATION=${ABLATION:-p2_wavelet_frelu}
MODEL_YAML=${MODEL_YAML:-configs/detector/yolo11l-p2.yaml}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/server_yolov11_p2_module_search}
LOG_DIR=${LOG_DIR:-outputs/logs/server_yolov11_p2_module_search}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-4}
WORKERS=${WORKERS:-4}
IMGSZ=${IMGSZ:-1280}
INIT_WEIGHTS=${INIT_WEIGHTS:-yolo11l.pt}
NMS_CONF=${NMS_CONF:-0.001}
NMS_IOU=${NMS_IOU:-0.55}

mkdir -p "$PROJECT" "$LOG_DIR"

case "$ABLATION" in
  p2_wavelet_frelu)
    METHOD="ProposedP2FR-Wavelet-yolo11l"
    MODULE="p2_head+wavelet_stem+tiny_frelu_neck"
    PATCHES="wavelet_stem,tiny_frelu_neck"
    ;;
  p2_dct_frelu)
    METHOD="ProposedP2FR-DCT-yolo11l"
    MODULE="p2_head+dct_stem+tiny_frelu_neck"
    PATCHES="dct_stem,tiny_frelu_neck"
    ;;
  p2_dynfreq_frelu)
    METHOD="ProposedP2FR-DynFreqC3-yolo11l"
    MODULE="p2_head+dynfreq_c3_small+tiny_frelu_neck"
    PATCHES="dynfreq_c3_small,tiny_frelu_neck"
    ;;
  p2_se_frelu)
    METHOD="ProposedP2FR-SE-yolo11l"
    MODULE="p2_head+se_neck+tiny_frelu_neck"
    PATCHES="se_neck,tiny_frelu_neck"
    ;;
  p2_cbam_frelu)
    METHOD="ProposedP2FR-CBAM-yolo11l"
    MODULE="p2_head+cbam_neck+tiny_frelu_neck"
    PATCHES="cbam_neck,tiny_frelu_neck"
    ;;
  p2_wavelet_cbam_frelu)
    METHOD="ProposedP2FR-WaveletCBAM-yolo11l"
    MODULE="p2_head+wavelet_stem+cbam_neck+tiny_frelu_neck"
    PATCHES="wavelet_stem,cbam_neck,tiny_frelu_neck"
    ;;
  p2_dynfreq_cbam_frelu)
    METHOD="ProposedP2FR-DynFreqC3CBAM-yolo11l"
    MODULE="p2_head+dynfreq_c3_small+cbam_neck+tiny_frelu_neck"
    PATCHES="dynfreq_c3_small,cbam_neck,tiny_frelu_neck"
    ;;
  p2_deform_frelu)
    METHOD="ProposedP2FR-Deform-yolo11l"
    MODULE="p2_head+partial_deformable_neck+tiny_frelu_neck"
    PATCHES="partial_deformable_neck,tiny_frelu_neck"
    ;;
  *)
    echo "Unknown ablation: $ABLATION" >&2
    exit 2
    ;;
esac

RUN_NAME="proposed_${ABLATION}_yolo11l_visdrone_p2fr_module_seed${SEED}"
LOG_FILE="$LOG_DIR/${RUN_NAME}.log"

{
  echo "[$(date -Is)] P2-FR module worker started"
  echo "Target GPU: $TARGET_GPU"
  echo "Ablation: $ABLATION"
  echo "Model YAML: $MODEL_YAML"
  echo "Init weights: $INIT_WEIGHTS"
  echo "Patches: $PATCHES"
  echo "Seed: $SEED"
  echo "Epochs/patience/imgsz/batch: $EPOCHS/$PATIENCE/$IMGSZ/$BATCH"

  conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo train \
    --model "$MODEL_YAML" \
    --init-weights "$INIT_WEIGHTS" \
    --data-yaml "$DATA_YAML" \
    --epochs "$EPOCHS" \
    --patience "$PATIENCE" \
    --imgsz "$IMGSZ" \
    --batch "$BATCH" \
    --workers "$WORKERS" \
    --device "$TARGET_GPU" \
    --seed "$SEED" \
    --method "$METHOD" \
    --ablation "$ABLATION" \
    --base-model "YOLOv11l-P2-FR-s123 family" \
    --proposed-module "$MODULE" \
    --implementation-status "implemented" \
    --model-patches "$PATCHES" \
    --project "$PROJECT" \
    --name "$RUN_NAME"

  WEIGHT=$(find "$PROJECT" -maxdepth 3 -path "*${RUN_NAME}/ultralytics/weights/best.pt" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
  if [[ -z "$WEIGHT" ]]; then
    echo "TRAIN_FAILED: best.pt not found for $RUN_NAME" >&2
    exit 1
  fi

  echo "[$(date -Is)] Training finished. Running class-aware NMS eval iou=$NMS_IOU conf=$NMS_CONF"
  conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
    --model "$WEIGHT" \
    --data-yaml "$DATA_YAML" \
    --imgsz "$IMGSZ" \
    --workers "$WORKERS" \
    --device "$TARGET_GPU" \
    --conf "$NMS_CONF" \
    --iou "$NMS_IOU" \
    --method "${METHOD}+NMS055" \
    --ablation "${ABLATION}+nms055" \
    --base-model "YOLOv11l-P2-FR-s123 family" \
    --proposed-module "${MODULE}+nms055" \
    --implementation-status "implemented" \
    --project "outputs/detectors/server_yolov11_p2_module_nms055" \
    --name "eval_${ABLATION}_seed${SEED}_nms055"

  echo "[$(date -Is)] P2-FR module worker finished"
} 2>&1 | tee "$LOG_FILE"
