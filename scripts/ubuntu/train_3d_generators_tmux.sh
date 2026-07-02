#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-marinecity-3d-generators}
BENCHMARK=${2:-outputs/experiments/marinecity_multiview_benchmark.json}
SCENE=${3:-marinecity}
METHODS=${METHODS:-nerf,instant_ngp,mip_nerf_360,gaussian_splatting}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/3d_generators}
RESULTS_DIR=${RESULTS_DIR:-outputs/experiments/3d_generation}
GPUS=${GPUS:-1}
RESOURCE_GUARD=${RESOURCE_GUARD:-1}
ALLOW_PLACEHOLDER_3D=${ALLOW_PLACEHOLDER_3D:-0}
MIN_FREE_GB=${MIN_FREE_GB:-80}
MAX_DISK_USE_PERCENT=${MAX_DISK_USE_PERCENT:-92}
MIN_RAM_GB=${MIN_RAM_GB:-16}
MIN_GPU_FREE_GB=${MIN_GPU_FREE_GB:-8}
GUARD_WAIT_SECONDS=${GUARD_WAIT_SECONDS:-120}

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
IFS=',' read -r -a gpu_list <<< "$GPUS"

clean_gpus=()
for gpu in "${gpu_list[@]}"; do
  gpu=${gpu//[[:space:]]/}
  [[ -z "$gpu" ]] && continue
  clean_gpus+=("$gpu")
done

if [[ "${#clean_gpus[@]}" -eq 0 ]]; then
  echo "GPUS must contain at least one GPU id."
  exit 1
fi

for gpu in "${clean_gpus[@]}"; do
  script="$RESULTS_DIR/${SESSION}_gpu${gpu}.sh"
  {
    echo "#!/usr/bin/env bash"
    echo "set -euo pipefail"
    printf 'cd %q\n' "$PWD"
    printf 'export CUDA_VISIBLE_DEVICES=%q\n' "$gpu"
    printf 'export CONDA_ENV=%q\n' "$CONDA_ENV"
    printf 'export RESOURCE_GUARD=%q\n' "$RESOURCE_GUARD"
    printf 'export ALLOW_PLACEHOLDER_3D=%q\n' "$ALLOW_PLACEHOLDER_3D"
    printf 'export MIN_FREE_GB=%q\n' "$MIN_FREE_GB"
    printf 'export MAX_DISK_USE_PERCENT=%q\n' "$MAX_DISK_USE_PERCENT"
    printf 'export MIN_RAM_GB=%q\n' "$MIN_RAM_GB"
    printf 'export MIN_GPU_FREE_GB=%q\n' "$MIN_GPU_FREE_GB"
    printf 'export GUARD_WAIT_SECONDS=%q\n' "$GUARD_WAIT_SECONDS"
    printf 'echo "3D generator worker physical GPU %s started at $(date -Is)"\n' "$gpu"
  } > "$script"
  chmod +x "$script"
done

job_index=0
for method in "${method_list[@]}"; do
  method=${method//[[:space:]]/}
  [[ -z "$method" ]] && continue
  gpu=${clean_gpus[$((job_index % ${#clean_gpus[@]}))]}
  script="$RESULTS_DIR/${SESSION}_gpu${gpu}.sh"
  log_file="$LOG_DIR/${method}_${SCENE}.log"
  result_file="$RESULTS_DIR/${method}_${SCENE}_result.json"
  {
    printf 'echo "START method=%s scene=%s gpu=%s at $(date -Is)"\n' "$method" "$SCENE" "$gpu"
    printf 'if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path %q --gpu %q --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a %q; fi\n' "$PWD" "$gpu" "$log_file"
    printf 'if [[ "${ALLOW_PLACEHOLDER_3D:-0}" != "1" ]]; then echo "SKIP method=%s scene=%s: local generative3d.external_runner is a placeholder. Install/connect an upstream 3D runner before paper-facing metrics, or set ALLOW_PLACEHOLDER_3D=1 only for command-contract smoke." 2>&1 | tee -a %q; exit 2; fi\n' "$method" "$SCENE" "$log_file"
    printf 'conda run --no-capture-output -n %q python -m generative3d.external_runner --allow-placeholder --method %q --scene %q --data %q --out %q 2>&1 | tee %q\n' \
      "$CONDA_ENV" "$method" "$SCENE" "$BENCHMARK" "$result_file" "$log_file"
    printf 'echo "DONE method=%s scene=%s gpu=%s at $(date -Is)"\n' "$method" "$SCENE" "$gpu"
  } >> "$script"
  job_index=$((job_index + 1))
done

first_gpu=${clean_gpus[0]}
tmux new-session -d -s "$SESSION" -n "gpu${first_gpu}" "$RESULTS_DIR/${SESSION}_gpu${first_gpu}.sh"
for gpu in "${clean_gpus[@]:1}"; do
  tmux new-window -t "$SESSION" -n "gpu${gpu}" "$RESULTS_DIR/${SESSION}_gpu${gpu}.sh"
done

echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Physical GPUs: ${clean_gpus[*]}"
echo "Logs: $LOG_DIR"
echo "Results: $RESULTS_DIR"
