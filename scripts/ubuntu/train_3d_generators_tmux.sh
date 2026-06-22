#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-marinecity-3d-generators}
BENCHMARK=${2:-outputs/experiments/marinecity_multiview_benchmark.json}
SCENE=${3:-marinecity}
METHODS=${METHODS:-nerf,instant_ngp,mip_nerf_360,gaussian_splatting}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/3d_generators}
RESULTS_DIR=${RESULTS_DIR:-outputs/experiments/3d_generation}

cd "$(dirname "$0")/../.."

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed."
  exit 1
fi

if [[ ! -f "$BENCHMARK" ]]; then
  echo "Missing benchmark manifest: $BENCHMARK"
  echo "Run scripts/ubuntu/prepare_marinecity_multiview_benchmark.sh first."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 1
fi

mkdir -p "$LOG_DIR" "$RESULTS_DIR"
IFS=',' read -r -a method_list <<< "$METHODS"

for gpu in 0 1; do
  script="$RESULTS_DIR/${SESSION}_gpu${gpu}.sh"
  {
    echo "#!/usr/bin/env bash"
    echo "set -euo pipefail"
    printf 'cd %q\n' "$PWD"
    printf 'export CUDA_VISIBLE_DEVICES=%q\n' "$gpu"
    printf 'export CONDA_ENV=%q\n' "$CONDA_ENV"
  } > "$script"
  chmod +x "$script"
done

job_index=0
for method in "${method_list[@]}"; do
  method=${method//[[:space:]]/}
  [[ -z "$method" ]] && continue
  gpu=$((job_index % 2))
  script="$RESULTS_DIR/${SESSION}_gpu${gpu}.sh"
  log_file="$LOG_DIR/${method}_${SCENE}.log"
  result_file="$RESULTS_DIR/${method}_${SCENE}_result.json"
  {
    printf 'echo "START method=%s scene=%s gpu=%s at $(date -Is)"\n' "$method" "$SCENE" "$gpu"
    printf 'conda run --no-capture-output -n %q python -m generative3d.external_runner --method %q --scene %q --data %q --out %q 2>&1 | tee %q\n' \
      "$CONDA_ENV" "$method" "$SCENE" "$BENCHMARK" "$result_file" "$log_file"
    printf 'echo "DONE method=%s scene=%s gpu=%s at $(date -Is)"\n' "$method" "$SCENE" "$gpu"
  } >> "$script"
  job_index=$((job_index + 1))
done

tmux new-session -d -s "$SESSION" -n gpu0 "$RESULTS_DIR/${SESSION}_gpu0.sh"
tmux new-window -t "$SESSION" -n gpu1 "$RESULTS_DIR/${SESSION}_gpu1.sh"

echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Logs: $LOG_DIR"
echo "Results: $RESULTS_DIR"
