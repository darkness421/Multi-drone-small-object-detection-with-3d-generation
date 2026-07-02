#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-p2fr-module-continuous-queue}

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session already exists: $SESSION"
  tmux attach -t "$SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" "bash scripts/ubuntu/run_p2fr_module_continuous_queue.sh"
echo "Started $SESSION"
echo "Attach with: tmux attach -t $SESSION"
