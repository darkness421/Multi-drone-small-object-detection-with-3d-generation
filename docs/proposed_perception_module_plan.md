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

## Three-Core Module Direction

Current paper-facing framing:

```text
Frequency-guided ambiguity-aware evidence completion for UAV small objects.
```

Detector-side modules should improve tiny-object evidence while producing
structured uncertainty/evidence that can be consumed later by 3D reconstruction
and the LLM/VLM reasoner. The detector claim remains AP/AP50/APsmall/FPS; the
system claim is tested later through ambiguity resolution and re-observation.

The current detector direction is organized into three core modules. See
`docs/proposed_detector_three_core_modules.md` for the detailed experiment map.

### Core 1. Compact Capacity Redistribution Module

Goal:

- reduce model size or keep the proposed detector below the YOLOv11l parameter
  budget
- redistribute capacity toward P2/P3 small-object evidence instead of spending
  too much capacity on heavy large-object branches

Current candidates:

- `P2CompV3-FR`
- `P2EffV3-FR`
- `P2BalV3-FR`
- `P2P4-FR`, a 4x/8x/16x-only detection-head candidate with `20.82M`
  parameters

### Core 2. Multi-Scale High-Resolution Evidence Module

Goal:

- preserve tiny-object features using P2/stride-4 and high-resolution neck
  outputs
- test the research hypothesis that 4x/8x/16x detection heads are more useful
  for UAV tiny objects than relying on a 32x detection head
- add dynamic frequency refinement around C3/C3k2 outputs, not only a fixed
  input wavelet stem

Current candidates:

- P2 detection head
- P2/P3/P4-only detection head: `Detect(P2/4, P3/8, P4/16)`
- `tiny_frelu_neck`
- `dynfreq_c3_p2`
- `dynfreq_c3_small`
- DCT/wavelet/CBAM variants as supporting ablations

Tiny-object spatial activation:

```text
h(x) = x - AvgPool3x3(x)
c(x) = DWConv3x3(x) + BN(x) + tanh(gamma) h(x)
y = max(x, c(x))
```

This keeps the spatially conditioned FReLU mechanism while biasing the condition
toward small edge/texture evidence. The current implementation is
`tiny_frelu_neck` in `detectors/proposed/modules.py`.

Dynamic frequency C3 refinement:

```text
low = AvgPool3x3(x)
high = x - low
[g_h, g_l] = Gate(GAP(x))
y = x + tanh(alpha) * (g_h * DWConv(high) + g_l * (DWConv(low) - x))
```

The current implementation is `DynFreqC3Refine` in
`detectors/proposed/modules.py`.

### Core 3. Overlap-Aware Small-Object Decision Module

Goal:

- reduce suppression errors for adjacent tiny objects
- separate crowded objects that standard NMS can collapse into one detection
- produce an ambiguity signal for later 3D/reasoner stages

Current candidates:

- class-aware NMS IoU sweep
- Soft-NMS or DIoU/CIoU-NMS if locally implemented
- WBF only for TTA/ensemble supplementary analysis
- adjacent-object subset evaluation for crowded scenes

## Ablation

- baseline
- + Core 1 compact/balanced P2 capacity redistribution
- + Core 2 TinyFReLU
- + Core 2 DynFreq-C3 P2 or P2/P3 refinement
- + Core 3 overlap-aware NMS decision
- supplementary module probes: wavelet stem, DCT stem, SE, CBAM, pooled
  self-attention, partial deformable neck, patch/tiling inference

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
- Expand only the winner to the same 3 seeds used by the comparison models:
  `42`, `123`, and `2026`.

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
- `scripts/ubuntu/start_yolov11_p2_balanced_search.sh`
- `scripts/ubuntu/run_under_param_target_queue.sh`

## Evaluation

Use the same VisDrone protocol as the baseline:

- preliminary 3 seeds: `42, 123, 2026`
- main comparison-consistent seeds: `42, 123, 2026`
- optional supplementary robustness seeds: `7, 3407`
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
