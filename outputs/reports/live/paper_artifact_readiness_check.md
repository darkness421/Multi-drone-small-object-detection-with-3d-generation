# Paper Artifact Readiness Check

Updated: `2026-06-26 08:19:54 KST`
Status: `paper_artifact_audit_ok_with_pending_gates`

## Summary

- Artifacts checked: `38`
- Missing required artifacts: `0`
- Stale/unsafe claim matches: `0`
- AeroGraph effective valid response coverage: `49/49`
- AeroGraph reviewed-candidate coverage: `49/49`
- AeroGraph external-provider replication ready: `False`
- AeroGraph table status: `aerograph_reasoner_table_candidate_external_pending`
- MarineCity qualitative gate: `marinecity_qualitative_gate_main_ready`
- MarineCity main full-frame ready: `True`
- Local main.tex present: `False`
- LaTeX patch integrity: `latex_patch_integrity_ok`
- Main.tex note: No local main.tex means current files are Overleaf-ready patches rather than a full local paper build.

## Claiming Summary

- `detector`: `ready`
- `marinecity_system`: `ready_as_real_cesium_smoke_protocol_only`
- `marinecity_qualitative`: `ready_for_main`
- `aerograph`: `candidate_ready_external_provider_pending`
- `final_3d_completion`: `pending_or_pilot_only`
- `local_compile`: `pending_main_tex_or_overleaf_sync`

## MarineCity Qualitative Gate

- Status: `marinecity_qualitative_gate_main_ready`
- Real Cesium OK: `True`
- System smoke OK: `True`
- Crop supplementary ready: `True`
- Full-frame main ready: `True`
- Best full-frame void ratio: `0.017828`
- Mean top-3 full-frame void ratio: `0.087552`
- Best crop void ratio: `0.003577`
- Claiming rule: Main paper full-frame qualitative figure may be promoted.

## Artifact Inventory

| group | path | placement | exists | status | note |
| --- | --- | --- | --- | --- | --- |
| main_detector | paper/sections/05_experiments_current_detector_status.tex | main | True | ok | Detector result section patch |
| main_detector | paper/tables/main_detector_comparison_table.tex | main | True | ok | Compact final detector table |
| main_detector | paper/tables/final_ablation_main_table.tex | main | True | ok | Compact final ablation table |
| main_detector | paper/tables/related_work_detector_status_table.tex | main | True | ok | Cited related-work detector table |
| main_detector | paper/figures/results/paper_fig01_main_detector_table.png | main_optional | True | ok | Detector table visual |
| main_detector | paper/figures/results/paper_fig04_ap_ap50_bar_chart.png | main_or_supp | True | ok | AP/AP50 chart |
| main_detector | paper/figures/results/paper_fig05_ap_params_scatter.png | main_or_supp | True | ok | AP vs params chart |
| main_system | paper/sections/06_marinecity_3d_readiness.tex | main | True | ok | MarineCity protocol section patch |
| main_system | paper/tables/marinecity_system_scenario_table.tex | main | True | ok | Real-Cesium smoke/protocol table |
| main_system | paper/tables/marinecity_system_token_results.csv | main_source | True | ok | Source CSV for real-Cesium detector-to-reasoner smoke table |
| main_system | paper/tables/marinecity_real_capture_benchmark_table.tex | main | True | ok | Verified real-Cesium capture-source table |
| main_system | paper/sections/07_marinecity_qualitative_figure_slots.tex | main_optional | True | ok | Safe qualitative figure slots |
| bundle | paper/sections/main_results_patch_bundle.tex | main_bundle | True | ok | Overleaf-ready main results patch bundle |
| bundle | paper/sections/supplementary_patch_bundle.tex | supp_bundle | True | ok | Overleaf-ready supplementary patch bundle |
| supp_detector | paper/sections/supp_detector_experiment_inventory.tex | supp | True | ok | Supplementary detector inventory |
| supp_detector | paper/tables/final_ablation_supplementary_table.tex | supp | True | ok | Full ablation table |
| supp_detector | paper/tables/tinyperson_640_stress_table.tex | supp | True | ok | TinyPerson 640 supplementary stress-test table |
| supp_detector | paper/figures/results/paper_fig10_final_ablation_metric_heatmap.png | supp | True | ok | Ablation heatmap |
| supp_detector | paper/figures/results/paper_fig11_final_detector_feature_activation_heatmap.png | supp | True | ok | Detector activation/heatmap sheet |
| supp_system | paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png | supp_or_main_smoke | True | ok | Three-scenario real-Cesium smoke sheet |
| supp_system | paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png | main_or_supp_smoke | True | ok | Real-Cesium detector preview contact sheet from SAFR-YOLO smoke run |
| supp_system | paper/figures/results/marinecity_system/marinecity_real_capture_benchmark_contact_sheet.png | supp | True | ok | Real-Cesium 3-scenario x 3-UAV capture contact sheet |
| supp_system | paper/figures/results/marinecity_system/marinecity_qualitative_selection_manifest.md | supp | True | ok | MarineCity qualitative selection rules |
| supp_system | paper/figures/results/marinecity_system/marinecity_qualitative_gate.md | supp | True | ok | MarineCity full-frame vs crop-only qualitative gate |
| supp_system | outputs/reports/live/marinecity_real_capture_benchmark.md | runbook | True | ok | Real-Cesium capture benchmark manifest summary |
| supp_system | outputs/reports/live/marinecity_detector_reasoner_smoke.md | runbook | True | ok | Real-Cesium detector-to-reasoner smoke report |
| pending_reasoner | paper/tables/aerograph_reasoner_results_placeholder.tex | pending | True | ok | AeroGraph table slot must stay pending until all prompt-pack non-mock responses are valid-schema complete |
| pending_reasoner | docs/aerograph_nonmock_collection_plan.md | runbook | True | ok | Non-mock reasoner collection gate |
| pending_reasoner | outputs/reports/live/aerograph_prompt_pack_integrity.md | audit | True | ok | AeroGraph prompt/template/batch consistency check |
| pending_reasoner | outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_packet.md | runbook | True | ok | One-file web LLM handoff for AeroGraph collection |
| pending_reasoner | outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_checklist.csv | runbook | True | ok | Per-prompt AeroGraph non-mock collection checklist |
| pending_reasoner | outputs/reports/live/aerograph_real_capture_prompt_pack/manifest.json | runbook | True | ok | Compact 23-prompt real-capture AeroGraph smoke pack |
| pending_reasoner | outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/README.md | runbook | True | ok | Compact real-capture web-provider batch index |
| pending_reasoner | outputs/reasoning/aerograph_real_capture_eval_dryrun/manifest.json | audit | True | ok | Compact real-capture prompt-pack runner dry-run check |
| pending_reasoner | scripts/normalize_aerograph_web_responses.py | runbook_helper | True | ok | Web LLM raw-output normalizer for AeroGraph manual responses |
| audit | paper/figures/results/paper_artifact_readiness_manifest.md | audit | True | ok | Human-readable artifact manifest |
| audit | outputs/reports/live/latex_patch_integrity_check.md | audit | True | ok | LaTeX input/figure/label integrity check |
| audit | docs/accv_research_package_readiness_audit_2026-06-25.md | audit | True | ok | Claim readiness audit |
