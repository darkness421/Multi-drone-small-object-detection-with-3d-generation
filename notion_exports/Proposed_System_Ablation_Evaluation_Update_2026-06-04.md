# Proposed System Ablation And Evaluation Update

Date: 2026-06-04

## Summary

We should present the paper as a full multi-UAV decision system, not only as a
new YOLO detector. The detector is evaluated separately as the 2D evidence
front-end, then the full system is evaluated as a stack:

```text
detector -> 3D evidence graph -> restoration / 3D generation -> selective reasoner
```

## Three Contributions

1. **Proposed small-object detector front-end**
   - YOLOv11/P2/TinyFReLU candidate.
   - NMS variants for adjacent small objects.
   - High-resolution protocol at 1280, with 960/1280/1536 sensitivity.

2. **Multi-UAV 3D evidence completion benchmark/system**
   - Synchronized multi-UAV views, camera poses, object IDs, 3D locations, and
     ambiguity labels.
   - Object-centric 3D graph for association, false merge/split handling, and
     final object-level decision making.

3. **Selective graph-grounded reasoner**
   - VLM/LLM is called only for ambiguous object nodes.
   - It produces final decision, rationale, ambiguity type, and optional
     re-observation request.
   - Explanations should cite graph evidence rather than hallucinated context.

## Main Ablation Stack

| Row | Detector | 3D Graph | Restoration / 3D Gen | Reasoner | Purpose |
| --- | --- | --- | --- | --- | --- |
| A | Baseline YOLOv11l | No | No | No | Single-image baseline |
| B | Proposed YOLO | No | No | No | Detector-only gain |
| C | Baseline YOLOv11l | Yes | No | No | 3D graph gain with baseline detector |
| D | Baseline YOLOv11l | Yes | Yes | No | Restoration/3D generation gain |
| E | Baseline YOLOv11l | Yes | Optional | Yes | Reasoner gain without proposed detector |
| F | Proposed YOLO | Yes | No | No | Detector-to-3D transfer |
| G | Proposed YOLO | Yes | Yes | No | Detector plus completion complementarity |
| H | Proposed YOLO | Yes | Yes | Yes | Full proposed system |

## Evaluation Metrics

Detector-only:

- AP, AP50, APsmall/APtiny
- recall, precision, F1
- Params, GFLOPs, FPS/latency
- crowded/adjacent-object subset
- input-size sensitivity: 960 / 1280 / 1536

Full system:

- final classification accuracy and macro-F1
- association F1
- 3D center error / 3D IoU
- false merge / false split
- ambiguity resolution rate
- wrong high-confidence rate
- re-observation gain
- VLM/LLM calls, cost, latency

Category-wise:

- per-class AP/AP50/recall/F1
- per-class final classification macro-F1
- per-class false merge/split
- per-class ambiguity resolution

Explainability:

- detector heat maps / Grad-CAM
- graph support and conflict edges
- before/after restoration or generated evidence
- reasoner rationale
- hallucinated-evidence rate
- invalid-rationale rate
- faithfulness by removing cited views

## Paper Update

The Overleaf paper has been updated to:

- use three main contributions
- include detector-only vs whole-system ablation framing
- add the system-stack ablation table
- add per-category performance and explainability evaluation text

Related repo docs:

- `docs/system_ablation_evaluation_plan.md`
- `docs/current_experiment_steps.md`
- `docs/survey_input_resolution_protocol.md`
