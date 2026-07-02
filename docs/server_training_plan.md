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
- paper-driven external candidates if compatible code/checkpoints are staged:
  LEAF-YOLO, LRDS-YOLO, CSFPR-RTDETR, UAVDet/UAVD-Mamba, HF-D-FINE, and
  RF-DETR-B as a secondary generic transformer check

The expanded sweep fills comparison gaps across older YOLO generations, YOLO26,
YOLOv10, paper-specific UAV detectors, non-YOLO transformer/Mamba families, and
medium-capacity models. These runs use the preliminary 3-seed set first.
YOLOv6s and YOLOv7 are treated as optional legacy checkpoints: the queue checks
whether the weights are loadable in the current Ultralytics environment and
skips them automatically if no compatible checkpoint is available.

Paper-model priority after the 2026-05-30 public-code re-check:

1. Built-in/reproducible rows first: YOLOv5/8/9/10/11/12/26 by size and
   RT-DETR where memory allows.
2. Add 2-3 external paper rows only after local adapters are ready:
   `LEAF-YOLO` as a lightweight YOLO-family UAV model, `CSFPR-RTDETR` as the
   UAV-specific RT-DETR/frequency model, and one Mamba/CNN or D-FINE candidate
   if runnable.
3. Keep `SOD-YOLO`, `DR-YOLO`, `LRDS-YOLO`, `UAVDet`, `HF-D-FINE`,
   `UFO-DETR`, `UAVD-Mamba`, and `RF-DETR-B` in the paper availability table
   until code, weights, and fair dataset adapters are verified.

## Seeds

Preliminary seed set:

- `42, 123, 2026`

Main statistical seed set:

- `42, 123, 2026`

Use three seeds for the main detector statistics so the proposed model and the
comparison models are evaluated consistently. Extra seeds such as `7` and
`3407` can be reported only as optional supplementary robustness checks.

## Strategy

1. Train all YOLO and non-YOLO baseline/comparison models with the preliminary
   3-seed set.
2. Keep the top comparison models and final proposed model on the same 3-seed
   main statistical set.
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

TinyPerson should be added as a detector-only supplementary stress test after
the best proposed detector family is selected. This is not the main stage gate,
but it is useful because ACCV 2024 small-object YOLO work also evaluates
VisDrone-style dense UAV scenes together with TinyPerson-style ultra-small
person detection.

Recommended TinyPerson scope:

- baseline: YOLOv11l
- final proposed detector
- Core 1 + Core 2 architecture before overlap-aware NMS, if time allows
- optional external comparison: LSOD-YOLO or a Universal-YOLO-style reproduced
  row only if code/weights/adapters are easy to stage
- seed: start with `42`, expand to `42, 123, 2026` only if the first run is
  promising
- report: AP, AP50, recall, F1, Params, GFLOPs, FPS

Keep TinyPerson in the supplementary material unless it becomes a very strong
result. The main detector table remains VisDrone-first, with UAVDT/TinyPerson
used to show generalization rather than to tune the proposed modules.

Cross-dataset comparison width:

| Dataset | Comparison width | Models |
| --- | --- | --- |
| VisDrone2019-DET | full | size-grouped YOLO rows, YOLOv11l/12l/8l, RT-DETR, selected runnable related-work models, final proposed |
| UAVDT | compact | YOLOv11l, best lightweight YOLO, best medium/large YOLO already trained, RT-DETR if available, final proposed |
| TinyPerson | minimal supplementary | YOLOv11l, final proposed, Core 1 + Core 2 variant, optional easy external tiny-person row |

Do not rerun every paper-specific external detector on every dataset. External
models are most valuable on VisDrone; UAVDT/TinyPerson mainly test whether the
final detector behavior transfers.

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

## Official Result Inclusion

Main-paper detector tables only include runs that match the official VisDrone
protocol:

- data YAML: `configs/detector/visdrone_yolo_data.yaml`
- `imgsz`: 1280
- `epochs`: 100
- `batch`: 8, unless a separate memory-adjusted table is explicitly declared
- deterministic: `true`

Large-model anchors are treated as a memory-adjusted comparison tier when
needed. Use `configs/experiments/large_detector_comparison.yaml` and
`scripts/ubuntu/train_large_comparison_after_session.sh` to run representative
L-size models after active proposed-ablation training:

- YOLOv8l
- YOLOv10l
- YOLO11l
- YOLO12l
- YOLO26l
- RT-DETR-L with complete seed coverage when memory allows

These large anchors are mainly for reviewer-facing capacity coverage. The
primary proposed-module claim should still compare against the best overall
baseline and best lightweight baseline under the same VisDrone protocol.

Older preliminary runs are preserved for sanity checks, but they are discarded
from the official CSV if any of the protocol fields differ. When an older run
and a fresh run share the same dataset, model, and seed, the official collector
keeps one logical row and lets the newer fresh run replace the older row once it
is complete.

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
GPUS=0 bash scripts/ubuntu/restart_fresh_server_queue.sh
```

This stops older training/pending tmux sessions, preserves existing outputs,
starts one `server-fresh-baselines` detector queue on GPU0, opens a
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

Collect strict official results, excluding protocol mismatches:

```bash
bash scripts/ubuntu/collect_official_server_results.sh
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
bash scripts/ubuntu/start_uavdt_comparisons_pending.sh
```

By default this pending session waits for
`server-large-comparison,server-top3-proposed-pending`, then launches the UAVDT
YOLO and RT-DETR comparison sessions. UAVDT command CSV/job scripts are kept
under `outputs/experiments/uavdt/`, logs under
`outputs/logs/server_uavdt_baselines/`, and detector runs under
`outputs/detectors/server_uavdt_baselines/`.

Queue the proposed detector ablation supervisor after the comparison queues:

```bash
bash scripts/ubuntu/train_proposed_ablation_after_session.sh
```

Queue paper-driven additions such as YOLOv10n, LEAF-YOLO, LRDS-YOLO, and
CSFPR-RTDETR after the main comparison queues:

```bash
bash scripts/ubuntu/train_paper_comparison_models_after_session.sh
```

External paper models are not assumed to be Ultralytics built-in checkpoints.
The availability checker keeps them blocked until a compatible local
checkpoint/config or adapter is staged, so unavailable paper models do not get
mixed into official CSVs as failed baseline runs.

The proposed queue defaults to `WAIT_FOR=server-uavdt-comparisons-pending`.
If UAVDT is not ready, that supervisor exits safely and the proposed queue can
continue. The queue now runs the implemented detector-side ablations:
`control`, `wavelet_stem`, `se_neck`, `cbam_neck`,
`partial_deformable_neck`, `wavelet_se`, `wavelet_cbam`, and
`full_proposed`. Each run records `model_patches` in
`outputs/experiments/proposed_ablation_commands.csv`, then collection merges
fresh baseline rows with proposed rows so the dashboard/stage gate can identify
the best proposed variant. `tiling_inference` remains eval-only until the tiled
detector evaluator is complete.

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
