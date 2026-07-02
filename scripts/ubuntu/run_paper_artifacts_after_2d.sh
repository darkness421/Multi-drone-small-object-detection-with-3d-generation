#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
POLL_SECONDS=${POLL_SECONDS:-300}
WAIT_FOR_FINAL_2D=${WAIT_FOR_FINAL_2D:-1}
WAIT_FOR_RELATED_WORK=${WAIT_FOR_RELATED_WORK:-1}
FINAL_2D_LOG=${FINAL_2D_LOG:-outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log}
FINAL_2D_PATTERN=${FINAL_2D_PATTERN:-QUEUE_FINISHED final P2P4-SelfAttnFR ablation}
RELATED_WORK_LOG=${RELATED_WORK_LOG:-outputs/logs/related_work_consistency/queue.log}
RELATED_WORK_PATTERN=${RELATED_WORK_PATTERN:-QUEUE_FINISHED related-work 1280 consistency retrain}
LOG_DIR=${LOG_DIR:-outputs/logs/paper_artifacts_after_2d}
MANIFEST=${MANIFEST:-outputs/reports/live/nightly_paper_artifacts_manifest.md}

mkdir -p "$LOG_DIR" outputs/reports/live paper/figures/results
log_file="$LOG_DIR/queue.log"

log() {
  echo "[$(date -Is)] $*" | tee -a "$log_file"
}

wait_for_marker() {
  local enabled="$1"
  local file="$2"
  local pattern="$3"
  local label="$4"
  if [[ "$enabled" != "1" ]]; then
    log "Skip wait for $label"
    return 0
  fi
  log "Waiting for $label marker: $pattern"
  while true; do
    if [[ -f "$file" ]] && grep -Fq "$pattern" "$file"; then
      log "Found $label marker"
      return 0
    fi
    sleep "$POLL_SECONDS"
  done
}

run_py() {
  local module="$1"
  shift
  log "RUN python -m $module $*"
  MPLCONFIGDIR="$PWD/.cache/matplotlib" \
  YOLO_CONFIG_DIR="$PWD/.cache/ultralytics" \
  conda run --no-capture-output -n "$CONDA_ENV" python -m "$module" "$@"
}

run_optional() {
  local label="$1"
  shift
  if "$@"; then
    log "OK $label"
  else
    log "WARN $label failed; continuing so other paper artifacts are still refreshed"
  fi
}

log "Paper artifact refresh queue started"
wait_for_marker "$WAIT_FOR_FINAL_2D" "$FINAL_2D_LOG" "$FINAL_2D_PATTERN" "final detector ablation"
wait_for_marker "$WAIT_FOR_RELATED_WORK" "$RELATED_WORK_LOG" "$RELATED_WORK_PATTERN" "related-work comparison"

run_optional "collect related-work detector results" run_py scripts.collect_related_work_detector_results
run_optional "build final detector table preview" run_py scripts.build_final_detector_table_preview
run_optional "build detector rankings" run_py scripts.build_detector_rankings
run_optional "build live paper figures" run_py scripts.build_paper_detector_result_figures --out-dir outputs/reports/live
run_optional "build paper figures copy" run_py scripts.build_paper_detector_result_figures --out-dir paper/figures/results
run_optional "build supplementary detector analysis" run_py scripts.build_supplementary_detector_analysis --out-dir outputs/reports/live/supplementary_detector_analysis
run_optional "build live training dashboard" run_py scripts.build_live_training_dashboard --out outputs/reports/live/training_dashboard.png

cat > "$MANIFEST" <<EOF
# Nightly Paper Artifacts

Updated: $(date -Is)

Generated after final 2D and related-work queue markers.

Key outputs:

- \`outputs/reports/final_detector_table_preview.md\`
- \`outputs/reports/final_detector_table_preview.csv\`
- \`outputs/reports/final_detector_table_preview.tex\`
- \`outputs/reports/detector_rankings/\`
- \`outputs/reports/live/training_dashboard.png\`
- \`outputs/reports/live/paper_fig01_main_detector_table.png\`
- \`outputs/reports/live/paper_fig03_related_work_status_table.png\`
- \`outputs/reports/live/paper_fig08_final_ablation_status_table.png\`
- \`outputs/reports/live/supplementary_detector_analysis/\`
- \`paper/figures/results/\`

Protocol note:

- Related-work comparison is strict Sec. 2.1 only.
- LEAF-YOLO is internal-only unless the manuscript is revised to cite it.
- CSFPR-RTDETR and MFFSODNet are the staged runnable related-work queue.
EOF

log "QUEUE_FINISHED paper artifacts after 2D"
