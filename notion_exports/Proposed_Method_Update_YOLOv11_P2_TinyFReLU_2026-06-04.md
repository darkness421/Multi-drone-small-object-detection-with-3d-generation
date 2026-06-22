# Proposed Method Update - YOLOv11 + P2 + TinyFReLU

Updated: 2026-06-04

## Decision

The next detector-side proposal should move from medium YOLO screening to the YOLOv11 family if the current medium candidates remain below the best large baseline.

Current best baseline:

| Method | AP | AP50 | F1 | Params | GFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| YOLOv11l | 0.3777 | 0.5981 | 0.6248 | 25.32M | 87.3 |

The paper-facing success condition is not simply higher AP. The preferred result is:

- AP higher than YOLOv11l.
- Params near or below 25.32M.
- GFLOPs near YOLOv11l if possible.
- Better recall on tiny / adjacent / crowded objects.

## Next Proposed Detector Candidates

| Candidate | Purpose | Init | Expected Cost |
| --- | --- | --- | --- |
| YOLOv11l + TinyFReLU neck | Activation-only test | yolo11l.pt | near YOLOv11l |
| YOLOv11l + CBAM + TinyFReLU | Attention + activation | yolo11l.pt | slightly above YOLOv11l |
| YOLOv11l-P2 + TinyFReLU | stride-4 tiny-object head | partial yolo11l.pt | 26.12M / 113.6 GFLOPs |
| YOLOv11l-P2 + Wavelet + CBAM + TinyFReLU | full small-object variant | partial yolo11l.pt | highest next-step cost |

Optional efficient variant:

- YOLOv11m-P2 has 20.59M params and 88.9 GFLOPs, which fits the efficiency story better, but `yolo11m.pt` is not currently available locally. Use it after downloading or preparing weights.

## TinyFReLU Activation

The activation is a modified FReLU-style spatial activation for small objects:

```text
h(x) = x - AvgPool3x3(x)
c(x) = BN(DWConv3x3(x)) + tanh(gamma) h(x)
y = max(x, c(x))
```

Reasoning:

- FReLU adds spatial conditioning to ReLU-style activation.
- The added high-frequency residual preserves weak edge and texture cues.
- This is useful for tiny UAV objects that disappear after coarse downsampling.

Implementation:

- `detectors/proposed/modules.py`
- Patch name: `tiny_frelu_neck`

## P2 / 4-Fold Downsampling Head

The new P2 config is:

- `configs/detector/yolo11-p2.yaml`

Ultralytics can be called with:

- `configs/detector/yolo11l-p2.yaml`
- `configs/detector/yolo11m-p2.yaml`

The YAML adds Detect(P2, P3, P4, P5), where P2 is stride 4. This directly targets tiny and adjacent objects where stride-32 feature maps are too coarse.

## NMS / Adjacent Object Follow-Up

After a promising checkpoint exists, run post-processing sweeps:

- standard NMS
- Soft-NMS linear / Gaussian
- DIoU-NMS or CIoU-NMS
- WBF for TTA or ensemble checkpoints
- IoU thresholds: 0.45, 0.55, 0.65, 0.75
- confidence thresholds: 0.001, 0.01, 0.05

Report separately on:

- all validation frames
- tiny objects
- adjacent / overlapping boxes
- high-density frames

## Files Updated

- `detectors/proposed/modules.py`
- `detectors/ultralytics_runner.py`
- `detectors/train_yolo.py`
- `scripts/proposed_ablation_jobs.py`
- `configs/detector/yolo11-p2.yaml`
- `configs/experiments/yolov11_p2_tiny_activation_next_step.yaml`
- `docs/proposed_perception_module_plan.md`
- `docs/current_experiment_steps.md`
- Overleaf method/setup/results/ablation text

## Next Action

Keep the current screening monitor running:

```bash
tmux attach -t server-proposed-metrics
```

If the current medium candidates remain below YOLOv11l, start the YOLOv11/P2/TinyFReLU next-step queue from:

```text
configs/experiments/yolov11_p2_tiny_activation_next_step.yaml
```
