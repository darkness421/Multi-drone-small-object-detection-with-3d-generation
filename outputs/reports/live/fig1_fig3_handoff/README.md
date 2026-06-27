# Fig. 1/Fig. 3 Simulation Handoff Package

Purpose: collect the real Isaac/MarineCity, multi-UAV detector, 3D evidence, and reasoner assets that will replace placeholder panels in Main Fig. 1 and Main Fig. 3.

Stable figures: Fig. 2, SelfAttnFR, TinyFReLU, and overlap-aware NMS are treated as architecture/module figures and do not need revision unless the final detector changes.

## Current Revision Decision

- Fig. 1 should be revised with the current real-Cesium MarineCity 3-UAV captures and should no longer rely on generic/synthetic city panels.
- Fig. 3 should be revised now for detector previews and cross-view EvidenceToken graph, but the neural 3D completion panel and non-mock AeroGraph output panel must stay visually marked as pending until those gates finish.
- Use the current smoke-test assets as visual/evidence-flow material, not as final neural 3D reconstruction or external LLM validation.

## Copied Assets

| Status | Figure | File | Source | Use |
|---|---|---|---|---|
| copied | Fig. 1 | `fig1_map_multiuav_preview.png` | `outputs/reports/live/marinecity_real_capture_benchmark_contact_sheet.png` | Use as the real MarineCity multi-UAV observation/map panel. Shows 3 scenarios x 3 UAV captures at 140-160 m. |
| copied | Fig. 1/Fig. 3 | `fig1_fig3_three_scenario_system_panel.png` | `outputs/reports/live/marinecity_system_test_10plus/contact_sheet_3_scenarios.png` | Compact system-level visual summary for locked ROI, adjacent overlap, and coastline multi-view scenarios. |
| copied | Fig. 1 | `fig1_uav01_rgb.png` | `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_001_uav_01_rgb.png` | Raw UAV view for the multi-UAV observations column. |
| copied | Fig. 1 | `fig1_uav02_rgb.png` | `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_002_uav_02_rgb.png` | Raw UAV view for the multi-UAV observations column. |
| copied | Fig. 1 | `fig1_uav03_rgb.png` | `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_003_uav_03_rgb.png` | Raw UAV view for the multi-UAV observations column. |
| copied | Fig. 1 | `fig1_uav01_isaac_bbox.png` | `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_001_uav_01_bbox_preview.png` | Ground-truth-like Isaac object layout/bbox preview. |
| copied | Fig. 1 | `fig1_uav02_isaac_bbox.png` | `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_002_uav_02_bbox_preview.png` | Ground-truth-like Isaac object layout/bbox preview. |
| copied | Fig. 1 | `fig1_uav03_isaac_bbox.png` | `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_003_uav_03_bbox_preview.png` | Ground-truth-like Isaac object layout/bbox preview. |
| copied | Fig. 3 | `fig3_uav01_yolo_detection.png` | `outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/previews/frame_001_uav_01_rgb_pred.png` | P2P4-SelfAttnFR output from one simulated UAV view. |
| copied | Fig. 3 | `fig3_uav02_yolo_detection.png` | `outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/previews/frame_002_uav_02_rgb_pred.png` | P2P4-SelfAttnFR output from one simulated UAV view. |
| copied | Fig. 3 | `fig3_uav03_yolo_detection.png` | `outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/previews/frame_003_uav_03_rgb_pred.png` | P2P4-SelfAttnFR output from one simulated UAV view. |
| copied | Fig. 3 | `fig3_evidence_tokens.jsonl` | `outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/evidence_tokens.jsonl` | Structured detector output to drive the 3D evidence graph/reasoner panel. |
| copied | Fig. 3 | `fig3_detector_smoke_summary.json` | `outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/detector_smoke_summary.json` | Summary for current detector-on-simulation smoke test. |
| copied | Fig. 3 | `fig3_real_cesium_detector_preview_contact_sheet.png` | `paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png` | Current real-Cesium SAFR-YOLO detector-preview sheet from the 3-scenario smoke run. |
| copied | Fig. 3 | `fig3_crossview_evidence_graph_smoke.png` | `outputs/reports/live/marinecity_crossview_evidence_graph.png` | Current real-Cesium cross-view EvidenceToken graph with support/conflict/missing edges. |
| copied | Fig. 3 | `fig3_depth_pointcloud_smoke_topdown.png` | `paper/figures/results/marinecity_system/marinecity_depth_pointcloud_smoke_topdown.png` | Depth-backed 3D geometry smoke preview. Use as handoff context, not as neural 3D completion evidence. |
| copied | Fig. 3 | `fig3_s0_locked_roi_panel.png` | `paper/figures/results/marinecity_system/s0_scenario_panel.png` | Locked MarineCity ROI scenario panel. |
| copied | Fig. 3 | `fig3_s1_adjacent_overlap_panel.png` | `paper/figures/results/marinecity_system/s1_scenario_panel.png` | Adjacent/overlap ambiguity scenario panel. |
| copied | Fig. 3 | `fig3_s2_coastline_multiview_panel.png` | `paper/figures/results/marinecity_system/s2_scenario_panel.png` | Coastline multi-view scenario panel. |
| copied | Fig. 1/Fig. 3 | `fig1_fig3_capture_quality_top8.png` | `paper/figures/results/marinecity_system/marinecity_capture_quality_top8.png` | Visual QA sheet for selecting clean real-Cesium views and avoiding black/void regions. |
| copied | Fig. 1/Fig. 3 | `fig1_fig3_crop_candidates_top12.png` | `paper/figures/results/marinecity_system/marinecity_real_capture_crop_top12.png` | Crop-only framing candidates for artist guidance; do not use as a synthetic replacement. |
| copied | Fig. 1/Fig. 3 | `fig1_fig3_capture_plan.json` | `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/capture_plan.json` | UAV altitude, pose, weather, and camera metadata. |
| copied | Fig. 1/Fig. 3 | `fig1_fig3_replicator_capture_summary.json` | `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct_capture_summary.json` | Isaac output summary: UAV count, object count, bbox counts, and stage origin. |
| copied | Fig. 1/Fig. 3 | `fig1_fig3_isaac_stage_opened.json` | `outputs/logs/gpu1_isaac51_streaming/marinecity_stage_opened.json` | Proof that the MarineCity stage opened in the GPU1 Isaac streaming run. |

## Final Missing Assets

| File | Needed After Final Simulation/Reasoner Experiments |
|---|---|
| `fig3_final_neural3d_completion_render.png` | Final neural 3D completion or novel-view rendering after NeRF/Instant-NGP/3DGS-style evaluation. |
| `fig3_final_nonmock_aerograph_decision_panel.png` | Final non-mock AeroGraph Reasoner output panel: belief, uncertainty, action, verifier result. |

## Figure Update Guidance

- Fig. 1 should use `fig1_map_multiuav_preview.png`, the three `fig1_uav*_rgb.png` views, and the three `fig1_uav*_isaac_bbox.png` previews while keeping the high-level CoM3D-ACE pipeline layout.
- Fig. 3 should use `fig3_real_cesium_detector_preview_contact_sheet.png`, `fig3_crossview_evidence_graph_smoke.png`, and `fig3_depth_pointcloud_smoke_topdown.png` for the current evidence-flow story.
- Fig. 3's final neural 3D completion and non-mock AeroGraph panels should be replaced later by actual runner/provider outputs.
- Keep diagrams compact. Detailed equations and module internals stay in Fig. 2 and supplementary figures.
- Do not present the current smoke-test detector output as the final 3D/reasoner result until the full simulation experiment is completed.
