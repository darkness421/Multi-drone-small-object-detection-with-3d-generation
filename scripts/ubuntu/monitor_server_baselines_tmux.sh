#!/usr/bin/env bash
set -euo pipefail

MONITOR_SESSION=${1:-server-baseline-monitor}
TRAIN_SESSION=${2:-server-visdrone-baselines}
INTERVAL=${3:-60}
LOG_DIR=${LOG_DIR:-outputs/logs/server_baselines}
COMMAND_CSV=${COMMAND_CSV:-outputs/experiments/server_baseline_commands.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/server_baseline_dashboard.png}

cd "$(dirname "$0")/../.."

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed."
  exit 1
fi

if tmux has-session -t "$MONITOR_SESSION" 2>/dev/null; then
  echo "Monitor tmux session already exists: $MONITOR_SESSION"
  echo "Attach: tmux attach -t $MONITOR_SESSION"
  exit 0
fi

mkdir -p "$LOG_DIR" "$(dirname "$COMMAND_CSV")" "$(dirname "$DASHBOARD")"

tmux new-session -d -s "$MONITOR_SESSION" -n gpu \
  "cd '$PWD' && watch -n 2 'nvidia-smi || true'"

tmux new-window -t "$MONITOR_SESSION" -n training \
  "cd '$PWD' && while true; do clear; date -Is; echo 'Training session mirror: $TRAIN_SESSION'; echo; if tmux has-session -t '$TRAIN_SESSION' 2>/dev/null; then tmux list-windows -t '$TRAIN_SESSION'; echo; for pane in \$(tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}' | grep '^$TRAIN_SESSION:'); do echo '== '\"\$pane\"' =='; tmux capture-pane -p -S -24 -t \"\$pane\"; echo; done; else echo 'No training session yet.'; tmux ls 2>/dev/null || true; fi; sleep 5; done"

tmux new-window -t "$MONITOR_SESSION" -n logs \
  "cd '$PWD' && while true; do latest=\$(find '$LOG_DIR' -type f -name '*.log' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-); if [[ -n \"\${latest:-}\" ]]; then echo \"Tailing \$latest\"; tail -n 80 -F \"\$latest\"; else echo 'Waiting for logs...'; sleep 5; fi; done"

tmux new-window -t "$MONITOR_SESSION" -n metrics \
  "cd '$PWD' && while true; do clear; date -Is; echo; conda run --no-capture-output -n '${CONDA_ENV:-com3d-ace}' python -m scripts.live_metrics_report --project-dir outputs/detectors/server_baselines --summary-csv outputs/experiments/live/server_baseline_summary.csv 2>/dev/null || true; echo; echo 'Command queue:'; tail -n 8 '$COMMAND_CSV' 2>/dev/null || true; echo; echo 'Dashboard: $DASHBOARD'; ls -lh '$DASHBOARD' 2>/dev/null || true; sleep 10; done"

tmux new-window -t "$MONITOR_SESSION" -n dashboard \
  "cd '$PWD' && bash scripts/ubuntu/live_server_dashboard.sh '$INTERVAL'"

tmux select-window -t "$MONITOR_SESSION:gpu"

echo "Started monitor tmux session: $MONITOR_SESSION"
echo "Attach monitor: tmux attach -t $MONITOR_SESSION"
echo "Attach training: tmux attach -t $TRAIN_SESSION"
echo "Dashboard PNG: $DASHBOARD"
