#!/usr/bin/env bash
set -euo pipefail

BASE_RUN_ID=${BASE_RUN_ID:-fresh_20260519_131739}
RESUME_ID=${RESUME_ID:-resume_$(date +%Y%m%d_%H%M%S)}
SESSION=${SESSION:-server-fresh-baselines-resume}
MONITOR_SESSION=${MONITOR_SESSION:-server-baseline-monitor}
DUAL_VIEW_SESSION=${DUAL_VIEW_SESSION:-server-training-dual-view}
VIEWER_SESSION=${VIEWER_SESSION:-server-live-viewer}
VIEWER_PORT=${VIEWER_PORT:-8766}
STOP_EXISTING=${STOP_EXISTING:-1}

CONDA_ENV=${CONDA_ENV:-com3d-ace}
RUN_EVAL=${RUN_EVAL:-1}
ROC_AUC=${ROC_AUC:-1}
LIVE_INTERVAL=${LIVE_INTERVAL:-60}
GPUS=${GPUS:-0,1}
DEDUP_KEY=${DEDUP_KEY:-dataset,model,seed,ablation,proposed_module}
WORKERS=${WORKERS:-4}
RESOURCE_GUARD=${RESOURCE_GUARD:-1}
MIN_FREE_GB=${MIN_FREE_GB:-100}
MAX_DISK_USE_PERCENT=${MAX_DISK_USE_PERCENT:-92}
MIN_RAM_GB=${MIN_RAM_GB:-16}
MIN_GPU_FREE_GB=${MIN_GPU_FREE_GB:-6}
GUARD_WAIT_SECONDS=${GUARD_WAIT_SECONDS:-60}

BASE_PROJECT=${BASE_PROJECT:-outputs/detectors/server_fresh_baselines/$BASE_RUN_ID}
RESUME_PROJECT=${RESUME_PROJECT:-outputs/detectors/server_fresh_baselines/${BASE_RUN_ID}_${RESUME_ID}}
DETECTOR_ROOTS=${DETECTOR_ROOTS:-$BASE_PROJECT,$RESUME_PROJECT}
EXPERIMENT_ROOT=${EXPERIMENT_ROOT:-outputs/experiments/server_fresh/$BASE_RUN_ID}
LOG_DIR=${LOG_DIR:-outputs/logs/server_fresh_baselines/${BASE_RUN_ID}_${RESUME_ID}}
REPORT_DIR=${REPORT_DIR:-outputs/reports/server_fresh_baselines/$BASE_RUN_ID}
COMMAND_CSV=${COMMAND_CSV:-$EXPERIMENT_ROOT/server_baseline_commands.csv}
RESUME_COMMAND_CSV=${RESUME_COMMAND_CSV:-$EXPERIMENT_ROOT/${RESUME_ID}_commands.csv}
JOB_ROOT=${JOB_ROOT:-$EXPERIMENT_ROOT/jobs/$RESUME_ID}
PRECHECK_RESULTS_CSV=${PRECHECK_RESULTS_CSV:-$JOB_ROOT/precheck_results.csv}
JOB_TSV=${JOB_TSV:-$JOB_ROOT/resume_jobs.tsv}

LIVE_RESULTS_CSV=${LIVE_RESULTS_CSV:-$EXPERIMENT_ROOT/live/server_baseline_results.csv}
LIVE_SUMMARY_CSV=${LIVE_SUMMARY_CSV:-$EXPERIMENT_ROOT/live/server_baseline_summary.csv}
LIVE_PVALUES_CSV=${LIVE_PVALUES_CSV:-$EXPERIMENT_ROOT/live/server_baseline_pvalues.csv}
LIVE_DASHBOARD=${LIVE_DASHBOARD:-outputs/reports/live/${BASE_RUN_ID}_server_baseline_dashboard.png}
LIVE_FIGURES_DIR=${LIVE_FIGURES_DIR:-outputs/reports/live/${BASE_RUN_ID}_figures}
FINAL_RESULTS_CSV=${FINAL_RESULTS_CSV:-$EXPERIMENT_ROOT/server_baseline_results.csv}
FINAL_SUMMARY_CSV=${FINAL_SUMMARY_CSV:-$EXPERIMENT_ROOT/server_baseline_summary.csv}
FINAL_PVALUES_CSV=${FINAL_PVALUES_CSV:-$EXPERIMENT_ROOT/server_baseline_pvalues.csv}
FINAL_DASHBOARD=${FINAL_DASHBOARD:-$REPORT_DIR/figures/server_baseline_dashboard.png}

cd "$(dirname "$0")/../.."
ROOT=$PWD

export MPLCONFIGDIR="${MPLCONFIGDIR:-$ROOT/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$ROOT/.cache/ultralytics}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$ROOT/.cache}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"

echo "Fresh queue reboot recovery"
echo "  base run id:    $BASE_RUN_ID"
echo "  resume id:      $RESUME_ID"
echo "  session:        $SESSION"
echo "  base project:   $BASE_PROJECT"
echo "  resume project: $RESUME_PROJECT"
echo "  detector roots: $DETECTOR_ROOTS"
echo "  workers:        $WORKERS"
echo "  guard:          $RESOURCE_GUARD (disk >= ${MIN_FREE_GB}GB, disk <= ${MAX_DISK_USE_PERCENT}%, RAM >= ${MIN_RAM_GB}GB, GPU free >= ${MIN_GPU_FREE_GB}GB)"
echo ""

if [[ ! -f "$COMMAND_CSV" ]]; then
  echo "Missing original command CSV: $COMMAND_CSV" >&2
  exit 1
fi

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready \
  --paths-config configs/paths.ubuntu.yaml \
  --data-yaml configs/detector/visdrone_yolo_data.yaml \
  --strict

if [[ "$STOP_EXISTING" == "1" ]]; then
  for old_session in "$SESSION" "$MONITOR_SESSION" "$DUAL_VIEW_SESSION" "$VIEWER_SESSION"; do
    tmux kill-session -t "$old_session" 2>/dev/null || true
  done
fi

mkdir -p "$RESUME_PROJECT" "$LOG_DIR" "$REPORT_DIR/figures" "$LIVE_FIGURES_DIR" "$JOB_ROOT" \
  "$(dirname "$LIVE_RESULTS_CSV")" "$(dirname "$LIVE_DASHBOARD")"

ROOT_ARGS=()
IFS=',' read -r -a root_list <<< "$DETECTOR_ROOTS"
for root in "${root_list[@]}"; do
  root=${root//[[:space:]]/}
  [[ -z "$root" ]] && continue
  ROOT_ARGS+=(--detector-root "$root")
done
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.collect_detector_metrics \
  "${ROOT_ARGS[@]}" \
  --dedupe-key "$DEDUP_KEY" \
  --out "$PRECHECK_RESULTS_CSV"

COMMAND_CSV="$COMMAND_CSV" PRECHECK_RESULTS_CSV="$PRECHECK_RESULTS_CSV" JOB_TSV="$JOB_TSV" \
RESUME_COMMAND_CSV="$RESUME_COMMAND_CSV" RESUME_ID="$RESUME_ID" LOG_DIR="$LOG_DIR" GPUS="$GPUS" WORKERS="$WORKERS" \
conda run --no-capture-output -n "$CONDA_ENV" python - <<'PY'
import csv
import os
from pathlib import Path

command_csv = Path(os.environ["COMMAND_CSV"])
results_csv = Path(os.environ["PRECHECK_RESULTS_CSV"])
job_tsv = Path(os.environ["JOB_TSV"])
resume_command_csv = Path(os.environ["RESUME_COMMAND_CSV"])
resume_id = os.environ["RESUME_ID"]
log_dir = Path(os.environ["LOG_DIR"])
gpus = [gpu.strip() for gpu in os.environ.get("GPUS", "0,1").split(",") if gpu.strip()]
default_workers = os.environ.get("WORKERS", "4")
if not gpus:
    raise SystemExit("GPUS must contain at least one GPU id")

with command_csv.open("r", encoding="utf-8-sig", newline="") as handle:
    commands = list(csv.DictReader(handle))
with results_csv.open("r", encoding="utf-8-sig", newline="") as handle:
    results = list(csv.DictReader(handle))

completed = {
    (row.get("model", ""), row.get("seed", ""))
    for row in results
    if row.get("status") == "completed"
}

jobs = []
for row in commands:
    key = (row.get("model", ""), row.get("seed", ""))
    if key in completed:
        continue
    jobs.append(row)

job_tsv.parent.mkdir(parents=True, exist_ok=True)
resume_command_csv.parent.mkdir(parents=True, exist_ok=True)
fields = [
    "model",
    "seed",
    "gpu",
    "imgsz",
    "batch",
    "workers",
    "epochs",
    "data_yaml",
    "run_name",
    "log_file",
]
with job_tsv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for index, row in enumerate(jobs):
        original_run_name = row.get("run_name") or f"{Path(row.get('model', 'model')).stem}_seed{row.get('seed', '')}"
        run_name = f"{original_run_name}_{resume_id}"
        log_file = log_dir / f"{run_name}.log"
        writer.writerow(
            {
                "model": row.get("model", ""),
                "seed": row.get("seed", ""),
                "gpu": gpus[index % len(gpus)],
                "imgsz": row.get("imgsz") or "1280",
                "batch": row.get("batch") or "8",
                "workers": row.get("workers") or default_workers,
                "epochs": row.get("epochs") or "100",
                "data_yaml": row.get("data_yaml") or "configs/detector/visdrone_yolo_data.yaml",
                "run_name": run_name,
                "log_file": str(log_file),
            }
        )

with resume_command_csv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "created_at",
            "session",
            "model",
            "seed",
            "physical_gpu",
            "ultralytics_device",
            "imgsz",
            "batch",
            "workers",
            "epochs",
            "data_yaml",
            "run_name",
            "log_file",
            "status",
            "command",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    for row in csv.DictReader(job_tsv.open("r", encoding="utf-8", newline=""), delimiter="\t"):
        command = (
            f"CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES={row['gpu']} conda run --no-capture-output "
            f"-n $CONDA_ENV python -m detectors.train_yolo train --model {row['model']} "
            f"--data-yaml {row['data_yaml']} --epochs {row['epochs']} --imgsz {row['imgsz']} "
            f"--batch {row['batch']} --workers {row['workers']} --device 0 --seed {row['seed']} "
            f"--project $RESUME_PROJECT --name {row['run_name']}"
        )
        writer.writerow(
            {
                "created_at": "",
                "session": "",
                "model": row["model"],
                "seed": row["seed"],
                "physical_gpu": row["gpu"],
                "ultralytics_device": "0",
                "imgsz": row["imgsz"],
                "batch": row["batch"],
                "workers": row["workers"],
                "epochs": row["epochs"],
                "data_yaml": row["data_yaml"],
                "run_name": row["run_name"],
                "log_file": row["log_file"],
                "status": "queued",
                "command": command,
            }
        )

print(f"Resume jobs: {len(jobs)}")
for row in jobs:
    print(f"  {row.get('model')} seed={row.get('seed')} batch={row.get('batch')} previous_status=not_completed")
PY

job_count=$(tail -n +2 "$JOB_TSV" | wc -l)
if [[ "$job_count" -eq 0 ]]; then
  echo "No interrupted or missing jobs remain. Collecting combined results only."
  DETECTOR_ROOTS="$DETECTOR_ROOTS" DEDUPE_KEY="$DEDUP_KEY" RESULTS_CSV="$FINAL_RESULTS_CSV" \
    SUMMARY_CSV="$FINAL_SUMMARY_CSV" PVALUES_CSV="$FINAL_PVALUES_CSV" DASHBOARD="$FINAL_DASHBOARD" \
    REPORT_DIR="$REPORT_DIR" CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/collect_server_results.sh "$BASE_PROJECT"
  exit 0
fi

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
    printf 'export CUDA_VISIBLE_DEVICES=%q\n' "$gpu"
    echo 'export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"'
    printf 'export RESOURCE_GUARD=%q\n' "$RESOURCE_GUARD"
    printf 'export MIN_FREE_GB=%q\n' "$MIN_FREE_GB"
    printf 'export MAX_DISK_USE_PERCENT=%q\n' "$MAX_DISK_USE_PERCENT"
    printf 'export MIN_RAM_GB=%q\n' "$MIN_RAM_GB"
    printf 'export MIN_GPU_FREE_GB=%q\n' "$MIN_GPU_FREE_GB"
    printf 'export GUARD_WAIT_SECONDS=%q\n' "$GUARD_WAIT_SECONDS"
    printf 'export MPLCONFIGDIR=%q\n' "$MPLCONFIGDIR"
    printf 'export YOLO_CONFIG_DIR=%q\n' "$YOLO_CONFIG_DIR"
    printf 'export XDG_CACHE_HOME=%q\n' "$XDG_CACHE_HOME"
    echo 'mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"'
    printf 'echo "Resume GPU worker %s started at $(date -Is)"\n' "$gpu"
  } > "$script"
  chmod +x "$script"
done

while IFS=$'\t' read -r model seed gpu imgsz batch workers epochs data_yaml run_name log_file; do
  [[ "$model" == "model" ]] && continue
  [[ -z "$model" ]] && continue
  job_script="$JOB_ROOT/gpu${gpu}.sh"
  {
    printf '\necho "START resume model=%s seed=%s gpu=%s batch=%s at $(date -Is)"\n' "$model" "$seed" "$gpu" "$batch"
    printf 'if [[ "${RESOURCE_GUARD:-1}" == "1" ]]; then bash scripts/ubuntu/check_resource_margin.sh --path %q --gpu %q --min-free-gb "$MIN_FREE_GB" --max-disk-use-percent "$MAX_DISK_USE_PERCENT" --min-ram-gb "$MIN_RAM_GB" --min-gpu-free-gb "$MIN_GPU_FREE_GB" --wait-seconds "$GUARD_WAIT_SECONDS" 2>&1 | tee -a %q; fi\n' "$ROOT" "$gpu" "$log_file"
    printf 'if conda run --no-capture-output -n %q python -m detectors.train_yolo train --model %q --data-yaml %q --epochs %q --imgsz %q --batch %q --workers %q --device 0 --seed %q --project %q --name %q 2>&1 | tee %q; then\n' \
      "$CONDA_ENV" "$model" "$data_yaml" "$epochs" "$imgsz" "$batch" "$workers" "$seed" "$RESUME_PROJECT" "$run_name" "$log_file"
    printf '  echo "TRAIN_OK model=%s seed=%s gpu=%s at $(date -Is)" | tee -a %q\n' "$model" "$seed" "$gpu" "$log_file"
    printf '  if [[ %q == 1 ]]; then\n' "$RUN_EVAL"
    printf '    run_dir=$(find %q -maxdepth 1 -type d \\( -name %q -o -name %q \\) -printf "%%T@ %%p\\n" | sort -nr | head -n 1 | cut -d" " -f2-)\n' "$RESUME_PROJECT" "$run_name" "*_${run_name}"
    printf '    if [[ -n "${run_dir:-}" && -f "$run_dir/ultralytics/weights/best.pt" ]]; then\n'
    printf '      eval_args=(eval --model "$run_dir/ultralytics/weights/best.pt" --data-yaml %q --imgsz %q --workers %q --device 0 --project %q --name %q)\n' "$data_yaml" "$imgsz" "$workers" "$RESUME_PROJECT" "eval_${run_name}"
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
done < "$JOB_TSV"

for gpu in "${gpu_list[@]}"; do
  gpu=${gpu//[[:space:]]/}
  [[ -z "$gpu" ]] && continue
  {
    printf '\necho "Resume GPU worker %s finished at $(date -Is)"\n' "$gpu"
    printf 'touch %q\n' "$JOB_ROOT/gpu${gpu}.done"
  } >> "$JOB_ROOT/gpu${gpu}.sh"
done

collector="$JOB_ROOT/collect_when_done.sh"
{
  echo "#!/usr/bin/env bash"
  echo "set -uo pipefail"
  printf 'cd %q\n' "$ROOT"
  printf 'echo "Resume collector waiting for GPU workers at $(date -Is)"\n'
  for gpu in "${gpu_list[@]}"; do
    gpu=${gpu//[[:space:]]/}
    [[ -z "$gpu" ]] && continue
    printf 'while [[ ! -f %q ]]; do echo "Waiting for gpu%s at $(date -Is)"; sleep 60; done\n' "$JOB_ROOT/gpu${gpu}.done" "$gpu"
  done
  printf 'echo "All resume GPU workers finished; collecting combined results at $(date -Is)"\n'
  printf 'DETECTOR_ROOTS=%q DEDUPE_KEY=%q RESULTS_CSV=%q SUMMARY_CSV=%q PVALUES_CSV=%q DASHBOARD=%q REPORT_DIR=%q CONDA_ENV=%q bash scripts/ubuntu/collect_server_results.sh %q 2>&1 | tee %q\n' \
    "$DETECTOR_ROOTS" "$DEDUP_KEY" "$FINAL_RESULTS_CSV" "$FINAL_SUMMARY_CSV" "$FINAL_PVALUES_CSV" "$FINAL_DASHBOARD" "$REPORT_DIR" "$CONDA_ENV" "$BASE_PROJECT" "$LOG_DIR/final_collection.log"
  printf 'echo "Resume queue complete at $(date -Is)" | tee -a %q\n' "$LOG_DIR/final_collection.log"
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

PROJECT_DIR="$RESUME_PROJECT" DETECTOR_ROOTS="$DETECTOR_ROOTS" DEDUPE_KEY="$DEDUP_KEY" \
  RESULTS_CSV="$LIVE_RESULTS_CSV" SUMMARY_CSV="$LIVE_SUMMARY_CSV" PVALUES_CSV="$LIVE_PVALUES_CSV" \
  LOG_DIR="$LOG_DIR" COMMAND_CSV="$RESUME_COMMAND_CSV" DASHBOARD="$LIVE_DASHBOARD" CONDA_ENV="$CONDA_ENV" \
  FIGURES_DIR="$LIVE_FIGURES_DIR" \
  bash scripts/ubuntu/monitor_server_baselines_tmux.sh "$MONITOR_SESSION" "$SESSION" "$LIVE_INTERVAL"

tmux new-session -d -s "$VIEWER_SESSION" -n viewer \
  "cd '$ROOT' && conda run --no-capture-output -n '$CONDA_ENV' python -m scripts.ubuntu.live_training_viewer --host 0.0.0.0 --port '$VIEWER_PORT' --training-session '$SESSION' --project-dir '$RESUME_PROJECT' --summary-csv '$LIVE_SUMMARY_CSV' --log-dir '$LOG_DIR' --dashboard '$FINAL_DASHBOARD' --live-dashboard '$LIVE_DASHBOARD' --figure-dir '$LIVE_FIGURES_DIR'"

tmux new-session -d -s "$DUAL_VIEW_SESSION" -n both \
  "cd '$ROOT' && while true; do clear; echo 'GPU0 / resume queue'; date -Is; echo; tmux capture-pane -p -S -22 -t '$SESSION:0.0'; sleep 2; done"
tmux split-window -h -t "$DUAL_VIEW_SESSION:0" \
  "cd '$ROOT' && while true; do clear; echo 'GPU1 / resume queue'; date -Is; echo; tmux capture-pane -p -S -22 -t '$SESSION:1.0'; sleep 2; done"
tmux select-layout -t "$DUAL_VIEW_SESSION:0" even-horizontal

cat <<EOF
Started reboot recovery queue.

Resume jobs:      $job_count
Training tmux:    tmux attach -t $SESSION
Dual view tmux:   tmux attach -t $DUAL_VIEW_SESSION
Monitor tmux:     tmux attach -t $MONITOR_SESSION
Browser viewer:   http://$(hostname -I | awk '{print $1}'):$VIEWER_PORT/

Base project:     $BASE_PROJECT
Resume project:   $RESUME_PROJECT
Resume commands:  $RESUME_COMMAND_CSV
Live summary:     $LIVE_SUMMARY_CSV
Live figures:     $LIVE_FIGURES_DIR
Final report:     $REPORT_DIR/README.md
EOF
