# Isaac / 3D / Reasoner Readiness Plan

Updated: 2026-06-22 04:46 KST

This note is the short operational plan for starting the MarineCity Isaac Sim,
3D reconstruction, and AeroGraph Reasoner experiments in the next one to two
days while the 2D detector queue continues.

## Current Status

Detector lane:

- GPU0 is currently running the related-work consistency queue.
- GPU1 is assigned to the Isaac / 3D / reasoner lane while detector work
  continues on GPU0.
- Do not interrupt active detector runs just to start a long Isaac export.
- The selected 2D detector is named `SAFR-YOLO`; the current implementation
  label is `P2P4-SelfAttnFR`, and final numbers should use the confirmed
  3-seed checkpoint.

MarineCity/Isaac lane:

- Repo-side dry-run is ready.
- Ubuntu server Isaac status as of 2026-06-22:
  - Local Isaac 4.5 launch path hangs at the Kit windowing layer and should not
    be used for long experiments.
  - Docker Isaac Sim 5.1.0 on host GPU1 passes compatibility/smoke checks.
  - The container sees only one RTX 5090, exposed internally as active GPU 0.
  - Reusable launch scripts:
    - `scripts/ubuntu/run_gpu1_isaac51_container_smoke.sh`
    - `scripts/ubuntu/start_gpu1_isaac51_container_smoke.sh`
    - `scripts/ubuntu/run_gpu1_isaac51_marinecity_stage.sh`
    - `scripts/ubuntu/start_gpu1_isaac51_marinecity_stage.sh`
- Historical GPU1 Isaac artifacts from early smoke checks, kept for traceability
  only and not used as paper-facing MarineCity evidence:
  - `outputs/isaac_exports/marinecity_gpu1_container_smoke/capture_plan.json`
  - `outputs/isaac_exports/marinecity_gpu1_container_smoke/isaac_replicator_capture_template.py`
  - `outputs/isaac_exports/marinecity_gpu1_stage1/marinecity_proxy_stage.usda`
  - `outputs/isaac_exports/marinecity_gpu1_stage1/marinecity_proxy_stage_summary.json`
  - `outputs/isaac_exports/marinecity_gpu1_stage1/capture_plan.json`
  - `outputs/isaac_exports/marinecity_gpu1_stage1/isaac_replicator_capture_template.py`
  - `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct_capture_summary.json`
  - `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_001_uav_01_rgb.png`
  - `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_002_uav_02_rgb.png`
  - `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_003_uav_03_rgb.png`
- Existing generated files:
  - `outputs/experiments/marinecity_isaac_dry_run_manifest.json`
  - `outputs/experiments/marinecity_isaac_capture_plan.json`
  - `outputs/experiments/marinecity_isaac_replicator_template.py`
  - `outputs/experiments/marinecity_multiview_benchmark.json`
  - `outputs/experiments/marinecity_multiview_benchmark_readiness.json`
- Current dry-run protocol:
  - 36 planned frames
  - 4 scenes
  - train / val / unseen-angle test split
  - RGB, depth, mask, 2D/3D bbox, camera parameter, and pose fields planned
- The old proxy-stage camera check used mixed altitudes and is no longer the
  active simulation target. For the real Cesium MarineCity lane, use the
  user-verified UAV-style altitude band of `140--160 m`:
  - S0: `140/150/160 m`
  - S1: `145/150/155 m`
  - S2: `160/150/140 m`
  Keep this separate from CesiumGeoreference height and old `900 m` debug
  viewpoints.
- The tiny real Isaac export is now validated on Docker Isaac 5.1/GPU1 with
  direct Replicator annotators:
  - 3 UAV camera RGB exports at 1280x720
  - distance-to-camera depth arrays and preview PNGs
  - semantic/instance segmentation payloads
  - tight 2D boxes and 3D boxes
  - camera parameters
  - bbox overlay preview PNGs
  - bbox counts by view: 7, 10, and 12
- Real-Cesium MarineCity actor-session smoke export is complete for S0/S1/S2.
  The remaining work is paper-quality recapture/framing and external-provider reasoner
  validation, not a proxy-city replacement.
- Real NeRF/Instant-NGP/Mip-NeRF 360/3DGS runners are not connected yet; the
  current 3D runner boundary is intentionally a placeholder.

Reasoner lane:

- The reasoner should start as a system-level smoke test after detector outputs
  and MarineCity multi-view evidence exist.
- Do not make the LLM/VLM always-on. The main claim should be selective
  graph-grounded reasoning for ambiguous objects.
- Cosmos is not required for the first ACCV reasoner experiment. Keep it as an
  optional later world-model/video-generation path, not the default reasoner.

## Day 0: Preparation Before Heavy Isaac Work

Goal: make the next Isaac session a smoke/export session, not debugging chaos.

Checklist:

- Confirm the Isaac Sim install path.
  - Windows default: `C:\isaacsim`
  - Otherwise set `ISAAC_ROOT` before running the launch script.
- Confirm whether the MarineCity scene source is:
  - local USD under `assets/marinecity/`,
  - Cesium/3D Tiles loaded in Isaac/Omniverse,
  - or a temporary proxy city stage for the first export.
- Regenerate the repo-side manifest if the scene plan changes.
- Keep `GPU0` for detector training.
- Use `GPU1` for Isaac/3D/reasoner only when it is not running detector work.
- Freeze the detector checkpoint for downstream tests once the current 3-seed
  confirmation is stable.

Useful commands:

```bash
bash scripts/ubuntu/start_gpu1_isaac51_container_smoke.sh
```

```bash
bash scripts/ubuntu/start_gpu1_isaac51_marinecity_stage.sh
```

```bash
CONTAINER_NAME=isaac-gpu1-rep-direct-$(date +%Y%m%d-%H%M%S) \
HOST_OUT=outputs/isaac_exports/marinecity_gpu1_replicator_direct \
CONTAINER_OUT=/tmp/com3d_isaac_replicator_direct \
SCRIPT=simulation/isaac/capture_marinecity_replicator_direct.py \
TIMEOUT_SECONDS=540 FRAMES=1 \
bash scripts/ubuntu/run_gpu1_isaac51_proxy_capture.sh
```

```bat
scripts\25_prepare_marinecity_windows_benchmark.bat
set ISAAC_ROOT=C:\path\to\isaacsim
scripts\26_launch_isaac_marinecity_visible.bat
```

## Day 1: Isaac Smoke And Tiny Export

Goal: produce a very small real Isaac export before attempting the full dataset.

Smoke export target:

- Load the MarineCity or proxy city stage.
- Create 2 to 4 UAV camera prims.
- Capture 5 to 10 frames first.
- Export:
  - RGB
  - depth or distance-to-camera
  - semantic/instance masks
  - tight 2D boxes
  - 3D boxes
  - camera parameters
  - UAV pose
- Save under `outputs/isaac_exports/marinecity_smoke/`.

Pass condition:

- The exported files load from normal Python.
- Every frame has a camera pose, image path, and object metadata.
- At least one ambiguous small-object case is visible enough for detector and
  reasoner smoke tests.

Current result:

- Historical proxy smoke passed on 2026-06-22 with
  `outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/`; this remains
  internal only.
- Real-Cesium MarineCity viewer160 actor-session smoke is complete for S0/S1/S2
  with detector tokens and deterministic rule-based AeroGraph verifier outputs. It should be
  treated as system-validation evidence, while final paper visuals still require
  cleaner recapture/framing from the user-verified live Isaac view.

Failure handling:

- Do not substitute a fake/proxy city for paper-facing MarineCity evidence. If
  Cesium tiles fail, stop with diagnostics and keep any proxy output as
  internal schema validation only.
- If Isaac 4.5 local launch stalls, use the Docker 5.1.0 path. This is the
  verified Ubuntu server path for GPU1.

## Day 2: 3D And Reasoner Smoke

Goal: verify the full downstream chain on a tiny subset.

3D reconstruction smoke:

- Start with 3D Gaussian Splatting or Instant-NGP first because they are the
  fastest practical smoke-test candidates.
- Keep NeRF and Mip-NeRF 360 as comparison methods after the data path works.
- Save initial outputs under `outputs/experiments/3d_generation/`.

Reasoner smoke:

- Build graph evidence from detector outputs and multi-view geometry.
- Select only high-ambiguity object hypotheses.
- Run these methods:
  - detector-only
  - detector + 3D evidence graph
  - detector + 3D graph + AeroGraph Reasoner
  - detector + 3D graph + AeroGraph Reasoner + re-observation policy
- Cache all LLM/VLM responses before analysis.
- Use API/closed LLM first if speed is important; use local VLM/LLM on GPU1 only
  when it will not block detector or 3D jobs.

Minimum reasoner output schema:

```json
{
  "object_id": "obj_0001",
  "decision": "accept|revise|reobserve|reject",
  "class_name": "sedan",
  "confidence": 0.0,
  "evidence": ["multi-view agreement", "geometry residual", "visual cue"],
  "requested_next_view": "side_view",
  "safety_check": "passed"
}
```

## Metrics To Prepare

3D metrics:

- PSNR
- SSIM
- LPIPS
- FPS
- train time
- VRAM
- disk size
- detector AP on rendered held-out views
- small-object failure cases: holes, floaters, blur, view-dependent artifacts

Reasoner metrics:

- final object accuracy
- ambiguity resolution rate
- correction rate
- over-correction rate
- re-observation success
- LLM/VLM call count
- latency
- token/cost proxy
- JSON parse success
- explanation usefulness

## Main Paper vs Supplement

Main paper:

- Explain why the 3D benchmark exists.
- Show one compact MarineCity/Isaac figure.
- Report detector-only vs detector+3D vs detector+3D+reasoner once measured.
- Keep the claim self-contained.

Supplement:

- Full Isaac export details.
- Camera trajectories and scene taxonomy.
- 3D method hyperparameters.
- Extra qualitative renderings.
- Reasoner prompt, JSON schema, cached response examples, and failure cases.

## Start Gate

Start full Isaac/3D work when at least two of these are true:

- GPU1 is free or intentionally assigned to the system lane. Done on 2026-06-22.
- A confirmed detector checkpoint is available for downstream evaluation.
- The real Cesium MarineCity USD scene loads successfully in Isaac. The current
  saved base is `/home/oem/UAV/uav_marinecity/uavmarine.usd`.
- The tiny smoke export writes RGB/depth/pose/bbox files without schema errors.
  Done on 2026-06-22 with the Replicator direct v5 export.

After this gate, keep the system lane on the real Cesium actor-session workflow:
clean recapture, detector tokens, 3D evidence grouping, and external-provider AeroGraph
Reasoner evaluation.

## Official References

- Isaac Sim requirements:
  https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html
- Isaac Sim Replicator getting-started scripts:
  https://docs.isaacsim.omniverse.nvidia.com/latest/replicator_tutorials/tutorial_replicator_getting_started.html
- Isaac Sim standalone Python environment:
  https://docs.isaacsim.omniverse.nvidia.com/latest/python_scripting/manual_standalone_python.html
