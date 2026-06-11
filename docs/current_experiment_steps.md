# Current Experiment Steps

Updated: 2026-06-11

This page is the operational step tracker for the server experiments. It should
be read together with `docs/server_progress.md`,
`docs/server_training_plan.md`, and `docs/server_gpu_allocation.md`.

## GPU Policy

- Until the current detector queues finish, do not interrupt active tmux runs.
- After the current queue clears, use GPU0 for proposed-detector follow-up around
  `P2P4-SelfAttnFR-s123` while keeping the parameter budget near or below the
  YOLOv11l baseline.
- Use GPU1 for reviewer-facing comparison coverage: YOLO family scale sweeps and
  runnable related-work models.
- Start MarineCity/Isaac/LLM-reasoner GPU work after the detector comparison
  queue is stable enough for the main ACCV table.

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

Status: active for the current under-parameter detector search.

The detector search is now organized as three paper-facing core modules:

- Core 1: compact capacity redistribution for reducing/controlling model size.
- Core 2: multi-scale high-resolution evidence using P2/P3, TinyFReLU, and
  DynFreq-C3 refinement. A new `P2/P3/P4-only` branch directly tests the
  4x/8x/16x downsampling-head hypothesis from UAV small-object research.
- Core 3: overlap-aware small-object decision through NMS/adjacent-object
  analysis.

Detailed module map:

```text
docs/proposed_detector_three_core_modules.md
```

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
- `P2BalV3 + dynfreq_c3_p2 + tiny_frelu_neck`
- `P2BalV3 + dynfreq_c3_small + tiny_frelu_neck`
- `P2P4 + tiny_frelu_neck`
- `P2P4 + dynfreq_c3_p2 + tiny_frelu_neck`
- `P2P4 + dynfreq_c3_small + tiny_frelu_neck`

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
- `P2BalV3-FR`: about 25.28M params; current under-parameter balanced
  candidate.
- `P2CompV3-FR`: about 24.08M params; current compact-capacity candidate.
- `P2EffV3-FR`: about 23.15M params; current efficiency candidate.
- `dynfreq_c3_p2` adds only a small P2 C3/C3k2 refinement block, intended to
  stay below the YOLOv11l parameter budget when used with `P2BalV3`.
- `P2P4-FR`: 20.82M params / 109.3 GFLOPs at 640 reference size; detects only
  from P2/4, P3/8, and P4/16.
- YOLOv11m-P2: 20.59M params / 88.9 GFLOPs; use this if `yolo11m.pt` is
  downloaded or otherwise available for partial initialization.

## Step 4. Expand Winning Proposed Variant

Status: pending final candidate freeze.

Config:

```text
configs/experiments/top3_proposed_detector_main.yaml
```

Procedure:

- finish the current one-seed architecture search first
- freeze one winning proposed detector family before statistical expansion
- edit config to keep only the winning backbone/module pair and exact modules
- run seeds `42`, `123`, and `2026` for the main comparison-consistent
  statistics; do this after the winning model is fixed, not during exploratory
  screening
- use extra seeds only as optional supplementary robustness checks, not as the
  main detector table

Do not compute p-values from one-seed screening. After the final candidate is
frozen, compute mean/std and paired p-values against the strongest baseline
groups:

- strongest YOLO large baseline, currently YOLOv11l
- strongest compact/lightweight baseline
- strongest runnable related-work comparison model, where protocol-compatible
  results are available

Primary statistical metrics:

- AP
- AP50
- recall
- F1

Paper organization after the final detector is frozen:

- main paper: one compact detector comparison table, one compact detector
  ablation table, and one efficiency trade-off plot or table
- supplementary: full per-seed table, p-values, all module ablations,
  input-resolution sweep, per-category metrics, NMS variants, adjacent-object
  subset, heat maps, and failure cases

Current high-priority final-candidate families:

- high-accuracy compact line: `P2CompV3-SEFR`
- stronger compact trade-off line: `P2P4-SelfAttnFR`
- keep `P2P4-SelfAttnFR-s123` running because it is already competitive while
  using about `20.82M` params

## Step 4b. Fill Reviewer-Facing YOLO Scale Coverage

Status: queued after active detector runs.

Rationale:

- Reviewers may question whether the proposed detector was compared only against
  convenient YOLO sizes.
- Keep simple YOLO family baselines separate from prior-art paper models. A
  model such as `LEAF-YOLO` is related work, not a plain YOLO scale baseline,
  even though its name contains YOLO.
- The main detector table should therefore include available nano/small/medium/
  large anchors for each YOLO family where the checkpoint can be loaded fairly.
- If a family does not provide the exact `n/s/m/l` naming convention, record the
  practical scale anchors and mark unavailable variants clearly.

Queue defaults:

- YOLOv5u: `n/s/m/l`
- YOLOv8: `n/s/m/l`
- YOLOv9: `t/s/m/c/e` practical anchors, because `n/l` are not always exposed
  as Ultralytics checkpoints
- YOLOv10: `n/s/m/l`
- YOLO11: `n/s/m/l`
- YOLO12: `n/s/m/l`
- YOLO26: `n/s/m/l`
- RT-DETR-L as the non-YOLO large anchor

Launcher:

```bash
bash scripts/ubuntu/train_extra_comparison_models_after_session.sh
```

The launcher uses `CHECK_MODELS=1`, so unavailable checkpoints are skipped and
documented rather than blocking the queue.

Paper/table grouping:

- Group A: `Plain YOLO family baselines` for YOLOv5u/8/9/10/11/12/26 scale
  comparisons trained under our protocol.
- Group B: `Generic non-YOLO baselines` for RT-DETR-style stock baselines.
- Group C: `Related-work prior models` for paper-proposed detectors such as
  LEAF-YOLO, CSFPR-RTDETR, SFFEF-YOLO, LSOD-YOLO, UAVDet, and HF-D-FINE.
- Group D: `Ours` for the selected proposed detector and its ablations.

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
