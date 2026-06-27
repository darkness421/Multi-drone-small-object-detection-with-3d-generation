# MarineCity Depth View-Consistency Sanity

Updated: `2026-06-27 13:45:26 KST`
Status: `marinecity_depth_view_consistency_sanity_ready`

- Dataset: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d/dataset_manifest.json`
- Contact sheet: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_depth_view_consistency_sanity/marinecity_depth_view_consistency_contact_sheet.png`
- Source UAVs -> target UAV: `['uav_01', 'uav_02']` -> `uav_03`
- Mean fill ratio: `0.231`
- Mean PSNR on filled pixels: `10.01`
- Mean luma SSIM on filled pixels: `0.417`

| Scenario | Sources | Target | Fill | PSNR | SSIM-luma | MAE |
|---|---|---|---:|---:|---:|---:|
| uavmarine_s0_viewer160_session_recapture | uav_01,uav_02 | uav_03 | 0.231 | 9.99 | 0.417 | 54.81 |
| uavmarine_s1_viewer160_session_recapture | uav_01,uav_02 | uav_03 | 0.231 | 10.05 | 0.426 | 54.13 |
| uavmarine_s2_viewer160_session_recapture | uav_01,uav_02 | uav_03 | 0.232 | 9.97 | 0.408 | 54.72 |

Claiming rule: This is a depth-backed cross-view sanity check from real RGB/depth/pose captures. It is not a neural 3D reconstruction benchmark and must not be reported as NeRF/3DGS performance.
