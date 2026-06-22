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

## 2026-05-24 Baseline Collection Status

Server reboot recovery and final collection status:

- No long detector training process is currently running.
- Both RTX 5090 GPUs are available for the next queue.
- VisDrone dataset readiness passes for raw, YOLO, and COCO-style processed
  paths.
- The fresh VisDrone comparison result table contains 45 run rows and 15 model
  summary rows.
- Completed 3-seed summaries are available for the YOLO comparison set,
  including YOLOv5su, YOLOv8n/s, YOLOv9s, YOLOv10n/s/m, YOLOv11n/s,
  YOLOv12n/s/m, and YOLOv26n/s.
- Current best overall baseline is `YOLOv12m`; current best lightweight
  baseline is `YOLOv9s`.
- Large YOLO checkpoints have not yet been run as a full comparison tier.
  Representative L-size anchors are now planned separately: YOLOv8l, YOLOv10l,
  YOLO11l, YOLO12l, YOLO26l, and RT-DETR-L seed completion.
- RT-DETR-L is not a complete repeated-seed comparison yet. The retry at
  `batch=2` still hit CUDA OOM, so it should be reported as incomplete or
  rerun with a lower-memory setting before being used as a statistical
  comparison.
- `rtdetr-r18` is not bundled in the current Ultralytics model config set; the
  available RT-DETR configs are larger variants such as `rtdetr-l`,
  `rtdetr-x`, `rtdetr-resnet50`, and `rtdetr-resnet101`.
- The current consolidated server report bundle is under
  `outputs/reports/server_with_proposed/`.
- The detector stage gate still recommends
  `finish_baselines_then_build_proposed` because no real proposed detector
  candidate rows exist yet.
- `./see train` now attaches to whichever active training session exists,
  instead of pointing at a stale resume session.
- The proposed-ablation launcher now restarts the side-by-side tmux view and
  browser viewer when a proposed queue starts.

Current report files:

```bash
outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_results.csv
outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_summary.csv
outputs/experiments/server_fresh/fresh_20260519_131739/server_baseline_pvalues.csv
outputs/reports/server_with_proposed/README.md
```

Next:

1. Do not start the placeholder `full_proposed` run as if it were the final
   proposed detector.
2. Either mark RT-DETR-L as incomplete or rerun a lower-memory non-YOLO
   comparison if a complete non-YOLO baseline is required.
3. Implement the real proposed detector pieces before the ablation queue:
   wavelet/high-frequency stem, partial deformable/lightweight adaptive neck,
   and tiled small-object inference.
4. Start the proposed ablation queue only after those implementations are
   enabled in `configs/experiments/proposed_detector_ablation.yaml`.
5. Recollect with `bash scripts/ubuntu/collect_proposed_results.sh` and use the
   detector stage gate to decide whether to proceed to Marine City 3D benchmark
   construction.

## 2026-05-24 Proposed Ablation Expansion

Implemented the next proposed-detector experiment structure:

- Added runtime model patches for `wavelet_stem`, `se_neck`, `cbam_neck`, and
  `partial_deformable_neck`.
- Added runnable ablations for `control`, `wavelet_stem`, `se_neck`,
  `cbam_neck`, `partial_deformable_neck`, `wavelet_se`, `wavelet_cbam`, and
  `full_proposed`.
- `full_proposed` currently means Wavelet stem + CBAM neck + partial
  deformable neck. Tiling remains a later eval-only stage after a checkpoint is
  selected.
- The train wrapper records `model_patches` and `patch_summary` in each run
  summary.
- Result collection and summary CSVs now keep `model_patches`, so SE/CBAM and
  full proposed variants can be separated in the dashboard and p-value tables.
- Proposed variants receive distinct dashboard colors instead of being hidden
  under the same YOLO version color.
- `collect_proposed_results.sh` now defaults to the fresh baseline roots plus
  `outputs/detectors/server_proposed_ablation`, so the next dashboard compares
  baselines and proposed ablations in one report.

Next:

1. Start the proposed ablation queue in tmux when ready:
   `WAIT_AFTER_START=0 bash scripts/ubuntu/train_proposed_ablation_after_session.sh`.
2. Monitor with `./see`, `./see train`, or the browser viewer printed by the
   launcher.
3. After completion, run `bash scripts/ubuntu/collect_proposed_results.sh`.
4. Use the updated dashboard and stage gate to choose the best proposed variant
   before moving to qualitative/Grad-CAM and Marine City 3D benchmark work.

## 2026-05-24 Large-Model Comparison Anchors

Added a follow-up queue for reviewer-facing L-size baseline coverage:

- Config: `configs/experiments/large_detector_comparison.yaml`
- Launcher: `scripts/ubuntu/train_large_comparison_after_session.sh`
- Default wait target: `server-proposed-ablation`
- Default GPU policy: GPU0 only until the GPU1 CUDA allocation issue is fixed.
- Default model specs:
  `yolov8l.pt:2,yolov10l.pt:2,yolo11l.pt:2,yolo12l.pt:2,yolo26l.pt:2,rtdetr-l.pt:2`

This queue should run after proposed ablations, or during an idle window, so
the server keeps enough memory and disk margin. L-size results should be
reported as a capacity anchor tier, while the main proposed lightweight claim
continues to compare against the best lightweight and best overall baselines.

## 2026-05-26 Top-3 Proposed Module Pivot

Baseline/proposed collection now shows:

- Best overall baseline: `YOLOv12m`
- Second strong medium baseline: `YOLOv10m`
- Best lightweight/small baseline: `YOLOv9s`
- Best current proposed candidate on the old YOLO11s base:
  `Proposed-CBAM-yolo11s`

Decision:

- Move proposed-module experiments from YOLO11s-only to a top-3 backbone
  screening stage.
- Queue candidate modules on `yolo12m.pt`, `yolov10m.pt`, and `yolov9s.pt`:
  `se_neck`, `cbam_neck`, `partial_deformable_neck`, `wavelet_cbam`, and
  `full_proposed`.
- Use existing baseline rows as the baseline/control ablation reference instead
  of retraining duplicate control runs for every backbone.
- Select the best backbone/module pair, then expand only that winner to 3 seeds
  or 5 seeds for final paper statistics.

Implementation updates:

- `detectors/proposed/modules.py` now detects the actual detection-head feature
  layers instead of assuming fixed YOLO11-style neck indices. This makes the
  patch system compatible with YOLOv12m, YOLOv10m, YOLOv9s, and YOLO11s-style
  heads.
- `scripts/proposed_ablation_jobs.py` now supports `--skip-completed` and
  continues to later jobs if one ablation fails/OOMs.
- Added top-3 configs:
  `configs/experiments/top3_proposed_detector_screening.yaml` and
  `configs/experiments/top3_proposed_detector_main.yaml`.
- Added launcher:
  `scripts/ubuntu/train_top3_proposed_ablation_after_session.sh`.

Current queue policy:

- Keep the active `server-large-comparison` run alive.
- Do not use GPU1 for training until the CUDA allocation issue is fixed.
- After `server-large-comparison` finishes, start the top-3 proposed screening
  queue on GPU0.

Recent paper comparison candidates added to the comparison plan:

- LRDS-YOLO
- SOD-YOLO
- DR-YOLO
- LSOD-YOLO
- MASF-YOLO
- TOE-YOLO
- MFR-YOLO
- UAVDet
- HF-D-FINE
- CSFPR-RTDETR
- UFO-DETR

These are marked `external_required`; they should be run only if compatible
checkpoints/configs are staged locally or adapters are implemented.

The Notion research database shared on 2026-05-26 was readable through the
public Notion collection API. It contains 70 rows; the detector-related rows
include recent YOLO, RT-DETR/DETR, D-FINE, Mamba, coarse-fine alignment,
density-guided, and frequency-domain UAV small-object papers. For experiment
planning, the key additions are:

- `UAVDet`: CNN-Mamba hybrid detector, useful as a non-YOLO efficient model.
- `HF-D-FINE`: D-FINE family tiny-object detector with high-resolution feature
  enhancement.
- `CSFPR-RTDETR`: RT-DETR-style frequency/position relation detector.
- `UFO-DETR`: frequency-guided end-to-end DETR candidate.

Priority for actual runs:

1. Finish current YOLO/RT-DETR baselines and top-3 proposed ablation.
2. Add only 2-3 external paper models that provide runnable code or weights.
3. Prefer one YOLO-specialized model, one DETR/RT-DETR model, and one Mamba or
   D-FINE model so the comparison table is not just another YOLO size sweep.

## 2026-05-26 Report And Result Cleanup

The report/result tree was reorganized so the next paper-writing pass has a
clear entry point:

- `docs/README.md` is now the documentation index.
- `outputs/reports/README.md` points to the current report, live dashboard, PPT,
  and archive.
- `outputs/experiments/README.md` points to the current result CSV/JSON files
  and archive.
- Superseded report bundles moved to `outputs/reports/archive/`.
- Smoke tests, old official snapshots, and initial baseline summaries moved to
  `outputs/experiments/archive/`.
- Older docs moved to `docs/archive/`.

Current paper-facing detector report:

```bash
outputs/reports/server_with_proposed/README.md
outputs/reports/server_with_proposed/figures/
outputs/reports/server_with_proposed/tables/
```

Live training monitoring remains separate:

```bash
outputs/reports/live/
```

The quick status page for the active queue, dataset readiness, top detector
rows, and paper-model availability is:

```bash
outputs/reports/detector_experiment_status.md
```

## 2026-05-27 UAVDT Cross-Dataset Preparation

UAVDT is now ready as the second detector dataset:

- Raw/extracted official data: `data/raw/UAVDT/_official_extract`
- YOLO data: `data/processed/uavdt_yolo`
- COCO JSON: `data/processed/uavdt_coco.json`
- Readiness check: passed for train/val/test with no placeholders or missing
  labels.

The converter now keeps only official `M####` UAVDT sequences and prioritizes
`*_gt.txt` over `*_gt_whole.txt` and `*_gt_ignore.txt`, so evaluation toolkit
folders do not leak into the detector dataset.

Next queued step:

```bash
bash scripts/ubuntu/start_uavdt_comparisons_pending.sh
```

This pending session waits for `server-large-comparison` and
`server-top3-proposed-pending`, then starts UAVDT YOLO and RT-DETR comparison
runs with organized outputs:

- Commands/jobs: `outputs/experiments/uavdt/`
- Logs: `outputs/logs/server_uavdt_baselines/`
- Runs: `outputs/detectors/server_uavdt_baselines/`
