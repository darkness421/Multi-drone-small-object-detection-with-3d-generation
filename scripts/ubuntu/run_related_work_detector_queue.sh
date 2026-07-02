#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
SEEDS=${SEEDS:-42,123,2026}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
IMGSZ=${IMGSZ:-1280}
BATCH=${BATCH:-4}
DATA_YAML=${DATA_YAML:-configs/detector/visdrone_yolo_data.yaml}
PROJECT=${PROJECT:-outputs/detectors/related_work_detectors}
LOG_DIR=${LOG_DIR:-outputs/logs/related_work_detectors}
EXPERIMENT_ROOT=${EXPERIMENT_ROOT:-outputs/experiments}
QUEUE_CSV=${QUEUE_CSV:-outputs/experiments/related_work_detector_queue.csv}
RUN_TRAINING=${RUN_TRAINING:-1}
WAIT_FOR_SESSION=${WAIT_FOR_SESSION:-}
WAIT_FOR_SESSIONS=${WAIT_FOR_SESSIONS:-}
MIN_RELATED_WORK_TARGETS=${MIN_RELATED_WORK_TARGETS:-5}
ALLOW_INTERNAL_LEAF=${ALLOW_INTERNAL_LEAF:-0}
RELATED_WORK_RECORDS_THIS_RUN=0
RELATED_WORK_RUNNABLE_OR_ADAPTER_THIS_RUN=0

mkdir -p "$PROJECT" "$LOG_DIR" "$EXPERIMENT_ROOT" "$(dirname "$QUEUE_CSV")"

queue_log="$LOG_DIR/queue.log"

log() {
  echo "[$(date -Is)] $*" | tee -a "$queue_log"
}

if [[ ! -f "$QUEUE_CSV" ]]; then
  echo "created_at,priority,candidate,family,requested_paths,selected_model,status,reason" > "$QUEUE_CSV"
fi

record() {
  local priority="$1"
  local candidate="$2"
  local family="$3"
  local requested="$4"
  local selected="$5"
  local status="$6"
  local reason="$7"
  printf '"%s","%s","%s","%s","%s","%s","%s","%s"\n' \
    "$(date -Is)" "$priority" "$candidate" "$family" "$requested" "$selected" "$status" "$reason" >> "$QUEUE_CSV"
  RELATED_WORK_RECORDS_THIS_RUN=$((RELATED_WORK_RECORDS_THIS_RUN + 1))
  case "$status" in
    QUEUED_RELATED_WORK|ADAPTER_REQUIRED_GITHUB_AVAILABLE|GITHUB_STAGING_REQUIRED|SKIPPED_EXTERNAL_REQUIRED)
      RELATED_WORK_RUNNABLE_OR_ADAPTER_THIS_RUN=$((RELATED_WORK_RUNNABLE_OR_ADAPTER_THIS_RUN + 1))
      ;;
  esac
}

is_yolo_loadable() {
  local model="$1"
  MODEL_TO_CHECK="$model" conda run --no-capture-output -n "$CONDA_ENV" python - <<'PY' >/dev/null 2>&1
import os
from ultralytics import YOLO

YOLO(os.environ["MODEL_TO_CHECK"])
PY
}

select_loadable_model() {
  local requested="$1"
  local item
  IFS=',' read -r -a items <<< "$requested"
  for item in "${items[@]}"; do
    item=${item//[[:space:]]/}
    [[ -z "$item" ]] && continue
    if [[ -f "$item" ]] && is_yolo_loadable "$item"; then
      echo "$item"
      return 0
    fi
  done
  return 1
}

run_candidate() {
  local priority="$1"
  local candidate="$2"
  local family="$3"
  local requested="$4"
  local reason="$5"
  local session_slug
  local selected

  session_slug=$(echo "$candidate" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-')
  session_slug=${session_slug%-}

  log "Checking related-work candidate: $candidate ($priority)"
  if ! selected=$(select_loadable_model "$requested"); then
    log "SKIPPED_EXTERNAL_REQUIRED $candidate: stage compatible weights/config first. Requested: $requested"
    record "$priority" "$candidate" "$family" "$requested" "" "SKIPPED_EXTERNAL_REQUIRED" "$reason"
    return 0
  fi

  log "QUEUED_RELATED_WORK $candidate selected_model=$selected seeds=$SEEDS"
  record "$priority" "$candidate" "$family" "$requested" "$selected" "QUEUED_RELATED_WORK" "$reason"

  if [[ "$RUN_TRAINING" != "1" ]]; then
    log "RUN_TRAINING=0, not launching $candidate."
    return 0
  fi

  local session="related-${session_slug}"
  MODELS="$selected" \
  SEEDS="$SEEDS" \
  DATA_YAML="$DATA_YAML" \
  PROJECT="$PROJECT" \
  LOG_DIR="$LOG_DIR" \
  CONDA_ENV="$CONDA_ENV" \
  GPU_LIST="${RELATED_WORK_GPU:-1}" \
  RUN_EVAL=1 \
  ROC_AUC=1 \
  DATASET_TAG=visdrone \
  bash scripts/ubuntu/train_visdrone_baselines_tmux.sh "$session" "$EPOCHS" "$BATCH" "$IMGSZ"

  while tmux has-session -t "$session" 2>/dev/null; do
    log "Waiting for related-work session to finish: $session"
    sleep 300
  done
  log "FINISHED_RELATED_WORK $candidate"
}

record_policy_only() {
  local priority="$1"
  local candidate="$2"
  local family="$3"
  local requested="$4"
  local status="$5"
  local reason="$6"

  log "$status $candidate: $reason"
  record "$priority" "$candidate" "$family" "$requested" "" "$status" "$reason"
}

run_github_candidate() {
  local priority="$1"
  local candidate="$2"
  local family="$3"
  local requested="$4"
  local repo_dir="$5"
  local reason="$6"
  local selected

  log "Checking GitHub-backed candidate: $candidate ($priority)"
  if selected=$(select_loadable_model "$requested"); then
    log "QUEUED_RELATED_WORK $candidate selected_model=$selected seeds=$SEEDS"
    record "$priority" "$candidate" "$family" "$requested" "$selected" "QUEUED_RELATED_WORK" "$reason"

    if [[ "$RUN_TRAINING" != "1" ]]; then
      log "RUN_TRAINING=0, not launching $candidate."
      return 0
    fi

    local session_slug
    session_slug=$(echo "$candidate" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-')
    session_slug=${session_slug%-}
    MODELS="$selected" \
    SEEDS="$SEEDS" \
    DATA_YAML="$DATA_YAML" \
    PROJECT="$PROJECT" \
    LOG_DIR="$LOG_DIR" \
    CONDA_ENV="$CONDA_ENV" \
    GPU_LIST="${RELATED_WORK_GPU:-1}" \
    RUN_EVAL=1 \
    ROC_AUC=1 \
    DATASET_TAG=visdrone \
    bash scripts/ubuntu/train_visdrone_baselines_tmux.sh "related-${session_slug}" "$EPOCHS" "$BATCH" "$IMGSZ"
    return 0
  fi

  if [[ -d "$repo_dir" ]]; then
    record_policy_only "$priority" "$candidate" "$family" "$requested" "ADAPTER_REQUIRED_GITHUB_AVAILABLE" "$reason Repo is staged at $repo_dir, but no loadable checkpoint/export is staged yet."
  else
    record_policy_only "$priority" "$candidate" "$family" "$requested" "GITHUB_STAGING_REQUIRED" "$reason Public GitHub/code exists, but the repo/checkpoint is not staged locally yet."
  fi
}

wait_for_session() {
  local session="$1"
  [[ -z "$session" ]] && return 0
  log "Waiting for session before related-work queue: $session"
  while tmux has-session -t "$session" 2>/dev/null; do
    sleep 300
  done
  log "Wait session cleared: $session"
}

wait_for_sessions() {
  local sessions="$1"
  local session
  [[ -z "$sessions" ]] && return 0
  IFS=',' read -r -a items <<< "$sessions"
  for session in "${items[@]}"; do
    session=${session//[[:space:]]/}
    wait_for_session "$session"
  done
}

run_csfpr_rtdetr() {
  local requested="external/CSFPR-RTDETR/weights/visdrone.pt,external/CSFPR-RTDETR/ultralytics/cfg/modelY/CSFPR-RTDETR.yaml"
  local weight="external/CSFPR-RTDETR/weights/visdrone.pt"
  local data="external/CSFPR-RTDETR/dataset/visdrone_local.yaml"

  log "Checking related-work candidate: CSFPR-RTDETR (P1)"
  if [[ ! -f "$weight" || ! -f "$data" ]]; then
    log "SKIPPED_EXTERNAL_REQUIRED CSFPR-RTDETR: missing $weight or $data"
    record "P1" "CSFPR-RTDETR" "RT-DETR / spatial-frequency" "$requested" "" "SKIPPED_EXTERNAL_REQUIRED" "Stage CSFPR repo, VisDrone checkpoint, and local dataset yaml."
    return 0
  fi

  log "QUEUED_RELATED_WORK CSFPR-RTDETR selected_model=$weight"
  record "P1" "CSFPR-RTDETR" "RT-DETR / spatial-frequency" "$requested" "$weight" "QUEUED_RELATED_WORK" "UAV-specific RT-DETR-style model with staged VisDrone checkpoint."
  if [[ "$RUN_TRAINING" != "1" ]]; then
    log "RUN_TRAINING=0, not launching CSFPR-RTDETR."
    return 0
  fi

  GPU="${RELATED_WORK_GPU:-0}" \
  CONDA_ENV="$CONDA_ENV" \
  IMGSZ="${CSFPR_IMGSZ:-1280}" \
  BATCH="${CSFPR_BATCH:-1}" \
  LOG_DIR="$LOG_DIR" \
  PROJECT="$PROJECT" \
  bash scripts/ubuntu/run_csfpr_rtdetr_eval.sh
}

run_leaf_yolo() {
  local requested="external/LEAF-YOLO/cfg/LEAF-YOLO/leaf-sizen/weights/best.pt,external/LEAF-YOLO/cfg/LEAF-YOLO/leaf-sizes/weights/best.pt"
  local nano_weight="external/LEAF-YOLO/cfg/LEAF-YOLO/leaf-sizen/weights/best.pt"
  local small_weight="external/LEAF-YOLO/cfg/LEAF-YOLO/leaf-sizes/weights/best.pt"
  local data="external/LEAF-YOLO/data/visdrone_local.yaml"

  log "Checking GitHub-backed candidate: LEAF-YOLO (P1)"
  if [[ ! -f "$nano_weight" || ! -f "$small_weight" || ! -f "$data" ]]; then
    log "ADAPTER_REQUIRED_GITHUB_AVAILABLE LEAF-YOLO: missing local weights or dataset yaml."
    record "P1" "LEAF-YOLO" "YOLOv7 / lightweight UAV" "$requested" "" "ADAPTER_REQUIRED_GITHUB_AVAILABLE" "GitHub-backed lightweight UAV detector; stage weights/data yaml before evaluation."
    return 0
  fi

  log "QUEUED_RELATED_WORK LEAF-YOLO selected_model=$nano_weight;$small_weight"
  record "P1" "LEAF-YOLO" "YOLOv7 / lightweight UAV" "$requested" "$nano_weight;$small_weight" "QUEUED_RELATED_WORK" "GitHub-backed lightweight UAV detector with staged LEAF-YOLO-N and LEAF-YOLO weights."
  if [[ "$RUN_TRAINING" != "1" ]]; then
    log "RUN_TRAINING=0, not launching LEAF-YOLO."
    return 0
  fi

  GPU="${RELATED_WORK_GPU:-1}" \
  CONDA_ENV="$CONDA_ENV" \
  IMGSZ="${LEAF_IMGSZ:-1280}" \
  BATCH="${LEAF_BATCH:-4}" \
  LOG_DIR="$LOG_DIR" \
  PROJECT="$PROJECT/leaf_yolo" \
  bash scripts/ubuntu/run_leaf_yolo_eval.sh
}

log "Related-work detector queue started"
log "Purpose: add runnable related-work detector baselines from the paper survey without blocking proposed-model search."
log "Seeds=$SEEDS epochs=$EPOCHS patience=$PATIENCE imgsz=$IMGSZ batch=$BATCH min_related_work_targets=$MIN_RELATED_WORK_TARGETS"

wait_for_session "$WAIT_FOR_SESSION"
wait_for_sessions "$WAIT_FOR_SESSIONS"
run_csfpr_rtdetr
if [[ "$ALLOW_INTERNAL_LEAF" == "1" ]]; then
  run_leaf_yolo
else
  record_policy_only \
    "internal" \
    "LEAF-YOLO" \
    "YOLOv7 / lightweight UAV" \
    "external/LEAF-YOLO/cfg/LEAF-YOLO/leaf-sizen/weights/best.pt,external/LEAF-YOLO/cfg/LEAF-YOLO/leaf-sizes/weights/best.pt" \
    "INTERNAL_ONLY_EXCLUDED" \
    "Excluded by default because the user requested LEAF-YOLO not be used as a paper-facing comparison row."
fi

run_candidate \
  "P1" \
  "SFFEF-YOLO" \
  "YOLOv8 / tiny-head UAV" \
  "weights/sffef-yolo.pt,sffef-yolo.pt,external/SFFEF-YOLO/weights/sffef-yolo.pt,external/SFFEF-YOLO/runs/train/exp/weights/best.pt" \
  "Same-dataset UAV detector on VisDrone2019-DET, UAVDT, and TinyPerson; run only if a compatible checkpoint/config is staged."

run_candidate \
  "P1" \
  "LSOD-YOLO" \
  "YOLOv8 / lightweight small-object" \
  "weights/lsod-yolo.pt,lsod-yolo.pt,external/LSOD-YOLO/weights/lsod-yolo.pt,external/LSOD-YOLO/runs/train/exp/weights/best.pt" \
  "Same-dataset lightweight detector on VisDrone2019, TinyPerson, LEVIR-Ship, and UAVDT; run only if a compatible checkpoint/config is staged."

run_candidate \
  "P1" \
  "HF-D-FINE" \
  "D-FINE / high-resolution tiny-object" \
  "weights/hf-d-fine.pt,hf-d-fine.pt,external/HF-D-FINE/weights/hf-d-fine.pt,external/HF-D-FINE/runs/train/exp/weights/best.pt" \
  "Same-dataset non-YOLO target on VisDrone, AI-TOD, and UAVDT; run only after a compatible D-FINE adapter/checkpoint is staged."

run_candidate \
  "P1" \
  "UAVDet" \
  "CNN-Mamba / efficient UAV" \
  "weights/uavdet.pt,uavdet.pt,external/UAVDet/weights/uavdet.pt,external/UAVDet/runs/train/exp/weights/best.pt" \
  "Same-dataset CNN-Mamba target on VisDrone, UAVDT, and DroneVehicle; run only if modality and adapter assumptions are fair."

run_github_candidate \
  "P1" \
  "DR-YOLO" \
  "YOLOv7 / drone small-object" \
  "weights/dr-yolo.pt,external/DR-YOLO/weights/dr-yolo.pt,external/DR-YOLO/runs/train/exp/weights/best.pt" \
  "external/DR-YOLO" \
  "GitHub-backed drone small-object detector; run after staging code, weights, and YOLOv7 adapter."

run_github_candidate \
  "P2" \
  "SOD-YOLO" \
  "UAV YOLO / release pending" \
  "weights/sod-yolo.pt,external/SOD-YOLO/sod-yolo.pt,external/SOD-YOLO/weights/sod-yolo.pt" \
  "external/SOD-YOLO" \
  "GitHub page exists, but code/weights may be release-pending; pass full reproduction unless runnable assets appear."

run_github_candidate \
  "P2" \
  "UAVD-Mamba" \
  "Mamba / multimodal UAV" \
  "weights/uavd-mamba.pt,external/UAVD-Mamba/weights/uavd-mamba.pt" \
  "external/UAVD-Mamba" \
  "GitHub-backed Mamba detector; only fair if modality/input adapter can match our VisDrone protocol."

run_github_candidate \
  "P2" \
  "RF-DETR-B" \
  "RF-DETR / generic transformer" \
  "weights/rf-detr-b.pt,external/rf-detr/weights/rf-detr-b.pt,external/RF-DETR/weights/rf-detr-b.pt" \
  "external/rf-detr" \
  "GitHub-backed generic detector sanity check; lower priority than UAV-specific candidates."

run_candidate \
  "P2" \
  "GCL-YOLO" \
  "YOLOv5 / lightweight P5-removal" \
  "weights/gcl-yolo.pt,gcl-yolo.pt,external/GCL-YOLO/weights/gcl-yolo.pt,external/GCL-YOLO/runs/train/exp/weights/best.pt" \
  "Backup same-dataset reference on VisDrone-DET2021 and UAVDT; useful if a compatible checkpoint/reproduction is staged."

run_candidate \
  "P2" \
  "SRTSOD-YOLO" \
  "YOLO11 / UAV small-object" \
  "weights/srtsod-yolo.pt,srtsod-yolo.pt,external/SRTSOD-YOLO/weights/srtsod-yolo.pt,external/SRTSOD-YOLO/runs/train/exp/weights/best.pt" \
  "Recent YOLO11 same-dataset reference on VisDrone and UAVDT; run only with staged compatible assets."

run_github_candidate \
  "P2" \
  "YOLO11s-UAV" \
  "YOLO11 / UAV small-object" \
  "weights/yolo11s-uav.pt,yolo11s-uav.pt,external/YOLO11s-UAV/weights/yolo11s-uav.pt,external/YOLO11s-UAV/runs/train/exp/weights/best.pt" \
  "external/YOLO11s-UAV" \
  "Recent YOLO11 same-dataset reference on VisDrone-DET2019, UAVDT-DET, and TinyPerson; public repo exists, but it must include a loadable checkpoint/export or full training adapter before we count it as an executed comparison."

record_policy_only \
  "P1" \
  "LRDS-YOLO" \
  "lightweight UAV YOLO" \
  "weights/lrds-yolo.pt,weights/lrds-yolo.yaml,external/LRDS-YOLO/lrds-yolo.pt" \
  "PASS_NO_PUBLIC_GITHUB" \
  "No staged public GitHub/code path is available now. Keep as cited related work; do not spend full reproduction time."

record_policy_only \
  "P1" \
  "BPD-YOLO" \
  "lightweight UAV YOLO" \
  "weights/bpd-yolo.pt,weights/bpd-yolo.yaml,external/BPD-YOLO/bpd-yolo.pt" \
  "PASS_NO_PUBLIC_GITHUB" \
  "No staged public GitHub/code path is available now. Use only lightweight idea-level ablations if the module is simple."

record_policy_only \
  "P2" \
  "No-code lightweight ideas" \
  "module ablation" \
  "NMS,activation,wavelet,DCT,attention,P2 head" \
  "LIGHTWEIGHT_ABLATION_ONLY" \
  "Allowed path for no-GitHub papers: test simple transferable ideas inside our proposed YOLO branch, not full model reproduction."

if (( RELATED_WORK_RECORDS_THIS_RUN < MIN_RELATED_WORK_TARGETS )); then
  log "WARN: related-work target count below requested minimum: recorded=$RELATED_WORK_RECORDS_THIS_RUN required=$MIN_RELATED_WORK_TARGETS"
else
  log "Related-work target count satisfied: recorded=$RELATED_WORK_RECORDS_THIS_RUN required=$MIN_RELATED_WORK_TARGETS"
fi

if (( RELATED_WORK_RUNNABLE_OR_ADAPTER_THIS_RUN < MIN_RELATED_WORK_TARGETS )); then
  log "WARN: fewer than $MIN_RELATED_WORK_TARGETS related-work candidates are runnable or adapter-staged today: runnable_or_adapter=$RELATED_WORK_RUNNABLE_OR_ADAPTER_THIS_RUN"
else
  log "Runnable/adapter related-work candidate count satisfied: runnable_or_adapter=$RELATED_WORK_RUNNABLE_OR_ADAPTER_THIS_RUN required=$MIN_RELATED_WORK_TARGETS"
fi

log "Related-work detector queue finished"
log "Queue CSV: $QUEUE_CSV"
