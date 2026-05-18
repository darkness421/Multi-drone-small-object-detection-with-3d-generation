# Server Training Plan

## Stage

We are rebuilding the detector baseline pipeline for reproducible Ubuntu server
experiments. Long training is launched manually in tmux after checks pass.

## Dataset

Primary baseline dataset: `VisDrone2019-DET`

Sweep config: `configs/detector/server_baseline_sweep.yaml`

Default training settings:

- `imgsz`: 1280
- `epochs`: 100
- `batch`: script argument
- `device`: script argument, using physical GPU ids with `CUDA_DEVICE_ORDER=PCI_BUS_ID`
- deterministic mode is recorded unless `--non-deterministic` is passed

## Models

Baseline sweep:

- YOLOv8n
- YOLOv8s
- YOLOv11n
- YOLOv11s
- YOLOv12n
- YOLOv12s
- RT-DETR family, defaulting to an Ultralytics RT-DETR checkpoint until R18 is available

Expanded comparison sweep after the top-3 seed extension:

- YOLOv5su
- YOLOv9s
- YOLOv10s
- YOLOv26n
- YOLOv26s
- YOLOv12m

The expanded sweep fills comparison gaps across older YOLO generations, YOLO26,
and a medium-capacity model. These runs use the preliminary 3-seed set first.
YOLOv6s and YOLOv7 are treated as optional legacy checkpoints: the queue checks
whether the weights are loadable in the current Ultralytics environment and
skips them automatically if no compatible checkpoint is available.

## Seeds

Preliminary seed set:

- `42, 123, 2026`

Main statistical seed set:

- `42, 123, 2026, 7, 3407`

Three seeds are preliminary statistical analysis only. Five or more seeds are
used for the main statistical result.

## Strategy

1. Train all baseline models with 3 seeds.
2. Extend the top 2-3 models to 5 seeds.
3. Add the proposed perception module to the best overall baseline or best
   lightweight baseline.

## Core Metrics

Detector baseline ranking focuses on:

- AP / mAP50-95
- AP50
- APsmall when available
- FPS or inference latency
- params / GFLOPs when available

Model size is grouped by measured parameter count, not only by checkpoint suffix:

- `nano`: < 5M params
- `small`: 5M to < 15M params
- `medium`: 15M to < 35M params
- `large`: 35M to < 75M params
- `xlarge`: >= 75M params

The result CSV separates identity and capacity so YOLO generation, model size,
and non-YOLO detectors can be compared without mixing meanings:

- `detector_family`: `YOLO`, `RT-DETR`, `D-FINE`, `DETR`, or `Other`
- `architecture_group`: `yolo` or `non_yolo`
- `model_version`: detector generation such as `v8`, `v12`, `v26`, or `RT-DETR`
- `yolo_version`: YOLO generation only, blank for non-YOLO models
- `model_scale` / `name_size_tag`: checkpoint-name scale such as `nano`,
  `small`, `medium`, `large`, `xlarge`, `base`, or `r18`
- `param_size_group`: measured parameter-count bin
- `size_group`: measured parameter-count bin when available, otherwise the
  checkpoint-name scale

Seed statistics and p-values are computed from repeated seed results. The main
p-value table focuses on AP, AP50, recall, and F1.

## ROC-AUC Definitions

Detector ROC-AUC is confidence based. Object-level detector ROC-AUC labels a
detection positive if it matches a ground-truth object at IoU >= 0.5; unmatched
detections are false positives.

Ambiguity ROC-AUC is separate. It will later use hard-case labels from the
ambiguity scorer and report AUROC/AUPRC/ECE/Brier.

## Ubuntu Commands

Generate and run a two-GPU baseline queue:

```bash
bash scripts/ubuntu/prepare_visdrone_dataset_tmux.sh
bash scripts/ubuntu/preflight_baseline.sh --strict
bash scripts/ubuntu/train_visdrone_baselines_tmux.sh server-visdrone-baselines 100 8 1280
```

The queue runs validation after each training job by default. Set
`RUN_EVAL=0` to train only, or `ROC_AUC=0` to skip detector confidence ROC-AUC.

Run a two-model pair for one seed:

```bash
bash scripts/ubuntu/train_visdrone_pair_tmux.sh visdrone-pair yolov8n.pt yolo11n.pt 42 100 8 1280
```

Watch:

```bash
bash scripts/ubuntu/watch_training.sh server-visdrone-baselines
```

Collect after training:

```bash
bash scripts/ubuntu/collect_server_results.sh
```

Queue the expanded comparison sweep after the current top-3 seed extension:

```bash
bash scripts/ubuntu/train_extra_comparison_models_after_session.sh
```
