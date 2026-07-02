# AeroGraph Non-Mock Collection Plan

Updated: 2026-06-26 KST

This runbook describes the AeroGraph Reasoner validation workflow. Current
detector-to-3D-graph outputs are valid integration evidence; external LLM/VLM
responses are used only when benchmarking the reasoning layer itself.

## Current State

- Prompt pack: `outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl`
- Web batches: `outputs/reports/live/aerograph_prompt_pack/web_batches/`
- Web batch index: `outputs/reports/live/aerograph_prompt_pack/web_batches/README.md`
- Collection packet: `outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_packet.md`
- Checklist CSV: `outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_checklist.csv`
- Raw web-output drop folder: `outputs/reasoning/aerograph_web_raw_batches/`
- Manual response target: `outputs/reasoning/aerograph_manual_responses.jsonl`
- Current reviewed-candidate coverage: `49/49` via
  `outputs/reasoning/aerograph_prompt_pack_eval_manual_web/manifest.json`
- Current direct manual-response file coverage: `0/49`
- Current real-capture compact smoke pack:
  `outputs/reports/live/aerograph_real_capture_prompt_pack/`
  (`23` prompts, matching the latest 3-scenario x 3-UAV real-Cesium detector
  smoke run). Use this for quick external-provider smoke checks before spending time on
  the full 49-prompt table gate.
- Compact smoke web packet:
  `outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.md`
  with checklist
  `outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_checklist.csv`.
  Save compact raw web answers under
  `outputs/reasoning/aerograph_real_capture_web_raw_batches/` and import them
  into `outputs/reasoning/aerograph_real_capture_manual_responses.jsonl`.
- Current external-provider blocker: no `OPENAI_API_KEY`,
  `AEROGRAPH_COMMAND`, or local model command is configured in the active shell.

## Acceptance Criteria

The current reviewed candidate is available for internal checking. Promote
AeroGraph to an external-provider benchmark only when all conditions below are
true:

1. All 49 current prompts have valid-schema external-provider responses.
2. Each row preserves either `index` or both `scenario_id` and `object_id`.
3. Each response parses to valid AeroGraph JSON with:
   `decision`, `predicted_class`, `confidence`, `evidence_clues`,
   `missing_evidence`, and `recommended_action`.
4. The importer produces a manifest with
   `non_mock_outputs_ready: true`.
5. `scripts/build_aerograph_reasoner_table.py` promotes that manifest and
   rewrites `paper/tables/aerograph_reasoner_external_slot.tex` from a
   complete external-provider run.
6. The status dashboard shows `49/49` valid-schema coverage for the selected
   final provider manifest.

## Manual External-Provider Collection

Run each batch with the selected provider and collect JSONL output lines into:

```text
outputs/reasoning/aerograph_manual_responses.jsonl
```

Batch files:

```text
outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md
outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_02_011-020.md
outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_03_021-030.md
outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_04_031-040.md
outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_05_041-049.md
```

For the shorter current real-capture smoke check, use these three batches
instead and save responses to
`outputs/reasoning/aerograph_real_capture_manual_responses.jsonl`:

```text
outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md
outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_02_011-020.md
outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_03_021-023.md
```

Import the compact smoke responses with:

```bash
python scripts/import_aerograph_manual_responses.py \
  --prompt-pack outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl \
  --responses outputs/reasoning/aerograph_real_capture_manual_responses.jsonl \
  --provider-label "External web LLM real-capture smoke" \
  --out-dir outputs/reasoning/aerograph_real_capture_eval_manual_web
```

This compact run is useful for debugging the provider and wording on current
captures. The final paper table still uses the 49-prompt gate unless we
explicitly switch the paper protocol to the compact 23-prompt smoke setting.

If a provider CLI/API is available, run the compact smoke directly without
touching the final 49-prompt paper-table slot:

```bash
# OpenAI API smoke
OPENAI_API_KEY=... \
AEROGRAPH_PROVIDER=openai \
AEROGRAPH_OPENAI_MODEL=gpt-5.1 \
SESSION=aerograph-real-capture-smoke \
bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh

# local command smoke
AEROGRAPH_PROVIDER=command \
AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' \
SESSION=aerograph-real-capture-smoke-command \
bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh
```

The compact smoke writes:

```text
outputs/reports/live/aerograph_real_capture_nonmock_smoke_status.md
outputs/reasoning/aerograph_real_capture_eval_openai/manifest.json
outputs/reasoning/aerograph_real_capture_eval_command/manifest.json
```

This smoke gate is only a provider-connection and current-capture validation
step. It must not replace the 49-prompt final AeroGraph table unless the paper
protocol is explicitly changed.

Batch progress is tracked in:

```text
outputs/reports/live/aerograph_nonmock_readiness_status.md
```

The readiness report lists each batch as `valid/expected`, so after adding
new JSONL responses you can immediately see which batch still needs work or
which rows failed schema validation.

For a single human-facing handoff file, use:

```text
outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_packet.md
```

If a web model returns JSONL inside markdown fences, as a JSON array, or with
extra prose, save the raw text and normalize one file, multiple files, a
directory, or a glob before import:

```bash
# Save raw answers as:
# outputs/reasoning/aerograph_web_raw_batches/batch_01.md
# ...
# outputs/reasoning/aerograph_web_raw_batches/batch_05.md

python scripts/normalize_aerograph_web_responses.py \
  --input outputs/reasoning/aerograph_web_raw_batches/ \
  --out outputs/reasoning/aerograph_manual_responses.normalized.jsonl \
  --append-to outputs/reasoning/aerograph_manual_responses.jsonl
```

Import and promote:

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
python scripts/build_aerograph_web_collection_packet.py
python scripts/import_aerograph_manual_responses.py \
  --responses outputs/reasoning/aerograph_manual_responses.jsonl \
  --provider-label "External web LLM" \
  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_manual_web
python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/check_paper_artifact_readiness.py
python scripts/check_latex_patch_integrity.py
PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png
python scripts/build_accv_status_snapshot.py
```

## Option B: OpenAI API

Only run this when `OPENAI_API_KEY` is configured in the shell. Choose the model
explicitly through `--openai-model`; do not rely on stale default model names.

Queue wrapper:

```bash
OPENAI_API_KEY=... \
AEROGRAPH_PROVIDER=openai \
AEROGRAPH_OPENAI_MODEL=gpt-5.1 \
SESSION=aerograph-external_provider-49 \
bash scripts/ubuntu/start_aerograph_nonmock_queue.sh
```

Preflight behavior:

- The wrapper refuses to start tmux if `OPENAI_API_KEY` is missing for
  `AEROGRAPH_PROVIDER=openai`.
- The wrapper refuses to start tmux if `AEROGRAPH_COMMAND` is missing for
  `AEROGRAPH_PROVIDER=command` or `AEROGRAPH_PROVIDER=command`.
- If `AEROGRAPH_ENV_FILE` is provided, it must be readable before tmux starts.
  This avoids a silent background session that immediately exits without
  producing external-provider evidence.

Private env-file option, useful when starting from an already-running tmux
server:

```bash
cat > /tmp/aerograph_openai.env <<'EOF'
export OPENAI_API_KEY='...'
export AEROGRAPH_PROVIDER=openai
export AEROGRAPH_OPENAI_MODEL=gpt-5.1
EOF
chmod 600 /tmp/aerograph_openai.env
AEROGRAPH_ENV_FILE=/tmp/aerograph_openai.env \
SESSION=aerograph-external_provider-49 \
bash scripts/ubuntu/start_aerograph_nonmock_queue.sh
```

Direct command:

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
python scripts/run_aerograph_prompt_pack.py \
  --provider openai \
  --openai-model "$AEROGRAPH_OPENAI_MODEL" \
  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_openai \
  --resume \
  --retry-unconfigured \
  --checkpoint-every 1 \
  --sleep-sec 1.0
python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/build_accv_status_snapshot.py
```

The queue wrapper runs the prompt pack, rebuilds the AeroGraph table, refreshes
readiness checks, and updates the live dashboards. It exits without producing
mock evidence if the API key is missing.

## Option C: Local Command Provider

Use this when a CLI reads the prompt from stdin and returns only AeroGraph JSON.

Queue wrapper:

```bash
AEROGRAPH_PROVIDER=command \
AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' \
SESSION=aerograph-external_provider-49-command \
bash scripts/ubuntu/start_aerograph_nonmock_queue.sh
```

For any hosted or local agent exposed through a local CLI, wrap the
provider so the command reads one AeroGraph prompt from `stdin` and returns one
JSON object with the required fields only. Use a private env file when the
command contains credentials, browser profile paths, or machine-local tokens.

Direct command:

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' \
python scripts/run_aerograph_prompt_pack.py \
  --provider command \
  --command "$AEROGRAPH_COMMAND" \
  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_command \
  --resume \
  --retry-unconfigured \
  --checkpoint-every 1
python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/build_accv_status_snapshot.py
```

## Paper Claiming Rule

Until the external-provider acceptance criteria pass, use only this wording:

> AeroGraph prompt pack and import pipeline are ready; current MarineCity
> outputs validate detector-to-evidence-token integration, and a reviewed
> 49-prompt AeroGraph candidate table is available. Final external/local
> provider replication remains pending.

After the criteria pass, report the external-provider table and cite the provider/model
used in the experiment environment section.

## Plumbing Test

The local plumbing test validates the runner/checker/table-builder path without
creating paper evidence:

```bash
bash scripts/ubuntu/run_aerograph_plumbing_test.sh
```

Expected behavior:

- `outputs/reasoning/aerograph_prompt_pack_eval_plumbing_test/manifest.json`
  reports `aerograph_eval_plumbing_test_complete`.
- The same manifest has `paper_claim_allowed: false` and
  `non_mock_outputs_ready: false`.
- `paper/tables/aerograph_reasoner_external_slot.tex` remains conservative until an external-provider run is imported.
