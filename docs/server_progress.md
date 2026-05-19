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
