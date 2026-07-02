#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-server-visdrone-baselines}
EPOCHS=${2:-100}
BATCH=${3:-8}
IMGSZ=${4:-1280}
SEEDS=${SEEDS:-42,123,2026}
MODELS=${MODELS:-yolov8n.pt,yolov8s.pt,yolo11n.pt,yolo11s.pt,yolo12n.pt,yolo12s.pt,rtdetr-l.pt}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
DATASET_TAG=${DATASET_TAG:-}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
PROJECT=${PROJECT:-outputs/detectors/server_baselines}
EXPERIMENT_ROOT=${EXPERIMENT_ROOT:-outputs/experiments}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}
GPU_LIST=${GPU_LIST:-0,1}

cd "$(dirname "$0")/../.."
ROOT=$PWD
STAMP=$(date +%Y%m%d_%H%M%S)
JOB_ROOT="$EXPERIMENT_ROOT/server_baseline_jobs/$STAMP"
COMMAND_CSV="$EXPERIMENT_ROOT/server_baseline_commands.csv"

if [[ -z "$DATASET_TAG" ]]; then
  data_base=$(basename "$DATA_YAML")
  DATASET_TAG=${data_base%_yolo_data.yaml}
  DATASET_TAG=${DATASET_TAG%_data.yaml}
  DATASET_TAG=${DATASET_TAG%.yaml}
fi
DATASET_TAG=${DATASET_TAG//[^[:alnum:]_-]/_}

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Install tmux or run the generated job scripts manually."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 1
fi

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready --paths-config configs/paths.ubuntu.yaml --data-yaml "$DATA_YAML" --strict

mkdir -p "$JOB_ROOT" "$LOG_DIR" "$PROJECT" "$EXPERIMENT_ROOT"
if [[ ! -f "$COMMAND_CSV" ]]; then
  echo "created_at,session,model,seed,physical_gpu,ultralytics_device,imgsz,batch,epochs,data_yaml,run_name,log_file,status,command" > "$COMMAND_CSV"
fi

IFS=',' read -r -a gpu_list <<< "$GPU_LIST"
active_gpus=()
for gpu in "${gpu_list[@]}"; do
  gpu=${gpu//[[:space:]]/}
  [[ -z "$gpu" ]] && continue
  active_gpus+=("$gpu")
  script="$JOB_ROOT/gpu${gpu}.sh"
  {
    echo "#!/usr/bin/env bash"
    echo "set -euo pipefail"
    printf 'cd %q\n' "$ROOT"
    echo 'export CUDA_DEVICE_ORDER=PCI_BUS_ID'
    echo 'export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"'
    printf 'export CONDA_ENV=%q\n' "$CONDA_ENV"
    printf 'export MPLCONFIGDIR=%q\n' "$ROOT/.cache/matplotlib"
    printf 'export YOLO_CONFIG_DIR=%q\n' "$ROOT/.cache/ultralytics"
    echo 'mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"'
  } > "$script"
  chmod +x "$script"
done

if [[ ${#active_gpus[@]} -eq 0 ]]; then
  echo "GPU_LIST did not contain any GPU ids: $GPU_LIST" >&2
  exit 2
fi

IFS=',' read -r -a model_list <<< "$MODELS"
IFS=',' read -r -a seed_list <<< "$SEEDS"

job_index=0
for model in "${model_list[@]}"; do
  model=${model//[[:space:]]/}
  [[ -z "$model" ]] && continue
  model_slug=${model%.pt}
  model_slug=${model_slug//[^[:alnum:]_/-]/_}
  model_slug=${model_slug//\//_}
  for seed in "${seed_list[@]}"; do
    seed=${seed//[[:space:]]/}
    [[ -z "$seed" ]] && continue
    gpu="${active_gpus[$((job_index % ${#active_gpus[@]}))]}"
    run_name="${model_slug}_${DATASET_TAG}_seed${seed}"
    log_file="$LOG_DIR/${run_name}.log"
    job_script="$JOB_ROOT/gpu${gpu}.sh"
    command="CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n $CONDA_ENV python -m detectors.train_yolo train --model $model --data-yaml $DATA_YAML --epochs $EPOCHS --imgsz $IMGSZ --batch $BATCH --device $gpu --seed $seed --project $PROJECT --name $run_name"
    printf '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","queued","%s"\n' \
      "$(date -Is)" "$SESSION" "$model" "$seed" "$gpu" "$gpu" "$IMGSZ" "$BATCH" "$EPOCHS" "$DATA_YAML" "$run_name" "$log_file" "$command" >> "$COMMAND_CSV"
    {
      printf 'echo "START model=%s seed=%s physical_gpu=%s at $(date -Is)"\n' "$model" "$seed" "$gpu"
      printf 'conda run --no-capture-output -n %q python -m detectors.train_yolo train --model %q --data-yaml %q --epochs %q --imgsz %q --batch %q --device %q --seed %q --project %q --name %q 2>&1 | tee %q\n' \
        "$CONDA_ENV" "$model" "$DATA_YAML" "$EPOCHS" "$IMGSZ" "$BATCH" "$gpu" "$seed" "$PROJECT" "$run_name" "$log_file"
      printf 'if [[ %q == 1 ]]; then\n' "$RUN_EVAL"
      printf '  run_dir=$(find %q -maxdepth 1 -type d -name "*_%s" -printf "%%T@ %%p\\n" | sort -nr | head -n 1 | cut -d" " -f2-)\n' "$PROJECT" "$run_name"
      printf '  if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then\n'
      printf '    eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml %q --imgsz %q --device %q --project %q --name %q)\n' "$DATA_YAML" "$IMGSZ" "$gpu" "$PROJECT" "eval_${run_name}"
      printf '    if [[ %q == 1 ]]; then eval_args+=(--roc-auc); fi\n' "$ROC_AUC"
      printf '    conda run --no-capture-output -n %q python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a %q\n' "$CONDA_ENV" "$log_file"
      printf '  fi\n'
      printf 'fi\n'
      printf 'echo "DONE model=%s seed=%s physical_gpu=%s at $(date -Is)"\n' "$model" "$seed" "$gpu"
    } >> "$job_script"
    job_index=$((job_index + 1))
  done
done

first_gpu="${active_gpus[0]}"
tmux new-session -d -s "$SESSION" -n "gpu${first_gpu}" "$JOB_ROOT/gpu${first_gpu}.sh"
for gpu in "${active_gpus[@]:1}"; do
  tmux new-window -t "$SESSION" -n "gpu${gpu}" "$JOB_ROOT/gpu${gpu}.sh"
done

echo "Started tmux session: $SESSION"
echo "Dataset tag: $DATASET_TAG"
echo "GPU list: ${active_gpus[*]}"
echo "Attach: tmux attach -t $SESSION"
echo "Job scripts: $JOB_ROOT"
echo "Command CSV: $COMMAND_CSV"
echo "Logs: $LOG_DIR"
