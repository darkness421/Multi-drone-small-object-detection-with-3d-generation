# Isaac Sim Notes

Use this folder for Isaac Sim scripts, USD scene notes, and extension setup.

## Expected Flow

1. Install or locate Isaac Sim and run the compatibility/smoke check.
2. Load or create the Haeundae Marine City geospatial scene.
3. Attach Cesium/3D Tiles or another USD/geospatial context.
4. Spawn the planned multi-UAV camera rigs from
   `outputs/experiments/marinecity_isaac_capture_plan.json`.
5. Synchronize RGB, depth, masks, 2D/3D bounding boxes, camera parameters, and
   UAV pose export.
6. Save exported data under `outputs/isaac_exports/`.

## Current Readiness - 2026-06-16

The one-to-two-day startup plan for Isaac / 3D / reasoner experiments is:

```text
docs/isaac_3d_reasoner_readiness_2026-06-16.md
```

Use that note as the active checklist before starting long Isaac exports.

## Repo-Side Dry-Run

Repo-side dry-run is ready:

- `outputs/experiments/marinecity_isaac_dry_run_manifest.json`
- `outputs/experiments/marinecity_isaac_capture_plan.json`
- `outputs/experiments/marinecity_isaac_replicator_template.py`
- `outputs/experiments/marinecity_multiview_benchmark.json`

Current dry-run split:

- 36 planned frames
- 4 scenes
- 6 view angles: nadir, front-oblique, side-view, rear-oblique, right-oblique,
  left-oblique
- 19 train / 7 val / 10 unseen-angle test frames

The actual MarineCity USD/Cesium scene is not present yet. Treat this as capture
protocol readiness, not a completed rendered dataset.

Current start rule:

- Run repo-side readiness anytime.
- Run Isaac visible smoke once the install path and scene/proxy stage are known.
- Start full 3D/reasoner experiments only after a tiny real export validates
  RGB/depth/pose/bbox schema.

## Local Isaac Path

Isaac Sim was not found in the current command PATH during the first environment check.

When installed or located, record it here:

```text
ISAAC_SIM_PATH=<path-to-isaac-sim>
```
