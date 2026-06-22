#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-server-visdrone-baselines}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}

cd "$(dirname "$0")/../.."

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Attaching to tmux session: $SESSION"
  exec tmux attach -t "$SESSION"
fi

echo "No tmux session named '$SESSION'. Showing latest logs from $LOG_DIR."
mkdir -p "$LOG_DIR"
find "$LOG_DIR" -type f -name "*.log" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 5 | cut -d' ' -f2- | while read -r log; do
  echo "==> $log"
  tail -n 40 "$log"
done
