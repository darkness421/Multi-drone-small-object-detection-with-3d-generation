#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-tinyperson-download}
LOG_DIR=${LOG_DIR:-outputs/logs/datasets}
RAW_ROOT=${RAW_ROOT:-data/raw/TinyPerson}

mkdir -p "$LOG_DIR" "$RAW_ROOT"
log_file="$LOG_DIR/tinyperson_download_$(date +%Y%m%d_%H%M%S).log"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "TinyPerson download session already running: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" \
  "cd '$PWD' && RAW_ROOT='$RAW_ROOT' LOG_DIR='$LOG_DIR' bash scripts/ubuntu/download_tinyperson_dataset.sh 2>&1 | tee '$log_file'"

echo "Started TinyPerson download session: $SESSION"
echo "Log: $log_file"
echo "Attach with: tmux attach -t $SESSION"
