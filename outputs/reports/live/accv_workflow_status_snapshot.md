# ACCV Workflow Status Snapshot

Updated: `2026-06-26 09:06:54 KST`

## Detector Status

- Selected detector: `Ours: P2P4-SelfAttnFR`
- Ours vs YOLOv11l AP gap: `0.004506`
- Ours vs UAVDet final-table AP gap: `0.000979`
- Ours vs UAVDet queue-best AP gap: `0.002613`
- UAVDet queue: `all_seed_results_present`; seeds started `3/3`; seeds completed `3/3`
- UAVDet active seed: `None`; best seed: `42`; best AP: `0.37955`; best AP50: `0.60167`

| Rank | Model | AP | AP50 | F1 | Params | Seeds |
|---:|---|---:|---:|---:|---:|---|
| 1 | Ours: P2P4-SelfAttnFR | 0.3822 | 0.6052 | 0.6273 | 20.82M | 42,123,2026 |
| 2 | UAVDet [16] | 0.3812 | 0.6005 | 0.6203 | 33.55M | 42,123,2026 |
| 3 | BPD-YOLO [7] | 0.3804 | 0.5986 | 0.6187 | 24.53M | 42,123,2026 |
| 4 | YOLOv11l | 0.3777 | 0.5981 | 0.6248 | 25.32M | 123,2026,42 |
| 5 | YOLOv12l | 0.3771 | 0.5958 | 0.6219 | 26.40M | 123,2026,42 |
| 6 | YOLOv8l | 0.3765 | 0.5963 | 0.6198 | 43.64M | 123,2026,42 |
| 7 | SFFEF-YOLO [4] | 0.3749 | 0.5914 | 0.6137 | 20.87M | 42,123,2026 |
| 8 | YOLOv9c | 0.3738 | 0.5942 | 0.6210 | 25.54M | 123,2026,42 |

### UAVDet 3-Seed Queue

| Seed | Status | Latest Epoch | Best Epoch | Best AP | Best AP50 | Epochs Since Best |
|---:|---|---:|---:|---:|---:|---:|
| 42 | finished | 43 | 38 | 0.3795 | 0.6017 | 5 |
| 123 | finished | 38 | 33 | 0.3779 | 0.5976 | 5 |
| 2026 | finished | 38 | 33 | 0.3783 | 0.5960 | 5 |

## MarineCity System

- Real-Cesium scenario count: `3`
- Token-level system tests: `49`
- Artifact status: `marinecity_system_test_artifacts_complete`
- Real-capture detector/reasoner smoke: `marinecity_detector_reasoner_smoke_artifacts_ready`; tokens `23`; report `outputs/reports/live/marinecity_detector_reasoner_smoke.md`
- Detector preview sheet: `paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png`
- Live overlay: `session_overlay_added`; camera set `True`; profile `viewer160_marinecity_roi`
- Real Cesium: Google tiles `True`, terrain `True`, fake city `False`
- UAV altitude policy: `{'band_m': [140, 160], 'default_m': 160, 'user_locked_review_height_m': 160, 'verified_viewer160_recapture_m': {'uav_01': 140, 'uav_02': 150, 'uav_03': 160}, 'note': 'Use 140-160 m for UAV/camera observation; keep CesiumGeoreference readback logged separately.'}`
- Viewer camera: eye `[8.0, -2.0, 160.0]`, target `[-22.0, -13.0, 15.0]`
- Cesium target georef height: `160`; latest GUI readback `200.0`, requested/applied `None`/`None`
- Georef note: The user-verified MarineCity review height is 160 m, and the UAV/camera observation band is locked to 140-160 m. The live CesiumGeoreference readback is logged separately because it can lag until the next recapture/status export.
- Qualitative gate: `marinecity_qualitative_gate_main_ready`
- Full-frame ready: `True`; best full void `0.017828`; mean top-3 void `0.087552`
- Crop supplementary ready: `True`; best crop void `0.003577`; area `0.9025`
- Clean full-frame recapture plan: `outputs/reports/live/marinecity_clean_recapture_plan.json`; status `main_full_frame_ready`; needed improvement `{'best_black_ratio_delta_to_threshold': 0.0, 'mean_top3_black_ratio_delta_to_threshold': 0.0}`
- Dashboard: `outputs/reports/live/marinecity_simulation_dashboard.png`

## AeroGraph Reasoner

- Prompt pack: `aerograph_prompt_pack_ready`, prompts `49`
- Prompt class counts: `{'bus': 16, 'car': 29, 'pedestrian': 4}`
- Real-capture compact prompt pack: `aerograph_real_capture_prompt_pack_ready`, prompts `23`, classes `{'bus': 8, 'car': 15}`
- Real-capture compact web batches: `aerograph_web_batches_ready`, count `3`; dry-run `aerograph_eval_dry_run_ready`, paper-claim `False`
- Web batches: `aerograph_web_batches_ready`, count `5`, dir `outputs/reports/live/aerograph_prompt_pack/web_batches`
- Dry-run status: `aerograph_eval_dry_run_ready`
- Paper table status: `aerograph_reasoner_table_candidate_external_pending`, selected manifest ``
- Reasoner readiness status: `aerograph_reviewed_candidate_ready_external_pending`
- Effective valid response coverage: `49/49`; ratio `1.0`
- Reviewed-candidate coverage: `49/49`
- External-provider replication ready: `False`
- Full manual template: `outputs/reports/live/aerograph_prompt_pack/aerograph_manual_response_template_all.jsonl`
- Non-mock readiness report: `outputs/reports/live/aerograph_nonmock_readiness_status.md`
- Non-mock collection plan: `docs/aerograph_nonmock_collection_plan.md`

## Queue Gates

- UAVDet log tail: `[2026-06-25T19:23:05+09:00] QUEUE_FINISHED UAVDet inspired reproduction queue`
- TinyPerson log tail: `[2026-06-26T06:52:33+09:00] Dashboard: outputs/reports/live/tinyperson_640_dashboard.png`
- TinyPerson gate: `finished_tinyperson_640_stress_test`

## Dashboard Links

- Training dashboard: `outputs/reports/live/training_dashboard.png`
- MarineCity dashboard: `outputs/reports/live/marinecity_simulation_dashboard.png`

## Paper-Ready Artifacts

- Readiness audit: `outputs/reports/live/accv_research_package_readiness_audit.md`
- Tracked readiness audit: `docs/accv_research_package_readiness_audit_2026-06-25.md`
- Paper artifact manifest: `paper/figures/results/paper_artifact_readiness_manifest.md`
- Paper artifact check: `outputs/reports/live/paper_artifact_readiness_check.json`; status `paper_artifact_audit_ok_with_pending_gates`; missing `0`; stale claims `0`
- LaTeX patch check: `outputs/reports/live/latex_patch_integrity_check.json`; status `latex_patch_integrity_ok`
- Detector table: `paper/tables/main_detector_comparison_table.tex`
- MarineCity system table: `paper/tables/marinecity_system_scenario_table.tex`
- AeroGraph placeholder table: `paper/tables/aerograph_reasoner_results_placeholder.tex`
