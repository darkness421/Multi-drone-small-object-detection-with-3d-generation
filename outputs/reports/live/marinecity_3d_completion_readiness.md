# MarineCity 3D Completion Readiness

Updated: `2026-06-26 13:25:15 KST`
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
- Input dataset manifest: `outputs/experiments/3d_generation/marinecity_real_capture_neural3d/dataset_manifest.json`
- Dataset frames train/heldout: `9` / `6` / `3`
- Transforms: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d/transforms.json`
- Comparison CSV: `outputs/experiments/3d_generation_comparison.csv`
- Comparison rows: `0`
- Metric result rows: `0`
- Result JSON count: `0`
- Methods ready: `[]`
- Missing expected methods: `['nerf', 'instant_ngp', 'mip_nerf_360', 'gaussian_splatting']`

Claiming rule: The real-Cesium RGB/depth/pose capture source and neural-3D transforms package are ready for the 3D handoff. Neural 3D completion/reconstruction remains pending until non-placeholder metric rows are collected.

Next action: run the 3D generation/completion runner on the verified MarineCity captures and collect PSNR/SSIM/LPIPS/FPS/runtime rows before upgrading this from pending to a paper benchmark claim.
