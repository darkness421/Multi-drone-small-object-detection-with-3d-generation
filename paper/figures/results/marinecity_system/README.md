# MarineCity System Figures

Generated from the real-Cesium MarineCity multi-UAV smoke-test bundle.

Source bundle:

- `outputs/reports/live/marinecity_system_test_10plus/`

Paper-facing candidates:

- `contact_sheet_3_scenarios.png`: compact scenario-level qualitative summary. Use in main paper only if space allows; otherwise supplementary.
- `contact_sheet_token_tests.png`: all current token-level image-to-detector-to-reasoner tests. Recommended for supplementary.
- `s0_scenario_panel.png`: locked ROI scenario detail.
- `s1_scenario_panel.png`: adjacent/overlap scenario detail.
- `s2_scenario_panel.png`: coastline/multiview scenario detail.
- `marinecity_capture_quality_top8.png`: ranked visual QA sheet from existing
  real-Cesium captures. Use to choose candidates and to justify a final recapture.
- `marinecity_capture_quality_rank.csv`: source ranking table with black/void
  ratio, brightness, and camera-profile metadata.
- `marinecity_real_capture_crop_top12.png`: crop-only qualitative candidates
  from existing real-Cesium captures. Use this as a framing guide for final
  recapture, not as a synthetic replacement.
- `marinecity_real_capture_crop_candidates.csv`: crop boxes and QA metrics for
  the candidate sheet.
- `marinecity_real_capture_crop_manifest.json`: reproducibility metadata for the
  crop-only candidate generation.

Important current limitation:

- These are smoke-test artifacts with `rule_based_aerograph` verifier outputs.
- The 3D component is currently an evidence-graph/depth-backed reasoning smoke test, not a final NeRF/3DGS reconstruction result.
- Final paper screenshots should be regenerated after object placement, ROI coverage, and external LLM/VLM validation are improved.
- Current best existing visual folder is
  `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s0_viewer160_road_roi_diag`,
  but its top-3 black/void ratio is still about `42.7%`; treat it as a smoke-test
  visual, not the final main-paper image.
- The best crop-only candidate reduces black/void ratio to about `0.34%`, but
  it is a cropped view and may not show the full multi-UAV scenario. Use it to
  guide the final Isaac viewport/recapture framing.
