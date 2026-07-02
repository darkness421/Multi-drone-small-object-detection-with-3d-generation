#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
SEEDS=${SEEDS:-42}
EPOCHS=${EPOCHS:-50}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-64}
WORKERS=${WORKERS:-4}
IMG_SIZE=${IMG_SIZE:-224}
DATA_YAML=${DATA_YAML:-configs/detector/tinyperson_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/tinyperson_224_aux_sweep}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_224_aux_sweep}
STATE_DIR=${STATE_DIR:-outputs/experiments/tinyperson_224_aux_sweep}
REPORT_DIR=${REPORT_DIR:-outputs/reports/tinyperson_224_aux_sweep}
DASHBOARD=${DASHBOARD:-outputs/reports/live/tinyperson_224_aux_sweep_dashboard.png}

RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/tinyperson_224_aux_sweep/results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/tinyperson_224_aux_sweep/summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/tinyperson_224_aux_sweep/pvalues.csv}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/tinyperson_224_aux_sweep/stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/tinyperson_224_aux_sweep/stage_gate.md}
PROPOSED_GATE_JSON=${PROPOSED_GATE_JSON:-outputs/experiments/tinyperson_224_aux_sweep/proposed_overwhelm_gate.json}
PROPOSED_GATE_MD=${PROPOSED_GATE_MD:-outputs/experiments/tinyperson_224_aux_sweep/proposed_overwhelm_gate.md}

mkdir -p "$PROJECT" "$LOG_DIR" "$STATE_DIR" "$REPORT_DIR" "$(dirname "$DASHBOARD")"
QUEUE_LOG="$LOG_DIR/queue.log"
PLAN_CSV="$STATE_DIR/queue.csv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record() {
  local job="$1"
  local seed="$2"
  local status="$3"
  local note="$4"
  if [[ ! -f "$PLAN_CSV" ]]; then
    echo "updated_at,job,seed,status,note" > "$PLAN_CSV"
  fi
  printf '"%s","%s","%s","%s","%s"\n' "$(date -Is)" "$job" "$seed" "$status" "$note" >> "$PLAN_CSV"
}

data_ready() {
  local root train val
  root=$(awk '/^path:/ {print $2; exit}' "$DATA_YAML")
  train=$(awk '/^train:/ {print $2; exit}' "$DATA_YAML")
  val=$(awk '/^val:/ {print $2; exit}' "$DATA_YAML")
  [[ -n "${root:-}" && -n "${train:-}" && -n "${val:-}" ]] || return 1
  [[ -d "$root/$train" && -d "$root/$val" ]] || return 1
}

latest_completed_weight() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 \
    -path "*_${run_name}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

run_train_eval() {
  local job="$1"
  local method="$2"
  local model="$3"
  local init_weights="$4"
  local ablation="$5"
  local module="$6"
  local patches="$7"
  local implementation_status="$8"
  local seed="$9"
  local run_name="${job}_tinyperson224_aux_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"

  if [[ -n "$(latest_completed_weight "$run_name")" ]]; then
    log "Skipping completed TinyPerson224 aux job=$job seed=$seed"
    record "$job" "$seed" "skipped_completed" "$run_name"
    return 0
  fi

  log "START TinyPerson224 aux job=$job seed=$seed gpu=$GPU imgsz=$IMG_SIZE"
  record "$job" "$seed" "started" "model=$model patches=$patches"

  bash scripts/ubuntu/check_resource_margin.sh \
    --path "$PWD" \
    --gpu "$GPU" \
    --min-free-gb "${MIN_FREE_GB:-40}" \
    --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-94}" \
    --min-ram-gb "${MIN_RAM_GB:-12}" \
    --min-gpu-free-gb "${MIN_GPU_FREE_GB:-8}" \
    --wait-seconds "${GUARD_WAIT_SECONDS:-120}" 2>&1 | tee -a "$log_file"

  local args=(
    train
    --model "$model"
    --data-yaml "$DATA_YAML"
    --epochs "$EPOCHS"
    --patience "$PATIENCE"
    --imgsz "$IMG_SIZE"
    --batch "$BATCH"
    --workers "$WORKERS"
    --device "$GPU"
    --seed "$seed"
    --project "$PROJECT"
    --name "$run_name"
    --method "$method"
    --ablation "$ablation"
    --base-model "$model"
    --proposed-module "$module"
    --implementation-status "$implementation_status"
  )
  if [[ -n "$init_weights" ]]; then
    args+=(--init-weights "$init_weights")
  fi
  if [[ -n "$patches" ]]; then
    args+=(--model-patches "$patches")
  fi

  if CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo "${args[@]}" 2>&1 | tee -a "$log_file"; then
    log "TRAIN_OK TinyPerson224 aux job=$job seed=$seed"
    record "$job" "$seed" "train_ok" "$run_name"
  else
    log "TRAIN_FAILED TinyPerson224 aux job=$job seed=$seed"
    record "$job" "$seed" "failed" "$run_name"
    return 0
  fi

  local weight
  weight=$(latest_completed_weight "$run_name")
  if [[ -n "$weight" && -f "$weight" ]]; then
    CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
      --model "$weight" \
      --data-yaml "$DATA_YAML" \
      --imgsz "$IMG_SIZE" \
      --workers "$WORKERS" \
      --device "$GPU" \
      --project "$PROJECT" \
      --name "eval_${run_name}" \
      --method "$method" \
      --ablation "$ablation" \
      --base-model "$model" \
      --proposed-module "$module" \
      --implementation-status "$implementation_status" \
      --model-patches "$patches" \
      --roc-auc 2>&1 | tee -a "$log_file" || log "WARN eval failed for job=$job seed=$seed"
  fi

  collect_results
}

collect_results() {
  log "Collecting TinyPerson224 aux sweep results"
  DETECTOR_ROOTS="$PROJECT" \
  RESULTS_CSV="$RESULTS_CSV" \
  SUMMARY_CSV="$SUMMARY_CSV" \
  PVALUES_CSV="$PVALUES_CSV" \
  DASHBOARD="$DASHBOARD" \
  STAGE_GATE_JSON="$STAGE_GATE_JSON" \
  STAGE_GATE_MD="$STAGE_GATE_MD" \
  PROPOSED_GATE_JSON="$PROPOSED_GATE_JSON" \
  PROPOSED_GATE_MD="$PROPOSED_GATE_MD" \
  REPORT_DIR="$REPORT_DIR" \
  CONDA_ENV="$CONDA_ENV" \
  STAGE_GATE_DATASET="TinyPerson" \
  bash scripts/ubuntu/collect_server_results.sh "$PROJECT" 2>&1 | tee -a "$QUEUE_LOG" || \
    log "WARN TinyPerson224 aux collection returned non-zero"
}

main() {
  log "TinyPerson224 auxiliary sweep requested"
  log "Policy: internal-only 224 stress test; Top5 completed rows stay in outputs/experiments/tinyperson_224_top5 and are not repeated here."
  log "GPU=$GPU seeds=$SEEDS imgsz=$IMG_SIZE epochs=$EPOCHS patience=$PATIENCE batch=$BATCH"
  if ! data_ready; then
    log "TinyPerson data is not ready at $DATA_YAML"
    record "data_ready" "-" "blocked" "$DATA_YAML"
    exit 1
  fi
  record "queue" "-" "requested" "gpu=$GPU seeds=$SEEDS imgsz=$IMG_SIZE"

  IFS=',' read -r -a seed_items <<< "$SEEDS"
  for seed in "${seed_items[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue

    # YOLO-family rows not included in the completed Top5 set.
    for spec in \
      "yolov8n|YOLOv8n-TinyPerson224Aux|yolov8n.pt" \
      "yolov8s|YOLOv8s-TinyPerson224Aux|yolov8s.pt" \
      "yolov8m|YOLOv8m-TinyPerson224Aux|yolov8m.pt" \
      "yolov9t|YOLOv9t-TinyPerson224Aux|yolov9t.pt" \
      "yolov9s|YOLOv9s-TinyPerson224Aux|yolov9s.pt" \
      "yolo11n|YOLOv11n-TinyPerson224Aux|yolo11n.pt" \
      "yolo11s|YOLOv11s-TinyPerson224Aux|yolo11s.pt" \
      "yolo11m|YOLOv11m-TinyPerson224Aux|yolo11m.pt" \
      "yolo12n|YOLOv12n-TinyPerson224Aux|yolo12n.pt" \
      "yolo12s|YOLOv12s-TinyPerson224Aux|yolo12s.pt" \
      "yolo12m|YOLOv12m-TinyPerson224Aux|yolo12m.pt" \
      "yolo12l|YOLOv12l-TinyPerson224Aux|yolo12l.pt" \
      "yolov10n|YOLOv10n-TinyPerson224Aux|yolov10n.pt" \
      "yolov10s|YOLOv10s-TinyPerson224Aux|yolov10s.pt" \
      "yolov10m|YOLOv10m-TinyPerson224Aux|yolov10m.pt" \
      "yolov10l|YOLOv10l-TinyPerson224Aux|yolov10l.pt" \
      "yolo26n|YOLOv26n-TinyPerson224Aux|yolo26n.pt" \
      "yolo26s|YOLOv26s-TinyPerson224Aux|yolo26s.pt" \
      "yolo26m|YOLOv26m-TinyPerson224Aux|yolo26m.pt" \
      "yolo26l|YOLOv26l-TinyPerson224Aux|yolo26l.pt" \
      "yolov5nu|YOLOv5nu-TinyPerson224Aux|yolov5nu.pt" \
      "yolov5su|YOLOv5su-TinyPerson224Aux|yolov5su.pt" \
      "yolov5mu|YOLOv5mu-TinyPerson224Aux|yolov5mu.pt" \
      "yolov5lu|YOLOv5lu-TinyPerson224Aux|yolov5lu.pt" \
      "rtdetr_l|RT-DETR-L-TinyPerson224Aux|rtdetr-l.pt"
    do
      IFS='|' read -r job method model <<< "$spec"
      run_train_eval "$job" "$method" "$model" "" "tinyperson224_aux_yolo_family" "baseline auxiliary sweep" "" "implemented_auxiliary_only" "$seed"
    done

    # Lightweight related-work-inspired reproductions, kept separate from VisDrone paper claims.
    run_train_eval \
      "sffef_yolo_reimpl" \
      "SFFEF-YOLO [4] TinyPerson224Aux reimplementation" \
      "configs/detector/yolo11l-p2p4-balanced-v1.yaml" \
      "yolo11l.pt" \
      "tinyperson224_aux_sffef_yolo_reimpl" \
      "tiny-head + fine-grained feature fusion reproduction" \
      "cbam_neck,tiny_frelu_neck" \
      "paper_faithful_reimplementation_auxiliary_only" \
      "$seed"

    run_train_eval \
      "bpd_yolo_reimpl" \
      "BPD-YOLO [7] TinyPerson224Aux reimplementation" \
      "configs/detector/yolo11l-p2-balanced-v2.yaml" \
      "yolo11l.pt" \
      "tinyperson224_aux_bpd_yolo_reimpl" \
      "P2/L-FPN-style semantic/detail refinement reproduction" \
      "se_neck,rf_context_neck" \
      "paper_faithful_reimplementation_auxiliary_only" \
      "$seed"

    run_train_eval \
      "hf_dfine_reimpl" \
      "HF-D-FINE [12] TinyPerson224Aux high-resolution reproduction" \
      "yolo11l.pt" \
      "" \
      "tinyperson224_aux_hf_dfine_reimpl" \
      "high-resolution frequency/detail refinement reproduction" \
      "dct_stem,dynfreq_c3_neck,tiny_frelu_neck" \
      "paper_faithful_reimplementation_auxiliary_only" \
      "$seed"

    run_train_eval \
      "uavdet_inspired_reimpl" \
      "UAVDet [16] TinyPerson224Aux inspired reproduction" \
      "configs/detector/yolo11l-p2p4-balanced-v1.yaml" \
      "yolo11l.pt" \
      "tinyperson224_aux_uavdet_inspired" \
      "P2/P3/P4 high-resolution heads + lightweight SSM-style context + DWR local refinement" \
      "uavdet_mamba_neck,dwr_neck" \
      "uavdet_inspired_reproduction_auxiliary_only" \
      "$seed"

    run_train_eval \
      "yolo11s_uav_simam_dwr_repro" \
      "YOLO11s-UAV TinyPerson224Aux module reproduction" \
      "yolo11s.pt" \
      "" \
      "tinyperson224_aux_yolo11s_uav_module_repro" \
      "module-level reproduction from public YOLO11s-UAV snippets" \
      "simam_neck,dwr_neck" \
      "module_reproduction_auxiliary_only" \
      "$seed"
  done

  collect_results
  record "queue" "-" "complete" "TinyPerson224 auxiliary sweep finished"
  log "QUEUE_FINISHED TinyPerson224 auxiliary sweep"
  log "Dashboard: $DASHBOARD"
}

main "$@"
