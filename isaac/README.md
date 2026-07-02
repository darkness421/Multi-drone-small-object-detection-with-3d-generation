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

## Current Readiness - 2026-06-22

The active Ubuntu server path is Docker Isaac Sim 5.1.0 on host GPU1. Local
Isaac 4.5 currently stalls during Kit windowing startup, so do not use it for
long experiments.

Verified commands:

```bash
bash scripts/ubuntu/run_gpu1_isaac51_container_smoke.sh
```

```bash
bash scripts/ubuntu/run_gpu1_isaac51_marinecity_stage.sh
```

Current generated GPU1 artifacts:

- `outputs/isaac_exports/marinecity_gpu1_container_smoke/capture_plan.json`
- `outputs/isaac_exports/marinecity_gpu1_container_smoke/isaac_replicator_capture_template.py`
- `outputs/isaac_exports/marinecity_gpu1_stage1/marinecity_proxy_stage.usda`
- `outputs/isaac_exports/marinecity_gpu1_stage1/marinecity_proxy_stage_summary.json`
- `outputs/isaac_exports/marinecity_gpu1_stage1/capture_plan.json`
- `outputs/isaac_exports/marinecity_gpu1_stage1/isaac_replicator_capture_template.py`
- `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct_capture_summary.json`
- `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/*_rgb.png`
- `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/*_depth.npy`
- `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/*_bbox_preview.png`

Tiny real export status:

- Passed on Docker Isaac Sim 5.1.0 / host GPU1.
- 3 UAV camera views are exported at 1280x720.
- RGB, distance-to-camera depth, semantic/instance segmentation, tight 2D
  boxes, 3D boxes, camera parameters, bbox JSON, and bbox preview images are
  available.
- Bbox counts in the proxy smoke export are 7, 10, and 12 across the three UAV
  views.
- This validates the export schema for the 3D/reasoner lane. The remaining
  realism upgrade is replacing the proxy geometry with Cesium/MarineCity tiles.

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

The GPU1 proxy USD stage now contains 3 UAV camera rigs, 12 fine-grained proxy
objects, road/coastal/building context, and ambiguity clusters. Treat this as
Isaac/protocol readiness, not a completed rendered dataset. Real proxy
RGB/depth/bbox export is connected; the final Cesium MarineCity scene still
needs to be connected.

Current start rule:

- Run repo-side readiness anytime.
- Run Isaac visible smoke once the install path and scene/proxy stage are known.
- Start proxy 3D/reasoner smoke now that the tiny real export validates
  RGB/depth/pose/bbox schema.
- Start full MarineCity/Cesium experiments after the geospatial stage is
  connected.

## Local Isaac Path

Isaac Sim was not found in the current command PATH during the first environment check.

When installed or located, record it here:

```text
ISAAC_SIM_PATH=<path-to-isaac-sim>
```
