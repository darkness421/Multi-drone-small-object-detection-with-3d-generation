# AeroGraph Web Batch Index

Use these batches when no CLI/API provider is configured. Paste one batch
file into Factory/ChatGPT/web LLM, collect JSONL output, and append it to:

```text
outputs/reasoning/aerograph_manual_responses.jsonl
```

The active prompt pack has 49 prompts across 5 batches.

| Batch | Items | Count | Scenario Counts | File |
| ---: | --- | ---: | --- | --- |
| 1 | 1-10 | 10 | S0:10 | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md` |
| 2 | 11-20 | 10 | S0:3, S1:7 | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_02_011-020.md` |
| 3 | 21-30 | 10 | S1:10 | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_03_021-030.md` |
| 4 | 31-40 | 10 | S2:10 | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_04_031-040.md` |
| 5 | 41-49 | 9 | S2:9 | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_05_041-049.md` |

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
  --input outputs/reasoning/aerograph_web_raw_batches/ \
  --out outputs/reasoning/aerograph_manual_responses.normalized.jsonl \
  --append-to outputs/reasoning/aerograph_manual_responses.jsonl
```

## Import Commands

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
python scripts/build_aerograph_web_collection_packet.py
python scripts/import_aerograph_manual_responses.py --prompt-pack outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl --responses outputs/reasoning/aerograph_manual_responses.jsonl --provider-label "Factory/ChatGPT web" --out-dir outputs/reasoning/aerograph_prompt_pack_eval_manual_web
python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/check_paper_artifact_readiness.py
python scripts/check_latex_patch_integrity.py
PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png
python scripts/build_accv_status_snapshot.py
```
