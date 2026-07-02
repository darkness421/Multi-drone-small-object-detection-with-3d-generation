#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-1}
IMGSZ=${IMGSZ:-1280}
BATCH=${BATCH:-4}
LOG_DIR=${LOG_DIR:-outputs/logs/related_work_detectors}
PROJECT=${PROJECT:-outputs/detectors/related_work_detectors/leaf_yolo}
LEAF_ROOT=${LEAF_ROOT:-external/LEAF-YOLO}
DATA_YAML=${LEAF_DATA_YAML:-data/visdrone_local.yaml}

mkdir -p "$LOG_DIR" "$PROJECT"

run_leaf() {
  local tag="$1"
  local weight="$2"
  local name="leaf_yolo_${tag}_visdrone_eval_img${IMGSZ}"
  local log_file="$LOG_DIR/${name}.log"

  if [[ ! -f "$LEAF_ROOT/$weight" ]]; then
    echo "[$(date -Is)] SKIP LEAF-YOLO $tag missing weight: $LEAF_ROOT/$weight" | tee -a "$LOG_DIR/queue.log"
    return 0
  fi

  echo "[$(date -Is)] Starting LEAF-YOLO $tag eval on GPU${GPU}" | tee "$log_file"
  (
    cd "$LEAF_ROOT"
    MPLCONFIGDIR="/home/oem/projects/multi-uav-marine-city/.cache/matplotlib" \
    YOLO_CONFIG_DIR="/home/oem/projects/multi-uav-marine-city/.cache/ultralytics" \
    CUDA_DEVICE_ORDER=PCI_BUS_ID \
    conda run --no-capture-output -n "$CONDA_ENV" python test.py \
      --data "$DATA_YAML" \
      --img "$IMGSZ" \
      --batch "$BATCH" \
      --conf 0.01 \
      --iou 0.5 \
      --device "$GPU" \
      --weights "$weight" \
      --project "../../$PROJECT" \
      --name "$name" \
      --no-trace \
      --save-json
  ) 2>&1 | tee -a "$log_file"
  echo "[$(date -Is)] Finished LEAF-YOLO $tag eval" | tee -a "$log_file"
}

run_leaf "n" "cfg/LEAF-YOLO/leaf-sizen/weights/best.pt"
run_leaf "s" "cfg/LEAF-YOLO/leaf-sizes/weights/best.pt"
