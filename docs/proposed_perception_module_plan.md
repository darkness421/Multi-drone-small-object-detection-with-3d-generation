# Proposed Perception Module Plan

## Stage

This starts after the detector baseline and expanded comparison sweeps are
complete enough to identify both:

- best overall baseline
- best lightweight baseline

The proposed model should not be tuned before the comparison set is stable.
After proposed ablations finish, move to the 3D generation and Marine City
benchmark stage only if the proposed model outperforms both selected comparison
targets on the detector gate metrics.

## Base Model

Initial candidates:

- YOLO11n
- YOLO11s

Current selection rule:

- use the best overall baseline if the goal is maximum detector quality
- use the best lightweight baseline if the goal is deployable multi-UAV
  efficiency
- keep YOLO11n/s as an architecture-friendly fallback only if the full baseline
  sweep shows they are competitive

Selection depends on the final AP/AP50/APsmall/FPS/Params/GFLOPs tradeoff after
all baseline and comparison models are collected.

## Module Ideas

- Wavelet stem for small-object high-frequency detail.
- Partial deformable neck for limited geometric flexibility without making the
  model too heavy.
- Patch / tiling inference for dense small-object scenes.

## Ablation

- baseline
- + Wavelet stem
- + partial deformable neck
- + patch/tiling inference
- full proposed perception module

Config scaffold:

- `configs/detector/proposed_yolo11_small_object.yaml`

Code scaffold:

- `detectors/proposed/`

## Evaluation

Use the same VisDrone protocol as the baseline:

- preliminary 3 seeds: `42, 123, 2026`
- main 5 seeds: `42, 123, 2026, 7, 3407`
- AP/AP50/APsmall/FPS as core metrics
- p-values from paired seed results
- qualitative examples and Grad-CAM cases matched to the baseline models

Stage gate:

```bash
bash scripts/ubuntu/check_detector_stage_gate.sh
```

The gate recommends one of:

- `finish_baselines_then_build_proposed`
- `iterate_proposed_detector`
- `proceed_to_3d_benchmark`
