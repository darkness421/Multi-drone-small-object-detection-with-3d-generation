# MarineCity Depth View-Consistency Sanity

Updated: `2026-06-29 03:06:17 KST`
Status: `marinecity_depth_view_consistency_sanity_ready`

- Dataset: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d/dataset_manifest.json`
- Contact sheet: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_depth_view_consistency_sanity/marinecity_depth_view_consistency_contact_sheet.png`
- Source UAVs -> target UAV: `['uav_01', 'uav_02']` -> `uav_03`
- Mean fill ratio: `0.328`
- Mean PSNR on filled pixels: `7.80`
- Mean luma SSIM on filled pixels: `0.045`

| Scenario | Sources | Target | Fill | PSNR | SSIM-luma | MAE |
|---|---|---|---:|---:|---:|---:|
| uavmarine_s0_viewer160_session_recapture | uav_01,uav_02 | uav_03 | 0.329 | 7.74 | 0.032 | 82.53 |
| uavmarine_s1_viewer160_session_recapture | uav_01,uav_02 | uav_03 | 0.330 | 7.76 | 0.035 | 82.31 |
| uavmarine_s2_viewer160_session_recapture | uav_01,uav_02 | uav_03 | 0.325 | 7.91 | 0.068 | 80.21 |

Claiming rule: This is a depth-backed cross-view sanity check from real RGB/depth/pose captures. It is not a neural 3D reconstruction benchmark and must not be reported as NeRF/3DGS performance.
