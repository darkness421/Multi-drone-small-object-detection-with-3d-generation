# Current Experiment Steps

Updated: 2026-06-04

This page is the operational step tracker for the server experiments. It should
be read together with `docs/server_progress.md`,
`docs/server_training_plan.md`, and `docs/server_gpu_allocation.md`.

## GPU Policy

- GPU0: detector baselines, comparison models, proposed detector ablations, UAVDT.
- GPU1: MarineCity 3D reconstruction, Isaac Sim smoke/export tasks, local VLM/LLM
  reasoner tests.

## Step 1. Finish Large Detector Anchors

Status: completed for the current VisDrone large-anchor gate.

Active queue:

```bash
tmux attach -t server-large-comparison
```

Current best large baseline:

- YOLOv11l: AP 0.3777, AP50 0.5981, F1 0.6248.
- Params/GFLOPs: 25.32M / 87.3.
- Close competitors: YOLOv12l and YOLOv8l.

## Step 2. Collect And Freeze Baseline Table

Status: completed for large baseline table; keep refreshing if new proposed
rows are added.

Command:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
bash scripts/ubuntu/check_detector_stage_gate.sh
```

Decision output:

- best overall baseline
- best lightweight baseline
- large-anchor capacity comparison
- incomplete or memory-adjusted rows clearly marked

## Step 3. Run Top-3 Proposed Detector Screening

Status: active.

Active session:

```bash
tmux attach -t server-top3-proposed-screening
```

Live numeric monitor:

```bash
tmux attach -t server-proposed-metrics
```

Screening config:

```text
configs/experiments/top3_proposed_detector_screening.yaml
```

Backbones:

- YOLOv12m
- YOLOv10m
- YOLOv9s

Ablations:

- SE neck
- CBAM neck
- partial deformable neck
- Wavelet + CBAM
- full proposed: Wavelet stem + CBAM neck + partial deformable neck

Gate:

- choose the best backbone/module pair by AP/AP50/APsmall first
- use recall/F1, FPS, Params, and GFLOPs as tie-breakers

Current observation:

- First `ProposedTop3-SE-yolo12m` seed finished below the YOLOv11l baseline.
- Monitor now displays the best baseline row, top baseline ranks, Params,
  GFLOPs, proposed latest/best metrics, and deltas.

If the remaining medium candidates do not approach YOLOv11l, stop expanding
weak medium seeds and move to Step 3b.

## Step 3b. YOLOv11/P2/Tiny-Activation Next-Step Screen

Status: pending session active; waits for `server-top3-proposed-screening` to
finish before launching.

Pending session:

```bash
tmux attach -t server-yolov11-p2-next-step-pending
```

Launch session after the wait clears:

```bash
tmux attach -t server-yolov11-p2-next-step
```

Config:

```text
configs/experiments/yolov11_p2_tiny_activation_next_step.yaml
```

Rationale:

- YOLOv11l is the current best baseline.
- P2/stride-4 feature maps preserve tiny-object details that can be lost by
  stride-32 heads.
- The `tiny_frelu_neck` activation uses a spatial condition plus a
  high-frequency residual to favor weak edge/texture evidence.
- NMS variants should be tested separately on adjacent-object and crowded-frame
  subsets.

One-seed candidates:

- `YOLOv11l + tiny_frelu_neck`
- `YOLOv11l + CBAM + tiny_frelu_neck`
- `YOLOv11l-P2 + tiny_frelu_neck`, initialized from `yolo11l.pt`
- `YOLOv11l-P2 + wavelet + CBAM + tiny_frelu_neck`, initialized from
  `yolo11l.pt`

Early stopping policy:

- Screening and supplementary pilot runs use `patience=30`.
- Final statistical confirmation runs use `patience=50`.
- The current in-progress top-3 run was launched with Ultralytics default
  `patience=100`; do not restart it only for patience unless the metric plateaus
  clearly below the gate.

Efficiency reference:

- YOLOv11l baseline: 25.32M params / 87.3 GFLOPs.
- YOLOv11l-P2 smoke test: 26.12M params; YAML alias loads successfully from
  `configs/detector/yolo11l-p2.yaml`.
- YOLOv11m-P2: 20.59M params / 88.9 GFLOPs; use this if `yolo11m.pt` is
  downloaded or otherwise available for partial initialization.

## Step 4. Expand Winning Proposed Variant

Status: pending Step 3.

Config:

```text
configs/experiments/top3_proposed_detector_main.yaml
```

Procedure:

- edit config to keep only the winning backbone/module pair
- run 3 seeds for preliminary statistics
- expand to 5 seeds for main paper statistics if it is the final candidate

## Step 5. Run UAVDT Cross-Dataset Validation

Status: pending session already exists.

Pending session:

```bash
tmux attach -t server-uavdt-comparisons-pending
```

The pending session waits for:

```text
server-large-comparison,server-top3-proposed-pending
```

Purpose:

- confirm the selected detector/proposed module is not VisDrone-only
- keep UAVDT as cross-dataset validation, not the primary stage gate

## Step 6. Add External Paper Models Selectively

Status: adapter-gated.

Do not try to reproduce every survey paper. Add only models with practical
code/checkpoint support.

Priority:

1. LEAF-YOLO as the lightweight YOLO-family UAV comparison.
2. CSFPR-RTDETR as the UAV-specific RT-DETR/frequency comparison.
3. One of UAVDet, UAVD-Mamba, HF-D-FINE, or RF-DETR-B only if the adapter is
   fair and stable.

Tracking config:

```text
configs/experiments/paper_detector_comparison.yaml
```

Availability report:

```text
outputs/reports/server_with_proposed/paper_model_availability.md
```

## Step 7. Detector-To-Graph Transfer

Status: pending selected detector checkpoints.

Question:

```text
Does stronger 2D small-object evidence improve multi-UAV 3D association,
ambiguity diagnosis, and targeted re-observation?
```

Metrics:

- 3D center error
- association F1
- false merge / false split
- ambiguity resolution rate
- re-observation gain
- final object accuracy

## Step 8. MarineCity 3D Reconstruction And Reasoner

Status: GPU1 preparation lane.

3D comparison methods:

- NeRF
- Instant-NGP
- Mip-NeRF 360
- 3D Gaussian Splatting

Reasoner policy:

- detector only
- detector + 3D graph
- detector + 3D graph + selective LLM/VLM final adjudicator
- detector + 3D graph + selective LLM/VLM + re-observation policy

The LLM/VLM reasoner is not always-on. It is only for ambiguous/hard cases.

## Live Monitoring Commands

Use these from a terminal on the server:

```bash
tmux attach -t server-current-experiments-view
tmux attach -t server-training-dual-view
tmux attach -t server-large-comparison
tmux attach -t server-baseline-monitor
tmux attach -t server-proposed-metrics
```

Live result files:

```text
outputs/experiments/server_fresh/large_20260524_140922/live/
outputs/reports/live/
```
