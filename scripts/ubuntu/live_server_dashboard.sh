#!/usr/bin/env bash
set -euo pipefail

INTERVAL=${1:-60}
DETECTOR_ROOT=${DETECTOR_ROOT:-outputs/detectors/server_baselines}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/live/server_baseline_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/live/server_baseline_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/live/server_baseline_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/server_baseline_dashboard.png}

cd "$(dirname "$0")/../.."

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$PWD/.cache/ultralytics}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/.cache}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME" "$(dirname "$RESULTS_CSV")" "$(dirname "$DASHBOARD")"

echo "Live dashboard loop"
echo "  detector root: $DETECTOR_ROOT"
echo "  results csv:   $RESULTS_CSV"
echo "  summary csv:   $SUMMARY_CSV"
echo "  p-values csv:  $PVALUES_CSV"
echo "  dashboard png: $DASHBOARD"
echo "  interval:      ${INTERVAL}s"
echo ""

while true; do
  started_at=$(date -Is)
  echo "== Refresh at $started_at =="
  conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.collect_detector_metrics \
    --detector-root "$DETECTOR_ROOT" \
    --out "$RESULTS_CSV"
  conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.summarize_seed_results \
    --results-csv "$RESULTS_CSV" \
    --out "$SUMMARY_CSV"
  conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.statistical_tests \
    --results-csv "$RESULTS_CSV" \
    --out "$PVALUES_CSV" || true
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_server_training_dashboard \
    --results-csv "$RESULTS_CSV" \
    --summary-csv "$SUMMARY_CSV" \
    --out "$DASHBOARD"
  echo "Latest summary:"
  SUMMARY_CSV="$SUMMARY_CSV" conda run --no-capture-output -n "$CONDA_ENV" python - <<'PY'
import csv
import os
from pathlib import Path

path = Path(os.environ["SUMMARY_CSV"])
if not path.exists():
    print("  no summary yet")
    raise SystemExit
rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
if not rows:
    print("  no rows yet")
    raise SystemExit
for row in rows:
    method = row.get("method") or row.get("model") or "unknown"
    family = row.get("detector_family") or "?"
    version = row.get("yolo_version") or row.get("model_version") or "?"
    size = row.get("param_size_group") or row.get("model_scale") or "?"
    ap = row.get("best_AP_mean_std") or row.get("best_AP_mean") or ""
    ap50 = row.get("best_AP50_mean_std") or row.get("best_AP50_mean") or ""
    seeds = row.get("seeds") or ""
    level = row.get("analysis_level") or ""
    print(f"  {method:12s} {family:7s} {version:8s} size={size:7s} AP={ap:16s} AP50={ap50:16s} seeds={seeds} ({level})")
PY
  echo ""
  sleep "$INTERVAL"
done
