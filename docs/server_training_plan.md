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
- YOLOv10n
- YOLOv10s
- YOLOv26n
- YOLOv26s
- YOLOv12m
- LRDS-YOLO, as an external paper-specific UAV small-object detector if a
  loadable implementation/checkpoint is available

The expanded sweep fills comparison gaps across older YOLO generations, YOLO26,
YOLOv10, paper-specific UAV detectors, and medium-capacity models. These runs
use the preliminary 3-seed set first.
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

1. Train all YOLO and non-YOLO baseline/comparison models with the preliminary
   3-seed set.
2. Extend the top 2-3 models to the 5-seed main statistical set.
3. Freeze the best overall baseline and best lightweight baseline as the
   comparison targets.
4. Modify the proposed perception model around the selected base detector.
5. Continue to 3D generation and Marine City benchmark construction only after
   the proposed detector outperforms both the best overall and best lightweight
   comparison targets on the agreed detector metrics.

This stage order avoids tuning the proposed module against an incomplete
comparison set.

## Cross-Dataset Baselines

After the VisDrone comparison sweep is stable, run a smaller representative
baseline set on UAVDT for cross-dataset validation:

- YOLOv8s
- YOLOv12s
- YOLOv11s
- YOLOv9s
- YOLOv10s
- YOLOv26s
- RT-DETR-L

UAVDT is not trained until the dataset readiness check passes. Expected raw
layout:

```text
data/raw/UAVDT/
  images/<sequence>/*.jpg
  annotations/<sequence>.txt
```

The converter also accepts common frame names such as `img000001.jpg` and
`000001.jpg`.

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

For a clean from-scratch server comparison restart, use the unified fresh queue:

```bash
bash scripts/ubuntu/restart_fresh_server_queue.sh
```

This stops older training/pending tmux sessions, preserves existing outputs,
starts one `server-fresh-baselines` queue with GPU0/GPU1 workers, opens a
side-by-side viewer, and points the live dashboard at a run-specific detector
root.

Realtime monitoring after the fresh queue starts:

```bash
tmux attach -t server-training-dual-view
tmux attach -t server-fresh-baselines
tmux attach -t server-baseline-monitor
```

The browser viewer refreshes the current training log, live metric table,
combined dashboard, and separated report figures for AP/AP50,
precision/recall/F1, seed AP distribution, Params-vs-AP, GFLOPs-vs-AP, and
FPS-vs-AP.

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

Check the detector stage gate:

```bash
bash scripts/ubuntu/check_detector_stage_gate.sh
```

The gate writes:

- `outputs/experiments/detector_stage_gate.json`
- `outputs/experiments/detector_stage_gate.md`

Queue the expanded comparison sweep after the current top-3 seed extension:

```bash
bash scripts/ubuntu/train_extra_comparison_models_after_session.sh
```

Prepare UAVDT after placing or staging the dataset:

```bash
SOURCE=/path/to/UAVDT bash scripts/ubuntu/prepare_uavdt_dataset.sh
```

Queue UAVDT cross-dataset baselines after the VisDrone queues:

```bash
bash scripts/ubuntu/train_uavdt_comparisons_after_session.sh
```

Queue the proposed detector ablation supervisor after the comparison queues:

```bash
bash scripts/ubuntu/train_proposed_ablation_after_session.sh
```

Queue paper-driven additions such as YOLOv10n and LRDS-YOLO after the main
comparison queues:

```bash
bash scripts/ubuntu/train_paper_comparison_models_after_session.sh
```

LRDS-YOLO is not assumed to be an Ultralytics built-in checkpoint. The script
checks `weights/lrds-yolo.pt` and `lrds-yolo.pt` by default, or a user-provided
`LRDS_MODELS=/path/to/checkpoint.pt`, and skips it if the current environment
cannot load it.

The proposed queue defaults to `WAIT_FOR=server-uavdt-comparisons-pending`.
If UAVDT is not ready, that supervisor exits safely and the proposed queue can
continue. The queue only runs implemented ablations; planned modules are logged
as `skipped_not_implemented` in
`outputs/experiments/proposed_ablation_commands.csv` until their real
implementation files are present.

Collect VisDrone and UAVDT together after both detector roots have completed
runs:

```bash
bash scripts/ubuntu/collect_cross_dataset_results.sh
```

Collect baseline plus proposed ablation rows:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
```

This writes a dataset-aware table and dashboard:

- `outputs/experiments/server_cross_dataset_results.csv`
- `outputs/experiments/server_cross_dataset_summary.csv`
- `outputs/experiments/server_cross_dataset_pvalues.csv`
- `outputs/reports/server_cross_dataset_dashboard.png`

All result rows include `dataset`, YOLO generation, detector family, checkpoint
scale, measured parameter-size group, params, and GFLOPs when logs expose them.
Paired p-values are computed within each dataset, not by pooling VisDrone and
UAVDT seeds. The cross-dataset wrapper keeps the stage gate filtered to the
primary `VisDrone2019-DET` rows by default; UAVDT is used as cross-dataset
validation rather than as the primary proposed-module gate.
