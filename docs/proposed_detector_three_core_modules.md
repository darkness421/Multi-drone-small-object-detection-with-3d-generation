# Proposed Detector: Three Core Modules

Updated: 2026-06-10

This note freezes the detector search direction into three paper-facing core
modules. The exact final model can still change after the current GPU search,
but every candidate should be explainable as one or more of these modules.

## Goal

Find a proposed detector that improves the YOLOv11l large baseline while keeping
the model size competitive.

Primary gate:

- AP greater than `0.3835`
- Params below `25.32M` if possible
- If Params increase, the paper must show the accuracy/complexity tradeoff
  against YOLOv11l, YOLOv12l, YOLOv8l, and runnable related-work models

## Core 1. Compact Capacity Redistribution Module

Purpose:

- Reduce model size or keep it under the YOLOv11l parameter budget.
- Move capacity away from less useful heavy large-object branches and preserve
  capacity in small-object branches.

Current implementation candidates:

- `P2CompV3-FR`: compressed P2 model, about `24.08M` params.
- `P2EffV3-FR`: efficient P2 model, about `23.15M` params.
- `P2BalV3-FR`: balanced model, about `25.28M` params.
- `P2P4-FR`: 4x/8x/16x detection heads only, `20.82M` params.

Paper role:

- This is the efficiency core.
- It answers the reviewer question: "Is the detector simply larger?"
- Ablation should compare YOLOv11l, P2 full, P2 balanced, P2 compressed, and
  P2 efficient under the same `imgsz=1280` protocol.

Success signal:

- Best case: AP/AP50 improve while Params are lower than YOLOv11l.
- Acceptable case: AP/AP50 improve with approximately equal Params.
- Backup case: AP/AP50 improve with increased Params, but only if larger
  comparison models do not dominate the proposed detector.

## Core 2. Multi-Scale High-Resolution Evidence Module

Purpose:

- Preserve tiny-object evidence before it collapses in large-stride features.
- Use P2/stride-4 and high-resolution neck features for VisDrone/UAV objects.
- Add dynamic frequency refinement to distinguish weak object edges from
  background texture.

Current implementation candidates:

- P2/P3/P4 detection heads: `Detect(P2/4, P3/8, P4/16)`.
- Four-head reference: `Detect(P2/4, P3/8, P4/16, P5/32)`.
- `tiny_frelu_neck`: spatial activation with high-frequency residual.
- `dynfreq_c3_p2`: dynamic frequency refinement on the P2 C3/C3k2 output.
- `dynfreq_c3_small`: dynamic frequency refinement on P2 and P3 outputs.

Current mathematical form:

```text
low = AvgPool3x3(x)
high = x - low
[g_h, g_l] = Gate(GAP(x))
y = x + tanh(alpha) * (g_h * DWConv(high) + g_l * (DWConv(low) - x))
```

Paper role:

- This is the multi-scale/frequency core.
- It connects the small-object observation from related work: high downsampling
  can erase tiny-object cues, so the detector must keep high-resolution
  evidence.
- The 4x/8x/16x-only head tests whether removing the 32x detection branch
  improves UAV small-object performance while also reducing model size.
- The module can be drawn as a C3/C3k2-side refinement block rather than only as
  an input wavelet stem.

Success signal:

- APsmall, recall, and F1 improve on small/crowded objects.
- Overall AP improves without a large parameter increase.
- Heat maps show stronger attention around small targets.

## Core 3. Overlap-Aware Small-Object Decision Module

Purpose:

- Reduce missed detections caused by adjacent-object bounding box overlap.
- Separate crowded small targets that standard NMS may suppress.
- Provide an ambiguity score that can later trigger 3D reconstruction or LLM/VLM
  re-observation.

Current implementation candidates:

- Class-aware NMS IoU sweep, especially around `0.50`, `0.55`, `0.60`.
- Soft-NMS or DIoU/CIoU-NMS if implemented locally.
- Weighted Boxes Fusion only for TTA/ensemble-style supplementary analysis.
- Rotation-TTA as an eval-only add-on: rotate the image, run the horizontal-box
  detector, rotate predictions back, then merge with overlap-aware NMS/WBF.
  This uses the rotated-object motivation from related work such as GLF-Net /
  reference `[30]` without pretending that a horizontal-box VisDrone detector
  learned a true angle parameter.
- Adjacent-object subset evaluation: cases where two or more GT boxes have high
  proximity or non-trivial overlap.

Paper role:

- This is the crowded-small-object decision core.
- It should not be presented as only a post-processing trick. The main claim is
  overlap-aware decision refinement for dense UAV scenes, with NMS variants as
  the first practical implementation.
- Reference `[30]` supports the idea that UAV/remote-sensing targets can benefit
  from orientation-aware localization in dense or oblique scenes. For our
  current detector table, the fair version is rotation-TTA/merge at inference.
  A true OBB detector requires oriented labels or synthetic oriented labels from
  the Isaac/MarineCity benchmark, so it belongs in the later 3D benchmark stage
  or supplementary future/extended ablation.
- It also links the detector to the later reasoner: ambiguous/overlapped cases
  become evidence tokens for 3D/LLM stages.

Success signal:

- Recall and F1 improve on adjacent-object subsets.
- Overall AP/AP50 do not drop.
- Qualitative examples show one object no longer suppressing a neighboring
  object.
- Rotation-TTA improves recall on oblique/elongated adjacent objects without
  hurting latency too much; report it separately because it changes inference
  cost.

## Main Ablation Table

Recommended main-paper rows:

| Row | Detector Variant | Core 1 | Core 2 | Core 3 | Purpose |
| --- | --- | --- | --- | --- | --- |
| 1 | YOLOv11l baseline | - | - | - | strong baseline |
| 2 | compact/balanced P2 | yes | partial | - | size redistribution |
| 3 | + TinyFReLU | yes | yes | - | spatial small-object activation |
| 4 | + DynFreq-C3 | yes | yes | - | dynamic frequency multi-scale refinement |
| 5 | + overlap-aware NMS | yes | yes | yes | final detector decision |

Supplementary rows:

- wavelet stem
- DCT stem
- CBAM neck
- SE neck
- self-attention/DINO-style pooled context
- partial deformable neck
- input-size sweep: `960`, `1280`, `1536`
- adjacent-object subset
- rotation-TTA / orientation-aware inference-only merge
- per-category AP/F1/recall
- heat maps and failure cases

Final heat-map evidence after model selection:

- quantitative heatmap: `baseline`, `Core 1 only`, `Core 2 only`, `Core 3
  only`, `Core 1 + Core 2`, and `Core 1 + Core 2 + Core 3`
- qualitative Grad-CAM/attention panel: same images and crops for every row
- recommended cases: tiny recovered true positive, adjacent-object NMS
  suppression, low-contrast miss, dense background false positive
- config: `configs/experiments/final_detector_core_ablation_heatmap.yaml`
- helper: `scripts/ubuntu/run_core_ablation_gradcam_plan.sh`

## Current Experiment Queue Mapping

Already completed or running:

- Core 1: `P2CompV3-FR`, `P2EffV3-FR`, `P2BalV3-FR`
- Core 2: `P2-FR`, `P2-DCT-FR`, `P2-CBAM-FR`, `P2-WCBAM-FR`
- Core 3: NMS055 evaluation and NMS sweep scripts

Newly queued candidates:

- `p2_balanced_v3_dynfreq_p2_tiny_frelu`
- `p2_balanced_v3_dynfreq_small_tiny_frelu`
- `p2p4_balanced_tiny_frelu`
- `p2p4_balanced_dynfreq_p2_tiny_frelu`
- `p2p4_balanced_dynfreq_small_tiny_frelu`
- `p2_dynfreq_frelu`
- `p2_dynfreq_cbam_frelu`

New compact-performance ideas queued after the current under-parameter stage:

- `p2_efficient_v3_dynfreq_p2_tiny_frelu`
  - idea: keep the `23.15M` efficient backbone, then recover small-object AP by
    adding DynFreq only to the P2 path.
  - expected effect: small AP/recall gain with minimal parameter increase.
- `p2_efficient_v3_se_tiny_frelu`
  - idea: add cheap channel gates to the efficient backbone instead of CBAM.
  - expected effect: better precision/background suppression with lower cost
    than CBAM/self-attention.
- `p2_compress_v3_dynfreq_p2_tiny_frelu`
  - idea: keep the `24.08M` compressed model and add only P2 dynamic frequency
    refinement.
  - expected effect: recover detail lost by compression without crossing
    YOLOv11l params.
- `p2_compress_v3_se_tiny_frelu`
  - idea: cheap channel recalibration for the compressed model.
  - expected effect: parameter-light precision/F1 recovery.
- `p2p4_balanced_se_tiny_frelu`
  - idea: keep the `20.82M` P2/P3/P4-only head and add SE gates.
  - expected effect: test whether the very compact no-P5 detector can recover
    enough AP with low-cost gating.
- `p2p4_balanced_selfattn_tiny_frelu`
  - idea: add pooled-token context to the compact P2/P3/P4 detector.
  - expected effect: recover global context lost by removing the 32x/P5 head,
    while still staying far below YOLOv11l params.

These candidates are deliberately cheaper than `CBAM + wavelet` or deformable
refinement. They test the paper-facing claim that the proposed detector improves
UAV small-object detection through capacity redistribution and high-resolution
evidence, not simply by adding more parameters.

## Decision Rule

If a candidate satisfies `AP > 0.3835` and `Params < 25.32M`, freeze it as the
detector front-end candidate and expand to multi-seed confirmation.

If no under-parameter candidate passes, use the best over-parameter candidate
only after confirming that larger YOLO and related-work comparison models do not
outperform it.

If DynFreq-C3 improves recall/F1 but not AP, keep it as a supplementary ablation
or combine it only with the best compact backbone.

## Post-Selection Statistical Plan

Do not spend full statistical budget before the strong proposed detector family
is selected. The current search stage should find the best architecture first;
after that, freeze the model definition and run the paper-facing statistics.

Selection gate:

- Pick one final proposed detector family after the one-seed search. The public
  detector name is `SAFR-YOLO`; the current implementation label is
  `P2P4-SelfAttnFR`.
- Lock the exact modules, YAML, input size, training recipe, and evaluation
  protocol before running repeated seeds.
- Keep comparison-model queues separate from proposed-model queues so the final
  detector claim is not mixed with architecture search artifacts.

Seed plan:

- Main paper statistics: seeds `42`, `123`, and `2026`.
- Optional supplementary robustness only: extra seeds such as `7` and `3407`
  may be added after the main paper table is fixed, but they should not replace
  the 3-seed comparison-consistent result.
- Report mean, standard deviation, and best seed for AP, AP50, precision,
  recall, F1, Params, GFLOPs, and FPS/latency.

Statistical tests:

- Use paired tests against the strongest YOLO baseline and the strongest compact
  baseline under the same dataset/protocol.
- Primary p-value metrics: AP, AP50, recall, and F1.
- Use paired t-test when per-seed differences are roughly normal; include
  Wilcoxon signed-rank as the safer non-parametric companion in supplementary
  material.
- Do not claim statistical significance from one-seed screening runs.

Ablation organization after freezing the final model:

- Main paper: compact ablation table with baseline, Core 1, Core 1 + Core 2,
  Core 1 + Core 2 + Core 3, and final proposed detector.
- Supplementary: full module sweep, input-resolution sweep, per-category
  results, adjacent-object subset, NMS variants, heat maps, failure cases, and
  all per-seed tables.
- Heat-map evidence should use the same images across ablation rows so reviewers
  can visually compare what each module changes.

Comparison-model organization:

- Main table should include YOLOv11l baseline, strong large YOLO anchors, the
  best compact/lightweight YOLO anchors, runnable related-work models, and the
  final proposed detector.
- Supplementary should include all completed nano/small/medium/large YOLO rows,
  runnable related-work rows, incomplete/memory-limited notes, and protocol
  differences such as `640` vs `1280` input resolution.
