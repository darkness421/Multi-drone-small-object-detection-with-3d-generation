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
- `device`: script argument, with physical GPU split through `CUDA_VISIBLE_DEVICES`
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
