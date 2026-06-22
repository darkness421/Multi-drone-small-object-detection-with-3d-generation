# Windows MarineCity Isaac Setup

This is the Windows-first entrypoint for the MarineCity multi-UAV benchmark.
It prepares the repo-side manifest and capture plan before any long Isaac Sim
export.

## Stage 0: Dry Run

Run from a normal Windows terminal in the repo:

```bat
scripts\25_prepare_marinecity_windows_benchmark.bat
```

This writes:

- `outputs\experiments\marinecity_isaac_dry_run_manifest.json`
- `outputs\experiments\marinecity_isaac_capture_plan.json`
- `outputs\experiments\marinecity_isaac_replicator_template.py`
- `outputs\experiments\marinecity_multiview_benchmark.json`

The dry-run creates tiny placeholder files only. It does not export real RGB,
depth, masks, or videos.

## Stage 1: Visible Isaac Sim Check

Set `ISAAC_ROOT` if Isaac Sim is not installed at `C:\isaacsim`:

```bat
set ISAAC_ROOT=C:\Users\%USERNAME%\AppData\Local\ov\pkg\isaac_sim-*
scripts\26_launch_isaac_marinecity_visible.bat
```

This opens:

- Isaac Sim GUI
- A visible Isaac Python smoke-check terminal

The smoke check verifies that Isaac's Replicator module imports and regenerates
the capture plan/template. It does not start a long capture.

## Stage 2: MarineCity Scene Requirements

The first export target is defined in:

```text
configs\sim\marinecity_windows_export.yaml
```

The scene should eventually contain:

- coastal city USD stage, optionally Cesium/OSM/custom USD assets
- 2, 3, and 4 UAV camera rigs
- vehicles, pedestrians, workers, small boats, debris
- clear/rain/snow conditions
- day/shadow/sunset lighting
- synchronized RGB, depth, masks, 2D/3D bbox, camera params, and UAV pose

## Stage 3: Benchmark Splits

The dry-run benchmark already separates view angles:

- train: seen camera angles
- val: side view
- test: rear/right oblique held-out angles

These splits feed the later 3D generation comparison:

```text
configs\experiments\3d_generation_comparison.yaml
```

## Notes

NVIDIA Isaac Sim versions differ, so the repo keeps Isaac-specific capture code
behind a generated Replicator template. The repo-side schema and benchmark
manifest stay testable with normal Windows Python.

Useful NVIDIA references:

- Isaac Sim Replicator getting-started scripts:
  https://docs.isaacsim.omniverse.nvidia.com/latest/replicator_tutorials/tutorial_replicator_getting_started.html
- Isaac Sim Replicator writers API:
  https://docs.isaacsim.omniverse.nvidia.com/latest/py/source/extensions/isaacsim.replicator.writers/docs/index.html
- Isaac Sim depth/camera examples:
  https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html
