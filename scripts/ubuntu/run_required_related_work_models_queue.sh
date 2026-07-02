#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
SEEDS=${SEEDS:-42,123,2026}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-4}
WORKERS=${WORKERS:-4}
IMG_SIZE=${IMG_SIZE:-1280}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/required_related_work_reimplementations}
LOG_DIR=${LOG_DIR:-outputs/logs/required_related_work_models}
STATE_DIR=${STATE_DIR:-outputs/experiments/required_related_work_models}
REPORT_DIR=${REPORT_DIR:-outputs/reports/required_related_work_models}

mkdir -p "$PROJECT" "$LOG_DIR" "$STATE_DIR" "$REPORT_DIR"
QUEUE_LOG="$LOG_DIR/queue.log"
PLAN_CSV="$STATE_DIR/queue.csv"
STATUS_CSV="$STATE_DIR/status.csv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record_plan() {
  local model="$1"
  local ref="$2"
  local protocol="$3"
  local status="$4"
  local note="$5"
  if [[ ! -f "$PLAN_CSV" ]]; then
    echo "updated_at,model,reference,protocol,status,note" > "$PLAN_CSV"
  fi
  printf '"%s","%s","%s","%s","%s","%s"\n' \
    "$(date -Is)" "$model" "$ref" "$protocol" "$status" "$note" >> "$PLAN_CSV"
}

write_status_header() {
  echo "updated_at,model,reference,implementation_type,run_status,result_status,note" > "$STATUS_CSV"
}

record_status() {
  local model="$1"
  local ref="$2"
  local implementation_type="$3"
  local run_status="$4"
  local result_status="$5"
  local note="$6"
  printf '"%s","%s","%s","%s","%s","%s","%s"\n' \
    "$(date -Is)" "$model" "$ref" "$implementation_type" "$run_status" "$result_status" "$note" >> "$STATUS_CSV"
}

count_result_csvs() {
  local root="$1"
  find "$root" -maxdepth 3 -name results.csv -type f 2>/dev/null | wc -l | tr -d ' '
}

record_existing_official_status() {
  local csfpr_count mffsod_count
  csfpr_count=$(count_result_csvs outputs/detectors/related_work_consistency/csfpr_rtdetr)
  mffsod_count=$(count_result_csvs outputs/detectors/related_work_consistency/mffsodnet)

  if [[ "$csfpr_count" -ge 3 ]]; then
    record_status "CSFPR-RTDETR" "[11]" "official/staged code" "completed" "3seed_results_found" "Found $csfpr_count result CSVs at 1280."
  else
    record_status "CSFPR-RTDETR" "[11]" "official/staged code" "needs_resume" "partial_results_found" "Found $csfpr_count result CSVs; expected 3."
  fi

  if [[ "$mffsod_count" -ge 3 ]]; then
    record_status "MFFSODNet" "[2]" "official scratch retrain" "completed" "3seed_results_found" "Found $mffsod_count result CSVs at 1280."
  else
    record_status "MFFSODNet" "[2]" "official scratch retrain" "needs_resume" "partial_results_found" "Found $mffsod_count result CSVs; expected 3."
  fi

  if PYTHONPATH=external/UAVDet conda run --no-capture-output -n "$CONDA_ENV" python - <<'PY' >/dev/null 2>&1
import mmcv, mmengine, mmdet
PY
  then
    record_status "UAVDet" "[16]" "official repo" "adapter_ready" "not_started" "MMDetection dependencies import successfully; queue an official UAVDet run next."
  else
    record_status "UAVDet" "[16]" "official repo" "dependency_pending" "not_runnable_in_current_env" "Repo is staged, but mmcv/mmengine are missing in the active env."
  fi
}

latest_completed_weight() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 \
    -path "*_${run_name}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

run_reimplementation() {
  local key="$1"
  local method="$2"
  local ref="$3"
  local model="$4"
  local init_weights="$5"
  local patches="$6"
  local module_note="$7"
  local seed="$8"

  local run_name="${key}_visdrone_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"
  local existing
  existing=$(latest_completed_weight "$run_name")
  if [[ -n "$existing" && -f "$existing" ]]; then
    log "Skipping completed required related-work reimplementation: $method seed=$seed"
    record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "skipped_completed" "$existing"
    return 0
  fi

  log "START required related-work reimplementation method=$method ref=$ref seed=$seed gpu=$GPU patches=$patches"
  record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "started" "$module_note"

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
    --ablation "$key"
    --base-model "$model"
    --proposed-module "$module_note"
    --implementation-status "paper_faithful_reimplementation_not_official_checkpoint"
    --model-patches "$patches"
  )
  if [[ -n "$init_weights" ]]; then
    args+=(--init-weights "$init_weights")
  fi

  if CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo "${args[@]}" 2>&1 | tee -a "$log_file"; then
    log "TRAIN_OK required related-work reimplementation method=$method seed=$seed"
    record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "train_ok" "$module_note"
  else
    log "TRAIN_FAILED required related-work reimplementation method=$method seed=$seed"
    record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "failed" "$module_note"
    return 1
  fi

  local weight
  weight=$(latest_completed_weight "$run_name")
  if [[ -n "$weight" && -f "$weight" ]]; then
    log "EVAL required related-work reimplementation method=$method seed=$seed weight=$weight"
    CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
      --model "$weight" \
      --data-yaml "$DATA_YAML" \
      --imgsz "$IMG_SIZE" \
      --workers "$WORKERS" \
      --device "$GPU" \
      --project "$PROJECT" \
      --name "eval_${run_name}" \
      --method "$method" \
      --ablation "$key" \
      --base-model "$model" \
      --proposed-module "$module_note" \
      --implementation-status "paper_faithful_reimplementation_not_official_checkpoint" \
      --model-patches "$patches" \
      --roc-auc 2>&1 | tee -a "$log_file" || log "WARN eval failed for $method seed=$seed"
  fi

  log "FINISH required related-work reimplementation method=$method seed=$seed"
  record_plan "$method" "$ref" "VisDrone 1280 seed=$seed" "finished" "$module_note"
}

collect_results() {
  log "Collecting required related-work reimplementation results."
  DETECTOR_ROOTS="$PROJECT" \
  RESULTS_CSV="$STATE_DIR/reimplementation_results.csv" \
  SUMMARY_CSV="$STATE_DIR/reimplementation_summary.csv" \
  PVALUES_CSV="$STATE_DIR/reimplementation_pvalues.csv" \
  DASHBOARD="$REPORT_DIR/reimplementation_dashboard.png" \
  STAGE_GATE_JSON="$STATE_DIR/reimplementation_stage_gate.json" \
  STAGE_GATE_MD="$STATE_DIR/reimplementation_stage_gate.md" \
  REPORT_DIR="$REPORT_DIR" \
  CONDA_ENV="$CONDA_ENV" \
  bash scripts/ubuntu/collect_server_results.sh "$PROJECT" 2>&1 | tee -a "$QUEUE_LOG" || \
    log "WARN required related-work result collection returned non-zero"
}

main() {
  log "Required related-work model queue started"
  log "Required set: CSFPR-RTDETR, MFFSODNet, SFFEF-YOLO, BPD-YOLO, UAVDet, HF-D-FINE"
  log "GPU=$GPU seeds=$SEEDS imgsz=$IMG_SIZE patience=$PATIENCE"
  write_status_header
  record_existing_official_status

  IFS=',' read -r -a seed_items <<< "$SEEDS"
  for seed in "${seed_items[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue

    run_reimplementation \
      "sffef_yolo_reimpl" \
      "SFFEF-YOLO [4] reimplementation" \
      "[4]" \
      "configs/detector/yolo11l-p2p4-balanced-v1.yaml" \
      "yolo11l.pt" \
      "cbam_neck,tiny_frelu_neck" \
      "tiny-head + fine-grained feature fusion reproduction" \
      "$seed"

    run_reimplementation \
      "bpd_yolo_reimpl" \
      "BPD-YOLO [7] reimplementation" \
      "[7]" \
      "configs/detector/yolo11l-p2-balanced-v2.yaml" \
      "yolo11l.pt" \
      "se_neck,rf_context_neck" \
      "P2/L-FPN-style semantic/detail refinement reproduction" \
      "$seed"

    run_reimplementation \
      "hf_dfine_reimpl" \
      "HF-D-FINE [12] high-resolution reproduction" \
      "[12]" \
      "yolo11l.pt" \
      "" \
      "dct_stem,dynfreq_c3_neck,tiny_frelu_neck" \
      "high-resolution frequency/detail refinement reproduction" \
      "$seed"
  done

  collect_results
  record_status "SFFEF-YOLO" "[4]" "paper-faithful reimplementation" "queued_or_completed" "see_reimplementation_summary" "$STATE_DIR/reimplementation_summary.csv"
  record_status "BPD-YOLO" "[7]" "paper-faithful reimplementation" "queued_or_completed" "see_reimplementation_summary" "$STATE_DIR/reimplementation_summary.csv"
  record_status "HF-D-FINE" "[12]" "paper-faithful reimplementation" "queued_or_completed" "see_reimplementation_summary" "$STATE_DIR/reimplementation_summary.csv"
  log "QUEUE_FINISHED required related-work model queue"
  log "Status CSV: $STATUS_CSV"
  log "Plan CSV: $PLAN_CSV"
}

main "$@"
