# System Ablation And Evaluation Plan

Updated: 2026-06-04

This plan separates the detector-only claim from the full multi-UAV system
claim. The paper should not evaluate only a proposed YOLO model; it should show
how detector quality transfers into 3D association, final classification,
ambiguity resolution, and graph-grounded reasoning.

## Contribution Structure

We use three main contributions:

1. Proposed small-object detector front-end.
   - High-resolution detector protocol.
   - YOLOv11/P2/TinyFReLU candidate.
   - Attention/frequency modules and crowded-object NMS variants.
   - Detector-only AP/AP50/APtiny/recall/F1/efficiency comparison.

2. Multi-UAV 3D evidence completion benchmark and system.
   - Synchronized multi-UAV views, camera poses, object IDs, 3D locations, and
     ambiguity labels.
   - Object-centric 3D evidence graph.
   - Restoration or 3D generation module for missing/degraded evidence.
   - Final object classification, association, 3D localization, false
     merge/split, and ambiguity-resolution evaluation.

3. Selective graph-grounded reasoner.
   - VLM/LLM is not always-on.
   - It is invoked only for ambiguous object nodes.
   - Outputs final decision, rationale, ambiguity type, and optional
     re-observation request.
   - Explanations must cite graph evidence, supporting/conflicting views, and
     missing evidence.

## Main Stack Ablation

| Row | Detector | 3D graph | Restoration / 3D gen | Reasoner | Purpose |
| --- | --- | --- | --- | --- | --- |
| A | Baseline YOLOv11l | No | No | No | Single-image baseline |
| B | Proposed YOLO | No | No | No | Detector-only gain |
| C | Baseline YOLOv11l | Yes | No | No | 3D graph gain with baseline detector |
| D | Baseline YOLOv11l | Yes | Yes | No | Restoration/3D generation gain with baseline detector |
| E | Baseline YOLOv11l | Yes | Optional | Yes | Reasoner gain without proposed detector |
| F | Proposed YOLO | Yes | No | No | Detector-to-3D transfer |
| G | Proposed YOLO | Yes | Yes | No | Detector plus completion complementarity |
| H | Proposed YOLO | Yes | Yes | Yes | Full proposed system |

Main claim:

```text
The proposed detector improves local 2D evidence.
The 3D graph improves object-level association and ambiguity handling.
The restoration/3D generation module improves missing or degraded evidence.
The selective reasoner improves final classification for ambiguous cases while
providing graph-grounded explanations.
```

## Metrics

Detector-only:

- AP, AP50, AP75.
- APsmall/APtiny, recall-small/tiny.
- precision, recall, F1.
- Params, GFLOPs, FPS, latency, memory.
- crowded/adjacent-object subset metrics.
- input-size sensitivity: 960, 1280, 1536.

System-level:

- final object classification accuracy.
- macro-F1.
- association F1.
- 3D center error and 3D IoU.
- false merge and false split.
- wrong high-confidence rate.
- ambiguity AUROC/AUPRC and ambiguity resolution rate.
- re-observation gain.
- VLM/LLM call count, token cost, latency, communication cost.

Category-wise:

- per-class detector AP/AP50/recall/F1.
- per-class final classification macro-F1.
- per-class false merge and false split.
- per-class ambiguity resolution.
- report hard classes separately: pedestrian, boat, obstacle/debris, occluded
  vehicle, and dense adjacent vehicles.

Explainability:

- detector heat maps or Grad-CAM.
- graph support/conflict edges.
- before/after restored or generated evidence.
- reasoner rationale.
- hallucinated-evidence rate.
- invalid-rationale rate.
- faithfulness check by removing cited supporting/conflicting views.
- human agreement on selected ambiguous cases.

## Paper Placement

Main paper:

- compact detector table.
- system-stack ablation table.
- one category-wise summary plot or table.
- one qualitative explanation panel.

Supplementary:

- full detector leaderboard and per-seed results.
- input-size curves.
- ablation heat maps.
- full per-category tables.
- prompt schema, reasoner outputs, failure cases, and faithfulness checks.
