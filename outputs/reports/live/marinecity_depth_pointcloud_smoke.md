# MarineCity Depth Point-Cloud Smoke

Updated: `2026-06-26 22:50:56 KST`
Status: `marinecity_depth_pointcloud_smoke_ready`

- Dataset status: `marinecity_neural3d_dataset_export_ready`
- Frames: `9`
- Points: `7584`
- PLY: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_depth_pointcloud_smoke/marinecity_depth_pointcloud_smoke.ply`
- Preview: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_depth_pointcloud_smoke/marinecity_depth_pointcloud_smoke_topdown.png`
- Paper preview: `/home/oem/projects/multi-uav-marine-city/paper/figures/results/marinecity_system/marinecity_depth_pointcloud_smoke_topdown.png`
- Bounds XYZ: `[[-200.243896484375, 109.62438201904297], [-205.28025817871094, 107.87459564208984], [-174.09237670898438, 35.32783508300781]]`
- Sampling stride: `32`; max depth `500.0` m

## Frame Counts

| Scenario | UAV | Split | Valid points | Altitude |
|---|---|---|---:|---:|
| uavmarine_s0_viewer160_session_recapture | uav_01 | train | 889 | 140.0 |
| uavmarine_s0_viewer160_session_recapture | uav_02 | train | 907 | 150.0 |
| uavmarine_s0_viewer160_session_recapture | uav_03 | test | 727 | 160.0 |
| uavmarine_s1_viewer160_session_recapture | uav_01 | train | 889 | 140.0 |
| uavmarine_s1_viewer160_session_recapture | uav_02 | train | 907 | 150.0 |
| uavmarine_s1_viewer160_session_recapture | uav_03 | test | 727 | 160.0 |
| uavmarine_s2_viewer160_session_recapture | uav_01 | train | 889 | 140.0 |
| uavmarine_s2_viewer160_session_recapture | uav_02 | train | 907 | 150.0 |
| uavmarine_s2_viewer160_session_recapture | uav_03 | test | 742 | 160.0 |

Claiming rule: This is a depth-fused geometry smoke artifact from real-Cesium RGB/depth/pose captures. It is not a neural NeRF/3DGS reconstruction benchmark.
