#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

DETECTOR_ROOT=${DETECTOR_ROOT:-outputs/detectors/server_top3_proposed_ablation}
INTERVAL=${INTERVAL:-10}
BASELINE_SUMMARY=${BASELINE_SUMMARY:-outputs/experiments/server_fresh/large_20260524_140922/server_baseline_summary.csv}
BASELINE_AP=${BASELINE_AP:-0.3776566666666667}
BASELINE_AP50=${BASELINE_AP50:-0.59809}
BASELINE_F1=${BASELINE_F1:-0.624751330466615}
BASELINE_NAME=${BASELINE_NAME:-YOLOv11l}

while true; do
  clear || true
  now=$(date -Is)
  latest=$(find "$DETECTOR_ROOT" -maxdepth 3 -type f -path "*/ultralytics/results.csv" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-)

  echo "Proposed live metrics - $now"
  echo "Detector root: $DETECTOR_ROOT"
  echo "Baseline summary: $BASELINE_SUMMARY"
  echo ""

  if command -v nvidia-smi >/dev/null 2>&1; then
    echo "GPU:"
    nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits \
      | awk -F, '{gsub(/^ +| +$/, "", $1); gsub(/^ +| +$/, "", $2); gsub(/^ +| +$/, "", $3); gsub(/^ +| +$/, "", $4); printf "  GPU%s  mem=%s/%s MiB  util=%s%%\n", $1, $2, $3, $4}'
    echo ""
  fi

  if [[ -z "${latest:-}" || ! -f "$latest" ]]; then
    echo "No live results.csv found yet."
    sleep "$INTERVAL"
    continue
  fi

  echo "Current results: $latest"
  echo ""

  python - "$latest" "$BASELINE_SUMMARY" "$BASELINE_NAME" "$BASELINE_AP" "$BASELINE_AP50" "$BASELINE_F1" <<'PY'
import csv
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
baseline_summary = Path(sys.argv[2])
fallback_baseline_name = sys.argv[3]
fallback_baseline_ap = float(sys.argv[4])
fallback_baseline_ap50 = float(sys.argv[5])
fallback_baseline_f1 = float(sys.argv[6])

rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
if not rows:
    print("No rows in results.csv yet.")
    raise SystemExit

def f(row, key, default=0.0):
    value = row.get(key, "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def f1(p, r):
    return 0.0 if p + r <= 0 else 2 * p * r / (p + r)

def fmt_m_params(value):
    return "-" if value <= 0 else f"{value / 1_000_000:.2f}M"

def fmt_gflops(value):
    return "-" if value <= 0 else f"{value:.1f}"

def current_run_info(results_path):
    run_dir = results_path.parent.parent
    run_dir_name = run_dir.name
    match = re.match(r"^\d{8}_\d{6}_(.+)$", run_dir_name)
    run_name = match.group(1) if match else run_dir_name
    log_path = Path("outputs/logs/server_baselines") / f"{run_name}.log"
    params = 0.0
    gflops = 0.0
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8", errors="replace")
        summaries = re.findall(r"summary:.*?([\d,]+) parameters.*?([\d.]+) GFLOPs", text)
        if summaries:
            raw_params, raw_gflops = summaries[-1]
            params = float(raw_params.replace(",", ""))
            gflops = float(raw_gflops)
    return run_name, params, gflops

baseline_rows = []
if baseline_summary.exists():
    baseline_rows = list(csv.DictReader(baseline_summary.open(encoding="utf-8-sig", newline="")))

if baseline_rows:
    baseline_rows.sort(key=lambda r: f(r, "best_AP_mean"), reverse=True)
    baseline = baseline_rows[0]
    baseline_name = baseline.get("method") or baseline.get("model") or fallback_baseline_name
    baseline_ap = f(baseline, "best_AP_mean", fallback_baseline_ap)
    baseline_ap50 = f(baseline, "best_AP50_mean", fallback_baseline_ap50)
    baseline_f1 = f(baseline, "best_F1_mean", fallback_baseline_f1)
else:
    baseline = {}
    baseline_name = fallback_baseline_name
    baseline_ap = fallback_baseline_ap
    baseline_ap50 = fallback_baseline_ap50
    baseline_f1 = fallback_baseline_f1

latest = rows[-1]
best = max(rows, key=lambda r: f(r, "metrics/mAP50-95(B)"))
run_name, proposed_params, proposed_gflops = current_run_info(path)

latest_epoch = int(f(latest, "epoch"))
latest_ap = f(latest, "metrics/mAP50-95(B)")
latest_ap50 = f(latest, "metrics/mAP50(B)")
latest_p = f(latest, "metrics/precision(B)")
latest_r = f(latest, "metrics/recall(B)")
latest_f1 = f1(latest_p, latest_r)
latest_box = f(latest, "train/box_loss")
latest_cls = f(latest, "train/cls_loss")
latest_dfl = f(latest, "train/dfl_loss")

best_epoch = int(f(best, "epoch"))
best_ap = f(best, "metrics/mAP50-95(B)")
best_ap50 = f(best, "metrics/mAP50(B)")
best_p = f(best, "metrics/precision(B)")
best_r = f(best, "metrics/recall(B)")
best_f1 = f1(best_p, best_r)

print("Best baseline:")
print(
    f"  {baseline_name}: AP={baseline_ap:.4f}  AP50={baseline_ap50:.4f}  "
    f"F1={baseline_f1:.4f}  Params={fmt_m_params(f(baseline, 'Params_mean'))}  "
    f"GFLOPs={fmt_gflops(f(baseline, 'GFLOPs_mean'))}"
)
if baseline_rows:
    print("  Top baselines by AP:")
    print("    method       AP      AP50      F1   Params  GFLOPs  seeds")
    for row in baseline_rows[:5]:
        method = (row.get("method") or row.get("model") or "?")[:11]
        seeds = row.get("seeds") or "-"
        print(
            f"    {method:11s} "
            f"{f(row, 'best_AP_mean'):.4f}  "
            f"{f(row, 'best_AP50_mean'):.4f}  "
            f"{f(row, 'best_F1_mean'):.4f}  "
            f"{fmt_m_params(f(row, 'Params_mean')):>7s}  "
            f"{fmt_gflops(f(row, 'GFLOPs_mean')):>6s}  "
            f"{seeds}"
        )
print("")

print("Current proposed model:")
print(f"  {run_name}")
print(f"  Params={fmt_m_params(proposed_params)}  GFLOPs={fmt_gflops(proposed_gflops)}")
print("")

print(f"Latest epoch: {latest_epoch}/100")
print(f"Latest: AP={latest_ap:.4f}  AP50={latest_ap50:.4f}  F1={latest_f1:.4f}  P={latest_p:.4f}  R={latest_r:.4f}  loss(box/cls/dfl)={latest_box:.4f}/{latest_cls:.4f}/{latest_dfl:.4f}")
print(f"Best in this run: epoch={best_epoch}  AP={best_ap:.4f}  AP50={best_ap50:.4f}  F1={best_f1:.4f}")
print("")
print("Proposed vs best baseline:")
print(" metric | proposed latest | proposed best | best baseline | latest delta | best delta")
print("--------+-----------------+---------------+---------------+--------------+-----------")
print(f" AP     | {latest_ap:15.4f} | {best_ap:13.4f} | {baseline_ap:13.4f} | {latest_ap - baseline_ap:+12.4f} | {best_ap - baseline_ap:+9.4f}")
print(f" AP50   | {latest_ap50:15.4f} | {best_ap50:13.4f} | {baseline_ap50:13.4f} | {latest_ap50 - baseline_ap50:+12.4f} | {best_ap50 - baseline_ap50:+9.4f}")
print(f" F1     | {latest_f1:15.4f} | {best_f1:13.4f} | {baseline_f1:13.4f} | {latest_f1 - baseline_f1:+12.4f} | {best_f1 - baseline_f1:+9.4f}")
print("")
print("Recent epochs:")
print(" epoch |    AP |  AP50 |    F1 |     P |     R | box_loss | cls_loss | dfl_loss")
print("-------+-------+-------+-------+-------+-------+----------+----------+---------")
for row in rows[-12:]:
    p = f(row, "metrics/precision(B)")
    r = f(row, "metrics/recall(B)")
    print(
        f"{int(f(row, 'epoch')):6d} | "
        f"{f(row, 'metrics/mAP50-95(B)'):.4f} | "
        f"{f(row, 'metrics/mAP50(B)'):.4f} | "
        f"{f1(p, r):.4f} | "
        f"{p:.4f} | "
        f"{r:.4f} | "
        f"{f(row, 'train/box_loss'):.4f} | "
        f"{f(row, 'train/cls_loss'):.4f} | "
        f"{f(row, 'train/dfl_loss'):.4f}"
    )
PY

  echo ""
  echo "Refresh interval: ${INTERVAL}s"
  sleep "$INTERVAL"
done
