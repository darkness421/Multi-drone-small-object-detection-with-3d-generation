#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SEEDS=${SEEDS:-42,123,2026}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
IMGSZ=${IMGSZ:-1280}
WORKERS=${WORKERS:-4}
CSFPR_GPU=${CSFPR_GPU:-1}
CSFPR_BATCH=${CSFPR_BATCH:-1}
MFFSOD_GPU=${MFFSOD_GPU:-1}
MFFSOD_BATCH=${MFFSOD_BATCH:-2}
WAIT_FOR_FINAL_2D=${WAIT_FOR_FINAL_2D:-1}
FINAL_2D_LOG=${FINAL_2D_LOG:-outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log}
FINAL_2D_PATTERN=${FINAL_2D_PATTERN:-QUEUE_FINISHED final P2P4-SelfAttnFR ablation}
WAIT_FOR_GPU_MEMORY=${WAIT_FOR_GPU_MEMORY:-1}
MAX_GPU_USED_MIB=${MAX_GPU_USED_MIB:-8000}
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

wait_for_final_2d() {
  if [[ "$WAIT_FOR_FINAL_2D" != "1" ]]; then
    return 0
  fi

  log "Waiting for final 2D queue marker: $FINAL_2D_PATTERN"
  while true; do
    if [[ -f "$FINAL_2D_LOG" ]] && grep -Fq "$FINAL_2D_PATTERN" "$FINAL_2D_LOG"; then
      log "Final 2D marker found; starting strict Sec. 2.1 related-work queue."
      return 0
    fi
    sleep 300
  done
}

wait_for_gpu_memory() {
  local gpu="$1"
  local used
  if [[ "$WAIT_FOR_GPU_MEMORY" != "1" ]]; then
    return 0
  fi

  while true; do
    used=$(nvidia-smi --id="$gpu" --query-gpu=memory.used --format=csv,noheader,nounits | head -n 1 | tr -d '[:space:]')
    if [[ -n "$used" && "$used" =~ ^[0-9]+$ && "$used" -le "$MAX_GPU_USED_MIB" ]]; then
      log "GPU$gpu memory is available: used=${used}MiB <= ${MAX_GPU_USED_MIB}MiB"
      return 0
    fi
    log "Waiting for GPU$gpu memory: used=${used:-unknown}MiB > ${MAX_GPU_USED_MIB}MiB"
    sleep 300
  done
}

record_audit_holds() {
  record "UAVDet" "audit" "Sec. 2.1 cited model; clone/audit before GPU training" "PENDING_ADAPTER_AUDIT" "official repo candidate identified; MMDetection/Mamba dependency and RGB-only fairness need validation"
  record "SFFEF-YOLO/FMFN/DS/BPD/LRDS/DG/D2A/UFO/CFIA/HF-D-FINE/DFFormer/RT-UAV-SOD" "citation" "Sec. 2.1 cited models without staged runnable assets" "CITATION_ONLY" "keep in coverage table; do not spend GPU until assets are confirmed"
  record "LEAF-YOLO-N/S" "excluded" "not cited in current Sec. 2.1" "INTERNAL_ONLY" "remove from paper-facing related-work queue unless the manuscript is revised to cite LEAF-YOLO"
}

run_mffsodnet() {
  local seed="$1"
  local name="mffsodnet_img${IMGSZ}_seed${seed}"
  local log_file="$LOG_DIR/${name}.log"

  if [[ ! -f external/MFFSODNet/tph-yolov5/train.py ]] || [[ ! -f external/MFFSODNet/tph-yolov5/models/MFFSODNet_3head_MS_Module_BDFPN.yaml ]]; then
    log "SKIP $name missing MFFSODNet extracted code/config."
    record "MFFSODNet" "$seed" "VisDrone 1280 train/val, scratch, 100e" "SKIPPED" "missing extracted code/config"
    return 0
  fi

  wait_for_gpu_memory "$MFFSOD_GPU"
  log "START MFFSODNet consistency retrain seed=$seed img=$IMGSZ gpu=$MFFSOD_GPU"
  record "MFFSODNet" "$seed" "VisDrone 1280 train/val, scratch, 100e, patience=$PATIENCE" "STARTED" "strict Sec. 2.1 related-work reproduction; official repo code, no pretrained weight"
  (
    cd external/MFFSODNet/tph-yolov5
    MPLCONFIGDIR="/home/oem/projects/multi-uav-marine-city/.cache/matplotlib" \
    YOLO_CONFIG_DIR="/home/oem/projects/multi-uav-marine-city/.cache/ultralytics" \
    PYTHONHASHSEED="$seed" \
    CUDA_DEVICE_ORDER=PCI_BUS_ID \
    TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
    conda run --no-capture-output -n "$CONDA_ENV" python train.py \
      --device "$MFFSOD_GPU" \
      --imgsz "$IMGSZ" \
      --epochs "$EPOCHS" \
      --batch-size "$MFFSOD_BATCH" \
      --workers "$WORKERS" \
      --patience "$PATIENCE" \
      --seed "$seed" \
      --data data/visdrone_local.yaml \
      --cfg models/MFFSODNet_3head_MS_Module_BDFPN.yaml \
      --weights '' \
      --hyp data/hyps/hyp.VisDrone.yaml \
      --project "../../../$PROJECT/mffsodnet" \
      --name "$name" \
      --exist-ok
  ) 2>&1 | tee "$log_file"
  log "FINISH MFFSODNet consistency retrain seed=$seed"
  record "MFFSODNet" "$seed" "VisDrone 1280 train/val, scratch, 100e, patience=$PATIENCE" "FINISHED" "$PROJECT/mffsodnet/$name"
}

run_csfpr() {
  local seed="$1"
  local name="csfpr_rtdetr_img${IMGSZ}_seed${seed}"
  local log_file="$LOG_DIR/${name}.log"

  if [[ ! -f external/CSFPR-RTDETR/ultralytics/cfg/modelY/CSFPR-RTDETR.yaml ]]; then
    log "SKIP $name missing CSFPR config."
    record "CSFPR-RTDETR" "$seed" "VisDrone 1280 train/val, scratch, 100e" "SKIPPED" "missing config"
    return 0
  fi

  wait_for_gpu_memory "$CSFPR_GPU"
  log "START CSFPR-RTDETR consistency retrain seed=$seed img=$IMGSZ gpu=$CSFPR_GPU"
  record "CSFPR-RTDETR" "$seed" "VisDrone 1280 train/val, scratch, 100e, patience=$PATIENCE" "STARTED" "strict Sec. 2.1 related-work reproduction"
  MPLCONFIGDIR="$PWD/.cache/matplotlib" \
  YOLO_CONFIG_DIR="$PWD/.cache/ultralytics" \
  PYTHONHASHSEED="$seed" \
  CUDA_DEVICE_ORDER=PCI_BUS_ID \
  TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.train_csfpr_rtdetr_consistency \
    --device "$CSFPR_GPU" \
    --imgsz "$IMGSZ" \
    --epochs "$EPOCHS" \
    --batch "$CSFPR_BATCH" \
    --workers "$WORKERS" \
    --patience "$PATIENCE" \
    --seed "$seed" \
    --project "$PROJECT/csfpr_rtdetr" \
    --name "$name" 2>&1 | tee "$log_file"
  log "FINISH CSFPR-RTDETR consistency retrain seed=$seed"
  record "CSFPR-RTDETR" "$seed" "VisDrone 1280 train/val, scratch, 100e, patience=$PATIENCE" "FINISHED" "$PROJECT/csfpr_rtdetr/$name"
}

log "Strict related-work 1280 consistency queue started"
log "Rule: only models cited in Sec. 2.1 UAV Small-object Evidence Generation are paper-facing candidates."
log "Runnable staged models for this queue: CSFPR-RTDETR and MFFSODNet. LEAF/DR/SOD/YOLO11s-UAV are internal-only unless added to Sec. 2.1."
log "Seeds=$SEEDS epochs=$EPOCHS imgsz=$IMGSZ CSFPR_GPU=$CSFPR_GPU MFFSOD_GPU=$MFFSOD_GPU wait_gpu_memory=$WAIT_FOR_GPU_MEMORY max_used=${MAX_GPU_USED_MIB}MiB"

record_audit_holds
wait_for_final_2d

IFS=',' read -r -a seed_items <<< "$SEEDS"
for seed in "${seed_items[@]}"; do
  seed=${seed//[[:space:]]/}
  [[ -z "$seed" ]] && continue
  run_csfpr "$seed"
done

for seed in "${seed_items[@]}"; do
  seed=${seed//[[:space:]]/}
  [[ -z "$seed" ]] && continue
  run_mffsodnet "$seed"
done

log "QUEUE_FINISHED related-work 1280 consistency retrain"
