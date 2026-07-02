# Experiment Steps And Progress Summary

Updated: 2026-05-30

Project working title:

```text
CoM3D-ACE = Cooperative Multi-UAV 3D Ambiguity-Centric Evidence Completion
```

This is the single-file summary of what we have done, what is running now, and
what should happen next. It links the detector baselines, proposed detector
module, UAVDT validation, MarineCity 3D reconstruction, and selective LLM/VLM
reasoner into one experiment path.

## Current Server State

Active detector lane:

- GPU0 is used for detector experiments.
- Current active tmux session: `server-large-comparison`.
- Current active run at last check:
  - dataset: VisDrone2019-DET
  - model: YOLOv12l
  - seed: 123
  - epoch: about 24/100
  - imgsz: 1280
  - batch: 2
  - GPU: 0

System/3D lane:

- GPU1 is reserved for MarineCity 3D reconstruction, Isaac Sim smoke/export
  tasks, and local VLM/LLM reasoner tests.
- GPU1 is currently mostly idle and should not steal detector work from GPU0.

Live monitoring:

```bash
tmux attach -t server-current-experiments-view
tmux attach -t server-training-dual-view
tmux attach -t server-large-comparison
tmux attach -t server-baseline-monitor
```

## What We Have Done

### Infrastructure

Done:

- Built Ubuntu server experiment structure under `scripts/ubuntu/`,
  `configs/`, `docs/`, `outputs/experiments/`, and `outputs/reports/`.
- Added environment checks for Python, conda, torch/CUDA, GPU names/count,
  OpenCV, numpy, scipy, sklearn, ultralytics, dataset roots, and output paths.
- Added dataset readiness checks for VisDrone and UAVDT.
- Added tmux queue launchers for baseline, large-model, proposed, UAVDT, and
  3D-generation stages.
- Added live monitoring with tmux and live dashboard outputs.
- Added Git ignore and report organization rules so datasets, weights, raw
  detector runs, logs, and caches are not pushed.

Key docs/configs:

- `docs/server_training_plan.md`
- `docs/server_progress.md`
- `docs/server_gpu_allocation.md`
- `docs/current_experiment_steps.md`
- `configs/experiments/server_gpu_allocation.yaml`

### VisDrone Dataset

Done:

- VisDrone2019-DET is the primary detector dataset.
- Raw, YOLO, and COCO-style processed paths have passed readiness checks.
- Official detector protocol is:
  - data YAML: `configs/detector/visdrone_yolo_data.yaml`
  - imgsz: 1280
  - epochs: 100
  - deterministic: true
  - batch: 8 for official small/medium runs, batch 2 for memory-adjusted
    large anchors

### Baseline Detector Results

Done:

- Completed 3-seed VisDrone runs for the main YOLO comparison set:
  - YOLOv5su
  - YOLOv8n/s
  - YOLOv9s
  - YOLOv10n/s/m
  - YOLOv11n/s
  - YOLOv12n/s/m
  - YOLOv26n/s
- Current best overall baseline from the completed fresh comparison set:
  - YOLOv12m
- Current best lightweight/small baseline:
  - YOLOv9s
- RT-DETR-L remains a memory-sensitive non-YOLO comparison and should be marked
  incomplete unless complete seed coverage is obtained.

Large-model anchor results so far:

| Model | Seeds Completed | AP Mean | AP50 Mean | Notes |
| --- | ---: | ---: | ---: | --- |
| YOLOv8l | 3 | 0.3765 | 0.5963 | completed large anchor |
| YOLOv10l | 3 | 0.3728 | 0.5890 | completed large anchor |
| YOLOv11l | 3 | 0.3777 | 0.5981 | current strongest large anchor |
| YOLOv12l | 1 + running | 0.3760 | 0.5944 | seed 123 currently running |

Reports:

- `outputs/reports/server_with_proposed/README.md`
- `outputs/reports/server_with_proposed/tables/`
- `outputs/reports/server_with_proposed/figures/`
- live updates under `outputs/reports/live/`

### Metrics And Reports

Done:

- AP / mAP50-95, AP50, precision, recall, F1, ROC-AUC, Params, and GFLOPs are
  collected when available.
- Seed summaries compute mean and standard deviation.
- p-value tooling supports paired t-test and Wilcoxon signed-rank tests.
- Dashboard figures are separated:
  - AP/AP50 bar plot
  - precision/recall/F1 plot
  - seed AP distribution
  - Params vs AP
  - GFLOPs vs AP
  - speed vs AP
- Report files were reorganized so current reports, live reports, and archives
  are easier to find.

### Proposed Detector Module

Done:

- Implemented runtime model patches for:
  - Wavelet stem
  - SE neck
  - CBAM neck
  - partial deformable neck
  - Wavelet + SE
  - Wavelet + CBAM
  - full proposed detector-side module
- Current proposed framing:

```text
Frequency-guided ambiguity-aware evidence completion for UAV small objects.
```

- Initial YOLO11s-only proposed runs showed that the old proposed candidate did
  not beat the strongest baseline, so we pivoted to top-3 backbone screening.

Top-3 proposed screening is prepared for:

- YOLOv12m
- YOLOv10m
- YOLOv9s

Pending session:

```bash
tmux attach -t server-top3-proposed-pending
```

### UAVDT Dataset

Done:

- UAVDT raw/extracted official data is staged.
- UAVDT YOLO and COCO converted outputs are prepared.
- Readiness check passed for train/val/test.
- UAVDT comparison queue is pending behind large baselines and top-3 proposed
  screening.

Pending session:

```bash
tmux attach -t server-uavdt-comparisons-pending
```

### Related-Paper Comparison Models

Done:

- Added a paper-model availability tracker:
  - `configs/experiments/paper_detector_comparison.yaml`
  - `outputs/reports/server_with_proposed/paper_model_availability.md`
- Added or tracked recent comparison candidates:
  - LEAF-YOLO
  - LRDS-YOLO
  - SOD-YOLO
  - DR-YOLO
  - LSOD-YOLO
  - MASF-YOLO
  - TOE-YOLO
  - MFR-YOLO
  - UAVDet
  - UAVD-Mamba
  - HF-D-FINE
  - CSFPR-RTDETR
  - UFO-DETR
  - RF-DETR-B

Current practical priority:

1. LEAF-YOLO as the lightweight YOLO-family UAV comparison.
2. CSFPR-RTDETR as the UAV-specific RT-DETR/frequency comparison.
3. One Mamba/D-FINE/RF-DETR candidate only if adapter and fairness checks pass.

Important:

- These are not counted as completed baselines until code, checkpoints, and
  adapters are staged locally and the runs are collected under the same metric
  protocol.

### ACCV Paper Direction

Done:

- Reframed the paper away from only a detector AP leaderboard.
- Main question:

```text
Does stronger 2D small-object evidence improve multi-UAV 3D association,
ambiguity diagnosis, and targeted re-observation?
```

- Figure plan:
  1. overall CoM3D-ACE framework
  2. detector module and ablation path
  3. Isaac/MarineCity multi-UAV benchmark construction
  4. weather restoration + 3D reconstruction + evidence completion
  5. optional appendix figure for LLM reasoner/re-observation

- Checked the remote experiment-plan branch and folded the remaining detector,
  3D, and reasoner tasks into the current execution order.
  It adds `docs/accv_revision_experiment_update.md`, but it was based on an
  older branch and should be merged only after updating its Tier 1/Tier 2 lists
  to match the current server plan.

## Full Experiment Steps

### Step 1. Finish VisDrone Detector Baselines

Status: mostly done.

Goal:

- establish reproducible detector baselines on VisDrone2019-DET
- group models by YOLO version, detector family, and measured parameter size

Done:

- YOLOv5/8/9/10/11/12/26 nano/small/medium style comparisons.
- 3-seed preliminary summaries.

Still running:

- large anchor queue, currently YOLOv12l seed 123.

Exit condition:

- complete or explicitly mark incomplete all large anchor rows:
  YOLOv8l, YOLOv10l, YOLOv11l, YOLOv12l, YOLOv26l, RT-DETR-L.

### Step 2. Freeze Baseline Table

Status: pending Step 1.

Commands:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
bash scripts/ubuntu/check_detector_stage_gate.sh
```

Output:

- best overall baseline
- best lightweight baseline
- complete/incomplete baseline labels
- main AP/AP50/APsmall/FPS/Params/GFLOPs table

### Step 3. Run Top-3 Proposed Detector Screening

Status: pending session exists.

Command/session:

```bash
tmux attach -t server-top3-proposed-pending
```

Backbones:

- YOLOv12m
- YOLOv10m
- YOLOv9s

Ablations:

- SE
- CBAM
- partial deformable neck
- Wavelet + CBAM
- full proposed

Exit condition:

- select one best backbone/module pair.

### Step 4. Expand Winning Proposed Variant

Status: pending Step 3.

Goal:

- run selected proposed model with the same 3 seeds as the main comparison
  models: `42`, `123`, and `2026`
- use extra seeds only as optional supplementary robustness checks

Metrics:

- AP
- AP50
- APsmall if available
- recall
- F1
- FPS
- Params
- GFLOPs
- p-values against best baseline and best lightweight baseline

### Step 5. Run UAVDT Cross-Dataset Validation

Status: pending session exists.

Command/session:

```bash
tmux attach -t server-uavdt-comparisons-pending
```

Goal:

- show the selected detector/proposed module is not VisDrone-only
- keep UAVDT as validation, not the primary model-selection gate

### Step 6. Add External Paper Models Selectively

Status: adapter-gated.

First external targets:

- LEAF-YOLO
- CSFPR-RTDETR

Optional after adapters:

- UAVDet or UAVD-Mamba
- HF-D-FINE
- RF-DETR-B
- LRDS-YOLO, SOD-YOLO, DR-YOLO if fair/runnable

Exit condition:

- add only 2-3 successful external rows to the paper table, not every surveyed
  paper.

### Step 7. Detector-To-Graph Transfer

Status: pending selected checkpoints.

Goal:

- convert detector outputs to EvidenceToken records
- test whether detector quality transfers to 3D graph quality

Metrics:

- 2D APsmall versus 3D center error
- association F1
- false merge / false split
- wrong high-confidence rate
- ambiguity resolution rate

### Step 8. MarineCity Multi-UAV Benchmark

Status: scaffolded / GPU1 lane.

Goal:

- build a synchronized MarineCity multi-UAV benchmark from Isaac/Cesium-style
  simulation assets
- include RGB, pose, camera intrinsics/extrinsics, depth when available,
  object IDs, view angle, altitude, weather, and ambiguity labels

Output:

- `outputs/experiments/marinecity_multiview_benchmark.json`

### Step 9. 3D Reconstruction And Generation Comparison

Status: scaffolded / GPU1 lane.

Methods:

- NeRF
- Instant-NGP
- Mip-NeRF 360
- 3D Gaussian Splatting
- our object/evidence-aware 3D method

Metrics:

- PSNR
- SSIM
- LPIPS
- rendering FPS
- training time
- downstream detector AP on rendered/held-out views

### Step 10. Weather Restoration Branch

Status: planned.

Goal:

- if rain, snow, fog, or glare exists in MarineCity data, split by condition
- test restoration or deep-unrolling-style enhancement before 3D reconstruction

Metrics:

- restoration quality
- reconstruction quality
- downstream small-object detector/evidence quality

### Step 11. Selective LLM/VLM Final Reasoner

Status: scaffolded / pending graph evidence.

Goal:

- do not call LLM/VLM for every object
- call it only for ambiguous/hard cases
- compare final adjudication and re-observation decisions

Methods:

- detector only
- detector + 3D graph
- detector + 3D graph + selective LLM/VLM
- detector + 3D graph + selective LLM/VLM + re-observation policy

Metrics:

- final object accuracy
- ambiguity resolution
- re-observation gain
- latency
- VLM/LLM call count
- cost proxy

### Step 12. Paper Packaging

Status: in progress.

Tables:

- detector baseline table
- large anchor table
- proposed ablation table
- UAVDT cross-dataset table
- detector-to-graph transfer table
- 3D reconstruction comparison table
- reasoner/re-observation ablation table

Figures:

- overall framework
- detector module
- MarineCity benchmark
- weather + 3D reconstruction/evidence completion
- optional LLM reasoner appendix figure

## Immediate Next Actions

1. Let `server-large-comparison` continue on GPU0.
2. Watch with:

```bash
tmux attach -t server-current-experiments-view
```

3. After large anchors finish, collect:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
bash scripts/ubuntu/check_detector_stage_gate.sh
```

4. Let the pending top-3 proposed screening start.
5. Use GPU1 only for 3D/Isaac/reasoner smoke tasks that do not interfere with
   detector GPU0.
