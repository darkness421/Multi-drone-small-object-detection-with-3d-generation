#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/continuous_detector_queue}
GPU=${GPU:-0}
mkdir -p "$LOG_DIR"
log_file="$LOG_DIR/poststage_artifacts.log"

log() {
  echo "[$(date -Is)] $*" | tee -a "$log_file"
}

latest_weight() {
  local root="$1"
  local pattern="$2"
  find "$root" -maxdepth 2 -type f -path "$pattern" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 1 | cut -d" " -f2-
}

log "Post-stage artifacts started"

log "Stage 3a: collect detector results/report with baseline + proposed + NMS confirmation roots"
DETECTOR_ROOTS="outputs/detectors/server_fresh_baselines/large_20260524_140922,outputs/detectors/server_yolov11_p2_confirm,outputs/detectors/server_yolov11_p2_balanced,outputs/detectors/server_yolov11_p2_balanced_v2,outputs/detectors/server_yolov11_p2_balanced_followup,outputs/detectors/server_yolov11_p2_slim,outputs/detectors/server_yolov11_p2_compression,outputs/detectors/nms_confirm_p2balv2,outputs/detectors/nms_sweep_efficient,outputs/detectors/nms_sweep_accuracy" \
RESULTS_CSV="outputs/experiments/server_with_p2_detector_results.csv" \
SUMMARY_CSV="outputs/experiments/server_with_p2_detector_summary.csv" \
PVALUES_CSV="outputs/experiments/server_with_p2_detector_pvalues.csv" \
DASHBOARD="outputs/reports/proposed_detector_search/figures/server_with_p2_detector_dashboard.png" \
REPORT_DIR="outputs/reports/proposed_detector_search" \
STAGE_GATE_JSON="outputs/experiments/server_with_p2_detector_stage_gate.json" \
STAGE_GATE_MD="outputs/experiments/server_with_p2_detector_stage_gate.md" \
CONDA_ENV="$CONDA_ENV" \
bash scripts/ubuntu/collect_proposed_results.sh 2>&1 | tee -a "$log_file" || log "WARN: result collection failed"

log "Stage 3b: build supplementary detector analysis figures"
conda run --no-capture-output -n "$CONDA_ENV" \
  python -m scripts.build_supplementary_detector_analysis \
  --summary-csv outputs/experiments/server_with_p2_detector_summary.csv \
  --summary-csv outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_summary.csv \
  --results-csv outputs/experiments/server_with_p2_detector_results.csv \
  --results-csv outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_results.csv \
  --out-dir outputs/reports/supplementary_detector 2>&1 | tee -a "$log_file" || log "WARN: supplementary figure build failed"

baseline_weight=$(latest_weight "outputs/detectors/server_fresh_baselines/large_20260524_140922" "*yolo11l*seed42/ultralytics/weights/best.pt")
proposed_weight=$(latest_weight "outputs/detectors/server_yolov11_p2_balanced_v2" "*p2_balanced_v2_tiny_frelu*seed42/ultralytics/weights/best.pt")

if [[ -n "${baseline_weight:-}" && -n "${proposed_weight:-}" ]]; then
  log "Stage 3c: build qualitative examples for YOLOv11l vs P2BalV2"
  conda run --no-capture-output -n "$CONDA_ENV" \
    python -m evaluation.qualitative_examples \
    --images-dir data/processed/visdrone_yolo/images/val \
    --weights "$baseline_weight" "$proposed_weight" \
    --out-dir outputs/qualitative/detection_examples \
    --max-images 12 \
    --imgsz 1280 \
    --device "$GPU" 2>&1 | tee -a "$log_file" || log "WARN: qualitative examples failed"

  log "Stage 3d: prepare Grad-CAM run plan"
  mapfile -t images < <(find data/processed/visdrone_yolo/images/val -maxdepth 1 -type f | sort | head -n 6)
  if [[ ${#images[@]} -gt 0 ]]; then
    conda run --no-capture-output -n "$CONDA_ENV" \
      python -m evaluation.gradcam_yolo \
      --weights "$baseline_weight" "$proposed_weight" \
      --images "${images[@]}" \
      --out-dir outputs/qualitative/gradcam 2>&1 | tee -a "$log_file" || log "WARN: Grad-CAM plan failed"
  else
    log "WARN: no validation images found for Grad-CAM plan"
  fi
else
  log "WARN: missing baseline/proposed weight for qualitative stages"
fi

log "Stage 4: MarineCity/Isaac readiness lane"
GPU=1 CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/start_gpu1_marinecity_lane.sh 2>&1 | tee -a "$log_file" || log "WARN: MarineCity readiness lane failed"

log "Post-stage artifacts finished"
