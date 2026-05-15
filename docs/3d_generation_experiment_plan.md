# 3D Generative Model Experiment Plan

## Goal

Build a Marine City multi-angle benchmark and compare 3D scene representations
for novel-view synthesis, downstream detector robustness, and qualitative
inspection.

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

Benchmark manifest:

- `outputs/experiments/marinecity_multiview_benchmark.json`

Split principle:

- train: seen angles
- val: side-view validation
- test_unseen_angle: rear/right oblique held-out views

The benchmark should include RGB, pose, optional depth, UAV ID, altitude, view
angle, scene ID, and timestamp. This makes view synthesis and downstream object
recognition comparable across methods.

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

Generate tmux jobs for the four methods:

```bash
bash scripts/ubuntu/train_3d_generators_tmux.sh
```

Collect result JSONs:

```bash
python -m evaluation.generative3d_compare \
  --results-dir outputs/experiments/3d_generation \
  --out outputs/experiments/3d_generation_comparison.csv
```

The current runner is a placeholder boundary. Replace
`generative3d.external_runner` calls with the upstream NeRF/Instant-NGP/Mip-NeRF
360/3DGS training commands once each external environment is installed.
