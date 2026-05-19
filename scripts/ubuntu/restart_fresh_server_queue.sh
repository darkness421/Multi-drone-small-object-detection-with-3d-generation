#!/usr/bin/env bash
set -euo pipefail

RUN_ID=${RUN_ID:-$(date +%Y%m%d_%H%M%S)}
SESSION=${SESSION:-server-fresh-baselines}
MONITOR_SESSION=${MONITOR_SESSION:-server-baseline-monitor}
DUAL_VIEW_SESSION=${DUAL_VIEW_SESSION:-server-training-dual-view}
VIEWER_SESSION=${VIEWER_SESSION:-server-live-viewer}
VIEWER_PORT=${VIEWER_PORT:-8766}
STOP_EXISTING=${STOP_EXISTING:-1}

CONDA_ENV=${CONDA_ENV:-com3d-ace}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
DATASET_TAG=${DATASET_TAG:-visdrone}
EPOCHS=${EPOCHS:-100}
IMGSZ=${IMGSZ:-1280}
SEEDS=${SEEDS:-42,123,2026}
GPUS=${GPUS:-0,1}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}
CHECK_MODELS=${CHECK_MODELS:-1}
LIVE_INTERVAL=${LIVE_INTERVAL:-60}

# Order is intentional: YOLOv10s starts first so the immediately visible run
# matches the current comparison focus. Batch can be set per model with
# model.pt:batch.
MODEL_SPECS=${MODEL_SPECS:-yolov10s.pt:8,yolov10n.pt:8,yolov9s.pt:8,yolov5su.pt:8,yolov8n.pt:8,yolov8s.pt:8,yolo11n.pt:8,yolo11s.pt:8,yolo12n.pt:8,yolo12s.pt:8,yolo26n.pt:8,yolo26s.pt:8,rtdetr-l.pt:4,yolov10m.pt:4,yolo12m.pt:4}

PROJECT=${PROJECT:-outputs/detectors/server_fresh_baselines/$RUN_ID}
EXPERIMENT_ROOT=${EXPERIMENT_ROOT:-outputs/experiments/server_fresh/$RUN_ID}
LOG_DIR=${LOG_DIR:-outputs/logs/server_fresh_baselines/$RUN_ID}
REPORT_DIR=${REPORT_DIR:-outputs/reports/server_fresh_baselines/$RUN_ID}
LIVE_RESULTS_CSV=${LIVE_RESULTS_CSV:-$EXPERIMENT_ROOT/live/server_baseline_results.csv}
LIVE_SUMMARY_CSV=${LIVE_SUMMARY_CSV:-$EXPERIMENT_ROOT/live/server_baseline_summary.csv}
LIVE_PVALUES_CSV=${LIVE_PVALUES_CSV:-$EXPERIMENT_ROOT/live/server_baseline_pvalues.csv}
LIVE_DASHBOARD=${LIVE_DASHBOARD:-outputs/reports/live/${RUN_ID}_server_baseline_dashboard.png}
FINAL_RESULTS_CSV=${FINAL_RESULTS_CSV:-$EXPERIMENT_ROOT/server_baseline_results.csv}
FINAL_SUMMARY_CSV=${FINAL_SUMMARY_CSV:-$EXPERIMENT_ROOT/server_baseline_summary.csv}
FINAL_PVALUES_CSV=${FINAL_PVALUES_CSV:-$EXPERIMENT_ROOT/server_baseline_pvalues.csv}
FINAL_DASHBOARD=${FINAL_DASHBOARD:-$REPORT_DIR/figures/server_baseline_dashboard.png}
COMMAND_CSV=${COMMAND_CSV:-$EXPERIMENT_ROOT/server_baseline_commands.csv}
JOB_ROOT=${JOB_ROOT:-$EXPERIMENT_ROOT/jobs}

cd "$(dirname "$0")/../.."
ROOT=$PWD

export MPLCONFIGDIR="${MPLCONFIGDIR:-$ROOT/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$ROOT/.cache/ultralytics}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$ROOT/.cache}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"

echo "Fresh server queue preflight"
echo "  run id:       $RUN_ID"
echo "  session:      $SESSION"
echo "  detector root:$PROJECT"
echo "  report dir:   $REPORT_DIR"
echo "  model specs:  $MODEL_SPECS"
echo "  seeds:        $SEEDS"
echo ""

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready \
  --paths-config configs/paths.ubuntu.yaml \
  --data-yaml "$DATA_YAML" \
  --strict

if [[ "$STOP_EXISTING" == "1" ]]; then
  for old_session in \
    server-extra-comparison-small \
    server-extra-comparison-medium \
    server-extra-comparisons-pending \
    server-additional-comparisons-pending \
    server-paper-yolo-comparison-pending \
    server-uavdt-comparisons-pending \
    server-proposed-ablation-pending \
    "$SESSION" \
    "$MONITOR_SESSION" \
    "$DUAL_VIEW_SESSION" \
    "$VIEWER_SESSION"; do
    tmux kill-session -t "$old_session" 2>/dev/null || true
  done
fi

mkdir -p "$PROJECT" "$EXPERIMENT_ROOT" "$LOG_DIR" "$REPORT_DIR/figures" "$JOB_ROOT" \
  "$(dirname "$LIVE_RESULTS_CSV")" "$(dirname "$LIVE_DASHBOARD")"

MODEL_SPECS="$MODEL_SPECS" CHECK_MODELS="$CHECK_MODELS" CONDA_ENV="$CONDA_ENV" \
  conda run --no-capture-output -n "$CONDA_ENV" python - <<'PY' > "$JOB_ROOT/model_specs.available"
import os
import sys

from ultralytics import YOLO

check = os.environ.get("CHECK_MODELS", "1") == "1"
specs = [item.strip() for item in os.environ["MODEL_SPECS"].split(",") if item.strip()]
available = []
for spec in specs:
    parts = spec.split(":")
    model = parts[0].strip()
    batch = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "8"
    if not check:
        available.append(f"{model}:{batch}")
        continue
    print(f"Checking model availability: {model}", file=sys.stderr, flush=True)
    try:
        YOLO(model)
    except Exception as exc:
        print(f"SKIP unavailable model {model}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    else:
        available.append(f"{model}:{batch}")
print(",".join(available))
PY

AVAILABLE_MODEL_SPECS=$(tail -n 1 "$JOB_ROOT/model_specs.available")
if [[ -z "$AVAILABLE_MODEL_SPECS" ]]; then
  echo "No available models after availability check."
  echo "Requested: $MODEL_SPECS"
  exit 1
fi

echo "Available model specs: $AVAILABLE_MODEL_SPECS"

echo "created_at,session,model,seed,physical_gpu,ultralytics_device,imgsz,batch,epochs,data_yaml,run_name,log_file,status,command" > "$COMMAND_CSV"

IFS=',' read -r -a gpu_list <<< "$GPUS"
for gpu in "${gpu_list[@]}"; do
  gpu=${gpu//[[:space:]]/}
  [[ -z "$gpu" ]] && continue
  script="$JOB_ROOT/gpu${gpu}.sh"
  {
    echo "#!/usr/bin/env bash"
    echo "set -uo pipefail"
    printf 'cd %q\n' "$ROOT"
    echo 'export CUDA_DEVICE_ORDER=PCI_BUS_ID'
    echo 'export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"'
    printf 'export MPLCONFIGDIR=%q\n' "$MPLCONFIGDIR"
    printf 'export YOLO_CONFIG_DIR=%q\n' "$YOLO_CONFIG_DIR"
    printf 'export XDG_CACHE_HOME=%q\n' "$XDG_CACHE_HOME"
    echo 'mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"'
    printf 'echo "GPU worker %s started at $(date -Is)"\n' "$gpu"
  } > "$script"
  chmod +x "$script"
done

IFS=',' read -r -a spec_list <<< "$AVAILABLE_MODEL_SPECS"
IFS=',' read -r -a seed_list <<< "$SEEDS"

job_index=0
gpu_count=${#gpu_list[@]}
for spec in "${spec_list[@]}"; do
  spec=${spec//[[:space:]]/}
  [[ -z "$spec" ]] && continue
  model=${spec%%:*}
  batch=${spec#*:}
  if [[ "$batch" == "$model" ]]; then
    batch=8
  fi
  model_slug=${model%.pt}
  model_slug=${model_slug//[^[:alnum:]_/-]/_}
  model_slug=${model_slug//\//_}
  for seed in "${seed_list[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue
    gpu=${gpu_list[$((job_index % gpu_count))]//[[:space:]]/}
    run_name="${model_slug}_${DATASET_TAG}_fresh_${RUN_ID}_seed${seed}"
    log_file="$LOG_DIR/${run_name}.log"
    job_script="$JOB_ROOT/gpu${gpu}.sh"
    command="CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n $CONDA_ENV python -m detectors.train_yolo train --model $model --data-yaml $DATA_YAML --epochs $EPOCHS --imgsz $IMGSZ --batch $batch --device $gpu --seed $seed --project $PROJECT --name $run_name"
    printf '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","queued","%s"\n' \
      "$(date -Is)" "$SESSION" "$model" "$seed" "$gpu" "$gpu" "$IMGSZ" "$batch" "$EPOCHS" "$DATA_YAML" "$run_name" "$log_file" "$command" >> "$COMMAND_CSV"
    {
      printf '\necho "START model=%s seed=%s gpu=%s batch=%s at $(date -Is)"\n' "$model" "$seed" "$gpu" "$batch"
      printf 'if conda run --no-capture-output -n %q python -m detectors.train_yolo train --model %q --data-yaml %q --epochs %q --imgsz %q --batch %q --device %q --seed %q --project %q --name %q 2>&1 | tee %q; then\n' \
        "$CONDA_ENV" "$model" "$DATA_YAML" "$EPOCHS" "$IMGSZ" "$batch" "$gpu" "$seed" "$PROJECT" "$run_name" "$log_file"
      printf '  echo "TRAIN_OK model=%s seed=%s gpu=%s at $(date -Is)" | tee -a %q\n' "$model" "$seed" "$gpu" "$log_file"
      printf '  if [[ %q == 1 ]]; then\n' "$RUN_EVAL"
      printf '    run_dir=$(find %q -maxdepth 1 -type d \\( -name %q -o -name %q \\) -printf "%%T@ %%p\\n" | sort -nr | head -n 1 | cut -d" " -f2-)\n' "$PROJECT" "$run_name" "*_${run_name}"
      printf '    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then\n'
      printf '      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml %q --imgsz %q --device %q --project %q --name %q)\n' "$DATA_YAML" "$IMGSZ" "$gpu" "$PROJECT" "eval_${run_name}"
      printf '      if [[ %q == 1 ]]; then eval_args+=(--roc-auc); fi\n' "$ROC_AUC"
      printf '      conda run --no-capture-output -n %q python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a %q || echo "EVAL_FAILED model=%s seed=%s at $(date -Is)" | tee -a %q\n' "$CONDA_ENV" "$log_file" "$model" "$seed" "$log_file"
      printf '    else\n'
      printf '      echo "EVAL_SKIPPED missing best.pt model=%s seed=%s at $(date -Is)" | tee -a %q\n' "$model" "$seed" "$log_file"
      printf '    fi\n'
      printf '  fi\n'
      printf 'else\n'
      printf '  echo "TRAIN_FAILED model=%s seed=%s gpu=%s at $(date -Is)" | tee -a %q\n' "$model" "$seed" "$gpu" "$log_file"
      printf 'fi\n'
      printf 'echo "DONE model=%s seed=%s gpu=%s at $(date -Is)" | tee -a %q\n' "$model" "$seed" "$gpu" "$log_file"
    } >> "$job_script"
    job_index=$((job_index + 1))
  done
done

for gpu in "${gpu_list[@]}"; do
  gpu=${gpu//[[:space:]]/}
  [[ -z "$gpu" ]] && continue
  {
    printf '\necho "GPU worker %s finished at $(date -Is)"\n' "$gpu"
    printf 'touch %q\n' "$JOB_ROOT/gpu${gpu}.done"
  } >> "$JOB_ROOT/gpu${gpu}.sh"
done

collector="$JOB_ROOT/collect_when_done.sh"
{
  echo "#!/usr/bin/env bash"
  echo "set -uo pipefail"
  printf 'cd %q\n' "$ROOT"
  printf 'echo "Collector waiting for GPU workers at $(date -Is)"\n'
  for gpu in "${gpu_list[@]}"; do
    gpu=${gpu//[[:space:]]/}
    [[ -z "$gpu" ]] && continue
    printf 'while [[ ! -f %q ]]; do echo "Waiting for gpu%s at $(date -Is)"; sleep 60; done\n' "$JOB_ROOT/gpu${gpu}.done" "$gpu"
  done
  printf 'echo "All GPU workers finished; collecting results at $(date -Is)"\n'
  printf 'DETECTOR_ROOT=%q RESULTS_CSV=%q SUMMARY_CSV=%q PVALUES_CSV=%q DASHBOARD=%q REPORT_DIR=%q CONDA_ENV=%q bash scripts/ubuntu/collect_server_results.sh %q 2>&1 | tee %q\n' \
    "$PROJECT" "$FINAL_RESULTS_CSV" "$FINAL_SUMMARY_CSV" "$FINAL_PVALUES_CSV" "$FINAL_DASHBOARD" "$REPORT_DIR" "$CONDA_ENV" "$PROJECT" "$LOG_DIR/final_collection.log"
  printf 'echo "Fresh queue complete at $(date -Is)" | tee -a %q\n' "$LOG_DIR/final_collection.log"
} > "$collector"
chmod +x "$collector"

first_gpu=${gpu_list[0]//[[:space:]]/}
tmux new-session -d -s "$SESSION" -n "gpu${first_gpu}" "$JOB_ROOT/gpu${first_gpu}.sh"
for gpu in "${gpu_list[@]:1}"; do
  gpu=${gpu//[[:space:]]/}
  [[ -z "$gpu" ]] && continue
  tmux new-window -t "$SESSION" -n "gpu${gpu}" "$JOB_ROOT/gpu${gpu}.sh"
done
tmux new-window -t "$SESSION" -n collect "$collector"

PROJECT_DIR="$PROJECT" RESULTS_CSV="$LIVE_RESULTS_CSV" SUMMARY_CSV="$LIVE_SUMMARY_CSV" PVALUES_CSV="$LIVE_PVALUES_CSV" \
  LOG_DIR="$LOG_DIR" COMMAND_CSV="$COMMAND_CSV" DASHBOARD="$LIVE_DASHBOARD" CONDA_ENV="$CONDA_ENV" \
  bash scripts/ubuntu/monitor_server_baselines_tmux.sh "$MONITOR_SESSION" "$SESSION" "$LIVE_INTERVAL"

tmux new-session -d -s "$VIEWER_SESSION" -n viewer \
  "cd '$ROOT' && conda run --no-capture-output -n '$CONDA_ENV' python -m scripts.ubuntu.live_training_viewer --host 0.0.0.0 --port '$VIEWER_PORT' --training-session '$SESSION' --project-dir '$PROJECT' --summary-csv '$LIVE_SUMMARY_CSV' --log-dir '$LOG_DIR' --dashboard '$FINAL_DASHBOARD' --live-dashboard '$LIVE_DASHBOARD'"

tmux new-session -d -s "$DUAL_VIEW_SESSION" -n both \
  "cd '$ROOT' && while true; do clear; echo 'GPU0 / fresh queue'; date -Is; echo; tmux capture-pane -p -S -22 -t '$SESSION:0.0'; sleep 2; done"
tmux split-window -h -t "$DUAL_VIEW_SESSION:0" \
  "cd '$ROOT' && while true; do clear; echo 'GPU1 / fresh queue'; date -Is; echo; tmux capture-pane -p -S -22 -t '$SESSION:1.0'; sleep 2; done"
tmux select-layout -t "$DUAL_VIEW_SESSION:0" even-horizontal

cat <<EOF
Started fresh server queue.

Run ID:          $RUN_ID
Training tmux:   tmux attach -t $SESSION
Dual view tmux:  tmux attach -t $DUAL_VIEW_SESSION
Monitor tmux:    tmux attach -t $MONITOR_SESSION
Browser viewer:  http://$(hostname -I | awk '{print $1}'):$VIEWER_PORT/

Detector root:   $PROJECT
Command CSV:     $COMMAND_CSV
Live summary:    $LIVE_SUMMARY_CSV
Final report:    $REPORT_DIR/README.md
EOF
