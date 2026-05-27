#!/usr/bin/env bash
set -euo pipefail

SESSION=${SESSION:-server-uavdt-download}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}
OUT_DIR=${OUT_DIR:-data/raw/downloads/uavdt}
MIN_FREE_GB=${MIN_FREE_GB:-35}
EXTRACT=${EXTRACT:-0}

cd "$(dirname "$0")/../.."

mkdir -p "$LOG_DIR" "$OUT_DIR"
log_file="$LOG_DIR/uavdt_download_$(date +%Y%m%d_%H%M%S).log"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -n download \
  "cd '$PWD' && OUT_DIR='$OUT_DIR' MIN_FREE_GB='$MIN_FREE_GB' EXTRACT='$EXTRACT' bash scripts/ubuntu/download_uavdt_dataset.sh 2>&1 | tee '$log_file'; echo; echo 'UAVDT download tmux job finished. Press Ctrl-b then d to detach.'; exec bash"

echo "Started UAVDT download session: $SESSION"
echo "Attach with:"
echo "  tmux attach -t $SESSION"
echo "Log:"
echo "  $log_file"
