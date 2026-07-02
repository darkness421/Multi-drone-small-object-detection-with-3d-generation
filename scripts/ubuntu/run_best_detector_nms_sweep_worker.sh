#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-0}
MODEL_SET=${MODEL_SET:-efficient}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
IMGSZ=${IMGSZ:-1280}
WORKERS=${WORKERS:-4}
PROJECT=${PROJECT:-outputs/detectors/nms_sweep_${MODEL_SET}}
LOG_DIR=${LOG_DIR:-outputs/logs/nms_sweep}

mkdir -p "$LOG_DIR" "$PROJECT"
log_file="$LOG_DIR/${MODEL_SET}_gpu${GPU}.log"

if [[ "$MODEL_SET" == "efficient" ]]; then
  labels=(
    "P2BalV2-FR-s42"
    "P2Bal-FR-s42"
  )
  weights=(
    "outputs/detectors/server_yolov11_p2_balanced_v2/20260606_122020_proposed_p2_balanced_v2_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed42/ultralytics/weights/best.pt"
    "outputs/detectors/server_yolov11_p2_balanced/20260606_044326_proposed_p2_balanced_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed42/ultralytics/weights/best.pt"
  )
elif [[ "$MODEL_SET" == "accuracy" ]]; then
  labels=(
    "P2-FR-s123"
    "YOLOv11l-s42"
  )
  weights=(
    "outputs/detectors/server_yolov11_p2_confirm/20260605_100151_proposed_p2_tiny_frelu_yolo11l_visdrone_yolov11_p2_confirm_seed123/ultralytics/weights/best.pt"
    "outputs/detectors/server_fresh_baselines/large_20260524_140922/20260528_072152_yolo11l_visdrone_large_fresh_large_20260524_140922_seed42/ultralytics/weights/best.pt"
  )
else
  echo "Unknown MODEL_SET: $MODEL_SET" | tee -a "$log_file"
  exit 2
fi

ious=(0.45 0.55 0.65 0.75)
confs=(0.001 0.01)
agnostic_flags=(0 1)

{
  echo "[NMS sweep] started at $(date -Is)"
  echo "MODEL_SET=$MODEL_SET GPU=$GPU DATA_YAML=$DATA_YAML IMGSZ=$IMGSZ"
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits || true
  echo
} 2>&1 | tee -a "$log_file"

for idx in "${!labels[@]}"; do
  label="${labels[$idx]}"
  weight="${weights[$idx]}"
  if [[ ! -f "$weight" ]]; then
    echo "[skip] missing weight for $label: $weight" 2>&1 | tee -a "$log_file"
    continue
  fi

  for conf in "${confs[@]}"; do
    for iou in "${ious[@]}"; do
      for agnostic in "${agnostic_flags[@]}"; do
        nms_label="classaware"
        nms_arg=()
        if [[ "$agnostic" == "1" ]]; then
          nms_label="agnostic"
          nms_arg=(--agnostic-nms)
        fi
        run_name="nms_${MODEL_SET}_${label}_conf${conf}_iou${iou}_${nms_label}"
        run_name="${run_name//./p}"

        {
          echo
          echo "[run] $(date -Is) $run_name"
          echo "weight=$weight"
        } 2>&1 | tee -a "$log_file"

        conda run --no-capture-output -n "$CONDA_ENV" \
          python -m detectors.train_yolo eval \
          --model "$weight" \
          --data-yaml "$DATA_YAML" \
          --imgsz "$IMGSZ" \
          --workers "$WORKERS" \
          --device "$GPU" \
          --conf "$conf" \
          --iou "$iou" \
          "${nms_arg[@]}" \
          --method "$label+nms_sweep" \
          --ablation "conf=${conf},iou=${iou},${nms_label}" \
          --project "$PROJECT" \
          --name "$run_name" 2>&1 | tee -a "$log_file"
      done
    done
  done
done

echo "[NMS sweep] finished at $(date -Is)" 2>&1 | tee -a "$log_file"
