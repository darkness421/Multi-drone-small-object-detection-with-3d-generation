# Server Progress

## 2026-05-15

Baseline infrastructure stage.

Completed:

- Added Ubuntu path config in `configs/paths.ubuntu.yaml`.
- Added Ubuntu environment and dataset readiness wrappers.
- Added tmux scripts for two-GPU VisDrone baseline queues and paired runs.
- Added result collectors for server baseline result CSV, summary CSV, and p-value CSV.
- Added detector ROC-AUC utilities separated from future ambiguity ROC-AUC.
- Added dashboard, qualitative examples, and Grad-CAM preparation entrypoints.
- Added proposed small-object perception module skeleton and config.
- Added Marine City multi-angle benchmark and 3D generative model comparison scaffolds.
- Added LLM-assisted final adjudicator and ablation evaluation scaffolds.
- Added Ubuntu VisDrone dataset preparation scripts for staging/downloading, conversion, and preflight.

Not run:

- No long detector training was started.
- No dataset copy or weight download was performed.

Next:

1. Run environment and dataset checks on the Ubuntu server.
2. Launch preliminary 3-seed baseline sweep in tmux.
3. Collect CSV/PNG summaries.
4. Extend top models to 5 seeds for main statistical analysis.
5. Add the proposed module to the best overall or best lightweight baseline.
6. Build Marine City multi-angle benchmark splits for 3D generation and reasoner ablations.

## 2026-05-18

Baseline execution status:

- Completed the initial 3-seed baseline sweep for YOLOv8n/s, YOLOv11n/s,
  YOLOv12n/s, and RT-DETR-L.
- Extended the current top-3 models to the 5-seed main statistical set:
  YOLOv8s, YOLOv12s, and YOLOv11s.
- Added parameter-count based model size grouping to the result collector.
- Planned an expanded comparison sweep with YOLOv5su, YOLOv9s, YOLOv10s,
  YOLOv26n, YOLOv26s, and YOLOv12m after the top-3 seed extension completes.
- Added optional YOLOv6s/YOLOv7 legacy checkpoints to the queue with automatic
  availability checks, because those names are not bundled as loadable weights
  in the current Ultralytics environment.
- Split detector result metadata into YOLO generation, detector family,
  checkpoint scale, measured parameter-size group, and YOLO/non-YOLO
  architecture group for clearer comparison plots and CSV summaries.
- Added a detector stage-gate plan: finish all baseline/comparison models first,
  tune the proposed detector only after the comparison set is stable, and move
  to Marine City 3D generation/benchmark work only after the proposed detector
  outperforms the best overall and best lightweight baselines.
- Added UAVDT preparation and cross-dataset comparison scripts. UAVDT currently
  needs actual raw files before conversion/training can start.
- Queued UAVDT comparison behind the VisDrone comparison supervisors; it will
  start only if UAVDT readiness passes.

Next:

1. Let `server-top3-seed5` finish.
2. Run the expanded comparison queue.
3. Recollect CSV, p-values, and dashboard.
4. Run `bash scripts/ubuntu/check_detector_stage_gate.sh`.
5. Select best overall and best lightweight baselines for qualitative analysis
   and proposed-module experiments.
6. Prepare UAVDT raw data and run cross-dataset baselines.
7. Start 3D generation and benchmark construction only after the detector gate
   recommends `proceed_to_3d_benchmark`.

## 2026-05-19

Comparison and extra-dataset preparation status:

- The expanded VisDrone comparison queue is running in tmux with both RTX 5090
  GPUs active.
- The pending queues cover small, medium, and non-YOLO baselines before moving
  to the proposed perception module.
- UAVDT conversion and comparison scripts are in place, but raw UAVDT files are
  not present yet under `data/raw/UAVDT`, so the UAVDT queue will wait/fail safe
  at readiness instead of starting an invalid run.
- The common tmux training script now tags run names by dataset, so UAVDT runs
  are written as `*_uavdt_seed*` instead of `*_visdrone_seed*`.
- Metric collection now infers `dataset` from the training/eval summary, data
  YAML, or run path and can collect multiple detector roots into one CSV.
- Seed p-values are computed within each dataset to avoid mixing VisDrone and
  UAVDT repeated-seed results.
- The cross-dataset collector filters the detector stage gate to
  `VisDrone2019-DET` by default, so UAVDT remains validation rather than the
  primary go/no-go criterion for proposed-module work.
- A cross-dataset collection wrapper was added:
  `bash scripts/ubuntu/collect_cross_dataset_results.sh`.

Current next actions:

1. Let the active VisDrone comparison queues finish.
2. Place or stage UAVDT raw data, then run
   `SOURCE=/path/to/UAVDT bash scripts/ubuntu/prepare_uavdt_dataset.sh`.
3. Keep the UAVDT comparison queue behind the VisDrone queues, or rerun
   `bash scripts/ubuntu/train_uavdt_comparisons_after_session.sh` after
   readiness passes.
4. Rebuild both the VisDrone-only and cross-dataset dashboards after completed
   runs are available.

## 2026-05-19 Proposed Queue Update

- Added a proposed detector ablation queue scaffold behind the comparison
  supervisors.
- The queue writes real method/ablation metadata into training summaries so
  result collection can identify proposed rows separately from YOLO baselines.
- Default implemented run: `control` on `yolo11s.pt` with the same VisDrone
  protocol and 3 preliminary seeds.
- Planned ablations are present in the queue config but skipped until the real
  module/evaluator exists:
  `wavelet_stem`, `partial_deformable_neck`, `tiling_inference`, and
  `full_proposed`.
- This avoids accidentally reporting unchanged baseline training as a proposed
  architecture.

Commands:

```bash
bash scripts/ubuntu/train_proposed_ablation_after_session.sh
bash scripts/ubuntu/collect_proposed_results.sh
```

## 2026-05-19 Paper Comparison Additions

- YOLOv10 was already represented by YOLOv10s and YOLOv10m in the comparison
  queues.
- Added YOLOv10n so the YOLOv10 family has nano/small/medium coverage for
  parameter-size comparisons.
- Added LRDS-YOLO to the paper-driven comparison list as an external UAV
  small-object detector. It is only run if a loadable checkpoint/config is
  available; otherwise the queue skips it and documents the missing model.
- Added `scripts/ubuntu/train_paper_comparison_models_after_session.sh` to run
  these additions after the main comparison supervisors.

## 2026-05-19 Report Organization

- Added `scripts/organize_server_reports.py` to build a compact report bundle
  under `outputs/reports/server_baselines/`.
- `bash scripts/ubuntu/collect_server_results.sh` now refreshes that bundle
  after metrics, statistics, dashboard, and stage-gate collection.
- The report bundle includes a Markdown index, copied CSV tables, dashboard
  figure, and stage-gate files while keeping datasets, weights, raw runs, logs,
  and caches ignored.
- The report figures are now split into separate PNGs for AP/AP50,
  precision/recall/F1, seed AP distribution, Params-vs-AP, GFLOPs-vs-AP, and
  FPS-vs-AP instead of relying only on the combined dashboard.
- Current report entry point:
  `outputs/reports/server_baselines/README.md`.

## 2026-05-19 Fresh Unified Queue Restart

- Added `scripts/ubuntu/restart_fresh_server_queue.sh` for a clean
  from-scratch comparison restart.
- The script stops old training/pending monitor sessions, preserves previous
  outputs, then starts one `server-fresh-baselines` tmux session with GPU0/GPU1
  workers and a collector window.
- The default order starts with `yolov10s.pt` so the first visible runs match
  the current comparison focus, then continues through YOLOv10n, YOLOv9s,
  YOLOv5su, YOLOv8/11/12 nano/small, YOLO26 nano/small, RT-DETR-L, YOLOv10m,
  and YOLO12m when checkpoints are loadable.
- Fresh live monitoring uses a run-specific detector root, CSVs, dashboard PNG,
  browser viewer, and side-by-side tmux viewer instead of mixing with older
  baseline outputs.
- The live browser viewer now shows separated report figures in addition to the
  combined dashboard: AP/AP50, precision/recall/F1, seed AP distribution,
  Params-vs-AP, GFLOPs-vs-AP, and FPS-vs-AP.
- The monitor tmux session also lists the separated live figures so failed,
  incomplete, and completed runs can be checked without opening the final report
  bundle.
- Added strict official-result collection. The official CSV now keeps only runs
  matching the VisDrone protocol (`imgsz=1280`, `epochs=100`, `batch=8`,
  deterministic training, and the VisDrone data YAML). Mismatched rows are
  written to an excluded CSV instead of being mixed into the main table.
- Older completed runs can still be used when they match the same protocol, but
  duplicate dataset/model/seed rows are deduplicated so fresh runs replace older
  rows once complete.

Fresh restart command:

```bash
bash scripts/ubuntu/restart_fresh_server_queue.sh
```

Strict official collection command:

```bash
bash scripts/ubuntu/collect_official_server_results.sh
```
