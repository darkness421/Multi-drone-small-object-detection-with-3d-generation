#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
POLL_SECONDS=${POLL_SECONDS:-300}
SEEDS=${SEEDS:-42,123,2026}
ABLATION=${ABLATION:-p2p4_balanced_selfattn_only}
LOG_DIR=${LOG_DIR:-outputs/logs/server_yolov11_p2p4_balanced}
QUEUE_LOG=${QUEUE_LOG:-outputs/logs/final_p2p4_selfattnfr_ablation_queue/queue.log}
PROJECT=${PROJECT:-outputs/detectors/server_yolov11_p2p4_balanced}
RESULTS_CSV=${RESULTS_CSV:-outputs/experiments/final_p2p4_selfattnfr_ablation_results.csv}
SUMMARY_CSV=${SUMMARY_CSV:-outputs/experiments/final_p2p4_selfattnfr_ablation_summary.csv}
PVALUES_CSV=${PVALUES_CSV:-outputs/experiments/final_p2p4_selfattnfr_ablation_pvalues.csv}
DASHBOARD=${DASHBOARD:-outputs/reports/live/final_p2p4_selfattnfr_ablation_dashboard.png}
STAGE_GATE_JSON=${STAGE_GATE_JSON:-outputs/experiments/final_p2p4_selfattnfr_ablation_stage_gate.json}
STAGE_GATE_MD=${STAGE_GATE_MD:-outputs/experiments/final_p2p4_selfattnfr_ablation_stage_gate.md}
REPORT_DIR=${REPORT_DIR:-outputs/reports/final_p2p4_selfattnfr_ablation_queue}
MARKER=${MARKER:-QUEUE_FINISHED final P2P4-SelfAttnFR ablation}

mkdir -p "$(dirname "$QUEUE_LOG")" "$REPORT_DIR" "$(dirname "$DASHBOARD")"

log() {
  echo "[$(date -Is)] $*" | tee -a "$QUEUE_LOG"
}

latest_status_after_last_start() {
  local log_file="$1"
  awk '
    /Starting balanced P2 job/ { status="" }
    /TRAIN_OK/ { status="ok" }
    /TRAIN_FAILED/ { status="failed" }
    END { print status }
  ' "$log_file"
}

log_file_for_seed() {
  local seed="$1"
  printf "%s/proposed_%s_yolo11l_visdrone_yolov11_p2_balanced_seed%s.log" "$LOG_DIR" "$ABLATION" "$seed"
}

wait_for_seed() {
  local seed="$1"
  local log_file
  local status
  log_file=$(log_file_for_seed "$seed")

  while true; do
    if [[ ! -f "$log_file" ]]; then
      log "Waiting for $ABLATION seed=$seed log: $log_file"
      sleep "$POLL_SECONDS"
      continue
    fi

    status=$(latest_status_after_last_start "$log_file")
    case "$status" in
      ok)
        log "Confirmed TRAIN_OK for $ABLATION seed=$seed"
        return 0
        ;;
      failed)
        log "BLOCKED: latest run failed for $ABLATION seed=$seed. Not emitting final 2D marker."
        return 1
        ;;
      *)
        log "Waiting for TRAIN_OK marker: $ABLATION seed=$seed"
        sleep "$POLL_SECONDS"
        ;;
    esac
  done
}

log "Manual finalizer requested for $ABLATION seeds=$SEEDS"

IFS=',' read -r -a seed_items <<< "$SEEDS"
for seed in "${seed_items[@]}"; do
  seed=${seed//[[:space:]]/}
  [[ -z "$seed" ]] && continue
  wait_for_seed "$seed"
done

log "All $ABLATION seed runs are TRAIN_OK; collecting final ablation results."
DETECTOR_ROOTS="outputs/detectors/server_baselines,$PROJECT" \
RESULTS_CSV="$RESULTS_CSV" \
SUMMARY_CSV="$SUMMARY_CSV" \
PVALUES_CSV="$PVALUES_CSV" \
DASHBOARD="$DASHBOARD" \
STAGE_GATE_JSON="$STAGE_GATE_JSON" \
STAGE_GATE_MD="$STAGE_GATE_MD" \
REPORT_DIR="$REPORT_DIR" \
CONDA_ENV="$CONDA_ENV" \
bash scripts/ubuntu/collect_server_results.sh "outputs/detectors/server_baselines,$PROJECT" 2>&1 | tee -a "$QUEUE_LOG" || \
  log "WARN: final ablation result collection returned non-zero after writing available outputs"

log "$MARKER"
log "Related-work 1280 queue can now proceed."
