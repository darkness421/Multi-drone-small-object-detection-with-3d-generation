# Proposed Perception Module Plan

## Stage

This starts after the detector baseline sweep. The proposed model should be
compared against both the best overall baseline and the best lightweight
baseline.

## Base Model

Initial candidates:

- YOLO11n
- YOLO11s

Selection depends on the server baseline AP/AP50/APsmall/FPS tradeoff.

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
