# AeroGraph Non-Mock Collection Plan

Updated: 2026-06-26 KST

This runbook is the paper-facing gate for the AeroGraph Reasoner experiment.
Current detector-to-3D-graph smoke outputs are valid integration evidence, but
the final AeroGraph result table must use non-mock LLM/VLM responses.

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
- Current external-provider blocker: no `OPENAI_API_KEY`,
  `AEROGRAPH_COMMAND`, Factory CLI, or local LLM command is configured in the
  active shell.

## Acceptance Criteria

The current Codex-assisted manual review candidate is paper-visible with a
clear caveat. Promote AeroGraph to a final external-provider benchmark only
when all conditions below are true:

1. All 49 current prompts have valid-schema non-mock responses.
2. Each row preserves either `index` or both `scenario_id` and `object_id`.
3. Each response parses to valid AeroGraph JSON with:
   `decision`, `predicted_class`, `confidence`, `evidence_clues`,
   `missing_evidence`, and `recommended_action`.
4. The importer produces a manifest with
   `non_mock_outputs_ready: true`.
5. `scripts/build_aerograph_reasoner_table.py` promotes that manifest and
   rewrites `paper/tables/aerograph_reasoner_results_placeholder.tex` from a
   complete non-mock run.
6. The status dashboard shows `49/49` valid-schema coverage for the selected
   final provider manifest.

## Option A: Factory / ChatGPT Web

Paste each batch file into the web model and collect JSONL output lines into:

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
  --provider-label "Factory/ChatGPT web" \
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
SESSION=aerograph-nonmock-49 \
bash scripts/ubuntu/start_aerograph_nonmock_queue.sh
```

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
SESSION=aerograph-nonmock-49 \
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

## Option C: Local / Factory Command Provider

Use this when a CLI reads the prompt from stdin and returns only AeroGraph JSON.

Queue wrapper:

```bash
AEROGRAPH_PROVIDER=command \
AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' \
SESSION=aerograph-nonmock-49-command \
bash scripts/ubuntu/start_aerograph_nonmock_queue.sh
```

Direct command:

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' \
python scripts/run_aerograph_prompt_pack.py \
  --provider command \
  --command "$AEROGRAPH_COMMAND" \
  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_factory \
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
> 49-prompt AeroGraph candidate table is available. Final GPT/Factory/local
> provider replication remains pending.

After the criteria pass, report the non-mock table and cite the provider/model
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
- `paper/tables/aerograph_reasoner_results_placeholder.tex` remains pending.
