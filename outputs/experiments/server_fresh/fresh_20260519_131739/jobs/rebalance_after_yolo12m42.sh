#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/oem/projects/multi-uav-marine-city}"
cd "$ROOT"

MODE="${MODE:-watch}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
CONDA_ENV="${CONDA_ENV:-com3d-ace}"
PROJECT="${PROJECT:-outputs/detectors/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713}"
LOG_DIR="${LOG_DIR:-outputs/logs/server_fresh_baselines/fresh_20260519_131739_resume_20260522_190713}"
DATA_YAML="${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}"
IMG="${IMG:-1280}"
WORKERS="${WORKERS:-4}"
BATCH="${BATCH:-4}"
EPOCHS="${EPOCHS:-100}"
CURRENT_LOG="${CURRENT_LOG:-$LOG_DIR/yolo12m_visdrone_fresh_fresh_20260519_131739_seed42_resume_20260522_190713.log}"
ORIGINAL_SESSION="${ORIGINAL_SESSION:-server-fresh-baselines-resume}"
CONT_SESSION="${CONT_SESSION:-server-isolated-continuation}"
DUAL_VIEW_SESSION="${DUAL_VIEW_SESSION:-server-training-dual-view}"
GPU1_SCRIPT="${GPU1_SCRIPT:-outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu1_memory_safe_recovery.sh}"

mkdir -p "$LOG_DIR"

guard_gpu() {
  local gpu="$1"
  bash scripts/ubuntu/check_resource_margin.sh \
    --path . \
    --gpu "$gpu" \
    --min-free-gb "${MIN_FREE_GB:-100}" \
    --max-disk-use-percent "${MAX_DISK_USE_PERCENT:-92}" \
    --min-ram-gb "${MIN_RAM_GB:-16}" \
    --min-gpu-free-gb "${MIN_GPU_FREE_GB:-6}" \
    --max-retries 1
}

run_gpu0_yolo12m_seed2026() {
  export CUDA_DEVICE_ORDER="${CUDA_DEVICE_ORDER:-PCI_BUS_ID}"
  export CUDA_VISIBLE_DEVICES=0
  export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

  local run_name="yolo12m_visdrone_fresh_fresh_20260519_131739_seed2026_isolated_${RUN_ID}"
  local log_file="$LOG_DIR/${run_name}.log"

  guard_gpu 0
  echo "ISOLATED_GPU0_START model=yolo12m.pt seed=2026 physical_gpu=0 ultralytics_device=0 at $(date --iso-8601=seconds)"
  if conda run --no-capture-output -n "$CONDA_ENV" \
    python -m detectors.train_yolo train \
      --model yolo12m.pt \
      --data-yaml "$DATA_YAML" \
      --epochs "$EPOCHS" \
      --imgsz "$IMG" \
      --batch "$BATCH" \
      --workers "$WORKERS" \
      --device 0 \
      --seed 2026 \
      --project "$PROJECT" \
      --name "$run_name" 2>&1 | tee "$log_file"; then
    echo "TRAIN_OK model=yolo12m.pt seed=2026 gpu=0 isolated=1 at $(date --iso-8601=seconds)" | tee -a "$log_file"
  else
    echo "TRAIN_FAILED model=yolo12m.pt seed=2026 gpu=0 isolated=1 at $(date --iso-8601=seconds)" | tee -a "$log_file"
    touch "outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu0_isolated.done"
    return 0
  fi

  local run_dir
  run_dir="$(find "$PROJECT" -maxdepth 1 -type d -name "*${run_name}" | sort | tail -1)"
  if [[ -n "$run_dir" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
    guard_gpu 0
    conda run --no-capture-output -n "$CONDA_ENV" \
      python -m detectors.train_yolo eval \
        --model "$run_dir/ultralytics/weights/best.pt" \
        --data-yaml "$DATA_YAML" \
        --imgsz "$IMG" \
        --workers "$WORKERS" \
        --device 0 \
        --project "$PROJECT" \
        --name "eval_${run_name}" \
        --roc-auc 2>&1 | tee -a "$log_file" || echo "EVAL_FAILED model=yolo12m.pt seed=2026 isolated=1 at $(date --iso-8601=seconds)" | tee -a "$log_file"
  fi

  echo "ISOLATED_GPU0_DONE at $(date --iso-8601=seconds)" | tee -a "$log_file"
  touch "outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu0_isolated.done"
}

collect_when_done() {
  echo "ISOLATED_COLLECTOR waiting at $(date --iso-8601=seconds)"
  while [[ ! -f outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu0_isolated.done ]]; do sleep 60; done
  while [[ ! -f outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu1_isolated.done ]]; do sleep 60; done
  echo "ISOLATED_COLLECTOR collecting at $(date --iso-8601=seconds)"
  DETECTOR_ROOTS="outputs/detectors/server_fresh_baselines/fresh_20260519_131739,${PROJECT}" \
  DEDUPE_KEY="dataset,model,seed,ablation,proposed_module" \
  RESULTS_CSV="outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_results.csv" \
  SUMMARY_CSV="outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_summary.csv" \
  PVALUES_CSV="outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_pvalues.csv" \
  DASHBOARD="outputs/reports/server_fresh_baselines/fresh_20260519_131739/figures/server_baseline_dashboard.png" \
  REPORT_DIR="outputs/reports/server_fresh_baselines/fresh_20260519_131739" \
  CONDA_ENV="$CONDA_ENV" \
    bash scripts/ubuntu/collect_server_results.sh "$PROJECT" 2>&1 | tee "$LOG_DIR/isolated_final_collection_${RUN_ID}.log"
}

start_continuation() {
  rm -f outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu0_isolated.done
  rm -f outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu1_isolated.done

  tmux kill-session -t "$CONT_SESSION" 2>/dev/null || true
  tmux new-session -d -s "$CONT_SESSION" -n gpu0 \
    "cd '$ROOT' && MODE=gpu0 RUN_ID='$RUN_ID' bash '$ROOT/outputs/experiments/server_fresh/fresh_20260519_131739/jobs/rebalance_after_yolo12m42.sh'"
  tmux new-window -t "$CONT_SESSION" -n gpu1 \
    "cd '$ROOT' && PHYSICAL_GPU=1 ULTRALYTICS_DEVICE=0 RUN_ID='$RUN_ID' bash '$ROOT/$GPU1_SCRIPT'; touch '$ROOT/outputs/experiments/server_fresh/fresh_20260519_131739/jobs/gpu1_isolated.done'"
  tmux new-window -t "$CONT_SESSION" -n collect \
    "cd '$ROOT' && MODE=collect RUN_ID='$RUN_ID' bash '$ROOT/outputs/experiments/server_fresh/fresh_20260519_131739/jobs/rebalance_after_yolo12m42.sh'"

  tmux kill-session -t "$DUAL_VIEW_SESSION" 2>/dev/null || true
  tmux new-session -d -s "$DUAL_VIEW_SESSION" -n both \
    "cd '$ROOT' && while true; do clear; echo 'GPU0 / isolated continuation'; date -Is; echo; tmux capture-pane -p -S -22 -t '$CONT_SESSION:0.0'; sleep 2; done"
  tmux split-window -h -t "$DUAL_VIEW_SESSION:0" \
    "cd '$ROOT' && while true; do clear; echo 'GPU1 / isolated recovery'; date -Is; echo; tmux capture-pane -p -S -22 -t '$CONT_SESSION:1.0'; sleep 2; done"
  tmux select-layout -t "$DUAL_VIEW_SESSION:0" even-horizontal

  echo "Started isolated continuation session: $CONT_SESSION"
}

watch_and_rebalance() {
  echo "GPU rebalance watcher started at $(date --iso-8601=seconds)"
  echo "Waiting for current job to finish: $CURRENT_LOG"
  while ! grep -q "DONE model=yolo12m.pt seed=42" "$CURRENT_LOG" 2>/dev/null; do
    echo
    echo "Still waiting at $(date --iso-8601=seconds)"
    tail -8 "$CURRENT_LOG" 2>/dev/null || true
    sleep 60
  done

  echo "Detected yolo12m seed42 DONE at $(date --iso-8601=seconds)"
  echo "Stopping old non-isolated GPU0 queue before yolo12m seed2026 can occupy both device files."
  tmux kill-window -t "$ORIGINAL_SESSION:0" 2>/dev/null || true
  start_continuation
}

case "$MODE" in
  gpu0)
    run_gpu0_yolo12m_seed2026
    ;;
  collect)
    collect_when_done
    ;;
  watch)
    watch_and_rebalance
    ;;
  *)
    echo "Unknown MODE=$MODE" >&2
    exit 2
    ;;
esac
