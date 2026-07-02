#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

WAIT_FOR=${WAIT_FOR:-server-top3-proposed-screening}
POLL_SECONDS=${POLL_SECONDS:-300}
SESSION=${SESSION:-server-input-size-sweep}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
CONFIG=${CONFIG:-configs/experiments/supp_detector_input_size_sweep.yaml}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
IMGSZ_LIST=${IMGSZ_LIST:-1280}
EPOCHS=${EPOCHS:-100}
SEEDS=${SEEDS:-42}
GPUS=${GPUS:-0}
ENABLE_PLANNED=${ENABLE_PLANNED:-0}
WAIT_AFTER_START=${WAIT_AFTER_START:-0}
SKIP_COMPLETED=${SKIP_COMPLETED:-1}
COMPLETED_RESULTS_CSV=${COMPLETED_RESULTS_CSV:-outputs/experiments/server_input_size_sweep_results.csv}

ROOT=$PWD
STAMP=$(date +%Y%m%d_%H%M%S)
JOB_ROOT="outputs/experiments/input_size_sweep_jobs/$STAMP"
MANIFEST_DIR="$JOB_ROOT/manifests"
mkdir -p "$MANIFEST_DIR"

batch_for_imgsz() {
  case "$1" in
    960) echo "${BATCH_960:-6}" ;;
    1280) echo "${BATCH_1280:-4}" ;;
    1536) echo "${BATCH_1536:-2}" ;;
    *) echo "${BATCH_DEFAULT:-2}" ;;
  esac
}

wait_for_sessions() {
  local sessions=$1
  [[ -z "$sessions" ]] && return
  while true; do
    local active=()
    IFS=',' read -r -a session_list <<< "$sessions"
    for session in "${session_list[@]}"; do
      session=${session//[[:space:]]/}
      [[ -z "$session" ]] && continue
      if tmux has-session -t "$session" 2>/dev/null; then
        active+=("$session")
      fi
    done
    if [[ "${#active[@]}" -eq 0 ]]; then
      return
    fi
    echo "Waiting for tmux sessions to finish: ${active[*]} at $(date -Is)"
    sleep "$POLL_SECONDS"
  done
}

wait_for_sessions "$WAIT_FOR"

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready \
  --paths-config configs/paths.ubuntu.yaml \
  --data-yaml "$DATA_YAML" \
  --strict

IFS=',' read -r -a gpu_list <<< "$GPUS"
IFS=',' read -r -a size_list <<< "$IMGSZ_LIST"

for imgsz in "${size_list[@]}"; do
  imgsz=${imgsz//[[:space:]]/}
  [[ -z "$imgsz" ]] && continue
  batch=$(batch_for_imgsz "$imgsz")
  size_root="$JOB_ROOT/imgsz${imgsz}"
  manifest="$MANIFEST_DIR/imgsz${imgsz}.json"
  args=(
    --config "$CONFIG"
    --job-root "$size_root"
    --manifest "$manifest"
    --session "$SESSION"
    --conda-env "$CONDA_ENV"
    --gpus "$GPUS"
    --epochs "$EPOCHS"
    --batch "$batch"
    --imgsz "$imgsz"
    --seeds "$SEEDS"
  )
  if [[ "$ENABLE_PLANNED" == "1" ]]; then
    args+=(--enable-planned)
  fi
  if [[ "$SKIP_COMPLETED" == "1" && -n "$COMPLETED_RESULTS_CSV" ]]; then
    args+=(--skip-completed)
    IFS=',' read -r -a completed_csvs <<< "$COMPLETED_RESULTS_CSV"
    for completed_csv in "${completed_csvs[@]}"; do
      completed_csv=${completed_csv//[[:space:]]/}
      [[ -z "$completed_csv" ]] && continue
      args+=(--completed-results-csv "$completed_csv")
    done
  fi
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.proposed_ablation_jobs "${args[@]}"
done

for gpu in "${gpu_list[@]}"; do
  gpu=${gpu//[[:space:]]/}
  [[ -z "$gpu" ]] && continue
  wrapper="$JOB_ROOT/gpu${gpu}_all_imgsz.sh"
  {
    echo "#!/usr/bin/env bash"
    echo "set -euo pipefail"
    printf 'cd %q\n' "$ROOT"
    for imgsz in "${size_list[@]}"; do
      imgsz=${imgsz//[[:space:]]/}
      [[ -z "$imgsz" ]] && continue
      printf 'echo "START input-size sweep imgsz=%s gpu=%s at $(date -Is)"\n' "$imgsz" "$gpu"
      printf 'bash %q\n' "$JOB_ROOT/imgsz${imgsz}/gpu${gpu}.sh"
      printf 'echo "DONE input-size sweep imgsz=%s gpu=%s at $(date -Is)"\n' "$imgsz" "$gpu"
    done
  } > "$wrapper"
  chmod +x "$wrapper"
done

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
else
  first_gpu=${gpu_list[0]//[[:space:]]/}
  tmux new-session -d -s "$SESSION" -n "gpu${first_gpu}" "$JOB_ROOT/gpu${first_gpu}_all_imgsz.sh"
  for gpu in "${gpu_list[@]:1}"; do
    gpu=${gpu//[[:space:]]/}
    [[ -z "$gpu" ]] && continue
    tmux new-window -t "$SESSION" -n "gpu${gpu}" "$JOB_ROOT/gpu${gpu}_all_imgsz.sh"
  done
  echo "Started input-size sweep tmux session: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Job root: $JOB_ROOT"
fi

if [[ "$WAIT_AFTER_START" == "1" ]]; then
  wait_for_sessions "$SESSION"
  echo "Input-size sweep complete at $(date -Is)"
fi
