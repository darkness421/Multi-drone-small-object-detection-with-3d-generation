# MarineCity 3D Completion Readiness

Updated: `2026-06-29 23:02:02 KST`
Status: `marinecity_3d_completion_ready`

## Capture Source

- `scenario_count`: `3`
- `frame_count`: `9`
- `uav_count`: `3`
- `altitude_range_m`: `[140.0, 160.0]`
- `terrain_all_valid`: `True`
- `google_tiles_all_valid`: `True`
- `mean_rgb_black_ratio`: `0.09315815489969137`
- `mean_depth_finite_ratio`: `0.9065288628472222`

## Neural 3D Results

- Input dataset ready: `True`
- Runner preflight: `marinecity_3d_runner_preflight_ready`
- Neural runner available: `True`
- Geometry smoke available: `True`
- Runner preflight report: `outputs/reports/live/marinecity_3d_runner_preflight.md`
- Depth point-cloud smoke ready: `True`
- Depth point-cloud points: `7584`
- Depth point-cloud preview: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_depth_pointcloud_smoke/marinecity_depth_pointcloud_smoke_topdown.png`
- Depth view-consistency sanity ready: `True`
- Depth view-consistency manifest: `outputs/experiments/3d_generation/marinecity_depth_view_consistency_sanity/manifest.json`
- Depth view-consistency contact sheet: `/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_depth_view_consistency_sanity.png`
- Depth view-consistency mean PSNR/SSIM/fill: `7.800951022764889` / `0.04476469196276306` / `0.32786820023148144`
- Input dataset manifest: `outputs/experiments/3d_generation/marinecity_real_capture_neural3d/dataset_manifest.json`
- Dataset frames train/heldout: `9` / `6` / `3`
- Transforms: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d/transforms.json`
- Comparison CSV: `outputs/experiments/3d_generation_comparison.csv`
- Comparison rows: `3`
- Metric result rows: `3`
- Result JSON count: `3`
- Methods ready: `['gaussian_splatting', 'instant_ngp', 'nerf']`
- Missing expected methods: `['mip_nerf_360']`

Claiming rule: The real-Cesium RGB/depth/pose capture source, neural-3D transforms package, and depth point-cloud smoke are ready. At least one non-placeholder neural-3D runner metric row upgrades the result to a system-level smoke validation. Do not claim a full 3D benchmark until additional runner families or longer validation runs are collected.

Next action: keep the single-runner Nerfacto row as system smoke evidence, then add Instant-NGP/3DGS or longer validation only if time allows before upgrading to a full benchmark claim.
