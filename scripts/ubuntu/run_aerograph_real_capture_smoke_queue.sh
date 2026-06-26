#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT=${REPO_ROOT:-/home/oem/projects/multi-uav-marine-city}
cd "$REPO_ROOT"

PROVIDER=${AEROGRAPH_PROVIDER:-openai}
OPENAI_MODEL=${AEROGRAPH_OPENAI_MODEL:-gpt-5.1}
PROMPT_PACK=${AEROGRAPH_PROMPT_PACK:-outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl}
SLEEP_SEC=${AEROGRAPH_SLEEP_SEC:-1.0}
CHECKPOINT_EVERY=${AEROGRAPH_CHECKPOINT_EVERY:-1}
TIMEOUT=${AEROGRAPH_TIMEOUT:-180}

case "$PROVIDER" in
  openai)
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
      echo "[AeroGraph real-capture smoke] OPENAI_API_KEY is not set." >&2
      exit 2
    fi
    OUT_DIR=${AEROGRAPH_OUT_DIR:-outputs/reasoning/aerograph_real_capture_eval_openai}
    PROVIDER_ARGS=(--provider openai --openai-model "$OPENAI_MODEL")
    ;;
  command)
    COMMAND=${AEROGRAPH_COMMAND:-}
    if [[ -z "$COMMAND" ]]; then
      echo "[AeroGraph real-capture smoke] AEROGRAPH_COMMAND is not set." >&2
      exit 2
    fi
    OUT_DIR=${AEROGRAPH_OUT_DIR:-outputs/reasoning/aerograph_real_capture_eval_command}
    PROVIDER_ARGS=(--provider command --command "$COMMAND")
    ;;
  *)
    echo "[AeroGraph real-capture smoke] Unsupported AEROGRAPH_PROVIDER='$PROVIDER' (use openai or command)." >&2
    exit 2
    ;;
esac

echo "[AeroGraph real-capture smoke] repo=$REPO_ROOT"
echo "[AeroGraph real-capture smoke] provider=$PROVIDER out=$OUT_DIR prompt_pack=$PROMPT_PACK"

python scripts/build_marinecity_real_capture_aerograph_prompt_pack.py
python scripts/build_aerograph_web_batches.py \
  --prompt-pack outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl \
  --out-dir outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches \
  --archive-dir outputs/reports/archive/aerograph_real_capture_prompt_pack/web_batches \
  --responses outputs/reasoning/aerograph_real_capture_manual_responses.jsonl \
  --raw-output-dir outputs/reasoning/aerograph_real_capture_web_raw_batches \
  --normalized-responses outputs/reasoning/aerograph_real_capture_manual_responses.normalized.jsonl \
  --provider-label "ChatGPT/Codex web real-capture smoke" \
  --import-out-dir outputs/reasoning/aerograph_real_capture_eval_manual_web \
  --promotion-mode smoke
python scripts/build_aerograph_web_collection_packet.py \
  --prompt-pack outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl \
  --web-batch-manifest outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/manifest.json \
  --manual-responses outputs/reasoning/aerograph_real_capture_manual_responses.jsonl \
  --raw-output-dir outputs/reasoning/aerograph_real_capture_web_raw_batches \
  --normalized-responses outputs/reasoning/aerograph_real_capture_manual_responses.normalized.jsonl \
  --provider-label "ChatGPT/Codex web real-capture smoke" \
  --import-out-dir outputs/reasoning/aerograph_real_capture_eval_manual_web \
  --gate-label "23-Prompt Real-Capture Smoke" \
  --promotion-mode smoke \
  --purpose "Purpose: collect compact non-mock AeroGraph responses for the current 23-token real-Cesium detector smoke run before the final 49-prompt paper-table gate." \
  --out-md outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.md \
  --out-csv outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_checklist.csv \
  --out-json outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.json

python scripts/run_aerograph_prompt_pack.py \
  "${PROVIDER_ARGS[@]}" \
  --prompt-pack "$PROMPT_PACK" \
  --out-dir "$OUT_DIR" \
  --resume \
  --retry-unconfigured \
  --checkpoint-every "$CHECKPOINT_EVERY" \
  --sleep-sec "$SLEEP_SEC" \
  --timeout "$TIMEOUT"

python scripts/build_aerograph_real_capture_smoke_status.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/check_external_gate_capabilities.py
python scripts/check_paper_artifact_readiness.py
python scripts/check_latex_patch_integrity.py
python scripts/build_accv_status_snapshot.py
python scripts/build_marinecity_simulation_dashboard.py
PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png

echo "[AeroGraph real-capture smoke] finished. See outputs/reports/live/aerograph_real_capture_nonmock_smoke_status.md"
