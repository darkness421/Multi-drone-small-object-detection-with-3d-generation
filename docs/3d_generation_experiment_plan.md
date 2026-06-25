# 3D Generative Model Experiment Plan

## Goal

Build a Marine City multi-angle benchmark and compare 3D scene representations
for novel-view synthesis, downstream detector robustness, and qualitative
inspection.

This stage can start in parallel on GPU1 while detector baselines and proposed
ablations continue on GPU0. The final detector-dependent downstream numbers
should still use the checkpoint selected by the detector stage gate, but Isaac
Sim setup, MarineCity manifest preparation, and 3D reconstruction smoke tests do
not need to wait for every detector comparison to finish.

Default server allocation:

- GPU0: detector baselines, comparison models, proposed ablations, UAVDT.
- GPU1: MarineCity 3D reconstruction, Isaac Sim export/smoke tasks, local
  VLM/LLM reasoner experiments.

## Reference Methods

The comparison set uses four methods:

- NeRF: canonical MLP radiance field baseline.
- Instant-NGP: fast hash-encoded neural field.
- Mip-NeRF 360: stronger outdoor/unbounded-scene radiance-field reference.
- 3D Gaussian Splatting: explicit anisotropic Gaussian representation for
  real-time rendering.

The user-provided review links cover NeRF, 3D Gaussian Splatting, and
Instant-NGP. Implementation planning follows the original paper definitions:
NeRF as continuous 5D radiance/density field, Instant-NGP as multiresolution
hash encoding, and 3DGS as optimized anisotropic 3D Gaussians with
visibility-aware splatting.

## Marine City Multi-Angle Benchmark

Legacy dry-run benchmark manifest:

- `outputs/experiments/marinecity_multiview_benchmark.json`

The legacy manifest above was useful for schema and split planning, but its
early RGB/depth files were dry-run placeholders. Do not cite that dry-run as a
completed real-Cesium dataset export.

Verified real-Cesium capture benchmark:

- `outputs/experiments/marinecity_real_capture_benchmark.json`
- `outputs/experiments/marinecity_real_capture_benchmark.csv`
- `outputs/reports/live/marinecity_real_capture_benchmark.md`
- `outputs/reports/live/marinecity_real_capture_benchmark_contact_sheet.png`

Readiness status on 2026-06-26:

- Real-Cesium capture source built from
  `/home/oem/UAV/uav_marinecity/outputs/isaac_exports`.
- Current selected scenarios: S0/S1/S2 viewer160 session recaptures.
- Captures: 3 scenarios x 3 UAV views = 9 RGB/depth/pose frames.
- UAV observation altitude band: 140/150/160 m.
- RGB resolution: 1280 x 720.
- Mean black/void ratio: 0.0914.
- Mean finite-depth ratio: 0.9083.
- Cesium World Terrain and Google Photorealistic 3D Tiles are valid in all
  selected scenarios.
- This is ready for depth-backed evidence-graph and reasoner smoke tests, but
  it is not yet a completed NeRF/Instant-NGP/Mip-NeRF 360/3DGS training result.

Earlier readiness status on 2026-06-08:

- Repo-side dry-run passed with normal Python, without Isaac imports.
- Generated files:
  - `outputs/experiments/marinecity_isaac_dry_run_manifest.json`
  - `outputs/experiments/marinecity_isaac_capture_plan.json`
  - `outputs/experiments/marinecity_isaac_replicator_template.py`
  - `outputs/experiments/marinecity_multiview_benchmark.json`
- Current dry-run protocol: 36 planned frames, 4 scenes, 6 view angles.
- Current split: 19 train, 7 val, 10 unseen-angle test.
- GPU1 readiness check passed with about 31 GB free VRAM, but no real 3D
  training was started because the external NeRF/3DGS runner is still a
  placeholder boundary.
- `assets/marinecity/marinecity_base.usd` is not present yet, so this is
  protocol readiness, not a completed Isaac/Cesium dataset export.

Split principle:

- train: seen angles
- val: side-view validation
- test_unseen_angle: rear/right oblique held-out views

The benchmark should include RGB, pose, optional depth, UAV ID, altitude, view
angle, scene ID, and timestamp. This makes view synthesis and downstream object
recognition comparable across methods.

Detector handoff:

- freeze the detector checkpoint selected by the proposed-model gate
- use the same detector for rendered-view downstream AP comparisons
- report whether 3D reconstruction improves final adjudicator decisions or only
  improves qualitative inspection

## Metrics

Quality:

- PSNR
- SSIM
- LPIPS

Efficiency:

- FPS
- training time
- VRAM
- disk size

Downstream:

- detector AP on rendered held-out views
- final adjudicator accuracy gain
- failure categories: holes, floaters, blurry small objects, view-dependent
  artifacts

## Commands

Create benchmark manifest:

```bash
bash scripts/ubuntu/prepare_marinecity_multiview_benchmark.sh \
  datasets/converters/dummy_marinecity_input.json \
  outputs/experiments/marinecity_multiview_benchmark.json
```

Windows dry-run preparation:

```bat
scripts\25_prepare_marinecity_windows_benchmark.bat
```

Visible Isaac Sim smoke check:

```bat
set ISAAC_ROOT=C:\path\to\isaacsim
scripts\26_launch_isaac_marinecity_visible.bat
```

The Windows dry-run writes a schema-valid Isaac manifest, a capture plan, a
Replicator template, and `outputs\experiments\marinecity_multiview_benchmark.json`
without exporting large RGB/depth files.

Linux/Ubuntu installation note:

- NVIDIA's current Isaac Sim documentation describes workstation launch via the
  unpacked standalone app and Python-package installation via NVIDIA's PyPI
  index. Isaac Sim 6.0 documentation is marked as an early developer release, so
  prefer a stable 5.x path for deadline-critical experiments unless the lab
  machine already has a newer working install.
- Official installation references:
  - https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_workstation.html
  - https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_python.html

Do not start long Isaac capture before the visible or headless smoke test
confirms that the camera prims, scene USD, Replicator writer, and output paths
are valid.

Generate tmux jobs for the four methods:

```bash
GPUS=1 bash scripts/ubuntu/train_3d_generators_tmux.sh
```

The Ubuntu 3D launcher defaults to `GPUS=1` so it does not steal GPU0 from the
detector queue.

GPU1 readiness lane:

```bash
bash scripts/ubuntu/start_gpu1_marinecity_lane.sh
```

This lane checks GPU1 resource margin, verifies the MarineCity benchmark/capture
files, and deliberately refuses to start placeholder 3D training unless
`ALLOW_PLACEHOLDER_3D=1` is set. Use it to reserve and monitor GPU1 while the
real 3DGS/Instant-NGP/NeRF runner is being connected.

Collect result JSONs:

```bash
python -m evaluation.generative3d_compare \
  --results-dir outputs/experiments/3d_generation \
  --out outputs/experiments/3d_generation_comparison.csv
```

The current runner is a placeholder boundary. Replace
`generative3d.external_runner` calls with the upstream NeRF/Instant-NGP/Mip-NeRF
360/3DGS training commands once each external environment is installed.

## Strategy For ACCV Submission

The 3D stage should not become an open-ended new-method rabbit hole. For the
ACCV deadline, use established 3D reconstruction/generation methods as the
primary comparison backbone and add only lightweight, evidence-aware modules
that directly support the CoM3D-ACE claim.

Recommended framing:

- Main paper: 3D reconstruction is used to support ambiguity-centric evidence
  completion, multi-view association, and re-observation decisions.
- Supplement: full NeRF/Instant-NGP/Mip-NeRF 360/3DGS quality comparisons,
  training details, extra renderings, and failure cases.
- Avoid claiming a fully new general-purpose 3D generator unless results are
  clearly strong and reproducible by late June.

## Model And Module Plan

Primary methods to run:

| Role | Method | Purpose |
| --- | --- | --- |
| Baseline 1 | NeRF | canonical neural radiance-field reference |
| Baseline 2 | Instant-NGP | fast hash-grid reconstruction baseline |
| Baseline 3 | Mip-NeRF 360 | stronger outdoor/unbounded-scene reference |
| Baseline 4 | 3D Gaussian Splatting | real-time explicit representation baseline |
| Ours-light | 3DGS or Instant-NGP + evidence-aware object weighting | object/evidence-aware reconstruction without building a huge new model |

Do not start by inventing a full 3D generator from scratch. The safer path is:

1. Run existing methods on the MarineCity multi-angle split.
2. Add a small restoration branch only for degraded scenes.
3. Add object/evidence-aware weighting or masking so small-object regions matter
   more during reconstruction/evaluation.
4. Test whether the reconstructed or restored views improve downstream detector
   confidence, association F1, 3D center error, ambiguity resolution, or VLM
   call reduction.

## Restoration Module Scope

Restoration is useful, but it should be a controlled ablation rather than a
second main contribution.

Recommended restoration variants:

| Variant | Use |
| --- | --- |
| No restoration | required baseline |
| Existing image restoration model | rain/snow/low-light pre-processing baseline |
| Lightweight object-aware restoration | optional proposed module; prioritize small-object boxes/crops |
| Full 3D + restoration + graph | system ablation only if stable |

The restoration module should be considered worth main-paper space only if it
improves downstream object evidence, not merely PSNR/SSIM. Good metrics are:

- AP on held-out rendered/restored views.
- small-object recall on degraded scenes.
- association F1 after 3D graph fusion.
- ambiguity resolution rate.
- VLM call reduction for hard weather cases.

## LLM/VLM Order

The LLM/VLM reasoner should come after detector + 3D graph outputs exist. It is
not a substitute for the 3D experiments.

Recommended order:

1. Detector evidence checkpoint selected.
2. MarineCity multi-view/pose data prepared.
3. Existing 3D reconstruction baselines run on a small representative scene set.
4. Optional restoration/object-aware module tested on degraded scenes.
5. 3D evidence graph generates ambiguity cases.
6. Selective LLM/VLM is tested only on high-ambiguity nodes.

This keeps LLM/VLM as a final adjudicator and re-observation planner, not the
core perception engine.

## Figure Timing

Figure work should begin before final 3D results are complete.

| Date Range | Figure Work |
| --- | --- |
| 2026-06-01 to 2026-06-07 | Draw schematic layouts for pipeline, evidence graph, and 3D/restoration branch |
| 2026-06-08 to 2026-06-16 | During 3D smoke tests, save candidate views, failure cases, camera layouts, and before/after panels |
| 2026-06-17 to 2026-06-24 | Replace placeholders with real renders, graph overlays, and reconstruction comparisons |
| 2026-06-25 to 2026-06-28 | Freeze main-paper figures; move extra detector/3D/restoration/LLM panels to supplement |
| 2026-06-29 to 2026-07-05 | Only polish captions, labels, and readability; avoid changing figure claims |

The final figure should not wait until every 3D model is finished. A rough Canva
or SVG layout can be ready now, then real 3D result panels can be dropped in once
the smoke tests and final runs finish.
