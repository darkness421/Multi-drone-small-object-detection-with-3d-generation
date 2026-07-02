#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-gpu1-isaac51-marinecity-stage-20260622}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu1_isaac51_marinecity_stage}
mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n marinecity-stage \
  "cd '$PWD' && LOG_DIR='$LOG_DIR' bash scripts/ubuntu/run_gpu1_isaac51_marinecity_stage.sh; exec bash"

echo "Started Isaac 5.1 GPU1 MarineCity stage session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Logs: $LOG_DIR"
