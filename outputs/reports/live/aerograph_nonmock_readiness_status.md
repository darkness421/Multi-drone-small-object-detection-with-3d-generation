# AeroGraph Non-Mock Readiness Status

- Status: `aerograph_external_provider_pending_responses`
- Prompt pack: `outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl`
- Prompt count: `54`
- Manual response file: `outputs/reasoning/aerograph_manual_responses.jsonl`
- Response rows: `0`
- Matched nonblank responses: `0/54`
- Matched valid schema responses: `0/54`
- Coverage ratio: `0.0`
- Valid coverage ratio: `0.0`
- Effective valid response coverage: `49/49` via `provider_manifest`
- Reviewed-candidate coverage: `49/54`
- External-provider replication ready: `False`
- Invalid JSONL response rows: `0`
- Invalid schema response rows: `0`
- Web batch manifest: `outputs/reports/live/aerograph_prompt_pack/web_batches/manifest.json`
- Web batch status: `aerograph_web_batches_ready`
- Web batch count: `6`
- Full manual template: `outputs/reports/live/aerograph_prompt_pack/aerograph_manual_response_template_all.jsonl`
- Paper table manifest: `outputs/reports/live/aerograph_reasoner_table_manifest.json`
- Paper table status: `aerograph_reasoner_table_complete`

## Interpretation

- External-provider responses are partially collected. Fill missing/blank/invalid rows before paper-table promotion.

## Provider Manifest Coverage

| Source | Status | Provider | Valid Responses | Reviewed Candidate | External Complete |
| --- | --- | --- | ---: | --- |
| `outputs/reasoning/aerograph_prompt_pack_eval_manual_web/manifest.json` | `aerograph_manual_import_complete` | `AeroGraph reviewed candidate` | `49/49` | `True` | `False` |
| `outputs/reasoning/aerograph_prompt_pack_eval_manual/manifest.json` | `aerograph_manual_import_complete` | `AeroGraph reviewed candidate` | `49/49` | `True` | `False` |

## Batch Progress

| Batch | Items | Valid Responses | Status | File |
| ---: | --- | ---: | --- | --- |
| 1 | 1-10 | 0/10 | pending | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md` |
| 2 | 11-20 | 0/10 | pending | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_02_011-020.md` |
| 3 | 21-30 | 0/10 | pending | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_03_021-030.md` |
| 4 | 31-40 | 0/10 | pending | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_04_031-040.md` |
| 5 | 41-50 | 0/10 | pending | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_05_041-050.md` |
| 6 | 51-54 | 0/4 | pending | `outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_06_051-054.md` |

## Missing Examples

- Next missing item index: `1`
- `S0:uav_01_bus_3_7`
- `S0:uav_01_car_6_8`
- `S0:uav_01_pedestrian_13_2`
- `S0:uav_02_bus_0_3`
- `S0:uav_02_bus_3_4`
- `S0:uav_02_bus_5_5`
- `S0:uav_02_bus_7_6`
- `S0:uav_02_car_0_3`
- `S0:uav_02_car_0_5`
- `S0:uav_02_car_10_6`
- `S0:uav_02_car_10_7`
- `S0:uav_02_car_13_7`
- `S0:uav_02_car_1_5`
- `S0:uav_02_car_2_3`
- `S0:uav_02_car_5_6`
- `S0:uav_02_car_7_6`
- `S0:uav_02_car_8_5`
- `S0:uav_02_car_9_8`
- `S0:uav_02_van_0_5`
- `S1:uav_01_bus_2_7`

## Promotion Commands

```bash
python scripts/check_aerograph_prompt_pack_integrity.py
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
