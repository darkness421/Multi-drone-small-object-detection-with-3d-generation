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

Current baseline-driven candidates after the 2026-05-19/24 VisDrone results:

- YOLOv12m: current best overall baseline
- YOLOv10m: current second-best medium baseline
- YOLOv9s: current best lightweight/small baseline

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
- SE neck attention as a low-cost channel recalibration baseline.
- CBAM neck attention as a stronger channel+spatial attention baseline.
- Partial deformable neck for limited geometric flexibility without making the
  model too heavy.
- Patch / tiling inference for dense small-object scenes.

## Ablation

- baseline
- + Wavelet stem
- + SE neck
- + CBAM neck
- + partial deformable neck
- + Wavelet stem + SE neck
- + Wavelet stem + CBAM neck
- + patch/tiling inference
- full trainable proposed perception module:
  Wavelet stem + CBAM neck + partial deformable neck

The dashboard/stage gate should select the best proposed variant after all
implemented ablations finish. The final proposed model name should not be fixed
before comparing AP/AP50/APsmall/FPS/Params/GFLOPs across these variants.

Top-3 proposed-module screening:

- Run one seed on YOLOv12m, YOLOv10m, and YOLOv9s.
- Attach the same module set to each backbone:
  SE neck, CBAM neck, partial deformable neck, Wavelet+CBAM, and full proposed.
- Use the existing baseline rows as the `baseline/control` ablation reference.
- Select the best backbone/module pair by AP first, AP50/recall/F1 second, and
  Params/GFLOPs/FPS as the deployability tie-breaker.
- Expand only the winner to 3 seeds, then 5 seeds if it becomes the final paper
  candidate.

Config scaffold:

- `configs/detector/proposed_yolo11_small_object.yaml`
- `configs/experiments/proposed_detector_ablation.yaml`
- `configs/experiments/top3_proposed_detector_screening.yaml`
- `configs/experiments/top3_proposed_detector_main.yaml`

Code scaffold:

- `detectors/proposed/`
- `scripts/proposed_ablation_jobs.py`
- `scripts/ubuntu/train_proposed_ablation_after_session.sh`

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

## Queue Policy

The proposed-ablation queue is attached after the VisDrone/UAVDT comparison
supervisors so it does not steal GPUs from baseline runs:

```bash
bash scripts/ubuntu/train_proposed_ablation_after_session.sh
```

Top-3 screening queue:

```bash
bash scripts/ubuntu/train_top3_proposed_ablation_after_session.sh
```

Default behavior is conservative:

- `control` is implemented and can be queued as a real YOLO11s control run.
- `wavelet_stem`, `se_neck`, `cbam_neck`, `partial_deformable_neck`,
  `wavelet_se`, `wavelet_cbam`, and `full_proposed` are implemented as runtime
  model patches and can be queued.
- `tiling_inference` remains eval-only until the tiled detector evaluator is
  complete.
- Planned eval-only modules are not trained by silently reusing the unchanged
  base model.

The queue records the exact `model_patches` string in the command CSV and run
summary, so result collection can separate SE, CBAM, wavelet, deformable, and
full proposed variants in the dashboard.

Collect baseline plus proposed rows:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
```
