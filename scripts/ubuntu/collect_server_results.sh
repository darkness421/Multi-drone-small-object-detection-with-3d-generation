#!/usr/bin/env bash
set -euo pipefail

DETECTOR_ROOT=${1:-outputs/detectors/server_baselines}
DETECTOR_ROOTS=${DETECTOR_ROOTS:-$DETECTOR_ROOT}
DEDUPE_KEY=${DEDUPE_KEY:-}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/server_baseline_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/server_baseline_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/server_baseline_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/server_baseline_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/detector_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/detector_stage_gate.md}
STAGE_GATE_DATASET=${STAGE_GATE_DATASET:-}
REPORT_DIR=${REPORT_DIR:-outputs/reports/server_baselines}

cd "$(dirname "$0")/../.."

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$PWD/.cache/ultralytics}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/.cache}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"

ROOT_ARGS=()
IFS=',' read -r -a root_list <<< "$DETECTOR_ROOTS"
for root in "${root_list[@]}"; do
  root=${root//[[:space:]]/}
  [[ -z "$root" ]] && continue
  ROOT_ARGS+=(--detector-root "$root")
done
if [[ -n "$DEDUPE_KEY" ]]; then
  ROOT_ARGS+=(--dedupe-key "$DEDUPE_KEY")
fi

conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.collect_detector_metrics "${ROOT_ARGS[@]}" --out "$RESULTS_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.summarize_seed_results --results-csv "$RESULTS_CSV" --out "$SUMMARY_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.statistical_tests --results-csv "$RESULTS_CSV" --out "$PVALUES_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_server_training_dashboard --results-csv "$RESULTS_CSV" --summary-csv "$SUMMARY_CSV" --out "$DASHBOARD"
STAGE_GATE_ARGS=(--summary-csv "$SUMMARY_CSV" --out-json "$STAGE_GATE_JSON" --out-md "$STAGE_GATE_MD")
if [[ -n "$STAGE_GATE_DATASET" ]]; then
  STAGE_GATE_ARGS+=(--dataset "$STAGE_GATE_DATASET")
fi
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.detector_stage_gate "${STAGE_GATE_ARGS[@]}"
FIGURE_ARGS=(--results-csv "$RESULTS_CSV" --summary-csv "$SUMMARY_CSV" --out-dir "$REPORT_DIR/figures")
if [[ -n "$STAGE_GATE_DATASET" ]]; then
  FIGURE_ARGS+=(--dataset "$STAGE_GATE_DATASET")
fi
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_server_report_figures "${FIGURE_ARGS[@]}"
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.organize_server_reports \
  --report-dir "$REPORT_DIR" \
  --results-csv "$RESULTS_CSV" \
  --summary-csv "$SUMMARY_CSV" \
  --pvalues-csv "$PVALUES_CSV" \
  --dashboard "$DASHBOARD" \
  --stage-gate-json "$STAGE_GATE_JSON" \
  --stage-gate-md "$STAGE_GATE_MD"

echo "Results: $RESULTS_CSV"
echo "Detector roots: $DETECTOR_ROOTS"
if [[ -n "$DEDUPE_KEY" ]]; then
  echo "Dedupe key: $DEDUPE_KEY"
fi
echo "Summary: $SUMMARY_CSV"
echo "P-values: $PVALUES_CSV"
echo "Dashboard: $DASHBOARD"
echo "Stage gate JSON: $STAGE_GATE_JSON"
echo "Stage gate report: $STAGE_GATE_MD"
echo "Report bundle: $REPORT_DIR/README.md"
if [[ -n "$STAGE_GATE_DATASET" ]]; then
  echo "Stage gate dataset: $STAGE_GATE_DATASET"
fi
