#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU=${GPU:-0}
SEEDS=${SEEDS:-42}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
BATCH=${BATCH:-16}
WORKERS=${WORKERS:-4}
IMG_SIZE=${IMG_SIZE:-640}
QUEUE_LABEL=${QUEUE_LABEL:-TinyPerson 640}
LABEL_SUFFIX=${LABEL_SUFFIX:-TinyPerson640}
RUN_SUFFIX=${RUN_SUFFIX:-tinyperson640}
DATA_YAML=${DATA_YAML:-configs/detector/tinyperson_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/tinyperson_640}
LOG_DIR=${LOG_DIR:-outputs/logs/tinyperson_640}
STATE_DIR=${STATE_DIR:-outputs/experiments/tinyperson_640}
REPORT_DIR=${REPORT_DIR:-outputs/reports/tinyperson_640}
POLL_SECONDS=${POLL_SECONDS:-300}
WAIT_FOR_2D=${WAIT_FOR_2D:-1}
WAIT_FOR_RELATED_WORK=${WAIT_FOR_RELATED_WORK:-1}
WAIT_FOR_UAVDET=${WAIT_FOR_UAVDET:-1}
WAIT_FOR_HEATMAP=${WAIT_FOR_HEATMAP:-1}
WAIT_FOR_DATA=${WAIT_FOR_DATA:-1}
TRY_PREPARE_DATA=${TRY_PREPARE_DATA:-1}
RUN_STRONG_YOLO_BASELINE=${RUN_STRONG_YOLO_BASELINE:-1}
RUN_EXTRA_TOP_BASELINES=${RUN_EXTRA_TOP_BASELINES:-1}
RUN_CORE_ABLATION=${RUN_CORE_ABLATION:-0}
RUN_RELATED_PLACEHOLDERS=${RUN_RELATED_PLACEHOLDERS:-0}
RELATED_WORK_LOG=${RELATED_WORK_LOG:-outputs/logs/required_related_work_models/queue.log}
RELATED_WORK_MARKER=${RELATED_WORK_MARKER:-QUEUE_FINISHED required related-work model queue}
UAVDET_LOG=${UAVDET_LOG:-outputs/logs/required_related_work_models/uavdet_inspired_after_required.log}
UAVDET_MARKER=${UAVDET_MARKER:-QUEUE_FINISHED UAVDet inspired reproduction queue}
HEATMAP_LOG=${HEATMAP_LOG:-outputs/logs/final_detector_heatmaps/queue.log}
HEATMAP_MARKER=${HEATMAP_MARKER:-QUEUE_FINISHED final detector heatmaps}

RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/tinyperson_640/results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/tinyperson_640/summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/tinyperson_640/pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/tinyperson_640_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/tinyperson_640/stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/tinyperson_640/stage_gate.md}
PROPOSED_GATE_JSON=${PROPOSED_GATE_JSON:-outputs/experiments/tinyperson_640/proposed_overwhelm_gate.json}
PROPOSED_GATE_MD=${PROPOSED_GATE_MD:-outputs/experiments/tinyperson_640/proposed_overwhelm_gate.md}

mkdir -p "$LOG_DIR" "$STATE_DIR" "$REPORT_DIR" "$PROJECT" "$(dirname "$DASHBOARD")"
QUEUE_LOG="$LOG_DIR/queue.log"
PLAN_TSV="$STATE_DIR/plan.tsv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

record_plan() {
  local stage="$1"
  local status="$2"
  local detail="$3"
  if [[ ! -f "$PLAN_TSV" ]]; then
    printf "updated_at\tstage\tstatus\tdetail\n" > "$PLAN_TSV"
  fi
  printf "%s\t%s\t%s\t%s\n" "$(date -Is)" "$stage" "$status" "$detail" >> "$PLAN_TSV"
}

marker_done() {
  local file="$1"
  local marker="$2"
  [[ -f "$file" ]] && grep -Fq "$marker" "$file"
}

wait_for_marker() {
  local enabled="$1"
  local stage="$2"
  local file="$3"
  local marker="$4"

  [[ "$enabled" == "1" ]] || {
    log "Skipping $stage wait because it is disabled."
    record_plan "$stage" "skipped" "disabled"
    return 0
  }

  while true; do
    if marker_done "$file" "$marker"; then
      log "$stage marker found."
      record_plan "$stage" "complete" "$marker"
      return 0
    fi

    log "Waiting for $stage before TinyPerson 640."
    log "Need marker: $file :: $marker"
    record_plan "$stage" "running" "$file"
    sleep "$POLL_SECONDS"
  done
}

wait_for_2d_markers() {
  [[ "$WAIT_FOR_2D" == "1" ]] || {
    log "Skipping 2D wait because WAIT_FOR_2D=$WAIT_FOR_2D"
    record_plan "wait_2d" "skipped" "disabled"
    return 0
  }

  local final_log="outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log"
  local final_marker="QUEUE_FINISHED final P2P4-SelfAttnFR ablation"

  while true; do
    if marker_done "$final_log" "$final_marker"; then
      log "2D final ablation marker found."
      record_plan "wait_2d" "complete" "$final_marker"
      return 0
    fi

    log "Waiting for 2D detector queue to finish before TinyPerson 640."
    log "Need marker: $final_log :: $final_marker"
    record_plan "wait_2d" "running" "$final_log"
    sleep "$POLL_SECONDS"
  done
}

data_ready() {
  local root train val
  root=$(awk '/^path:/ {print $2; exit}' "$DATA_YAML")
  train=$(awk '/^train:/ {print $2; exit}' "$DATA_YAML")
  val=$(awk '/^val:/ {print $2; exit}' "$DATA_YAML")
  [[ -n "${root:-}" && -n "${train:-}" && -n "${val:-}" ]] || return 1
  [[ -d "$root/$train" && -d "$root/$val" ]] || return 1
  find "$root/$train" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print -quit | grep -q .
  find "$root/$val" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print -quit | grep -q .
}

try_prepare_data() {
  [[ "$TRY_PREPARE_DATA" == "1" ]] || return 0
  if find data/raw/TinyPerson -type f -iname "*.json" -print -quit 2>/dev/null | grep -q .; then
    log "TinyPerson raw annotations detected; trying YOLO conversion."
    if bash scripts/ubuntu/prepare_tinyperson_dataset.sh 2>&1 | tee -a "$QUEUE_LOG"; then
      log "TinyPerson conversion finished."
    else
      log "TinyPerson conversion not ready yet; will keep polling."
    fi
  fi
}

wait_for_data() {
  while true; do
    if data_ready; then
      log "TinyPerson data is ready: $DATA_YAML"
      record_plan "data_ready" "complete" "$DATA_YAML"
      return 0
    fi

    try_prepare_data

    if data_ready; then
      log "TinyPerson data is ready after conversion: $DATA_YAML"
      record_plan "data_ready" "complete" "$DATA_YAML"
      return 0
    fi

    if [[ "$WAIT_FOR_DATA" != "1" ]]; then
      log "TinyPerson data is not ready; exiting because WAIT_FOR_DATA=$WAIT_FOR_DATA"
      record_plan "data_ready" "blocked" "$DATA_YAML"
      return 1
    fi

    log "TinyPerson data not ready yet. Expected YOLO tree from $DATA_YAML; polling."
    record_plan "data_ready" "waiting" "$DATA_YAML"
    sleep "$POLL_SECONDS"
  done
}

latest_completed_weight() {
  local run_name="$1"
  find "$PROJECT" -maxdepth 4 \
    -path "*_${run_name}/ultralytics/weights/best.pt" \
    -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-
}

run_train_eval() {
  local job_key="$1"
  local method="$2"
  local ablation="$3"
  local model="$4"
  local init_weights="$5"
  local module="$6"
  local patches="$7"
  local seed="$8"

  local run_name="${job_key}_${RUN_SUFFIX}_seed${seed}"
  local log_file="$LOG_DIR/${run_name}.log"

  if [[ -n "$(latest_completed_weight "$run_name")" ]]; then
    log "Skipping completed TinyPerson job: $run_name"
    record_plan "$job_key" "skipped_completed" "seed=$seed"
    return 0
  fi

  log "Starting $QUEUE_LABEL job=$job_key seed=$seed gpu=$GPU imgsz=$IMG_SIZE"
  record_plan "$job_key" "running" "seed=$seed gpu=$GPU"

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
    --base-model yolo11l.pt
    --proposed-module "$module"
    --implementation-status implemented
  )
  if [[ -n "$init_weights" ]]; then
    args+=(--init-weights "$init_weights")
  fi
  if [[ -n "$patches" ]]; then
    args+=(--model-patches "$patches")
  fi

  if CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo "${args[@]}" 2>&1 | tee -a "$log_file"; then
    log "TRAIN_OK TinyPerson job=$job_key seed=$seed"
    record_plan "$job_key" "train_ok" "seed=$seed"
  else
    log "TRAIN_FAILED TinyPerson job=$job_key seed=$seed"
    record_plan "$job_key" "failed" "seed=$seed"
    return 1
  fi

  local weight
  weight=$(latest_completed_weight "$run_name")
  if [[ -n "$weight" && -f "$weight" ]]; then
    conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo eval \
      --model "$weight" \
      --data-yaml "$DATA_YAML" \
      --imgsz "$IMG_SIZE" \
      --workers "$WORKERS" \
      --device "$GPU" \
      --project "$PROJECT" \
      --name "eval_${run_name}" \
      --method "$method" \
      --ablation "$ablation" \
      --base-model yolo11l.pt \
      --proposed-module "$module" \
      --implementation-status implemented \
      --roc-auc 2>&1 | tee -a "$log_file" || log "WARN: eval failed for $run_name"
  fi
}

run_related_placeholders() {
  [[ "$RUN_RELATED_PLACEHOLDERS" == "1" ]] || return 0
  local related_csv="$STATE_DIR/related_work_optional.csv"
  cat > "$related_csv" <<'CSV'
priority,method,planned_protocol,status,note
P1,CSFPR-RTDETR,TinyPerson 640 eval if adapter is ready,pending_adapter,Keep separate from our trained rows.
P2,LSOD-YOLO,TinyPerson 640 if runnable,pending_code_or_weights,Good citation even if not runnable.
P2,SFFEF-YOLO,TinyPerson 640 if runnable,pending_code_or_weights,Supports tiny-head motivation.
CSV
  log "Wrote optional related-work TinyPerson plan: $related_csv"
  record_plan "related_work_optional" "planned" "$related_csv"
}

collect_results() {
  log "Collecting $QUEUE_LABEL results."
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
    log "WARN: TinyPerson result collection returned non-zero"
}

main() {
  log "$QUEUE_LABEL after-2D core-model queue requested"
  log "Policy: run TinyPerson only after final 2D ablation, runnable related-work 1280 comparisons including UAVDet fallback, and final detector heatmap/qualitative preparation."
  log "Then use GPU$GPU for $QUEUE_LABEL while the other GPU is used for Isaac/3D/reasoner simulation."
  record_plan "queue" "requested" "gpu=$GPU seeds=$SEEDS imgsz=$IMG_SIZE core_models=ours,yolo11l,yolov9c,yolov8l,yolov9m waits=2d,required_related_work,uavdet,heatmap"
  wait_for_2d_markers
  wait_for_marker "$WAIT_FOR_RELATED_WORK" "wait_related_work_1280" "$RELATED_WORK_LOG" "$RELATED_WORK_MARKER"
  wait_for_marker "$WAIT_FOR_UAVDET" "wait_uavdet_1280" "$UAVDET_LOG" "$UAVDET_MARKER"
  wait_for_marker "$WAIT_FOR_HEATMAP" "wait_final_detector_heatmaps" "$HEATMAP_LOG" "$HEATMAP_MARKER"
  wait_for_data

  IFS=',' read -r -a seeds <<< "$SEEDS"
  for seed in "${seeds[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue
    run_train_eval \
      yolo11l \
      YOLOv11l-"$LABEL_SUFFIX" \
      tinyperson_yolo11l_baseline \
      yolo11l.pt \
      "" \
      baseline \
      "" \
      "$seed"

    if [[ "$RUN_STRONG_YOLO_BASELINE" == "1" ]]; then
      run_train_eval \
        yolov9c \
        YOLOv9c-"$LABEL_SUFFIX" \
        tinyperson_yolov9c_strong_baseline \
        yolov9c.pt \
        "" \
        strong_yolo_baseline \
        "" \
        "$seed"
    fi

    if [[ "$RUN_EXTRA_TOP_BASELINES" == "1" ]]; then
      run_train_eval \
        yolov8l \
        YOLOv8l-"$LABEL_SUFFIX" \
        tinyperson_yolov8l_large_baseline \
        yolov8l.pt \
        "" \
        strong_large_yolo_baseline \
        "" \
        "$seed"

      run_train_eval \
        yolov9m \
        YOLOv9m-"$LABEL_SUFFIX" \
        tinyperson_yolov9m_medium_baseline \
        yolov9m.pt \
        "" \
        strong_medium_yolo_baseline \
        "" \
        "$seed"
    fi

    run_train_eval \
      p2p4_selfattnfr \
      ProposedSize-P2P4BalancedSelfAttnTinyFReLU-yolo11l-"$LABEL_SUFFIX" \
      p2p4_balanced_selfattn_tiny_frelu \
      configs/detector/yolo11l-p2p4-balanced-v1.yaml \
      yolo11l.pt \
      p2p4_balanced_head+lite_self_attention_neck+tiny_frelu_neck \
      lite_self_attention_neck,tiny_frelu_neck \
      "$seed"

    if [[ "$RUN_CORE_ABLATION" == "1" ]]; then
      run_train_eval \
        p2p4_head_only \
        ProposedSize-P2P4HeadOnly-yolo11l-"$LABEL_SUFFIX" \
        p2p4_balanced_head_only \
        configs/detector/yolo11l-p2p4-balanced-v1.yaml \
        yolo11l.pt \
        p2p4_balanced_head \
        "" \
        "$seed"
    fi
  done

  run_related_placeholders
  collect_results
  record_plan "queue" "complete" "$QUEUE_LABEL stress test finished"
  log "QUEUE_FINISHED $QUEUE_LABEL stress test"
  log "Plan TSV: $PLAN_TSV"
  log "Dashboard: $DASHBOARD"
}

main "$@"
