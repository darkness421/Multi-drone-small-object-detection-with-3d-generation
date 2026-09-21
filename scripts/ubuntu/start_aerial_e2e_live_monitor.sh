#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SESSION="${1:-aerial-e2e-monitor}"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "monitor already running: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -c "$ROOT" \
  "python tools/aerial_e2e_live_monitor.py --results experiments/results.csv --snapshot outputs/monitor/live_status.json --interval 2"
echo "monitor started: tmux attach -t $SESSION"
