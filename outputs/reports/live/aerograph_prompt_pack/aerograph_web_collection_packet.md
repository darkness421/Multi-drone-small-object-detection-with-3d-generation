# AeroGraph 49-Prompt Web Collection Packet

Purpose: collect final non-mock AeroGraph Reasoner responses from a web LLM provider, then promote them to the paper table only after all rows pass schema validation.

## Current Coverage

- Total prompts: `49`
- Valid schema responses: `0/49`
- Invalid responses: `0`
- Pending responses: `49`
- Checklist CSV: `outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_checklist.csv`

## Batch Files

| Batch | Items | Count | Raw output target | Prompt file |
| ---: | --- | ---: | --- | --- |
| 1 | 1-10 | 10 | `outputs/reasoning/aerograph_web_raw_batches/batch_01.md` | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md` |
| 2 | 11-20 | 10 | `outputs/reasoning/aerograph_web_raw_batches/batch_02.md` | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_02_011-020.md` |
| 3 | 21-30 | 10 | `outputs/reasoning/aerograph_web_raw_batches/batch_03.md` | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_03_021-030.md` |
| 4 | 31-40 | 10 | `outputs/reasoning/aerograph_web_raw_batches/batch_04.md` | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_04_031-040.md` |
| 5 | 41-49 | 9 | `outputs/reasoning/aerograph_web_raw_batches/batch_05.md` | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_05_041-049.md` |

## Workflow

1. Paste each batch prompt file into the selected web LLM.
2. Save each raw answer into the matching raw output target above.
3. Normalize and merge all raw outputs:

```bash
python scripts/normalize_aerograph_web_responses.py \
  --input outputs/reasoning/aerograph_web_raw_batches/ \
  --out outputs/reasoning/aerograph_manual_responses.normalized.jsonl \
  --append-to outputs/reasoning/aerograph_manual_responses.jsonl
```

4. Import responses:

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
python scripts/import_aerograph_manual_responses.py \
  --prompt-pack outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl \
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

## Pending Items

| Index | Batch | Scenario | Object | Candidate | Status |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | S0 | `uav_01_bus_12_2` | bus | pending |
| 2 | 1 | S0 | `uav_01_bus_9_3` | bus | pending |
| 3 | 1 | S0 | `uav_01_car_6_8` | car | pending |
| 4 | 1 | S0 | `uav_02_bus_0_3` | bus | pending |
| 5 | 1 | S0 | `uav_02_bus_13_3` | bus | pending |
| 6 | 1 | S0 | `uav_02_car_0_3` | car | pending |
| 7 | 1 | S0 | `uav_02_car_0_5` | car | pending |
| 8 | 1 | S0 | `uav_02_car_10_6` | car | pending |
| 9 | 1 | S0 | `uav_02_car_10_7` | car | pending |
| 10 | 1 | S0 | `uav_02_car_1_5` | car | pending |
| 11 | 2 | S0 | `uav_02_car_8_5` | car | pending |
| 12 | 2 | S0 | `uav_02_car_9_8` | car | pending |
| 13 | 2 | S0 | `uav_03_bus_11_2` | bus | pending |
| 14 | 2 | S1 | `uav_01_bus_11_3` | bus | pending |
| 15 | 2 | S1 | `uav_01_car_6_8` | car | pending |
| 16 | 2 | S1 | `uav_01_pedestrian_13_2` | pedestrian | pending |
| 17 | 2 | S1 | `uav_02_bus_0_3` | bus | pending |
| 18 | 2 | S1 | `uav_02_bus_11_4` | bus | pending |
| 19 | 2 | S1 | `uav_02_bus_12_4` | bus | pending |
| 20 | 2 | S1 | `uav_02_bus_5_6` | bus | pending |
| 21 | 3 | S1 | `uav_02_car_0_3` | car | pending |
| 22 | 3 | S1 | `uav_02_car_0_5` | car | pending |
| 23 | 3 | S1 | `uav_02_car_10_6` | car | pending |
| 24 | 3 | S1 | `uav_02_car_10_7` | car | pending |
| 25 | 3 | S1 | `uav_02_car_13_7` | car | pending |
| 26 | 3 | S1 | `uav_02_car_1_5` | car | pending |
| 27 | 3 | S1 | `uav_02_car_8_5` | car | pending |
| 28 | 3 | S1 | `uav_02_car_9_6` | car | pending |
| 29 | 3 | S1 | `uav_02_car_9_8` | car | pending |
| 30 | 3 | S1 | `uav_03_bus_11_3` | bus | pending |
| 31 | 4 | S2 | `uav_01_bus_15_2` | bus | pending |
| 32 | 4 | S2 | `uav_01_car_6_8` | car | pending |
| 33 | 4 | S2 | `uav_01_pedestrian_13_2` | pedestrian | pending |
| 34 | 4 | S2 | `uav_01_pedestrian_14_1` | pedestrian | pending |
| 35 | 4 | S2 | `uav_01_pedestrian_7_3` | pedestrian | pending |
| 36 | 4 | S2 | `uav_02_bus_0_3` | bus | pending |
| 37 | 4 | S2 | `uav_02_bus_15_4` | bus | pending |
| 38 | 4 | S2 | `uav_02_bus_7_6` | bus | pending |
| 39 | 4 | S2 | `uav_02_car_0_3` | car | pending |
| 40 | 4 | S2 | `uav_02_car_0_5` | car | pending |
| 41 | 5 | S2 | `uav_02_car_10_6` | car | pending |
| 42 | 5 | S2 | `uav_02_car_10_7` | car | pending |
| 43 | 5 | S2 | `uav_02_car_13_7` | car | pending |
| 44 | 5 | S2 | `uav_02_car_1_5` | car | pending |
| 45 | 5 | S2 | `uav_02_car_7_6` | car | pending |
| 46 | 5 | S2 | `uav_02_car_8_5` | car | pending |
| 47 | 5 | S2 | `uav_02_car_9_6` | car | pending |
| 48 | 5 | S2 | `uav_02_car_9_8` | car | pending |
| 49 | 5 | S2 | `uav_03_bus_13_1` | bus | pending |
