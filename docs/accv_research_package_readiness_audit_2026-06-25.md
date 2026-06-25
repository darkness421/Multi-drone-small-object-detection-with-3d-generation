# ACCV Research Package Readiness Audit

Updated: `2026-06-25 KST`

This audit separates paper-claimable evidence from smoke-test or pending
evidence. Use it before updating the main paper, supplementary material, or
Overleaf/GitHub status.

Companion paper artifact index:
`paper/figures/results/paper_artifact_readiness_manifest.md`.

## Current Decision

- 2D detector section: **paper-ready with final wording review**.
- MarineCity/Isaac system section: **paper-ready as a real-Cesium system
  smoke/protocol result**, but not yet as a final 3D reconstruction benchmark.
- AeroGraph reasoner section: **reviewed 49-prompt candidate table available;
  external-provider replication still pending**.
- TinyPerson stress test: **completed but weak; use only as supplementary
  domain-shift/limitation evidence**.

## Paper-Claimable Now

| Area | Status | Evidence |
|---|---|---|
| Final 2D detector selection | Complete | `outputs/reports/live/accv_workflow_status_snapshot.md`, `paper/tables/main_detector_comparison_table.tex` |
| Ours vs YOLO/UAV related-work ranking | Complete | `outputs/reports/final_detector_table_preview.md`, `outputs/reports/detector_rankings/overall_1280_completed_performance_ranking.csv` |
| Related-work model rows | Complete for current paper table | `paper/tables/related_work_detector_status_table.tex`, `outputs/reports/live/paper_fig03_related_work_status_table.png` |
| Ablation table/figures | Complete | `outputs/reports/live/final_ablation_main_table.csv`, `outputs/reports/live/paper_fig08_final_ablation_main_table.png`, `outputs/reports/live/paper_fig10_final_ablation_metric_heatmap.png` |
| Grad-CAM-style detector qualitative sheet | Complete | `outputs/reports/live/paper_fig11_final_detector_feature_activation_heatmap.png`, `outputs/reports/live/final_detector_feature_activation_manifest.json` |
| Real-Cesium MarineCity loading and 3-scenario smoke test | Complete as smoke/protocol evidence | `outputs/reports/live/marinecity_system_test_10plus/manifest.json`, `paper/tables/marinecity_system_scenario_table.tex` |
| MarineCity visual QA and crop candidates | Complete for figure selection guidance | `paper/figures/results/marinecity_system/marinecity_capture_quality_rank.csv`, `paper/figures/results/marinecity_system/marinecity_real_capture_crop_candidates.csv` |
| MarineCity qualitative gate | Complete as a promotion gate | `outputs/reports/live/marinecity_qualitative_gate.md`, `paper/figures/results/marinecity_system/marinecity_qualitative_gate.md` |
| UAV/camera altitude policy | Complete | `outputs/reports/live/accv_workflow_status_snapshot.md`, `docs/uavmarine_multiuav_scenarios.md`, `paper/sections/06_marinecity_3d_readiness.tex` |

## Must Stay Pending Or Carefully Worded

| Area | Current State | Required Before Final Claim |
|---|---|---|
| AeroGraph external-provider reasoning accuracy | Reviewed 49-prompt candidate table, web batches, dry-run, and table builder exist; final paper claim remains pending | Complete one external-provider run over all 49 prompts and rebuild `paper/tables/aerograph_reasoner_results_placeholder.tex` |
| 3D reconstruction/restoration benchmark | Current evidence is detector-to-graph/system smoke, not final NeRF/3DGS/3D-completion benchmark | Run final 3D completion/restoration experiment or phrase as planned/initial protocol |
| Final MarineCity qualitative figure | Real-Cesium smoke, crop supplementary evidence, and clean full-frame main candidate are ready (`best full-frame void=0.017828`, `mean top-3 void=0.087552`) | Keep as paper candidate and re-check during final layout review |
| Isaac live GUI state | User-visible GUI has real Cesium, but paper evidence should come from saved screenshots/manifests | Export clean screenshots/panels after final altitude and ROI are locked |
| Supplementary references/page/layout audit | Paper sections exist, but final page budget/reference ordering needs a last compile review | Recompile Overleaf/GitHub paper and inspect references, table widths, and main/supp split |

## TinyPerson Status

TinyPerson640 is finished as a stress-test queue, but the values are near zero
for all tested models. This is not useful as a primary comparison table. It can
be used in supplementary material as evidence that cross-dataset tiny-person
transfer at 640px is a hard domain-shift case.

Authoritative source:

- `outputs/experiments/tinyperson_640/summary.csv`
- `outputs/reports/live/tinyperson_640_dashboard.png`

Do not use `outputs/experiments/tinyperson_640/stage_gate.md` as the source of
truth if it contradicts the summary CSV; that generic gate can misread this
stress-test naming.

## AeroGraph Next Action

Use the web batches if no CLI provider key is configured:

- Tracked runbook:
  `docs/aerograph_nonmock_collection_plan.md`
- Batch directory: `outputs/reports/live/aerograph_prompt_pack/web_batches/`
- Full manual response template:
  `outputs/reports/live/aerograph_prompt_pack/aerograph_manual_response_template_all.jsonl`
- Coverage checker:
  `python scripts/check_aerograph_nonmock_readiness.py`
- Response import command:

```bash
python scripts/import_aerograph_manual_responses.py \
  --responses outputs/reasoning/aerograph_manual_responses.jsonl \
  --provider-label "Factory/ChatGPT web" \
  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_manual_web
```

Then rebuild the paper table:

```bash
python scripts/build_aerograph_reasoner_table.py
```

The table builder should only promote complete non-mock manifests. Current
status is intentionally pending in:

- `outputs/reports/live/aerograph_nonmock_readiness_status.md`
- `outputs/reports/live/aerograph_reasoner_table_manifest.json`
- `paper/tables/aerograph_reasoner_results_placeholder.tex`

## MarineCity Qualitative Status

The current qualitative gate is:

- `outputs/reports/live/marinecity_qualitative_gate.md`
- Status: `marinecity_qualitative_gate_main_ready`
- Full-frame main ready: `True`
- Crop supplementary ready: `True`
- Best full-frame void ratio: `0.017828`
- Mean top-3 full-frame void ratio: `0.087552`

This means the current real-Cesium smoke/contact sheets and selected
full-frame/crop candidates are usable as paper candidates. Keep them labeled as
real-Cesium system/protocol evidence until the final 3D completion/restoration
benchmark is run.

## Main Paper Update Guidance

- Main paper detector section should use the compact final detector comparison
  table, not the long search inventory.
- Main paper MarineCity section should state that the current result validates
  a real-Cesium multi-UAV system pipeline and evidence-token export.
- Main paper should not claim a completed 3D reconstruction benchmark unless the
  final 3D completion/restoration experiment is run.
- Supplementary should carry the full ablation inventory, TinyPerson stress
  result, extra Grad-CAM/qualitative panels, and implementation details.
