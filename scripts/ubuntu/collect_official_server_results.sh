#!/usr/bin/env bash
set -euo pipefail

CONDA_ENV=${CONDA_ENV:-com3d-ace}
BASE_ROOT=${BASE_ROOT:-outputs/detectors/server_baselines}
FRESH_PARENT=${FRESH_PARENT:-outputs/detectors/server_fresh_baselines}
REQUIRE_DATA_YAML=${REQUIRE_DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
REQUIRE_IMGSZ=${REQUIRE_IMGSZ:-1280}
REQUIRE_EPOCHS=${REQUIRE_EPOCHS:-100}
REQUIRE_BATCH=${REQUIRE_BATCH:-8}
REQUIRE_DETERMINISTIC=${REQUIRE_DETERMINISTIC:-true}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/server_official_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/server_official_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/server_official_pvalues.csv}
EXCLUDED_CSV=${EXCLUDED_CSV:-outputs/experiments/server_official_excluded.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/server_official_dashboard.png}
REPORT_DIR=${REPORT_DIR:-outputs/reports/server_official}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/server_official_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/server_official_stage_gate.md}

cd "$(dirname "$0")/../.."

export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
export YOLO_CONFIG_DIR="${YOLO_CONFIG_DIR:-$PWD/.cache/ultralytics}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/.cache}"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR" "$XDG_CACHE_HOME"

latest_fresh=""
if [[ -d "$FRESH_PARENT" ]]; then
  latest_fresh=$(find "$FRESH_PARENT" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2- || true)
fi

DETECTOR_ROOTS=${DETECTOR_ROOTS:-}
if [[ -z "$DETECTOR_ROOTS" ]]; then
  DETECTOR_ROOTS="$BASE_ROOT"
  if [[ -n "$latest_fresh" ]]; then
    DETECTOR_ROOTS="$DETECTOR_ROOTS,$latest_fresh"
  fi
fi

ROOT_ARGS=()
IFS=',' read -r -a root_list <<< "$DETECTOR_ROOTS"
for root in "${root_list[@]}"; do
  root=${root//[[:space:]]/}
  [[ -z "$root" ]] && continue
  ROOT_ARGS+=(--detector-root "$root")
done

echo "Official server result collection"
echo "  detector roots: $DETECTOR_ROOTS"
echo "  require data:   $REQUIRE_DATA_YAML"
echo "  require imgsz:  $REQUIRE_IMGSZ"
echo "  require epochs: $REQUIRE_EPOCHS"
echo "  require batch:  $REQUIRE_BATCH"
echo "  require determ: $REQUIRE_DETERMINISTIC"
echo ""

conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.collect_detector_metrics \
  "${ROOT_ARGS[@]}" \
  --out "$RESULTS_CSV" \
  --excluded-out "$EXCLUDED_CSV" \
  --require-data-yaml "$REQUIRE_DATA_YAML" \
  --require-imgsz "$REQUIRE_IMGSZ" \
  --require-epochs "$REQUIRE_EPOCHS" \
  --require-batch "$REQUIRE_BATCH" \
  --require-deterministic "$REQUIRE_DETERMINISTIC" \
  --dedupe-key dataset,method,seed

conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.summarize_seed_results \
  --results-csv "$RESULTS_CSV" \
  --out "$SUMMARY_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.statistical_tests \
  --results-csv "$RESULTS_CSV" \
  --out "$PVALUES_CSV"
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_server_training_dashboard \
  --results-csv "$RESULTS_CSV" \
  --summary-csv "$SUMMARY_CSV" \
  --out "$DASHBOARD" \
  --dataset VisDrone2019-DET
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.build_server_report_figures \
  --results-csv "$RESULTS_CSV" \
  --summary-csv "$SUMMARY_CSV" \
  --out-dir "$REPORT_DIR/figures" \
  --dataset VisDrone2019-DET
conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.detector_stage_gate \
  --summary-csv "$SUMMARY_CSV" \
  --out-json "$STAGE_GATE_JSON" \
  --out-md "$STAGE_GATE_MD" \
  --dataset VisDrone2019-DET
conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.organize_server_reports \
  --report-dir "$REPORT_DIR" \
  --results-csv "$RESULTS_CSV" \
  --summary-csv "$SUMMARY_CSV" \
  --pvalues-csv "$PVALUES_CSV" \
  --dashboard "$DASHBOARD" \
  --stage-gate-json "$STAGE_GATE_JSON" \
  --stage-gate-md "$STAGE_GATE_MD"

echo "Official results: $RESULTS_CSV"
echo "Official summary: $SUMMARY_CSV"
echo "Excluded rows:    $EXCLUDED_CSV"
echo "Dashboard:        $DASHBOARD"
echo "Report bundle:    $REPORT_DIR/README.md"
