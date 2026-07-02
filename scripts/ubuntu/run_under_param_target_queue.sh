#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
GPU0=${GPU0:-0}
GPU1=${GPU1:-$GPU0}
TARGET_AP=${TARGET_AP:-0.3835}
TARGET_PARAMS_M=${TARGET_PARAMS_M:-25.32}
LOG_DIR=${LOG_DIR:-outputs/logs/under_param_target}
PROJECT_V2=${PROJECT_V2:-outputs/detectors/server_yolov11_p2_balanced_v2}
PROJECT_V3=${PROJECT_V3:-outputs/detectors/server_yolov11_p2_balanced_v3}
PROJECT_P2P4=${PROJECT_P2P4:-outputs/detectors/server_yolov11_p2p4_balanced}

mkdir -p "$LOG_DIR" "$PROJECT_V3"
queue_log="$LOG_DIR/queue.log"

log() {
  echo "[$(date -Is)] $*" | tee -a "$queue_log"
}

run_balanced() {
  local gpu="$1"
  local seed="$2"
  local ablation="$3"
  local model_yaml="$4"
  local project="$5"
  local log_dir="$6"
  log "Queueing $ablation seed=$seed on GPU$gpu model=$model_yaml"
  TARGET_GPU="$gpu" \
  SEED="$seed" \
  ABLATION="$ablation" \
  MODEL_YAML="$model_yaml" \
  PROJECT="$project" \
  LOG_DIR="$log_dir" \
  CONDA_ENV="$CONDA_ENV" \
  EPOCHS="${EPOCHS:-100}" \
  PATIENCE="${PATIENCE:-5}" \
  BATCH="${BATCH:-4}" \
  IMG_SIZE="${IMG_SIZE:-1280}" \
  bash scripts/ubuntu/start_yolov11_p2_balanced_search.sh
}

target_check() {
  local latest="$LOG_DIR/target_check.latest.txt"
  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.watch_live_training_scoreboard --once | tee "$latest" | tee -a "$queue_log"
  log "Target remains AP > $TARGET_AP and Params < ${TARGET_PARAMS_M}M."
  if grep -q "TARGET-under-param" "$latest"; then
    log "TARGET FOUND: AP > $TARGET_AP and Params < ${TARGET_PARAMS_M}M. Stopping queue."
    exit 0
  fi
}

log "Under-param target queue started"
log "Success target: AP > $TARGET_AP and Params < ${TARGET_PARAMS_M}M"
log "Stage 1: finish missing P2BalV2 seed confirmation, then evaluate NMS."

run_balanced "$GPU0" 2026 p2_balanced_v2_tiny_frelu configs/detector/yolo11l-p2-balanced-v2.yaml "$PROJECT_V2" outputs/logs/server_yolov11_p2_balanced_v2
GPU="$GPU0" CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/eval_p2balv2_nms055.sh
target_check

log "Stage 2: train P2BalV3, a slightly wider under-param candidate."
run_balanced "$GPU0" 42 p2_balanced_v3_tiny_frelu configs/detector/yolo11l-p2-balanced-v3.yaml "$PROJECT_V3" outputs/logs/server_yolov11_p2_balanced_v3
target_check

run_balanced "$GPU1" 123 p2_balanced_v3_tiny_frelu configs/detector/yolo11l-p2-balanced-v3.yaml "$PROJECT_V3" outputs/logs/server_yolov11_p2_balanced_v3
target_check

run_balanced "$GPU0" 2026 p2_balanced_v3_tiny_frelu configs/detector/yolo11l-p2-balanced-v3.yaml "$PROJECT_V3" outputs/logs/server_yolov11_p2_balanced_v3
target_check

log "Stage 3: DynFreq-C3 frequency refinement under the same parameter ceiling."
run_balanced "$GPU1" 123 p2_balanced_v3_dynfreq_p2_tiny_frelu configs/detector/yolo11l-p2-balanced-v3.yaml "$PROJECT_V3" outputs/logs/server_yolov11_p2_balanced_v3
target_check

run_balanced "$GPU0" 123 p2_balanced_v3_dynfreq_small_tiny_frelu configs/detector/yolo11l-p2-balanced-v3.yaml "$PROJECT_V3" outputs/logs/server_yolov11_p2_balanced_v3
target_check

log "Stage 4: P2/P3/P4-only head to test 4x/8x/16x downsampling evidence."
run_balanced "$GPU1" 123 p2p4_balanced_tiny_frelu configs/detector/yolo11l-p2p4-balanced-v1.yaml "$PROJECT_P2P4" outputs/logs/server_yolov11_p2p4_balanced
target_check

run_balanced "$GPU0" 123 p2p4_balanced_dynfreq_p2_tiny_frelu configs/detector/yolo11l-p2p4-balanced-v1.yaml "$PROJECT_P2P4" outputs/logs/server_yolov11_p2p4_balanced
target_check

run_balanced "$GPU1" 123 p2p4_balanced_dynfreq_small_tiny_frelu configs/detector/yolo11l-p2p4-balanced-v1.yaml "$PROJECT_P2P4" outputs/logs/server_yolov11_p2p4_balanced
target_check

log "Stage 5: compact module transfer from the strong P2-CBAM/P2-WCBAM evidence."
PROJECT_V2_MODULE=${PROJECT_V2_MODULE:-outputs/detectors/server_yolov11_p2_balanced_v2_modules}
LOG_V2_MODULE=${LOG_V2_MODULE:-outputs/logs/server_yolov11_p2_balanced_v2_modules}
run_balanced "$GPU0" 123 p2_balanced_v2_cbam_tiny_frelu configs/detector/yolo11l-p2-balanced-v2.yaml "$PROJECT_V2_MODULE" "$LOG_V2_MODULE"
target_check

run_balanced "$GPU1" 123 p2_balanced_v2_wavelet_tiny_frelu configs/detector/yolo11l-p2-balanced-v2.yaml "$PROJECT_V2_MODULE" "$LOG_V2_MODULE"
target_check

run_balanced "$GPU0" 123 p2_balanced_v2_selfattn_tiny_frelu configs/detector/yolo11l-p2-balanced-v2.yaml "$PROJECT_V2_MODULE" "$LOG_V2_MODULE"
target_check

run_balanced "$GPU1" 123 p2_balanced_v2_wavelet_selfattn_tiny_frelu configs/detector/yolo11l-p2-balanced-v2.yaml "$PROJECT_V2_MODULE" "$LOG_V2_MODULE"
target_check

log "Stage 6: under-parameter queue finished. If none pass, next design step is a P2BalV4 under the same parameter ceiling."

log "Stage 6A: new compact-performance ideas. Recover AP on smaller models before increasing params."
PROJECT_COMPACT_IDEAS=${PROJECT_COMPACT_IDEAS:-outputs/detectors/server_yolov11_p2_compact_ideas}
LOG_COMPACT_IDEAS=${LOG_COMPACT_IDEAS:-outputs/logs/server_yolov11_p2_compact_ideas}
run_balanced "$GPU0" 123 p2_efficient_v3_dynfreq_p2_tiny_frelu configs/detector/yolo11l-p2-efficient-v3.yaml "$PROJECT_COMPACT_IDEAS" "$LOG_COMPACT_IDEAS"
target_check

run_balanced "$GPU1" 123 p2_efficient_v3_se_tiny_frelu configs/detector/yolo11l-p2-efficient-v3.yaml "$PROJECT_COMPACT_IDEAS" "$LOG_COMPACT_IDEAS"
target_check

run_balanced "$GPU0" 123 p2_compress_v3_dynfreq_p2_tiny_frelu configs/detector/yolo11l-p2-compress-v3.yaml "$PROJECT_COMPACT_IDEAS" "$LOG_COMPACT_IDEAS"
target_check

run_balanced "$GPU1" 123 p2_compress_v3_se_tiny_frelu configs/detector/yolo11l-p2-compress-v3.yaml "$PROJECT_COMPACT_IDEAS" "$LOG_COMPACT_IDEAS"
target_check

log "Stage 6B: P2/P3/P4-only recovery ideas. Add cheap gates/context to the 20.82M head set."
run_balanced "$GPU0" 123 p2p4_balanced_se_tiny_frelu configs/detector/yolo11l-p2p4-balanced-v1.yaml "$PROJECT_P2P4" outputs/logs/server_yolov11_p2p4_balanced
target_check

run_balanced "$GPU1" 123 p2p4_balanced_selfattn_tiny_frelu configs/detector/yolo11l-p2p4-balanced-v1.yaml "$PROJECT_P2P4" outputs/logs/server_yolov11_p2p4_balanced
target_check

log "Stage 6C: compact idea queue finished. If none pass, use best AP/Params trade-off and move to final multi-seed confirmation."

if [[ "${RUN_RELATED_WORK_QUEUE:-1}" == "1" ]]; then
  log "Stage 7: launch related-work detector comparison queue."
  CONDA_ENV="$CONDA_ENV" \
  SEEDS="${RELATED_WORK_SEEDS:-42}" \
  EPOCHS="${RELATED_WORK_EPOCHS:-100}" \
  BATCH="${RELATED_WORK_BATCH:-4}" \
  CSFPR_IMGSZ="${RELATED_WORK_CSFPR_IMGSZ:-1280}" \
  CSFPR_BATCH="${RELATED_WORK_CSFPR_BATCH:-1}" \
  SESSION="${RELATED_WORK_SESSION:-related-work-detector-queue}" \
  bash scripts/ubuntu/start_related_work_detector_queue.sh
else
  log "Stage 5: related-work detector queue skipped because RUN_RELATED_WORK_QUEUE=0."
fi
