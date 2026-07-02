#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

TARGET_GPU=${TARGET_GPU:-1}
SESSION=${SESSION:-server-gpu${TARGET_GPU}-yolov11-p2-weekend}
SOURCE_CSV=${SOURCE_CSV:-outputs/experiments/yolov11_p2_tiny_activation_next_step_commands.csv}
LOG_DIR=${LOG_DIR:-outputs/logs/gpu${TARGET_GPU}_yolov11_p2_weekend}
RUNNER_DIR=${RUNNER_DIR:-outputs/experiments/gpu${TARGET_GPU}_yolov11_p2_weekend}
MAX_JOBS=${MAX_JOBS:-4}
SKIP_JOBS=${SKIP_JOBS:-0}
STOP_EXISTING=${STOP_EXISTING:-0}

mkdir -p "$LOG_DIR" "$RUNNER_DIR"

RUNNER="$RUNNER_DIR/run_gpu1_yolov11_p2_weekend.sh"

python - "$SOURCE_CSV" "$RUNNER" "$LOG_DIR" "$MAX_JOBS" "$TARGET_GPU" "$SKIP_JOBS" <<'PY'
import csv
import shlex
import sys
from pathlib import Path

source_csv = Path(sys.argv[1])
runner = Path(sys.argv[2])
log_dir = Path(sys.argv[3])
max_jobs = int(sys.argv[4])
target_gpu = sys.argv[5]
skip_jobs = int(sys.argv[6])

if not source_csv.exists():
    raise SystemExit(f"Missing command CSV: {source_csv}")

rows = list(csv.DictReader(source_csv.open(encoding="utf-8-sig", newline="")))
rows = [
    row for row in rows
    if row.get("session") == "dryrun-patience"
    and row.get("status") == "queued"
    and row.get("implementation_status") == "implemented"
]
rows = rows[skip_jobs:skip_jobs + max_jobs]
if not rows:
    raise SystemExit("No queued dryrun-patience rows found.")

lines = [
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    'cd "$(dirname "$0")/../../.."',
    f'echo "GPU{target_gpu} YOLOv11 P2 weekend search started at $(date -Is)"',
    'echo "Goal: beat YOLOv11l gate AP=0.3777 / AP50=0.5981 with near-25.3M params."',
    'echo ""',
]

for index, row in enumerate(rows, start=1):
    command = row["command"]
    command = command.replace("CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 ", "", 1)
    command = command.replace("--device 0", f"--device {target_gpu}", 1)
    run_name = row["run_name"]
    ablation = row["ablation"]
    log_path = log_dir / f"{run_name}.log"
    lines.extend([
        f'echo "[{index}/{len(rows)}] {ablation}: {run_name}"',
        f'echo "Log: {log_path}"',
        f"{command} 2>&1 | tee {shlex.quote(str(log_path))}",
        'echo ""',
    ])

lines.extend([
    f'echo "GPU{target_gpu} YOLOv11 P2 weekend search finished at $(date -Is)"',
])

runner.write_text("\n".join(lines) + "\n", encoding="utf-8")
runner.chmod(0o755)

print(f"Wrote {runner} with {len(rows)} jobs:")
for row in rows:
    print(f"  - {row['ablation']}: {row['run_name']}")
PY

if tmux has-session -t "$SESSION" 2>/dev/null; then
  if [[ "$STOP_EXISTING" == "1" ]]; then
    tmux kill-session -t "$SESSION"
  else
    echo "Session already exists: $SESSION"
    echo "Attach with: tmux attach -t $SESSION"
    exit 0
  fi
fi

tmux new-session -d -s "$SESSION" "bash $RUNNER"

cat <<EOF
GPU$TARGET_GPU proposed-detector weekend search started.

Session: $SESSION
Runner:  $RUNNER
Logs:    $LOG_DIR

Attach:
  tmux attach -t $SESSION

Monitor:
  DETECTOR_ROOT=outputs/detectors/server_yolov11_p2_next_step scripts/ubuntu/watch_proposed_metrics.sh
EOF
