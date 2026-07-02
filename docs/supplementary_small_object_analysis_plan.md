# Supplementary Small-Object Analysis Plan

This plan adds two reviewer-facing analyses to the ACCV supplementary material:
ablation heat maps and input pixel-size sensitivity.

## Why This Matters

Small-object detector papers are often challenged on two points:

- The gain may come from input resolution rather than the proposed module.
- The proposed module may improve aggregate AP but not actually focus on tiny or
  adjacent targets.

The supplementary material should answer both without overloading the main
paper.

## Analysis A. Ablation Heat Maps

Quantitative heat map:

- rows: final core-module ablations
- columns: AP, AP50, recall, F1
- cell values: delta against the matching control or baseline run
- purpose: show which module helps recall and F1 rather than only AP

Final rows after the best detector is selected:

- baseline
- Core 1 only: compact capacity redistribution
- Core 2 only: 4x/8x/16x multi-scale high-resolution evidence with
  TinyFReLU/DynFreq-C3
- Core 3 only: overlap-aware NMS/decision
- Core 1 + Core 2
- Core 1 + Core 2 + Core 3

Qualitative heat map:

- same images across baseline and ablations
- show original crop, predictions, heat map, blended overlay
- target cases: tiny true positives, adjacent targets, low-contrast misses,
  dense marine-city clutter

Command:

```bash
python -m scripts.build_supplementary_detector_analysis
```

Final core-ablation Grad-CAM plan:

```bash
BASELINE_WEIGHT=outputs/detectors/.../baseline/best.pt \
CORE1_WEIGHT=outputs/detectors/.../core1/best.pt \
CORE2_WEIGHT=outputs/detectors/.../core2/best.pt \
CORE3_WEIGHT=outputs/detectors/.../core3/best.pt \
CORE12_WEIGHT=outputs/detectors/.../core1_core2/best.pt \
FULL_WEIGHT=outputs/detectors/.../full/best.pt \
IMAGES="case1.jpg case2.jpg case3.jpg" \
bash scripts/ubuntu/run_core_ablation_gradcam_plan.sh
```

Outputs:

```text
outputs/reports/supplementary_detector/ablation_delta_heatmap.csv
outputs/reports/supplementary_detector/figures/ablation_delta_heatmap.png
outputs/qualitative/gradcam/core_ablation/gradcam_run_plan.json
```

## Analysis B. High-Resolution Input Pixel-Size Sweep

Pilot setting:

- official input size: 1280
- supplementary sensitivity sizes: 960 and 1536
- seed: 42
- models: current best baseline YOLOv11l and proposed P2/TinyFReLU candidate
- metrics: AP, AP50, recall, F1, FPS, latency, Params, GFLOPs

Command:

```bash
WAIT_FOR=server-top3-proposed-screening \
GPUS=0 SEEDS=42 \
bash scripts/ubuntu/train_input_size_sweep.sh
```

After the pilot:

- expand only the strongest baseline and strongest proposed detector to seeds
  42, 123, and 2026
- keep 1280 as the official detector protocol unless 1536 gives a meaningful
  AP or recall gain at acceptable cost
- if 1536 is too slow, report it as an efficiency boundary rather than a final
  operating point

Outputs:

```text
outputs/reports/supplementary_detector/input_size_sweep.csv
outputs/reports/supplementary_detector/figures/input_size_ap_ap50.png
outputs/reports/supplementary_detector/figures/input_size_efficiency.png
```

## Supplementary Figure Slots

Recommended ordering:

| Slot | Content | Purpose |
| --- | --- | --- |
| Fig. S1 | Full detector leaderboard | Shows all nano/small/medium/large baselines |
| Fig. S2 | Ablation delta heat map | Shows which module contributes |
| Fig. S3 | High-resolution AP/AP50 sensitivity curve | Separates module gains from high-resolution scaling |
| Fig. S4 | High-resolution runtime curve | Shows deployment cost |
| Fig. S5 | Core-module Grad-CAM/attention heat-map panel | Shows focus changes from Core 1, Core 2, Core 3, and full model |

## Main-Paper Boundary

Keep the main paper self-contained:

- main paper: final detector table, final proposed module summary, and one
  qualitative example if space allows
- supplementary: full heat maps, all input-size curves, per-seed tables,
  runtime details, and failure cases
- official detector rows remain `imgsz=1280`; `960` and `1536` are sensitivity
  checks, not a replacement protocol

If the proposed detector does not beat YOLOv11l, keep these analyses as evidence
that the detector is a strong evidence generator for the 3D graph rather than
the primary contribution.
