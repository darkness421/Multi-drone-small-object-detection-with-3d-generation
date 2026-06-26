#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

CONDA_ENV=${CONDA_ENV:-com3d-ace}
ENABLE_REQUIRED_RELATED=${ENABLE_REQUIRED_RELATED:-1}
ENABLE_MARINECITY_VIEWER160=${ENABLE_MARINECITY_VIEWER160:-1}
ENABLE_OPERATOR=${ENABLE_OPERATOR:-1}
LOG_DIR=${LOG_DIR:-outputs/logs/accv_continuous_queue}
SUMMARY="$LOG_DIR/start_summary.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date -Is)] $*" | tee -a "$SUMMARY"
}

log "ACCV continuous queue start requested"
log "CONDA_ENV=$CONDA_ENV"
log "ENABLE_REQUIRED_RELATED=$ENABLE_REQUIRED_RELATED"
log "ENABLE_MARINECITY_VIEWER160=$ENABLE_MARINECITY_VIEWER160"
log "ENABLE_OPERATOR=$ENABLE_OPERATOR"

if [[ "$ENABLE_REQUIRED_RELATED" == "1" ]]; then
  log "Starting/reusing required related-work queue"
  CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/start_required_related_work_models_queue.sh 2>&1 | tee -a "$SUMMARY" || \
    log "WARN required related-work queue start returned non-zero"
fi

if [[ "$ENABLE_MARINECITY_VIEWER160" == "1" ]]; then
  log "Starting/reusing MarineCity viewer160 queue"
  CONDA_ENV="$CONDA_ENV" bash scripts/ubuntu/start_marinecity_viewer160_pipeline_queue.sh 2>&1 | tee -a "$SUMMARY" || \
    log "WARN MarineCity viewer160 queue start returned non-zero"
fi

if [[ "$ENABLE_OPERATOR" == "1" ]]; then
  log "Starting/reusing agentic operator supervisor"
  CONDA_ENV="$CONDA_ENV" \
  ENABLE_OLLAMA_OPERATOR="${ENABLE_OLLAMA_OPERATOR:-0}" \
  ENABLE_OPENAI_ANALYST="${ENABLE_OPENAI_ANALYST:-0}" \
  INTERVAL="${INTERVAL:-300}" \
  bash scripts/ubuntu/start_agentic_operator.sh 2>&1 | tee -a "$SUMMARY" || \
    log "WARN agentic operator start returned non-zero"
fi

log "Current tmux sessions:"
tmux ls 2>/dev/null | tee -a "$SUMMARY" || true
log "Continuous queue handoff complete"

cat <<EOF

Continuous queue is configured.

Primary sessions:
  tmux attach -t required-related-work-models-gpu0
  tmux attach -t marinecity-viewer160-pipeline
  tmux attach -t server-agentic-operator

Live files:
  outputs/reports/live/training_dashboard.png
  outputs/reports/live/marinecity_simulation_dashboard.png
  outputs/experiments/marinecity_viewer160_pipeline_status.md
  outputs/automation/agentic_operator_status.md

OpenAI/ChatGPT:
  Set OPENAI_API_KEY and ENABLE_OPENAI_ANALYST=1 for the optional analyst.
  Set AEROGRAPH_PROVIDER=openai for non-mock AeroGraph runs.
EOF
