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

Current baseline-driven candidates after the 2026-05-19/24 and 2026-06-04
VisDrone results:

- YOLOv11l: current best large baseline, AP 0.3777 / AP50 0.5981 /
  F1 0.6248, 25.32M params, 87.3 GFLOPs.
- YOLOv12l and YOLOv8l: nearly tied large anchors.
- YOLOv12m and YOLOv10m: efficient medium anchors for screening.
- YOLOv9s: lightweight/small fallback.

Current selection rule:

- use the best overall baseline if the goal is maximum detector quality
- use the best lightweight baseline if the goal is deployable multi-UAV
  efficiency
- keep YOLO11n/s as an architecture-friendly fallback only if the full baseline
  sweep shows they are competitive

Selection depends on the final AP/AP50/APsmall/FPS/Params/GFLOPs tradeoff after
all baseline and comparison models are collected.

Updated next-step rule:

- If a proposed module is attached to a medium model, it must either exceed
  YOLOv11l or offer a clearly better efficiency tradeoff.
- If the medium screening remains below YOLOv11l, move the next detector round
  to the YOLOv11 family.
- Primary success target: AP greater than 0.3777 while keeping parameters near
  or below 25.32M. A small AP tie is only useful if Params/GFLOPs and crowded
  small-object recall improve.

## Module Ideas

Current paper-facing framing:

```text
Frequency-guided ambiguity-aware evidence completion for UAV small objects.
```

Detector-side modules should improve tiny-object evidence while producing
structured uncertainty/evidence that can be consumed later by 3D reconstruction
and the LLM/VLM reasoner. The detector claim remains AP/AP50/APsmall/FPS; the
system claim is tested later through ambiguity resolution and re-observation.

- Wavelet stem for small-object high-frequency detail.
- SE neck attention as a low-cost channel recalibration baseline.
- CBAM neck attention as a stronger channel+spatial attention baseline.
- Partial deformable neck for limited geometric flexibility without making the
  model too heavy.
- Patch / tiling inference for dense small-object scenes.
- P2 / stride-4 small-object detection head. The motivation is that stride-32
  features are too coarse for tiny UAV objects; a P2 branch preserves local
  edges and texture before objects collapse to a sub-cell signal.
- Tiny-object spatial activation. We add a FReLU-style activation with a
  learnable high-frequency condition:

```text
h(x) = x - AvgPool3x3(x)
c(x) = DWConv3x3(x) + BN(x) + tanh(gamma) h(x)
y = max(x, c(x))
```

This keeps the spatially conditioned FReLU idea while biasing the condition
toward small edge/texture evidence. The current implementation is
`tiny_frelu_neck` in `detectors/proposed/modules.py`.
- Crowded-object NMS ablation: standard NMS, Soft-NMS, DIoU/CIoU-NMS, WBF for
  TTA/ensembles, and IoU/confidence sweeps on adjacent-object subsets.

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

YOLOv11/P2 next-step screening:

- Use `configs/experiments/yolov11_p2_tiny_activation_next_step.yaml`.
- One-seed screen first:
  - `YOLOv11l + tiny_frelu_neck`
  - `YOLOv11l + CBAM + tiny_frelu_neck`
  - `YOLOv11l-P2 + tiny_frelu_neck`, initialized from `yolo11l.pt`
  - `YOLOv11l-P2 + wavelet + CBAM + tiny_frelu_neck`, initialized from
    `yolo11l.pt`
- The P2 architecture lives in `configs/detector/yolo11-p2.yaml`; calling
  `configs/detector/yolo11l-p2.yaml` lets Ultralytics infer scale `l`.
- Measured model sizes before training:
  - YOLOv11l baseline: 25.32M params / 87.3 GFLOPs from collected runs.
  - YOLOv11l-P2: 26.12M params / 113.6 GFLOPs.
  - YOLOv11m-P2: 20.59M params / 88.9 GFLOPs, promising if `yolo11m.pt`
    becomes available for partial initialization.

Config scaffold:

- `configs/detector/proposed_yolo11_small_object.yaml`
- `configs/experiments/proposed_detector_ablation.yaml`
- `configs/experiments/top3_proposed_detector_screening.yaml`
- `configs/experiments/top3_proposed_detector_main.yaml`
- `configs/experiments/yolov11_p2_tiny_activation_next_step.yaml`
- `configs/detector/yolo11-p2.yaml`

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
supervisors and defaults to GPU0. GPU1 is reserved for 3D reconstruction,
Isaac, and local VLM/LLM system experiments:

```bash
GPUS=0 bash scripts/ubuntu/train_proposed_ablation_after_session.sh
```

Top-3 screening queue:

```bash
GPUS=0 bash scripts/ubuntu/train_top3_proposed_ablation_after_session.sh
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
