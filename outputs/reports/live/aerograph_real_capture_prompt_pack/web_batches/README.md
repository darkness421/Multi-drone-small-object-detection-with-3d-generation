# AeroGraph Web Batch Index

Use these batches when no CLI/API provider is configured. Paste one batch
file into Factory/ChatGPT/web LLM, collect JSONL output, and append it to:

```text
outputs/reasoning/aerograph_real_capture_manual_responses.jsonl
```

The active prompt pack has 23 prompts across 3 batches.

| Batch | Items | Count | Scenario Counts | File |
| ---: | --- | ---: | --- | --- |
| 1 | 1-10 | 10 | S0:7, S1:3 | `outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md` |
| 2 | 11-20 | 10 | S1:5, S2:5 | `outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_02_011-020.md` |
| 3 | 21-23 | 3 | S2:3 | `outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_03_021-023.md` |

## Required Response Shape

Return JSONL only, one object per prompt item:

```json
{
  "index": 1,
  "scenario_id": "S0",
  "object_id": "example_object",
  "response_text": {
    "decision": "verified|rejected|uncertain",
    "predicted_class": "string",
    "confidence": 0.0,
    "evidence_clues": [],
    "missing_evidence": "string",
    "recommended_action": "string"
  }
}
```

The `response_text` value may be either a JSON object as above or a
JSON-encoded string containing the same object. The paper gate counts
only rows that parse successfully and pass the required-key schema.

Common failure cases rejected by the checker:

- prose or markdown fences around the JSONL output
- missing `index`, or missing both `scenario_id` and `object_id`
- `decision` outside `verified`, `rejected`, or `uncertain`
- `confidence` outside the `[0, 1]` range
- missing `evidence_clues`, `missing_evidence`, or `recommended_action`

## Optional Raw Output Normalizer

If the web model returns markdown fences, a JSON array, or prose around
the JSONL, save that raw text first, then normalize one file, multiple
files, a directory, or a glob:

```bash
python scripts/normalize_aerograph_web_responses.py \
  --input outputs/reasoning/aerograph_real_capture_web_raw_batches/ \
  --out outputs/reasoning/aerograph_real_capture_manual_responses.normalized.jsonl \
  --append-to outputs/reasoning/aerograph_real_capture_manual_responses.jsonl
```

## Import Commands

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
python scripts/build_aerograph_web_collection_packet.py --prompt-pack outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl --web-batch-manifest outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/manifest.json --manual-responses outputs/reasoning/aerograph_real_capture_manual_responses.jsonl --raw-output-dir outputs/reasoning/aerograph_real_capture_web_raw_batches --normalized-responses outputs/reasoning/aerograph_real_capture_manual_responses.normalized.jsonl --provider-label 'Factory/ChatGPT web real-capture smoke' --import-out-dir outputs/reasoning/aerograph_real_capture_eval_manual_web --gate-label '23-Prompt Real-Capture Smoke' --promotion-mode smoke --purpose 'Purpose: collect compact non-mock AeroGraph responses for the current 23-token real-Cesium detector smoke run. This validates provider behavior on current captures before the final 49-prompt paper-table gate.' --out-md outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.md --out-csv outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_checklist.csv --out-json outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.json
python scripts/import_aerograph_manual_responses.py --prompt-pack outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl --responses outputs/reasoning/aerograph_real_capture_manual_responses.jsonl --provider-label "Factory/ChatGPT web real-capture smoke" --out-dir outputs/reasoning/aerograph_real_capture_eval_manual_web
# Compact smoke only: inspect the manifest before any paper-table promotion.
cat outputs/reasoning/aerograph_real_capture_eval_manual_web/manifest.json
```
