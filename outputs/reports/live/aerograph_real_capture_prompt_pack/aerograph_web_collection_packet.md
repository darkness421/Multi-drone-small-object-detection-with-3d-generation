# AeroGraph 49-Prompt Web Collection Packet

Purpose: collect final non-mock AeroGraph Reasoner responses from a selected web LLM provider, then promote them to the paper table only after all rows pass schema validation.

## Current Coverage

- Total prompts: `23`
- Valid schema responses: `0/23`
- Invalid responses: `0`
- Pending responses: `23`
- Checklist CSV: `outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_checklist.csv`

## Batch Files

| Batch | Items | Count | Raw output target | Prompt file |
| ---: | --- | ---: | --- | --- |
| 1 | 1-10 | 10 | `outputs/reasoning/aerograph_real_capture_web_raw_batches/batch_01.md` | `outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md` |
| 2 | 11-20 | 10 | `outputs/reasoning/aerograph_real_capture_web_raw_batches/batch_02.md` | `outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_02_011-020.md` |
| 3 | 21-23 | 3 | `outputs/reasoning/aerograph_real_capture_web_raw_batches/batch_03.md` | `outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/aerograph_web_batch_03_021-023.md` |

## Workflow

1. Paste each batch prompt file into the selected web LLM.
2. Save each raw answer into the matching raw output target above.
3. Normalize and merge all raw outputs:

```bash
python scripts/normalize_aerograph_web_responses.py \
  --input outputs/reasoning/aerograph_real_capture_web_raw_batches/ \
  --out outputs/reasoning/aerograph_real_capture_manual_responses.normalized.jsonl \
  --append-to outputs/reasoning/aerograph_real_capture_manual_responses.jsonl
```

4. Import responses:

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
python scripts/import_aerograph_manual_responses.py \
  --prompt-pack outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl \
  --responses outputs/reasoning/aerograph_real_capture_manual_responses.jsonl \
  --provider-label "External web LLM" \
  --out-dir outputs/reasoning/aerograph_real_capture_eval_manual_web
python scripts/build_aerograph_reasoner_table.py
python scripts/check_aerograph_nonmock_readiness.py
python scripts/check_paper_artifact_readiness.py
python scripts/check_latex_patch_integrity.py
PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png
python scripts/build_accv_status_snapshot.py
```

## Pending Items

| Index | Batch | Scenario | Object | Candidate | Status |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | S0 | `uavmarine_s0_viewer160_session_recapture:uav_01:car:000` | car | pending |
| 2 | 1 | S0 | `uavmarine_s0_viewer160_session_recapture:uav_02:bus:003` | bus | pending |
| 3 | 1 | S0 | `uavmarine_s0_viewer160_session_recapture:uav_02:car:000` | car | pending |
| 4 | 1 | S0 | `uavmarine_s0_viewer160_session_recapture:uav_02:car:001` | car | pending |
| 5 | 1 | S0 | `uavmarine_s0_viewer160_session_recapture:uav_02:car:002` | car | pending |
| 6 | 1 | S0 | `uavmarine_s0_viewer160_session_recapture:uav_02:car:004` | car | pending |
| 7 | 1 | S0 | `uavmarine_s0_viewer160_session_recapture:uav_03:bus:000` | bus | pending |
| 8 | 1 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_01:bus:000` | bus | pending |
| 9 | 1 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_01:car:001` | car | pending |
| 10 | 1 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_02:bus:003` | bus | pending |
| 11 | 2 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_02:car:000` | car | pending |
| 12 | 2 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_02:car:001` | car | pending |
| 13 | 2 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_02:car:002` | car | pending |
| 14 | 2 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_02:car:004` | car | pending |
| 15 | 2 | S1 | `uavmarine_s1_viewer160_session_recapture:uav_03:bus:000` | bus | pending |
| 16 | 2 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_01:bus:000` | bus | pending |
| 17 | 2 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_01:car:001` | car | pending |
| 18 | 2 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_02:bus:004` | bus | pending |
| 19 | 2 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_02:car:000` | car | pending |
| 20 | 2 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_02:car:001` | car | pending |
| 21 | 3 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_02:car:002` | car | pending |
| 22 | 3 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_02:car:003` | car | pending |
| 23 | 3 | S2 | `uavmarine_s2_viewer160_session_recapture:uav_03:bus:000` | bus | pending |
