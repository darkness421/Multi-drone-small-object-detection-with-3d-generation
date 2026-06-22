#!/usr/bin/env bash
set -euo pipefail

WAIT_FOR=${WAIT_FOR:-server-fresh-baselines-resume,server-gpu1-recovery,server-isolated-continuation}
POLL_SECONDS=${POLL_SECONDS:-300}
SESSION=${SESSION:-server-proposed-ablation}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
CONFIG=${CONFIG:-configs/experiments/proposed_detector_ablation.yaml}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
EPOCHS=${EPOCHS:-100}
BATCH=${BATCH:-8}
IMGSZ=${IMGSZ:-1280}
PATIENCE=${PATIENCE:-}
SEEDS=${SEEDS:-42,123,2026}
GPUS=${GPUS:-0}
ENABLE_PLANNED=${ENABLE_PLANNED:-0}
SKIP_COMPLETED=${SKIP_COMPLETED:-0}
COMPLETED_RESULTS_CSV=${COMPLETED_RESULTS_CSV:-}
RESTART_VIEWER=${RESTART_VIEWER:-1}
VIEWER_SESSION=${VIEWER_SESSION:-server-live-viewer}
VIEWER_PORT=${VIEWER_PORT:-8766}
RESTART_DUAL_VIEW=${RESTART_DUAL_VIEW:-1}
DUAL_VIEW_SESSION=${DUAL_VIEW_SESSION:-server-training-dual-view}
PROJECT_DIR=${PROJECT_DIR:-outputs/detectors/server_proposed_ablation}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}
LIVE_SUMMARY_CSV=${LIVE_SUMMARY_CSV:-outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_summary.csv}
LIVE_DASHBOARD=${LIVE_DASHBOARD:-outputs/reports/server_with_proposed/figures/server_baseline_dashboard.png}
LIVE_FIGURES_DIR=${LIVE_FIGURES_DIR:-outputs/reports/server_with_proposed/figures}
WAIT_AFTER_START=${WAIT_AFTER_START:-1}

cd "$(dirname "$0")/../.."
ROOT=$PWD
STAMP=$(date +%Y%m%d_%H%M%S)
JOB_ROOT="outputs/experiments/proposed_ablation_jobs/$STAMP"
MANIFEST="$JOB_ROOT/manifest.json"

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

restart_viewer() {
  if [[ "$RESTART_VIEWER" != "1" ]]; then
    return
  fi
  tmux kill-session -t "$VIEWER_SESSION" 2>/dev/null || true
  tmux new-session -d -s "$VIEWER_SESSION" \
    "cd '$ROOT' && conda run --no-capture-output -n '$CONDA_ENV' python -m scripts.ubuntu.live_training_viewer --host 0.0.0.0 --port '$VIEWER_PORT' --training-session '$SESSION' --project-dir '$PROJECT_DIR' --summary-csv '$LIVE_SUMMARY_CSV' --log-dir '$LOG_DIR' --dashboard '$LIVE_DASHBOARD' --live-dashboard '$LIVE_DASHBOARD' --figure-dir '$LIVE_FIGURES_DIR'"
}

restart_dual_view() {
  if [[ "$RESTART_DUAL_VIEW" != "1" ]]; then
    return
  fi
  IFS=',' read -r -a gpu_list <<< "$GPUS"
  local first_gpu=${gpu_list[0]//[[:space:]]/}
  [[ -z "$first_gpu" ]] && return

  tmux kill-session -t "$DUAL_VIEW_SESSION" 2>/dev/null || true
  tmux new-session -d -s "$DUAL_VIEW_SESSION" -n both \
    "cd '$ROOT' && while true; do clear; echo 'GPU${first_gpu} / proposed queue'; date -Is; echo; tmux capture-pane -p -S -24 -t '$SESSION:0.0' 2>/dev/null || true; sleep 2; done"

  if [[ "${#gpu_list[@]}" -gt 1 ]]; then
    local second_gpu=${gpu_list[1]//[[:space:]]/}
    if [[ -n "$second_gpu" ]]; then
      tmux split-window -h -t "$DUAL_VIEW_SESSION:0" \
        "cd '$ROOT' && while true; do clear; echo 'GPU${second_gpu} / proposed queue'; date -Is; echo; tmux capture-pane -p -S -24 -t '$SESSION:1.0' 2>/dev/null || true; sleep 2; done"
      tmux select-layout -t "$DUAL_VIEW_SESSION:0" even-horizontal
    fi
  fi
}

wait_for_sessions "$WAIT_FOR"

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.check_dataset_ready \
  --paths-config configs/paths.ubuntu.yaml \
  --data-yaml "$DATA_YAML" \
  --strict

GEN_ARGS=(
  --config "$CONFIG"
  --job-root "$JOB_ROOT"
  --manifest "$MANIFEST"
  --session "$SESSION"
  --conda-env "$CONDA_ENV"
  --gpus "$GPUS"
  --epochs "$EPOCHS"
  --batch "$BATCH"
  --imgsz "$IMGSZ"
  --seeds "$SEEDS"
)
if [[ -n "$PATIENCE" ]]; then
  GEN_ARGS+=(--patience "$PATIENCE")
fi
if [[ "$ENABLE_PLANNED" == "1" ]]; then
  GEN_ARGS+=(--enable-planned)
fi
if [[ "$SKIP_COMPLETED" == "1" ]]; then
  GEN_ARGS+=(--skip-completed)
  if [[ -n "$COMPLETED_RESULTS_CSV" ]]; then
    IFS=',' read -r -a completed_csvs <<< "$COMPLETED_RESULTS_CSV"
    for completed_csv in "${completed_csvs[@]}"; do
      completed_csv=${completed_csv//[[:space:]]/}
      [[ -z "$completed_csv" ]] && continue
      GEN_ARGS+=(--completed-results-csv "$completed_csv")
    done
  fi
fi

conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.proposed_ablation_jobs "${GEN_ARGS[@]}"

QUEUED_COUNT=$(python - "$MANIFEST" <<'PY'
import json
import sys

print(json.loads(open(sys.argv[1], encoding="utf-8").read())["queued_count"])
PY
)

if [[ "$QUEUED_COUNT" == "0" ]]; then
  echo "No implemented proposed ablation jobs are queued."
  echo "Manifest: $MANIFEST"
  echo "Planned ablations were recorded as skipped_not_implemented."
  exit 0
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
else
  IFS=',' read -r -a gpu_list <<< "$GPUS"
  first_gpu=${gpu_list[0]//[[:space:]]/}
  tmux new-session -d -s "$SESSION" -n "gpu${first_gpu}" "$JOB_ROOT/gpu${first_gpu}.sh"
  for gpu in "${gpu_list[@]:1}"; do
    gpu=${gpu//[[:space:]]/}
    [[ -z "$gpu" ]] && continue
    tmux new-window -t "$SESSION" -n "gpu${gpu}" "$JOB_ROOT/gpu${gpu}.sh"
  done
  echo "Started proposed ablation tmux session: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  echo "Manifest: $MANIFEST"
fi

restart_viewer
restart_dual_view

echo "Dual view: tmux attach -t $DUAL_VIEW_SESSION"
echo "Browser viewer: http://$(hostname -I | awk '{print $1}'):$VIEWER_PORT/"

if [[ "$WAIT_AFTER_START" == "1" ]]; then
  wait_for_sessions "$SESSION"
  echo "Proposed ablation queue complete at $(date -Is)"
fi
