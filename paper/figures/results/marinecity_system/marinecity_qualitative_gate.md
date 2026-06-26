# MarineCity Qualitative Gate

Updated: `2026-06-26 10:34:13 KST`
Status: `marinecity_qualitative_gate_main_ready`

## Gate Checks

| Check | Value |
| --- | --- |
| `real_cesium_ok` | `True` |
| `system_smoke_ok` | `True` |
| `crop_supplementary_ready` | `True` |
| `full_frame_main_ready` | `True` |
| `google_tiles_valid` | `True` |
| `terrain_valid` | `True` |
| `fake_or_substitute_city_created` | `False` |

## Thresholds

| Metric | Threshold |
| --- | ---: |
| `full_black_max` | `0.1` |
| `mean_top3_black_max` | `0.15` |
| `crop_black_max` | `0.02` |
| `crop_area_min` | `0.35` |
| `min_token_tests` | `10` |

## Current Best Full-Frame Candidate

- Capture: `uavmarine_s2_viewer160_session_recapture`
- Image: `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_002_uav_02_rgb.png`
- Best black/void ratio: `0.017828`
- Mean top-3 black/void ratio: `0.087552`
- Camera profile: `viewer160_clean_fullframe`

## Current Best Crop Candidate

- Capture: `uavmarine_s2_viewer160_session_recapture`
- Source: `/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_002_uav_02_rgb.png`
- Crop path: `outputs/reports/live/marinecity_real_capture_crops/crops/uavmarine_s2_viewer160_session_recapture_frame_002_uav_02_rgb_crop.png`
- Black/void ratio: `0.003577`
- Area ratio: `0.9025`
- Score: `1.115215`

## System Smoke Evidence

- Manifest: `outputs/reports/live/marinecity_system_test_10plus/manifest.json`
- Status: `marinecity_system_test_artifacts_complete`
- Scenarios: `3`
- Token-level tests: `49`

## Claiming Rule

Main paper full-frame qualitative figure may be promoted.

## Next Actions

- Use the current full-frame real-Cesium MarineCity capture as the main-paper qualitative candidate.
- Keep the live real-Cesium MarineCity GUI at the user-verified 160 m review view.
- Use the reviewed AeroGraph candidate table with a caveat; reserve final reasoning claims for external-provider replication.
- Regenerate paper tables and figure manifests after any GPT/Factory/local provider replication pass.
