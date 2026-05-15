#!/usr/bin/env bash
set -euo pipefail

DETECTOR_ROOT=${1:-outputs/detectors/server_baselines}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/server_baseline_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/server_baseline_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/server_baseline_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/server_baseline_dashboard.png}

cd "$(dirname "$0")/../.."

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$PWD/.cache/ultralytics}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/.cache}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"

conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.collect_detector_metrics --detector-root "$DETECTOR_ROOT" --out "$RESULTS_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.summarize_seed_results --results-csv "$RESULTS_CSV" --out "$SUMMARY_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.statistical_tests --results-csv "$RESULTS_CSV" --out "$PVALUES_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_server_training_dashboard --results-csv "$RESULTS_CSV" --summary-csv "$SUMMARY_CSV" --out "$DASHBOARD"

echo "Results: $RESULTS_CSV"
echo "Summary: $SUMMARY_CSV"
echo "P-values: $PVALUES_CSV"
echo "Dashboard: $DASHBOARD"
