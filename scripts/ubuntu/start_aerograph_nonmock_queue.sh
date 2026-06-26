#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT=${REPO_ROOT:-/home/oem/projects/multi-uav-marine-city}
SESSION=${SESSION:-aerograph-nonmock-49}
LOG_DIR=${LOG_DIR:-outputs/logs/aerograph_nonmock}
mkdir -p "$REPO_ROOT/$LOG_DIR"

PROVIDER=${AEROGRAPH_PROVIDER:-openai}
if [[ "$PROVIDER" == "openai" && -z "${OPENAI_API_KEY:-}" && -z "${AEROGRAPH_ENV_FILE:-}" ]]; then
  echo "[AeroGraph] OPENAI_API_KEY is not set. Export it or pass AEROGRAPH_ENV_FILE before starting tmux." >&2
  exit 2
fi

TEMP_ENV_FILE=""
ENV_FILE=${AEROGRAPH_ENV_FILE:-}
if [[ -z "$ENV_FILE" ]]; then
  TEMP_ENV_FILE=$(mktemp "/tmp/aerograph_nonmock_${SESSION}.XXXXXX.env")
  chmod 600 "$TEMP_ENV_FILE"
  {
    printf 'export AEROGRAPH_PROVIDER=%q\n' "$PROVIDER"
    printf 'export AEROGRAPH_OPENAI_MODEL=%q\n' "${AEROGRAPH_OPENAI_MODEL:-gpt-5.1}"
    printf 'export AEROGRAPH_SLEEP_SEC=%q\n' "${AEROGRAPH_SLEEP_SEC:-1.0}"
    printf 'export AEROGRAPH_CHECKPOINT_EVERY=%q\n' "${AEROGRAPH_CHECKPOINT_EVERY:-1}"
    printf 'export AEROGRAPH_TIMEOUT=%q\n' "${AEROGRAPH_TIMEOUT:-180}"
    if [[ -n "${AEROGRAPH_OUT_DIR:-}" ]]; then
      printf 'export AEROGRAPH_OUT_DIR=%q\n' "$AEROGRAPH_OUT_DIR"
    fi
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
      printf 'export OPENAI_API_KEY=%q\n' "$OPENAI_API_KEY"
    fi
    if [[ -n "${AEROGRAPH_COMMAND:-}" ]]; then
      printf 'export AEROGRAPH_COMMAND=%q\n' "$AEROGRAPH_COMMAND"
    fi
  } > "$TEMP_ENV_FILE"
  ENV_FILE="$TEMP_ENV_FILE"
fi

tmux new-session -d -s "$SESSION" -n aerograph "cd '$REPO_ROOT' && \
  trap 'rm -f \"$TEMP_ENV_FILE\"' EXIT && \
  source '$ENV_FILE' && \
  bash scripts/ubuntu/run_aerograph_nonmock_queue.sh 2>&1 | tee '$LOG_DIR/queue.log'"

echo "[AeroGraph] started tmux session: $SESSION"
echo "[AeroGraph] log: $REPO_ROOT/$LOG_DIR/queue.log"
echo "[AeroGraph] attach: tmux attach -t $SESSION"
