#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
POLL_SECONDS=${POLL_SECONDS:-300}
WAIT_FOR_2D=${WAIT_FOR_2D:-1}
WAIT_FOR_RELATED_WORK=${WAIT_FOR_RELATED_WORK:-1}
FINAL_2D_LOG=${FINAL_2D_LOG:-outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log}
FINAL_2D_MARKER=${FINAL_2D_MARKER:-QUEUE_FINISHED final P2P4-SelfAttnFR ablation}
RELATED_WORK_LOG=${RELATED_WORK_LOG:-outputs/logs/related_work_consistency/queue.log}
RELATED_WORK_MARKER=${RELATED_WORK_MARKER:-QUEUE_FINISHED related-work 1280 consistency retrain}
LOG_DIR=${LOG_DIR:-outputs/logs/final_detector_heatmaps}
OUT_DIR=${OUT_DIR:-outputs/qualitative/gradcam/final_detector}
IMAGE_ROOT=${IMAGE_ROOT:-data/processed/visdrone_yolo/images/val}
TARGET_LAYER=${TARGET_LAYER:-auto-neck-last}
MARKER=${MARKER:-QUEUE_FINISHED final detector heatmaps}

mkdir -p "$LOG_DIR" "$OUT_DIR"
QUEUE_LOG="$LOG_DIR/queue.log"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

marker_done() {
  local file="$1"
  local marker="$2"
  [[ -f "$file" ]] && grep -Fq "$marker" "$file"
}

wait_for_marker() {
  local enabled="$1"
  local stage="$2"
  local file="$3"
  local marker="$4"

  [[ "$enabled" == "1" ]] || {
    log "Skipping $stage wait because it is disabled."
    return 0
  }

  while true; do
    if marker_done "$file" "$marker"; then
      log "$stage marker found."
      return 0
    fi
    log "Waiting for $stage: $file :: $marker"
    sleep "$POLL_SECONDS"
  done
}

latest_weight() {
  local pattern="$1"
  find outputs/detectors -type f -path "$pattern" -printf "%T@ %p\n" 2>/dev/null \
    | sort -nr \
    | head -n 1 \
    | cut -d" " -f2-
}

first_images() {
  find "$IMAGE_ROOT" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) \
    | sort \
    | head -n "${HEATMAP_IMAGE_COUNT:-6}"
}

log "Final detector heatmap/qualitative queue requested"
wait_for_marker "$WAIT_FOR_2D" "final 2D ablation" "$FINAL_2D_LOG" "$FINAL_2D_MARKER"
wait_for_marker "$WAIT_FOR_RELATED_WORK" "related-work 1280 consistency retrain" "$RELATED_WORK_LOG" "$RELATED_WORK_MARKER"

YOLO11L_WEIGHT=${YOLO11L_WEIGHT:-$(latest_weight "*/yolo11l*seed42*/ultralytics/weights/best.pt")}
YOLOV9C_WEIGHT=${YOLOV9C_WEIGHT:-$(latest_weight "*/yolov9c*seed42*/ultralytics/weights/best.pt")}
OURS_WEIGHT=${OURS_WEIGHT:-$(latest_weight "*/proposed_p2p4_balanced_selfattn_tiny_frelu_yolo11l*seed42*/ultralytics/weights/best.pt")}

YOLO11L_WEIGHT=${YOLO11L_WEIGHT:-yolo11l.pt}
YOLOV9C_WEIGHT=${YOLOV9C_WEIGHT:-yolov9c.pt}
OURS_WEIGHT=${OURS_WEIGHT:-configs/detector/yolo11l-p2p4-balanced-v1.yaml}

mapfile -t IMAGES_ARR < <(first_images)
if [[ "${#IMAGES_ARR[@]}" -eq 0 ]]; then
  log "WARN: no VisDrone validation images found under $IMAGE_ROOT; writing marker with missing-image note."
  printf '{"status":"missing_images","image_root":"%s"}\n' "$IMAGE_ROOT" > "$OUT_DIR/gradcam_run_plan.json"
else
  log "Preparing Grad-CAM/qualitative plan for core models."
  log "YOLOv11l weight: $YOLO11L_WEIGHT"
  log "YOLOv9c weight: $YOLOV9C_WEIGHT"
  log "Ours weight: $OURS_WEIGHT"
  conda run --no-capture-output -n "$CONDA_ENV" python -m evaluation.gradcam_yolo \
    --weights "$YOLO11L_WEIGHT" "$YOLOV9C_WEIGHT" "$OURS_WEIGHT" \
    --images "${IMAGES_ARR[@]}" \
    --target-layer "$TARGET_LAYER" \
    --out-dir "$OUT_DIR" 2>&1 | tee -a "$QUEUE_LOG" || \
      log "WARN: Grad-CAM plan generation returned non-zero"
fi

cat > "$OUT_DIR/README.md" <<EOF
# Final Detector Heatmap / Qualitative Plan

Generated: $(date -Is)

Order policy:
1. Finish final 2D ablation.
2. Finish runnable related-work 1280 experiments.
3. Prepare core-model heatmap/qualitative comparison.
4. Then run TinyPerson 640 and Isaac/3D/reasoner in parallel lanes.

Core models:
- YOLOv11l: $YOLO11L_WEIGHT
- YOLOv9c: $YOLOV9C_WEIGHT
- Ours P2P4-SelfAttnFR: $OURS_WEIGHT

Output:
- $OUT_DIR/gradcam_run_plan.json
EOF

log "$MARKER"
