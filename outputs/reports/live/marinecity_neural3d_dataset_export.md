# MarineCity Neural-3D Dataset Export

Updated: `2026-06-26 13:22:49 KST`
Status: `marinecity_neural3d_dataset_export_ready`

## Dataset

- Output directory: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d`
- Transforms: `/home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d/transforms.json`
- Frames/train/heldout: `9` / `6` / `3`
- Copied RGB/depth: `9` / `9`
- Scenarios/UAVs: `3` / `3`
- UAV altitude range: `[140.0, 160.0]` m
- Image size/HFOV: `[1280, 720]` / `55.0` deg
- Split rule: train=uav_01/uav_02 views for each scenario; heldout val/test=uav_03 views

## Runner Handoff

- `ns-train nerfacto --data /home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d`
- `python -m generative3d.external_runner --method instant_ngp --scene marinecity_real_capture --data /home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d`
- `python -m generative3d.external_runner --method gaussian_splatting --scene marinecity_real_capture --data /home/oem/projects/multi-uav-marine-city/outputs/experiments/3d_generation/marinecity_real_capture_neural3d`

Claiming rule: This package is a neural-3D input handoff. It upgrades source readiness, but it is not a NeRF/3DGS metric result.
