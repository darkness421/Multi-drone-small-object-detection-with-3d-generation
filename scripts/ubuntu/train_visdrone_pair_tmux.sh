#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-visdrone-pair}
MODEL_GPU0=${2:-yolov8n.pt}
MODEL_GPU1=${3:-yolo11n.pt}
SEED=${4:-42}
EPOCHS=${5:-100}
BATCH=${6:-8}
IMGSZ=${7:-1280}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
PROJECT=${PROJECT:-outputs/detectors/server_baselines}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}
COMMAND_CSV=${COMMAND_CSV:-outputs/experiments/server_baseline_commands.csv}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}

cd "$(dirname "$0")/../.."

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 1
fi

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready --paths-config configs/paths.ubuntu.yaml --data-yaml "$DATA_YAML" --strict
mkdir -p "$PROJECT" "$LOG_DIR" "$(dirname "$COMMAND_CSV")" .cache/matplotlib .cache/ultralytics
if [[ ! -f "$COMMAND_CSV" ]]; then
  echo "created_at,session,model,seed,physical_gpu,ultralytics_device,imgsz,batch,epochs,data_yaml,run_name,log_file,status,command" > "$COMMAND_CSV"
fi

run_one() {
  local model=$1
  local physical_gpu=$2
  local run_name=${model%.pt}_visdrone_seed${SEED}
  local log_file="$LOG_DIR/${run_name}.log"
  local command="CUDA_DEVICE_ORDER=PCI_BUS_ID conda run --no-capture-output -n $CONDA_ENV python -m detectors.train_yolo train --model $model --data-yaml $DATA_YAML --epochs $EPOCHS --imgsz $IMGSZ --batch $BATCH --device $physical_gpu --seed $SEED --project $PROJECT --name $run_name"
  printf '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","queued","%s"\n' \
    "$(date -Is)" "$SESSION" "$model" "$SEED" "$physical_gpu" "$physical_gpu" "$IMGSZ" "$BATCH" "$EPOCHS" "$DATA_YAML" "$run_name" "$log_file" "$command" >> "$COMMAND_CSV"
  CUDA_DEVICE_ORDER=PCI_BUS_ID PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" MPLCONFIGDIR="$PWD/.cache/matplotlib" YOLO_CONFIG_DIR="$PWD/.cache/ultralytics" \
    bash -lc "$command 2>&1 | tee '$log_file'"
  if [[ "$RUN_EVAL" == "1" ]]; then
    run_dir=$(find "$PROJECT" -maxdepth 1 -type d -name "*_${run_name}" -printf "%T@ %p\n" | sort -nr | head -n 1 | cut -d" " -f2-)
    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then
      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml "$DATA_YAML" --imgsz "$IMGSZ" --device "$physical_gpu" --project "$PROJECT" --name "eval_${run_name}")
      if [[ "$ROC_AUC" == "1" ]]; then
        eval_args+=(--roc-auc)
      fi
      CUDA_DEVICE_ORDER=PCI_BUS_ID PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" MPLCONFIGDIR="$PWD/.cache/matplotlib" YOLO_CONFIG_DIR="$PWD/.cache/ultralytics" \
        conda run --no-capture-output -n "$CONDA_ENV" python -m detectors.train_yolo "${eval_args[@]}" 2>&1 | tee -a "$log_file"
    fi
  fi
}

TMUX_ENV="export DATA_YAML='$DATA_YAML' CONDA_ENV='$CONDA_ENV' PROJECT='$PROJECT' LOG_DIR='$LOG_DIR' COMMAND_CSV='$COMMAND_CSV' SEED='$SEED' EPOCHS='$EPOCHS' BATCH='$BATCH' IMGSZ='$IMGSZ' SESSION='$SESSION' RUN_EVAL='$RUN_EVAL' ROC_AUC='$ROC_AUC'"
tmux new-session -d -s "$SESSION" -n gpu0 "cd '$PWD' && $TMUX_ENV; $(declare -f run_one); run_one '$MODEL_GPU0' 0"
tmux new-window -t "$SESSION" -n gpu1 "cd '$PWD' && $TMUX_ENV; $(declare -f run_one); run_one '$MODEL_GPU1' 1"

echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "GPU0: $MODEL_GPU0 seed $SEED"
echo "GPU1: $MODEL_GPU1 seed $SEED"
echo "Logs: $LOG_DIR"
