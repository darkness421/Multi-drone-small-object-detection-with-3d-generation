#!/usr/bin/env bash
set -euo pipefail

SESSION=${1:-server-uavdt-comparisons-pending}
LOG_DIR=${LOG_DIR:-outputs/logs/server_uavdt_baselines}
WAIT_FOR=${WAIT_FOR:-server-large-comparison,server-top3-proposed-pending}
POLL_SECONDS=${POLL_SECONDS:-300}

cd "$(dirname "$0")/../.."

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Run scripts/ubuntu/train_uavdt_comparisons_after_session.sh directly."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 1
fi

mkdir -p "$LOG_DIR"
log_file="$LOG_DIR/${SESSION}.log"
tmux new-session -d -s "$SESSION" -n pending \
  "cd '$PWD' && WAIT_FOR='$WAIT_FOR' POLL_SECONDS='$POLL_SECONDS' LOG_DIR='$LOG_DIR' bash scripts/ubuntu/train_uavdt_comparisons_after_session.sh 2>&1 | tee '$log_file'"

echo "Started tmux session: $SESSION"
echo "Waiting for: $WAIT_FOR"
echo "Attach: tmux attach -t $SESSION"
echo "Log: $log_file"
