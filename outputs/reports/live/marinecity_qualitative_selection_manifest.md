# MarineCity Qualitative Figure Selection

Updated: `2026-06-25 KST`

This manifest selects current MarineCity qualitative assets for the main paper and supplementary material.
All listed images are generated from real-Cesium MarineCity captures or detector-token smoke outputs; no fake/proxy city visual should be used for paper evidence.

## Recommendation

- Main paper: use `contact_sheet_3_scenarios.png` only as a clearly labeled real-Cesium system smoke/protocol figure if page budget allows.
- Supplementary: use `contact_sheet_token_tests.png`, `marinecity_capture_quality_top8.png`, and `marinecity_real_capture_crop_top12.png`.
- Final main qualitative figure is still pending a cleaner recapture/selection with low void ratio and visible object/UAV evidence.

## Current Best Full-Capture Candidate

- Capture: `uavmarine_s0_viewer160_tight_f52_shift_test`
- Best image: `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s0_viewer160_tight_f52_shift_test/real_cesium_capture/frame_002_uav_02_rgb.png`
- Mean top-3 black/void ratio: `0.0931`
- Best image black/void ratio: `0.0178`
- Camera profile: `viewer160_marinecity_roi`

## Current Best Crop Candidate

- Capture: `uavmarine_s2_viewer160_session_recapture`
- Source: `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_002_uav_02_rgb.png`
- Crop path: `outputs/reports/live/marinecity_real_capture_crops/crops/uavmarine_s2_viewer160_session_recapture_frame_002_uav_02_rgb_crop.png`
- Crop box: `[0, 0, 1216, 684]`
- Black/void ratio: `0.0036`
- Area ratio: `0.9025`
- Score: `1.1156`

## Paper-Facing Assets

| Asset | Path | Placement | Status |
|---|---|---|---|
| 3-scenario smoke contact sheet | `paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png` | Main optional / supplementary | Smoke-test ready; not final benchmark |
| Token-level system contact sheet | `paper/figures/results/marinecity_system/contact_sheet_token_tests.png` | Supplementary | Smoke-test ready |
| Visual QA top-8 sheet | `paper/figures/results/marinecity_system/marinecity_capture_quality_top8.png` | Supplementary / internal review | Shows full-capture void ratio issue |
| Crop top-12 sheet | `paper/figures/results/marinecity_system/marinecity_real_capture_crop_top12.png` | Supplementary / final recapture guide | Crop-only; not a replacement for a final full-scene figure |
| S0 scenario panel | `paper/figures/results/marinecity_system/s0_scenario_panel.png` | Supplementary | Scenario detail |
| S1 scenario panel | `paper/figures/results/marinecity_system/s1_scenario_panel.png` | Supplementary | Scenario detail |
| S2 scenario panel | `paper/figures/results/marinecity_system/s2_scenario_panel.png` | Supplementary | Scenario detail |

## Caption Constraints

- Say `real-Cesium MarineCity system smoke test`, not final benchmark result.
- Say `deterministic rule-based AeroGraph verifier` when using current reasoner outputs.
- Do not claim NeRF/3DGS/3D completion performance from these figures.
- For main paper, avoid crop-only figures unless captioned as visual framing evidence.
