#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-bidaily-publication-update}
START_IN_TMUX=${START_IN_TMUX:-0}
INTERVAL_HOURS=${INTERVAL_HOURS:-48}
RUN_ON_START=${RUN_ON_START:-1}

DO_MAIN_COMMIT=${DO_MAIN_COMMIT:-1}
DO_MAIN_PUSH=${DO_MAIN_PUSH:-1}
DO_OVERLEAF_SYNC=${DO_OVERLEAF_SYNC:-1}
DO_OVERLEAF_COMMIT=${DO_OVERLEAF_COMMIT:-1}
DO_OVERLEAF_PUSH=${DO_OVERLEAF_PUSH:-1}
DO_NOTION_EXPORT=${DO_NOTION_EXPORT:-1}
DO_NOTION_UPDATE=${DO_NOTION_UPDATE:-1}

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*"
}

if [[ "$START_IN_TMUX" == "1" && -z "${TMUX:-}" ]]; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    log "tmux session already exists: $SESSION"
    log "Attach with: tmux attach -t $SESSION"
    exit 0
  fi
  tmux new-session -d -s "$SESSION" \
    "cd '$PWD' && START_IN_TMUX=0 SESSION='$SESSION' INTERVAL_HOURS='$INTERVAL_HOURS' RUN_ON_START='$RUN_ON_START' DO_MAIN_COMMIT='$DO_MAIN_COMMIT' DO_MAIN_PUSH='$DO_MAIN_PUSH' DO_OVERLEAF_SYNC='$DO_OVERLEAF_SYNC' DO_OVERLEAF_COMMIT='$DO_OVERLEAF_COMMIT' DO_OVERLEAF_PUSH='$DO_OVERLEAF_PUSH' DO_NOTION_EXPORT='$DO_NOTION_EXPORT' DO_NOTION_UPDATE='$DO_NOTION_UPDATE' bash scripts/ubuntu/run_bidaily_publication_update.sh"
  log "Started tmux session: $SESSION"
  log "Attach with: tmux attach -t $SESSION"
  exit 0
fi

sleep_seconds=$((INTERVAL_HOURS * 3600))
iteration=0

log "Bi-daily publication loop started."
log "Interval: ${INTERVAL_HOURS}h"
log "Main repo commit/push: ${DO_MAIN_COMMIT}/${DO_MAIN_PUSH}"
log "Overleaf sync/commit/push: ${DO_OVERLEAF_SYNC}/${DO_OVERLEAF_COMMIT}/${DO_OVERLEAF_PUSH}"
log "Notion export/update: ${DO_NOTION_EXPORT}/${DO_NOTION_UPDATE}"

while true; do
  if [[ "$RUN_ON_START" == "1" || "$iteration" -gt 0 ]]; then
    log "Starting publication cycle ${iteration}."
    if DO_MAIN_COMMIT="$DO_MAIN_COMMIT" \
      DO_MAIN_PUSH="$DO_MAIN_PUSH" \
      DO_OVERLEAF_SYNC="$DO_OVERLEAF_SYNC" \
      DO_OVERLEAF_COMMIT="$DO_OVERLEAF_COMMIT" \
      DO_OVERLEAF_PUSH="$DO_OVERLEAF_PUSH" \
      DO_NOTION_EXPORT="$DO_NOTION_EXPORT" \
      DO_NOTION_UPDATE="$DO_NOTION_UPDATE" \
      bash scripts/ubuntu/publish_experiment_update.sh; then
      log "Publication cycle ${iteration} complete."
    else
      log "Publication cycle ${iteration} failed; loop will retry at the next interval."
    fi
  else
    log "RUN_ON_START=0, waiting until the first interval."
  fi

  iteration=$((iteration + 1))
  log "Sleeping for ${INTERVAL_HOURS}h."
  sleep "$sleep_seconds"
done
