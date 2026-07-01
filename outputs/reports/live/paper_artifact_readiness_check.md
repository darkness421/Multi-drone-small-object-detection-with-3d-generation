# Paper Artifact Readiness Check

Updated: `2026-07-02 01:17:45 KST`
Status: `paper_artifact_audit_submission_ready_with_optional_gates`

## Summary

- Artifacts checked: `53`
- Missing required artifacts: `0`
- Stale/unsafe claim matches: `0`
- AeroGraph effective valid response coverage: `49/49`
- AeroGraph reviewed-candidate coverage: `49/49`
- AeroGraph external-provider replication ready: `False`
- AeroGraph provider benchmark is optional for the current submission because the paper claim is limited to schema/verifier/action-policy validation.
- AeroGraph table status: `aerograph_reasoner_table_candidate_external_open`
- MarineCity qualitative gate: `marinecity_qualitative_gate_main_ready`
- MarineCity integration gate: `marinecity_system_integration_validation_ready_with_open_final_gates`; fails `0`, warnings `0`, open checks `1`
- MarineCity 3D completion gate: `marinecity_3d_completion_ready`; metric rows `3`
- External gate capabilities: `three_d_runner_available_aerograph_provider_missing`; AeroGraph provider `False`; neural-3D runner `True`
- MarineCity main full-frame ready: `True`
- Local main.tex present: `False`
- LaTeX patch integrity: `latex_patch_integrity_ok`
- Main.tex note: No local main.tex means current files are Overleaf-ready patches rather than a full local paper build.

## Claiming Summary

- `detector`: `ready`
- `marinecity_system`: `ready_as_real_cesium_system_validation`
- `marinecity_qualitative`: `ready_for_main`
- `aerograph`: `ready_as_schema_verifier_and_action_policy_validation`
- `aerograph_optional_external_provider`: `candidate_ready_needs_external_provider`
- `final_3d_completion`: `ready`
- `local_compile`: `open_main_tex_or_overleaf_sync`

## MarineCity Integration Gate

- Status: `marinecity_system_integration_validation_ready_with_open_final_gates`
- Fail/warn/open count: `0` / `0` / `1`
- Detector token count: `78`
- Detector classes: `{'bus': 17, 'car': 53, 'pedestrian': 6, 'van': 2}`
- Actor classes: `['bus', 'car', 'pedestrian', 'person', 'truck', 'van']`
- 3D status: `complete`
- LLM external ready: `False`

## MarineCity 3D Completion Gate

- Status: `marinecity_3d_completion_ready`
- Source capture ready: `True`
- Neural-3D input dataset ready: `True`
- Neural runner available: `True`
- Depth point-cloud validation ready: `True`; points `7584`
- Metric result rows: `3`
- Methods ready: `['gaussian_splatting', 'instant_ngp', 'nerf']`
- Missing expected methods: `['mip_nerf_360']`
- Claiming rule: The real-Cesium RGB/depth/pose capture source, neural-3D transforms package, and depth point-cloud validation are ready. At least one verified neural-3D runner metric row upgrades the result to a system-level validation. Do not claim a full 3D benchmark until additional runner families or longer validation runs are collected.

## External Gate Capabilities

- Status: `three_d_runner_available_aerograph_provider_missing`
- AeroGraph provider configured: `False`
- AeroGraph provider modes: `[]`
- Neural 3D runner configured: `True`
- Neural 3D dataset ready: `True`
- Neural 3D metric rows: `3`

## MarineCity Qualitative Gate

- Status: `marinecity_qualitative_gate_main_ready`
- Real Cesium OK: `True`
- System validation OK: `True`
- Crop supplementary ready: `True`
- Full-frame main ready: `True`
- Best full-frame void ratio: `0.017833`
- Mean top-3 full-frame void ratio: `0.093141`
- Best crop void ratio: `0.003579`
- Claiming rule: Main paper full-frame qualitative figure may be promoted.

## Artifact Inventory

| group | path | placement | exists | status | note |
| --- | --- | --- | --- | --- | --- |
| main_detector | paper/sections/05_experiments_current_detector_status.tex | main | True | ok | Detector result section patch |
| main_detector | paper/tables/main_detector_comparison_table.tex | main | True | ok | Compact final detector table |
| main_detector | paper/tables/final_ablation_main_table.tex | main | True | ok | Compact final ablation table |
| supp_detector | paper/tables/related_work_detector_status_table.tex | supp | True | ok | Cited related-work detector protocol table |
| main_detector | paper/figures/results/paper_fig01_main_detector_table.png | main_optional | True | ok | Detector table visual |
| main_detector | paper/figures/results/paper_fig04_ap_ap50_bar_chart.png | main_or_supp | True | ok | AP/AP50 chart |
| main_detector | paper/figures/results/paper_fig05_ap_params_scatter.png | main_or_supp | True | ok | AP vs params chart |
| main_system | paper/sections/06_marinecity_3d_readiness.tex | main | True | ok | MarineCity protocol section patch |
| main_system | paper/tables/marinecity_system_scenario_table.tex | main | True | ok | Real-Cesium system-validation protocol table |
| main_system | paper/tables/marinecity_system_token_results.csv | main_source | True | ok | Source CSV for real-Cesium detector-to-reasoner validation table |
| supp_system | paper/sections/supp_marinecity_system_details.tex | supp | True | ok | Supplementary MarineCity capture, graph, and reasoner details |
| supp_system | paper/tables/marinecity_real_capture_benchmark_table.tex | supp | True | ok | Verified real-Cesium capture-source table |
| supp_system | paper/tables/marinecity_crossview_evidence_graph_table.tex | supp | True | ok | Real-Cesium cross-view evidence graph validation table |
| main_system | paper/sections/07_marinecity_qualitative_figure_slots.tex | main_optional | True | ok | Safe qualitative figure slots |
| bundle | paper/sections/main_results_patch_bundle.tex | main_bundle | True | ok | Overleaf-ready main results patch bundle |
| bundle | paper/sections/supplementary_patch_bundle.tex | supp_bundle | True | ok | Overleaf-ready supplementary patch bundle |
| supp_detector | paper/sections/supp_detector_experiment_inventory.tex | supp | True | ok | Supplementary detector inventory |
| supp_detector | paper/tables/final_ablation_supplementary_table.tex | supp | True | ok | Full ablation table |
| supp_detector | paper/figures/results/paper_fig10_final_ablation_metric_heatmap.png | supp | True | ok | Ablation heatmap |
| supp_detector | paper/figures/results/paper_fig11_final_detector_feature_activation_heatmap.png | supp | True | ok | Detector activation/heatmap sheet |
| supp_system | paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png | supp_or_main_validation | True | ok | Three-scenario real-Cesium validation sheet |
| supp_system | paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png | main_or_supp_validation | True | ok | Real-Cesium detector preview contact sheet from SAFR-YOLO validation run |
| supp_system | paper/figures/results/marinecity_system/marinecity_real_capture_benchmark_contact_sheet.png | supp | True | ok | Real-Cesium 3-scenario x 3-UAV capture contact sheet |
| supp_system | paper/figures/results/marinecity_system/marinecity_crossview_evidence_graph.png | supp | True | ok | Real-Cesium cross-view evidence graph validation figure |
| supp_system | outputs/reports/live/marinecity_qualitative_selection_manifest.md | runbook | True | ok | MarineCity qualitative selection rules |
| supp_system | outputs/reports/live/marinecity_qualitative_gate.md | runbook | True | ok | MarineCity full-frame vs crop-only qualitative gate |
| supp_system | outputs/reports/live/marinecity_real_capture_benchmark.md | runbook | True | ok | Real-Cesium capture benchmark manifest summary |
| supp_system | outputs/reports/live/marinecity_detector_reasoner_smoke.md | runbook | True | ok | Real-Cesium detector-to-reasoner validation report |
| supp_system | outputs/reports/live/marinecity_crossview_evidence_graph.md | runbook | True | ok | Real-Cesium cross-view evidence graph validation report |
| supp_system | outputs/reports/live/marinecity_system_integration_check.md | runbook | True | ok | Real-Cesium object/UAV/camera/YOLO/3D/LLM integration gate |
| open_3d_gate | outputs/reports/live/marinecity_neural3d_dataset_export.md | runbook | True | ok | MarineCity real-capture neural-3D input dataset export |
| open_3d_gate | outputs/reports/live/marinecity_3d_runner_preflight.md | runbook | True | ok | MarineCity local neural-3D runner dependency preflight |
| open_3d_gate | outputs/reports/live/marinecity_depth_pointcloud_smoke.md | runbook | True | ok | MarineCity depth-fused 3D geometry validation artifact |
| open_3d_gate | paper/figures/results/marinecity_system/marinecity_depth_pointcloud_smoke_topdown.png | supp | True | ok | Depth point-cloud validation preview figure |
| main_system | paper/tables/marinecity_3d_completion_results_table.tex | main_or_supp_validation | True | ok | Compact neural 3D runner-family validation metric table |
| open_3d_gate | outputs/reports/live/marinecity_3d_completion_results_table.md | runbook | True | ok | Live summary for verified neural 3D metric rows |
| open_3d_gate | outputs/reports/live/marinecity_3d_completion_readiness.md | runbook | True | ok | MarineCity neural 3D completion readiness gate |
| supp_system | paper/tables/aerograph_reasoner_validation_summary.tex | supp | True | ok | Paper-safe AeroGraph schema and verifier validation summary |
| optional_reasoner_provider | paper/tables/aerograph_reasoner_external_slot.tex | optional | True | ok | Optional external-provider table slot; not used for the current main claim |
| optional_reasoner_provider | docs/aerograph_nonmock_collection_plan.md | runbook | True | ok | Optional external-provider reasoner collection plan |
| optional_reasoner_provider | outputs/reports/live/aerograph_prompt_pack_integrity.md | audit | True | ok | AeroGraph prompt/template/batch consistency check |
| optional_reasoner_provider | outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_packet.md | runbook | True | ok | Optional one-file web LLM handoff for AeroGraph collection |
| optional_reasoner_provider | outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_checklist.csv | runbook | True | ok | Optional per-prompt AeroGraph external-provider collection checklist |
| optional_reasoner_provider | outputs/reports/live/aerograph_real_capture_prompt_pack/manifest.json | runbook | True | ok | Compact 23-prompt real-capture AeroGraph validation pack |
| optional_reasoner_provider | outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/README.md | runbook | True | ok | Optional compact real-capture web-provider batch index |
| optional_reasoner_provider | outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.md | runbook | True | ok | Optional compact real-capture web-provider collection packet |
| optional_reasoner_provider | outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_checklist.csv | runbook | True | ok | Optional compact real-capture web-provider collection checklist |
| optional_reasoner_provider | outputs/reasoning/aerograph_real_capture_eval_dryrun/manifest.json | audit | True | ok | Compact real-capture prompt-pack runner dry-run check |
| optional_reasoner_provider | scripts/normalize_aerograph_web_responses.py | runbook_helper | True | ok | Web LLM raw-output normalizer for optional AeroGraph manual responses |
| audit | outputs/reports/live/paper_artifact_readiness_manifest.md | audit | True | ok | Human-readable artifact manifest |
| audit | outputs/reports/live/latex_patch_integrity_check.md | audit | True | ok | LaTeX input/figure/label integrity check |
| audit | outputs/reports/live/external_gate_capabilities.md | audit | True | ok | External provider and neural-3D runner capability check |
| audit | docs/accv_research_package_readiness_audit_2026-06-25.md | audit | True | ok | Claim readiness audit |
