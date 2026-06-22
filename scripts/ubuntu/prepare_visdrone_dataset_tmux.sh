#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-visdrone-data-prep}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}

cd "$(dirname "$0")/../.."

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Run scripts/ubuntu/prepare_visdrone_dataset.sh directly."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 1
fi

mkdir -p "$LOG_DIR"
log_file="$LOG_DIR/${SESSION}.log"
tmux new-session -d -s "$SESSION" -n prepare "cd '$PWD' && bash scripts/ubuntu/prepare_visdrone_dataset.sh 2>&1 | tee '$log_file'"

echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
