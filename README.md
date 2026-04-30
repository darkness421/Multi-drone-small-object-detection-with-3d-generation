# Cooperative Multi-UAV Small Object Detection in Marine City

NVIDIA Isaac Sim, Cesium geospatial context, and a cooperative multi-UAV perception pipeline for small object detection around Haeundae Marine City.

## Goal

Build a simulation and research workspace for:

- Multi-UAV observation in an urban/coastal scene
- Haeundae Marine City geospatial background through Cesium/3D Tiles
- Lightweight YOLO-based small-object candidate detection
- Patch-wavelet feature extraction and multi-view feature fusion
- 3D grounding, confidence reasoning, and re-observation planning

## Local Setup Status

Checked on this PC:

- Git: installed
- Visual Studio Code: installed
- Visual Studio 2022 Professional: installed
- NVIDIA GPU: RTX 4080 detected
- NVIDIA driver/CUDA runtime: detected by `nvidia-smi`

Connected:

- GitHub remote: https://github.com/darkness421/multi-uav-marine-city

Still to install/configure:

- GitHub CLI, optional but useful
- Isaac Sim executable/path
- Cesium ion access token, if using Cesium ion assets

## Repository Layout

```text
config/
  marine_city_scene.yaml
  uav_mission.yaml
docs/
  paper_plan.md
  setup_checklist.md
isaac/
  README.md
src/
  marine_uav_pipeline/
    __init__.py
    geo.py
    mission.py
tools/
  check_environment.ps1
.gitignore
README.md
```

## Next Milestones

1. Install or locate Isaac Sim and verify it can run on the RTX 4080.
2. Create a Cesium ion token and configure the Marine City geospatial scene.
3. Build the first Isaac scene with three UAV camera viewpoints.
4. Add the detection/fusion pipeline and export synchronized frames plus camera poses.
