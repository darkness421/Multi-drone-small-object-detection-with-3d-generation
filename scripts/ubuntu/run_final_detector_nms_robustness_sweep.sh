#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

GPU=${GPU:-0}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
IMGSZ=${IMGSZ:-1280}
WORKERS=${WORKERS:-4}
CONF=${CONF:-0.001}
IOUS=${IOUS:-"0.45 0.55 0.65 0.75"}
PROJECT=${PROJECT:-outputs/detectors/final_nms_robustness_sweep}
LOG_DIR=${LOG_DIR:-outputs/logs/final_nms_robustness_sweep}
STATE_DIR=${STATE_DIR:-outputs/experiments/final_nms_robustness_sweep}

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
    ours) echo "Ours: P2P4-SelfAttnFR" ;;
    yolov9c) echo "YOLOv9c" ;;
    *) echo "$model" ;;
  esac
}

write_header "$PLAN_CSV" "model,seed,conf,iou,nms_type,weight,run_name,status"
write_header "$STATUS_CSV" "model,seed,conf,iou,nms_type,run_name,status,started_at,finished_at"

log "QUEUE_START final detector NMS robustness sweep"
log "GPU=$GPU CONDA_ENV=$CONDA_ENV DATA_YAML=$DATA_YAML IMGSZ=$IMGSZ CONF=$CONF IOUS=$IOUS"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>&1 | tee -a "$LOG_FILE" || true

for model in ours yolov9c; do
  for seed in 42 123 2026; do
    weight="$(weight_for "$model" "$seed")"
    if [[ ! -f "$weight" ]]; then
      log "SKIP missing weight model=$model seed=$seed weight=$weight"
      continue
    fi
    for iou in $IOUS; do
      nms_type="classaware"
      run_name="final_nms_${model}_seed${seed}_conf${CONF}_iou${iou}_${nms_type}"
      run_name="${run_name//./p}"
      append_csv "$PLAN_CSV" "$model,$seed,$CONF,$iou,$nms_type,$weight,$run_name,queued"

      if [[ -d "$PROJECT/$run_name" ]]; then
        log "SKIP existing run_dir=$PROJECT/$run_name"
        append_csv "$STATUS_CSV" "$model,$seed,$CONF,$iou,$nms_type,$run_name,skipped_existing,,"
        continue
      fi

      started_at="$(date -Is)"
      log "RUN model=$model seed=$seed conf=$CONF iou=$iou nms=$nms_type run=$run_name"
      append_csv "$STATUS_CSV" "$model,$seed,$CONF,$iou,$nms_type,$run_name,running,$started_at,"

      conda run --no-capture-output -n "$CONDA_ENV" \
        python -m detectors.train_yolo eval \
        --model "$weight" \
        --data-yaml "$DATA_YAML" \
        --imgsz "$IMGSZ" \
        --workers "$WORKERS" \
        --device "$GPU" \
        --conf "$CONF" \
        --iou "$iou" \
        --method "$(method_for "$model")" \
        --ablation "nms_robustness_conf=${CONF}_iou=${iou}_${nms_type}" \
        --project "$PROJECT" \
        --name "$run_name" 2>&1 | tee -a "$LOG_FILE"

      finished_at="$(date -Is)"
      append_csv "$STATUS_CSV" "$model,$seed,$CONF,$iou,$nms_type,$run_name,complete,$started_at,$finished_at"
      log "DONE model=$model seed=$seed conf=$CONF iou=$iou nms=$nms_type run=$run_name"
    done
  done
done

log "QUEUE_FINISHED final detector NMS robustness sweep"
