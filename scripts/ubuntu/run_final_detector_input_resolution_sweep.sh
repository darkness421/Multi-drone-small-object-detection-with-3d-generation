#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
WORKERS=${WORKERS:-4}
CONF=${CONF:-0.001}
IOU=${IOU:-0.55}
IMGSZS=${IMGSZS:-"640 960 1280 1536"}
PROJECT=${PROJECT:-outputs/detectors/final_input_resolution_sweep}
LOG_DIR=${LOG_DIR:-outputs/logs/final_input_resolution_sweep}
STATE_DIR=${STATE_DIR:-outputs/experiments/final_input_resolution_sweep}

mkdir -p "$LOG_DIR" "$PROJECT" "$STATE_DIR"
LOG_FILE="$LOG_DIR/queue.log"
PLAN_CSV="$STATE_DIR/plan.csv"
STATUS_CSV="$STATE_DIR/status.csv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$LOG_FILE"
}

write_header() {
  if [[ ! -f "$1" ]]; then
    echo "$2" > "$1"
  fi
}

append_csv() {
  local path="$1"
  shift
  printf '%s\n' "$*" >> "$path"
}

weight_for() {
  local model="$1"
  local seed="$2"
  case "${model}:${seed}" in
    ours:42)
      echo "outputs/detectors/server_yolov11_p2p4_balanced/20260612_065130_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed42/ultralytics/weights/best.pt"
      ;;
    ours:123)
      echo "outputs/detectors/server_yolov11_p2p4_balanced/20260611_103331_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed123/ultralytics/weights/best.pt"
      ;;
    ours:2026)
      echo "outputs/detectors/server_yolov11_p2p4_balanced/20260612_065130_proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l_visdrone_yolov11_p2_balanced_seed2026/ultralytics/weights/best.pt"
      ;;
    yolov9c:42)
      echo "outputs/detectors/server_baselines/20260618_210146_yolov9c_visdrone_seed42/ultralytics/weights/best.pt"
      ;;
    yolov9c:123)
      echo "outputs/detectors/server_baselines/20260618_204816_yolov9c_visdrone_seed123/ultralytics/weights/best.pt"
      ;;
    yolov9c:2026)
      echo "outputs/detectors/server_baselines/20260619_052226_yolov9c_visdrone_seed2026/ultralytics/weights/best.pt"
      ;;
    *)
      return 1
      ;;
  esac
}

method_for() {
  local model="$1"
  case "$model" in
    ours) echo "Ours" ;;
    yolov9c) echo "YOLOv9c" ;;
    *) echo "$model" ;;
  esac
}

write_header "$PLAN_CSV" "model,seed,imgsz,conf,iou,nms_type,weight,run_name,status"
write_header "$STATUS_CSV" "model,seed,imgsz,conf,iou,nms_type,run_name,status,started_at,finished_at"

log "QUEUE_START final detector input-resolution eval-only sweep"
log "GPU=$GPU CONDA_ENV=$CONDA_ENV DATA_YAML=$DATA_YAML IMGSZS=$IMGSZS CONF=$CONF IOU=$IOU"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>&1 | tee -a "$LOG_FILE" || true

for model in ours yolov9c; do
  for seed in 42 123 2026; do
    weight="$(weight_for "$model" "$seed")"
    if [[ ! -f "$weight" ]]; then
      log "SKIP missing weight model=$model seed=$seed weight=$weight"
      continue
    fi
    for imgsz in $IMGSZS; do
      nms_type="classaware"
      run_name="final_input_${model}_seed${seed}_imgsz${imgsz}_conf${CONF}_iou${IOU}_${nms_type}"
      run_name="${run_name//./p}"
      append_csv "$PLAN_CSV" "$model,$seed,$imgsz,$CONF,$IOU,$nms_type,$weight,$run_name,queued"

      if compgen -G "$PROJECT/*_${run_name}" > /dev/null; then
        log "SKIP existing run=$run_name"
        append_csv "$STATUS_CSV" "$model,$seed,$imgsz,$CONF,$IOU,$nms_type,$run_name,skipped_existing,,"
        continue
      fi

      started_at="$(date -Is)"
      log "RUN model=$model seed=$seed imgsz=$imgsz conf=$CONF iou=$IOU nms=$nms_type run=$run_name"
      append_csv "$STATUS_CSV" "$model,$seed,$imgsz,$CONF,$IOU,$nms_type,$run_name,running,$started_at,"

      conda run --no-capture-output -n "$CONDA_ENV" \
        python -m detectors.train_yolo eval \
        --model "$weight" \
        --data-yaml "$DATA_YAML" \
        --imgsz "$imgsz" \
        --workers "$WORKERS" \
        --device "$GPU" \
        --conf "$CONF" \
        --iou "$IOU" \
        --method "$(method_for "$model")" \
        --ablation "input_resolution_eval_conf=${CONF}_iou=${IOU}_${nms_type}" \
        --project "$PROJECT" \
        --name "$run_name" 2>&1 | tee -a "$LOG_FILE"

      finished_at="$(date -Is)"
      append_csv "$STATUS_CSV" "$model,$seed,$imgsz,$CONF,$IOU,$nms_type,$run_name,complete,$started_at,$finished_at"
      log "DONE model=$model seed=$seed imgsz=$imgsz conf=$CONF iou=$IOU nms=$nms_type run=$run_name"
    done
  done
done

log "QUEUE_FINISHED final detector input-resolution eval-only sweep"
