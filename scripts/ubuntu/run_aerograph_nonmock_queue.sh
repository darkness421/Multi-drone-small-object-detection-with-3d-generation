#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT=${REPO_ROOT:-/home/oem/projects/multi-uav-marine-city}
cd "$REPO_ROOT"

PROVIDER=${AEROGRAPH_PROVIDER:-openai}
OPENAI_MODEL=${AEROGRAPH_OPENAI_MODEL:-gpt-5.1}
PROMPT_PACK=${AEROGRAPH_PROMPT_PACK:-outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl}
SLEEP_SEC=${AEROGRAPH_SLEEP_SEC:-1.0}
CHECKPOINT_EVERY=${AEROGRAPH_CHECKPOINT_EVERY:-1}
TIMEOUT=${AEROGRAPH_TIMEOUT:-180}

case "$PROVIDER" in
  openai)
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
      echo "[AeroGraph] OPENAI_API_KEY is not set; cannot run non-mock OpenAI provider." >&2
      exit 2
    fi
    OUT_DIR=${AEROGRAPH_OUT_DIR:-outputs/reasoning/aerograph_prompt_pack_eval_openai}
    PROVIDER_ARGS=(--provider openai --openai-model "$OPENAI_MODEL")
    ;;
  command)
    COMMAND=${AEROGRAPH_COMMAND:-}
    if [[ -z "$COMMAND" ]]; then
      echo "[AeroGraph] AEROGRAPH_COMMAND is not set; cannot run command provider." >&2
      exit 2
    fi
    OUT_DIR=${AEROGRAPH_OUT_DIR:-outputs/reasoning/aerograph_prompt_pack_eval_command}
    PROVIDER_ARGS=(--provider command --command "$COMMAND")
    ;;
  *)
    echo "[AeroGraph] Unsupported AEROGRAPH_PROVIDER='$PROVIDER' (use openai or command)." >&2
    exit 2
    ;;
esac

echo "[AeroGraph] repo=$REPO_ROOT"
echo "[AeroGraph] provider=$PROVIDER out=$OUT_DIR prompt_pack=$PROMPT_PACK"

python scripts/build_aerograph_prompt_pack.py
python scripts/build_aerograph_web_batches.py
python scripts/check_aerograph_prompt_pack_integrity.py

python scripts/run_aerograph_prompt_pack.py \
  --provider "${PROVIDER_ARGS[1]}" \
  "${PROVIDER_ARGS[@]:2}" \
  --prompt-pack "$PROMPT_PACK" \
  --out-dir "$OUT_DIR" \
  --resume \
  --retry-unconfigured \
  --checkpoint-every "$CHECKPOINT_EVERY" \
  --sleep-sec "$SLEEP_SEC" \
  --timeout "$TIMEOUT"

python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/check_external_gate_capabilities.py
python scripts/check_paper_artifact_readiness.py
python scripts/check_latex_patch_integrity.py
python scripts/build_accv_status_snapshot.py
python scripts/build_marinecity_simulation_dashboard.py
PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png

echo "[AeroGraph] finished. See outputs/reports/live/aerograph_nonmock_readiness_status.md"
