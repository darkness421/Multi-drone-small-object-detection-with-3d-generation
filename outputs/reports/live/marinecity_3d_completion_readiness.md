# MarineCity 3D Completion Readiness

Updated: `2026-06-27 13:45:26 KST`
Status: `marinecity_3d_input_dataset_ready_metrics_pending`

## Capture Source

- `scenario_count`: `3`
- `frame_count`: `9`
- `uav_count`: `3`
- `altitude_range_m`: `[140.0, 160.0]`
- `terrain_all_valid`: `True`
- `google_tiles_all_valid`: `True`
- `mean_rgb_black_ratio`: `0.0913768325617284`
- `mean_depth_finite_ratio`: `0.908344425154321`

## Neural 3D Results

- Input dataset ready: `True`
- Runner preflight: `marinecity_3d_runner_preflight_ready`
- Neural runner available: `False`
- Geometry smoke available: `True`
- Runner preflight report: `outputs/reports/live/marinecity_3d_runner_preflight.md`
- Depth point-cloud smoke ready: `True`
- Depth point-cloud points: `7584`
- Depth point-cloud preview: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_depth_pointcloud_smoke/marinecity_depth_pointcloud_smoke_topdown.png`
- Depth view-consistency sanity ready: `True`
- Depth view-consistency manifest: `outputs/experiments/3d_generation/marinecity_depth_view_consistency_sanity/manifest.json`
- Depth view-consistency contact sheet: `/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_depth_view_consistency_sanity.png`
- Depth view-consistency mean PSNR/SSIM/fill: `10.006380179999477` / `0.41711997326617684` / `0.23139286747685184`
- Input dataset manifest: `outputs/experiments/3d_generation/marinecity_real_capture_neural3d/dataset_manifest.json`
- Dataset frames train/heldout: `9` / `6` / `3`
- Transforms: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d/transforms.json`
- Comparison CSV: `outputs/experiments/3d_generation_comparison.csv`
- Comparison rows: `0`
- Metric result rows: `0`
- Result JSON count: `0`
- Methods ready: `[]`
- Missing expected methods: `['nerf', 'instant_ngp', 'mip_nerf_360', 'gaussian_splatting']`

Claiming rule: The real-Cesium RGB/depth/pose capture source, neural-3D transforms package, and depth point-cloud smoke are ready for the 3D handoff. Neural 3D completion/reconstruction remains pending until non-placeholder metric rows are collected.

Next action: run the 3D generation/completion runner on the verified MarineCity captures and collect PSNR/SSIM/LPIPS/FPS/runtime rows before upgrading this from pending to a paper benchmark claim.
