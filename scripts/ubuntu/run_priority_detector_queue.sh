#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
LOG_DIR=${LOG_DIR:-outputs/logs/priority_detector_queue}
STATE_DIR=${STATE_DIR:-outputs/experiments/priority_detector_queue}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/priority_detector_queue_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/priority_detector_queue_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/priority_detector_queue_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/priority_detector_queue_dashboard.png}
REPORT_DIR=${REPORT_DIR:-outputs/reports/priority_detector_queue}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/priority_detector_queue_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/priority_detector_queue_stage_gate.md}
STRICT_AP_TARGET=${STRICT_AP_TARGET:-0.3835}
BASELINE_PARAMS=${BASELINE_PARAMS:-25318190}
BASELINE_PARAMS_M=${BASELINE_PARAMS_M:-25.32}
IMG_SIZE=${IMG_SIZE:-1280}
BATCH=${BATCH:-4}
EPOCHS=${EPOCHS:-100}
PATIENCE=${PATIENCE:-5}
SEED_MAIN=${SEED_MAIN:-123}
CONFIRM_SEEDS=${CONFIRM_SEEDS:-42,2026}
CURRENT_SESSIONS=${CURRENT_SESSIONS:-compact-gpu0-p2p4-dynp2,compact-gpu1-p2p4-dynsmall}
RUN_TRADEOFF_CONFIRM=${RUN_TRADEOFF_CONFIRM:-1}
FINAL_TRADEOFF_ABLATION=${FINAL_TRADEOFF_ABLATION:-p2p4_balanced_selfattn_tiny_frelu}
FINAL_TRADEOFF_METHOD=${FINAL_TRADEOFF_METHOD:-P2P4-SelfAttnFR}
RUN_YOLO_FAMILY_SWEEP=${RUN_YOLO_FAMILY_SWEEP:-1}
YOLO_FAMILY_SEEDS=${YOLO_FAMILY_SEEDS:-42,123,2026}
YOLO_FAMILY_IMGSZ=${YOLO_FAMILY_IMGSZ:-1280}
YOLO_FAMILY_GPU_LIST=${YOLO_FAMILY_GPU_LIST:-0,1}

mkdir -p "$LOG_DIR" "$STATE_DIR" "$REPORT_DIR"
QUEUE_LOG="$LOG_DIR/queue.log"
DECISION_TSV="$STATE_DIR/decisions.tsv"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

init_state() {
  if [[ ! -f "$DECISION_TSV" ]]; then
    printf "created_at\tstage\tdecision\tdetail\n" > "$DECISION_TSV"
  fi
}

record_decision() {
  local stage="$1"
  local decision="$2"
  local detail="$3"
  printf "%s\t%s\t%s\t%s\n" "$(date -Is)" "$stage" "$decision" "$detail" >> "$DECISION_TSV"
}

session_exists() {
  tmux has-session -t "$1" 2>/dev/null
}

session_finished() {
  local session="$1"
  local text
  text=$(tmux capture-pane -pt "$session:0" -S -80 2>/dev/null || true)
  grep -Eq "(TRAIN_OK|TRAIN_FAILED|Balanced P2 job finished|P2-FR module lane finished|NMS sweep] finished)" <<< "$text"
}

wait_for_session() {
  local session="$1"
  [[ -z "$session" ]] && return 0
  while session_exists "$session"; do
    if session_finished "$session"; then
      log "Session has terminal marker and is treated as complete: $session"
      return 0
    fi
    log "Waiting for session: $session"
    sleep 300
  done
  log "Session cleared: $session"
}

wait_for_sessions_csv() {
  local sessions_csv="$1"
  local session
  IFS=',' read -r -a sessions <<< "$sessions_csv"
  for session in "${sessions[@]}"; do
    session=${session//[[:space:]]/}
    wait_for_session "$session"
  done
}

detector_roots() {
  local roots=(
    "outputs/detectors/server_yolov11_p2p4_balanced"
    "outputs/detectors/server_yolov11_p2_module_search"
    "outputs/detectors/server_yolov11_p2_module_nms055"
    "outputs/detectors/server_yolov11_p2_compact_ideas"
    "outputs/detectors/server_yolov11_p2_balanced_v2"
    "outputs/detectors/server_yolov11_p2_balanced_v3"
    "outputs/detectors/server_yolov11_p2_compression"
    "outputs/detectors/nms_sweep_efficient"
    "outputs/detectors/nms_sweep_accuracy"
  )
  local existing=()
  local root
  for root in "${roots[@]}"; do
    [[ -d "$root" ]] && existing+=("$root")
  done
  local IFS=,
  echo "${existing[*]}"
}

collect_results() {
  local roots
  roots=$(detector_roots)
  log "Collecting detector results from: $roots"
  DETECTOR_ROOTS="$roots" \
  RESULTS_CSV="$RESULTS_CSV" \
  SUMMARY_CSV="$SUMMARY_CSV" \
  PVALUES_CSV="$PVALUES_CSV" \
  DASHBOARD="$DASHBOARD" \
  STAGE_GATE_JSON="$STAGE_GATE_JSON" \
  STAGE_GATE_MD="$STAGE_GATE_MD" \
  REPORT_DIR="$REPORT_DIR" \
  PROPOSED_GATE_JSON="$STATE_DIR/proposed_overwhelm_gate.json" \
  PROPOSED_GATE_MD="$STATE_DIR/proposed_overwhelm_gate.md" \
  CONDA_ENV="$CONDA_ENV" \
  bash scripts/ubuntu/collect_server_results.sh "$roots" 2>&1 | tee -a "$QUEUE_LOG" || {
    log "WARN: full report collection returned non-zero; continuing with available results CSV for gate decisions."
  }
}

strict_candidate_line() {
  RESULT_PATH="$RESULTS_CSV" \
  STRICT_AP_TARGET="$STRICT_AP_TARGET" \
  BASELINE_PARAMS="$BASELINE_PARAMS" \
  python - <<'PY'
import csv
import os
from pathlib import Path

path = Path(os.environ["RESULT_PATH"])
target_ap = float(os.environ["STRICT_AP_TARGET"])
max_params = float(os.environ["BASELINE_PARAMS"])

def f(value):
    try:
        if value in (None, "", "nan", "NaN"):
            return None
        return float(value)
    except Exception:
        return None

if not path.exists():
    raise SystemExit(1)

rows = []
with path.open(encoding="utf-8-sig", newline="") as handle:
    for row in csv.DictReader(handle):
        method = row.get("method", "")
        ablation = row.get("ablation", "")
        proposed = row.get("is_proposed", "").lower() == "true"
        if not proposed and "Proposed" not in method:
            continue
        ap = f(row.get("best_AP"))
        params = f(row.get("Params"))
        if ap is None or params is None:
            continue
        if ap > target_ap and params < max_params:
            rows.append((ap, f(row.get("best_AP50")) or -1, params, ablation, method))

if not rows:
    raise SystemExit(1)

ap, ap50, params, ablation, method = max(rows, key=lambda item: (item[0], item[1], -item[2]))
print(f"{ablation}\t{method}\t{ap:.6f}\t{ap50:.6f}\t{params:.0f}")
PY
}

best_candidate_line() {
  RESULT_PATH="$RESULTS_CSV" python - <<'PY'
import csv
import os
from pathlib import Path

path = Path(os.environ["RESULT_PATH"])

def f(value):
    try:
        if value in (None, "", "nan", "NaN"):
            return None
        return float(value)
    except Exception:
        return None

rows = []
if path.exists():
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            method = row.get("method", "")
            if row.get("is_proposed", "").lower() != "true" and "Proposed" not in method:
                continue
            ap = f(row.get("best_AP"))
            if ap is None:
                continue
            ap50 = f(row.get("best_AP50")) or -1
            params = f(row.get("Params"))
            params_for_sort = params if params is not None else 10**12
            rows.append((ap, ap50, params_for_sort, row.get("ablation", ""), method))

if not rows:
    raise SystemExit(1)

ap, ap50, params, ablation, method = max(rows, key=lambda item: (item[0], item[1], -item[2]))
params_text = "NA" if params >= 10**12 else f"{params:.0f}"
print(f"{ablation}\t{method}\t{ap:.6f}\t{ap50:.6f}\t{params_text}")
PY
}

best_under_param_candidate_line() {
  RESULT_PATH="$RESULTS_CSV" \
  BASELINE_PARAMS="$BASELINE_PARAMS" \
  PREFERRED_ABLATION="$FINAL_TRADEOFF_ABLATION" \
  PREFERRED_METHOD="$FINAL_TRADEOFF_METHOD" \
  python - <<'PY'
import csv
import os
from pathlib import Path

path = Path(os.environ["RESULT_PATH"])
max_params = float(os.environ["BASELINE_PARAMS"])
preferred_ablation = os.environ.get("PREFERRED_ABLATION", "")
preferred_method = os.environ.get("PREFERRED_METHOD", "")

def f(value):
    try:
        if value in (None, "", "nan", "NaN"):
            return None
        return float(value)
    except Exception:
        return None

rows = []
if path.exists():
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            method = row.get("method", "")
            ablation = row.get("ablation", "")
            if row.get("is_proposed", "").lower() != "true" and "Proposed" not in method:
                continue
            ap = f(row.get("best_AP"))
            ap50 = f(row.get("best_AP50")) or -1
            params = f(row.get("Params"))
            if ap is None or params is None or params >= max_params:
                continue
            rows.append((ap, ap50, params, ablation, method))

preferred = [row for row in rows if row[3] == preferred_ablation]
if preferred:
    ap, ap50, params, ablation, method = max(preferred, key=lambda item: (item[0], item[1], -item[2]))
elif rows:
    ap, ap50, params, ablation, method = max(rows, key=lambda item: (item[0], item[1], -item[2]))
else:
    ablation = preferred_ablation
    method = preferred_method
    ap = ap50 = params = None

if not ablation:
    raise SystemExit(1)

ap_text = "NA" if ap is None else f"{ap:.6f}"
ap50_text = "NA" if ap50 is None else f"{ap50:.6f}"
params_text = "NA" if params is None else f"{params:.0f}"
print(f"{ablation}\t{method}\t{ap_text}\t{ap50_text}\t{params_text}")
PY
}

completed_best_exists() {
  local project="$1"
  local ablation="$2"
  local seed="$3"
  find "$project" -maxdepth 3 \
    -path "*proposed_${ablation}_yolo11l*seed${seed}/ultralytics/weights/best.pt" \
    -type f -print -quit | grep -q .
}

start_balanced_job() {
  local session="$1"
  local gpu="$2"
  local ablation="$3"
  local seed="$4"
  local project="${5:-outputs/detectors/server_yolov11_p2p4_balanced}"
  local log_dir="${6:-outputs/logs/server_yolov11_p2p4_balanced}"

  if session_exists "$session"; then
    log "Session already exists, not starting duplicate: $session"
    return 0
  fi

  if completed_best_exists "$project" "$ablation" "$seed"; then
    log "Skipping completed job: $ablation seed=$seed project=$project"
    return 0
  fi

  log "Starting job session=$session gpu=$gpu ablation=$ablation seed=$seed"
  tmux new-session -d -s "$session" -n train \
    "cd '$PWD' && TARGET_GPU='$gpu' SEED='$seed' ABLATION='$ablation' PROJECT='$project' LOG_DIR='$log_dir' CONDA_ENV='$CONDA_ENV' EPOCHS='$EPOCHS' PATIENCE='$PATIENCE' BATCH='$BATCH' IMG_SIZE='$IMG_SIZE' GUARD_WAIT_SECONDS=120 MIN_GPU_FREE_GB=8 LOCK_PROPOSED_TO_GPU0=0 bash scripts/ubuntu/start_yolov11_p2_balanced_search.sh; exec bash"
}

confirm_candidate() {
  local ablation="$1"
  local method="$2"
  local decision="${3:-PASS_CONFIRM}"
  local reason="${4:-Strict target passed}"
  log "$reason: $method ($ablation). Starting 3-seed confirmation if missing."
  record_decision "confirmation" "$decision" "$method $ablation"

  local seeds
  IFS=',' read -r -a seeds <<< "$CONFIRM_SEEDS"
  local seed0="${seeds[0]:-42}"
  local seed1="${seeds[1]:-2026}"
  local slug="${ablation//_/-}"

  start_balanced_job "priority-confirm-gpu0-${slug}-s${seed0}" 0 "$ablation" "$seed0"
  start_balanced_job "priority-confirm-gpu1-${slug}-s${seed1}" 1 "$ablation" "$seed1"
  wait_for_sessions_csv "priority-confirm-gpu0-${slug}-s${seed0},priority-confirm-gpu1-${slug}-s${seed1}"
  collect_results
}

confirm_tradeoff_candidate() {
  [[ "$RUN_TRADEOFF_CONFIRM" == "1" ]] || {
    log "Trade-off confirmation disabled by RUN_TRADEOFF_CONFIRM=$RUN_TRADEOFF_CONFIRM"
    return 0
  }

  local tradeoff_line
  if tradeoff_line=$(best_under_param_candidate_line); then
    IFS=$'\t' read -r ablation method ap ap50 params <<< "$tradeoff_line"
    log "Final trade-off confirmation candidate: $method ablation=$ablation AP=$ap AP50=$ap50 Params=$params"
    record_decision "tradeoff_gate" "TRADEOFF_CONFIRM" "$method AP=$ap AP50=$ap50 Params=$params ablation=$ablation"
    confirm_candidate "$ablation" "$method" "TRADEOFF_CONFIRM" "No strict under-param pass; confirming best trade-off candidate"
  else
    log "WARN: no trade-off candidate could be selected for confirmation."
    record_decision "tradeoff_gate" "NO_TRADEOFF_CANDIDATE" "none"
  fi
}

gate_or_continue() {
  local stage="$1"
  local strict_line
  if strict_line=$(strict_candidate_line); then
    IFS=$'\t' read -r ablation method ap ap50 params <<< "$strict_line"
    log "STRICT PASS at $stage: $method ablation=$ablation AP=$ap AP50=$ap50 Params=$params"
    record_decision "$stage" "STRICT_PASS" "$method AP=$ap AP50=$ap50 Params=$params ablation=$ablation"
    confirm_candidate "$ablation" "$method"
    return 0
  fi

  local best_line
  if best_line=$(best_candidate_line); then
    log "No strict pass at $stage. Current best: $best_line"
    record_decision "$stage" "NO_STRICT_PASS" "$best_line"
  else
    log "No strict pass at $stage. No proposed candidate rows found."
    record_decision "$stage" "NO_CANDIDATE" "none"
  fi
  return 1
}

run_selfattn_se_stage() {
  log "Fallback Stage A: P2P4 + SelfAttn/SE + TinyFReLU"
  start_balanced_job "priority-p2p4-selfattn-gpu0-s${SEED_MAIN}" 0 "p2p4_balanced_selfattn_tiny_frelu" "$SEED_MAIN"
  start_balanced_job "priority-p2p4-se-gpu1-s${SEED_MAIN}" 1 "p2p4_balanced_se_tiny_frelu" "$SEED_MAIN"
  wait_for_sessions_csv "priority-p2p4-selfattn-gpu0-s${SEED_MAIN},priority-p2p4-se-gpu1-s${SEED_MAIN}"
  collect_results
}

run_dct_wavelet_nms_stage() {
  log "Fallback Stage B: DCT/Wavelet modules, then NMS sweep."
  if ! completed_best_exists "outputs/detectors/server_yolov11_p2_module_search" "p2_dct_frelu" "$SEED_MAIN"; then
    if session_exists "priority-p2fr-dct-gpu0-s${SEED_MAIN}"; then
      log "Session already exists for P2 DCT module: priority-p2fr-dct-gpu0-s${SEED_MAIN}"
    else
      tmux new-session -d -s "priority-p2fr-dct-gpu0-s${SEED_MAIN}" -n train \
        "cd '$PWD' && TARGET_GPU=0 SEED='$SEED_MAIN' ABLATIONS='p2_dct_frelu' CONDA_ENV='$CONDA_ENV' EPOCHS='$EPOCHS' PATIENCE='$PATIENCE' BATCH='$BATCH' IMGSZ='$IMG_SIZE' bash scripts/ubuntu/run_p2fr_module_lane.sh; exec bash"
    fi
  else
    log "Skipping completed P2 DCT module seed=$SEED_MAIN"
  fi

  if ! completed_best_exists "outputs/detectors/server_yolov11_p2_module_search" "p2_wavelet_frelu" "$SEED_MAIN"; then
    if session_exists "priority-p2fr-wavelet-gpu1-s${SEED_MAIN}"; then
      log "Session already exists for P2 Wavelet module: priority-p2fr-wavelet-gpu1-s${SEED_MAIN}"
    else
      tmux new-session -d -s "priority-p2fr-wavelet-gpu1-s${SEED_MAIN}" -n train \
        "cd '$PWD' && TARGET_GPU=1 SEED='$SEED_MAIN' ABLATIONS='p2_wavelet_frelu' CONDA_ENV='$CONDA_ENV' EPOCHS='$EPOCHS' PATIENCE='$PATIENCE' BATCH='$BATCH' IMGSZ='$IMG_SIZE' bash scripts/ubuntu/run_p2fr_module_lane.sh; exec bash"
    fi
  else
    log "Skipping completed P2 Wavelet module seed=$SEED_MAIN"
  fi

  wait_for_sessions_csv "priority-p2fr-dct-gpu0-s${SEED_MAIN},priority-p2fr-wavelet-gpu1-s${SEED_MAIN}"
  collect_results

  log "Starting NMS sweep for best detector family."
  BASE_SESSION=priority-nms-sweep CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/start_best_detector_nms_sweep.sh 2>&1 | tee -a "$QUEUE_LOG"
  wait_for_sessions_csv "priority-nms-sweep-gpu0-efficient,priority-nms-sweep-gpu1-accuracy"
  collect_results
}

run_related_work() {
  log "Running related-work comparison queue: CSFPR-RTDETR and LEAF-YOLO if staged."
  SEEDS="${RELATED_WORK_SEEDS:-42,123,2026}" \
  EPOCHS=80 \
  PATIENCE=5 \
  IMGSZ="${RELATED_WORK_IMGSZ:-1280}" \
  BATCH=4 \
  RELATED_WORK_GPU=1 \
  CSFPR_IMGSZ="${CSFPR_IMGSZ:-1280}" \
  CSFPR_BATCH=1 \
  RUN_TRAINING=1 \
  CONDA_ENV="$CONDA_ENV" \
  bash scripts/ubuntu/run_related_work_detector_queue.sh 2>&1 | tee -a "$QUEUE_LOG" || log "WARN: related-work queue returned non-zero"

  conda run --no-capture-output -n "$CONDA_ENV" python -m scripts.collect_related_work_detector_results 2>&1 | tee -a "$QUEUE_LOG" || log "WARN: related-work result collection failed"
}

run_yolo_family_sweep() {
  [[ "$RUN_YOLO_FAMILY_SWEEP" == "1" ]] || {
    log "YOLO family scale sweep disabled by RUN_YOLO_FAMILY_SWEEP=$RUN_YOLO_FAMILY_SWEEP"
    return 0
  }

  log "Running YOLO-family scale sweep: nano/small/medium/large groups with seeds=$YOLO_FAMILY_SEEDS imgsz=$YOLO_FAMILY_IMGSZ."
  WAIT_FOR="" \
  SEEDS="$YOLO_FAMILY_SEEDS" \
  IMGSZ="$YOLO_FAMILY_IMGSZ" \
  GPU_LIST="$YOLO_FAMILY_GPU_LIST" \
  CONDA_ENV="$CONDA_ENV" \
  RESTART_VIEWER=0 \
  bash scripts/ubuntu/train_extra_comparison_models_after_session.sh 2>&1 | tee -a "$QUEUE_LOG" || log "WARN: YOLO family scale sweep returned non-zero"
}

main() {
  init_state
  log "Priority detector queue started"
  log "Policy: finish current P2P4 DynFreq jobs -> strict AP/params gate -> confirm or fallback -> related-work comparison."
  record_decision "start" "POLICY" "current=$CURRENT_SESSIONS target AP>$STRICT_AP_TARGET Params<$BASELINE_PARAMS_M M"

  wait_for_sessions_csv "$CURRENT_SESSIONS"
  collect_results
  if gate_or_continue "after_p2p4_dynfreq"; then
    run_yolo_family_sweep
    run_related_work
    log "Priority detector queue finished after strict pass confirmation."
    return 0
  fi

  run_selfattn_se_stage
  if gate_or_continue "after_p2p4_selfattn_se"; then
    run_yolo_family_sweep
    run_related_work
    log "Priority detector queue finished after SelfAttn/SE confirmation."
    return 0
  fi

  run_dct_wavelet_nms_stage
  if gate_or_continue "after_dct_wavelet_nms"; then
    run_yolo_family_sweep
    run_related_work
    log "Priority detector queue finished after DCT/Wavelet/NMS confirmation."
    return 0
  fi

  confirm_tradeoff_candidate
  run_yolo_family_sweep
  run_related_work
  log "Priority detector queue finished without strict under-param pass. Keep best trade-off candidate for paper discussion."
}

main "$@"
