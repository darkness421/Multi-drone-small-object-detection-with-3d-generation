# Detector Candidate Figure Update Brief

Updated: 2026-06-19 KST

Purpose: give GPT-5.5 Pro, a specialist figure-generation model, or a Canva
artist a compact working guide for updating detector-related figures while the
final 2D detector combination is still being decided.

Important: the final proposed 2D detector combination is not frozen yet. Treat
`P2P4-SelfAttnFR` as the current leading candidate / baseline drawing target,
not as the final paper model.

This document should be checked before redrawing:

- Main Fig. 1 overall CoM3D-ACE framework
- Main Fig. 2 proposed detector
- Supplementary Fig. S1 SelfAttnFR module
- Supplementary Fig. S2 TinyFReLU activation
- Supplementary Fig. S3 overlap-aware NMS

## Current Leading Candidate Status

Current leading detector candidate, not final:

```text
Public name: SAFR-YOLO
Implementation label: P2P4-SelfAttnFR
Backbone family: YOLOv11l-derived
Detection heads: P2/4, P3/8, P4/16
Context path: P5/32 context only, not a primary detection head
Core modules: high-resolution P2/P3/P4 heads + SelfAttnFR + TinyFReLU
Post-processing: overlap-aware NMS / NMS sweep as eval-stage refinement
```

Current 1280 / 3-seed result for the leading candidate:

| Model | AP | AP50 | F1 | Params | GFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| P2P4-SelfAttnFR | 0.3822 | 0.6052 | 0.6273 | 20.82M | 109.3 |

High-capacity comparison context:

| Model | Status | AP | AP50 | F1 | Params | GFLOPs |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| YOLOv9e | partial 2-seed, still running | about 0.3853 | about 0.6108 | about 0.6334 | 58.15M | 192.7 |

Main interpretation:

```text
YOLOv9e is a stronger high-capacity baseline, but it is much larger.
SAFR-YOLO is the current strongest parameter-performance trade-off candidate.
```

Do not write "outperforms all models" or "SOTA" in any figure.

## Pending 22M Budget Stretch Candidate

We may test stretch variants before freezing the detector figure:

```text
Candidate label: P2P4-SelfAttnRF-FR
Public label if selected: SAFR-YOLO-B22 or SAFR-YOLO with RF context
Target budget: <= 22M params
Reason: improve raw AP while remaining far smaller than YOLOv9e
```

Candidate module change:

```text
P2P4-SelfAttnFR
+ lightweight dilated receptive-field context on high-resolution neck outputs
```

Visual explanation:

- Keep the main SAFR-YOLO architecture intact.
- Add a small optional RF context branch inside or beside SelfAttnFR.
- Show it as depthwise dilated local context, not a large transformer.
- The branch should be visually small and lightweight.
- Suggested label: `Dilated RF context (d=2,3 DWConv)`.

Do not promote this candidate into the main paper figures unless it is confirmed
by the same 1280 / 3-seed protocol and explicitly selected as the paper model.
Before that, show it only as an optional / candidate note in supplementary,
internal slides, or figure-redraw instructions.

## Figure-Level Update Rules

### Main Fig. 1: Overall CoM3D-ACE Framework

Keep Fig. 1 system-level. Do not show all detector internals here.

Detector panel label:

```text
SAFR-YOLO 2D Evidence Generator
```

Small sublabel while using the current leading candidate:

```text
P2P4-SelfAttnFR implementation
```

If the 22M RF candidate is selected later:

```text
P2P4-SelfAttnRF-FR implementation
```

Do not add CBAM, DCT, wavelet, SE, or DynFreq labels to Fig. 1 unless they are
selected after the detector freeze.

### Main Fig. 2: Proposed Detector

This is the figure that should change if the selected detector combination
changes.

Current candidate figure should show:

```text
Input UAV crop
-> YOLOv11l-derived backbone
-> P2P4 FPN/PAN neck
-> P2/4, P3/8, P4/16 detection heads
-> SelfAttnFR refinement
-> TinyFReLU activation
-> overlap-aware NMS
-> EvidenceToken
```

Required visual details:

- P2/4, P3/8, and P4/16 are the current candidate detection heads.
- P5/32 is context only.
- SelfAttnFR sits before the detection heads.
- TinyFReLU can be drawn inside SelfAttnFR or immediately after local
  refinement.
- Overlap-aware NMS is post-processing, not a trainable backbone block.
- EvidenceToken includes bbox, class/logits, confidence, uncertainty, view/pose,
  and time.

If `P2P4-SelfAttnRF-FR` is selected later, update Fig. 2 by adding one small branch:

```text
SelfAttnFR block:
  1. pooled-token self-attention path
  2. local TinyFReLU refinement path
  3. lightweight dilated RF context path
```

Use a small note:

```text
RF context uses low-cost depthwise dilated refinement on high-resolution features.
```

Do not make the RF branch visually larger than the detector heads.

### Supplementary Fig. S1: SelfAttnFR Module

Current S1 should show two paths:

```text
pooled-token context path
local refinement path with TinyFReLU
```

If RF candidate is selected, update S1 to show three paths:

```text
pooled-token context path
local TinyFReLU refinement path
dilated RF context path
```

Suggested S1 flow:

```text
Input feature F
-> pooled-token self-attention -> context-refined feature
-> local refinement + TinyFReLU -> local feature
-> optional dilated RF context d=2,3 -> RF feature
-> concat + 1x1 fusion
-> refined output
```

Keep equations light in the figure. Put detailed equations in the text or
supplementary method subsection.

### Supplementary Fig. S2: TinyFReLU

TinyFReLU does not need to change if the RF candidate is selected.

Keep S2 focused on:

```text
depthwise spatial-condition branch
high-frequency residual branch
element-wise max with identity
```

Do not add the RF module here.

### Supplementary Fig. S3: Overlap-Aware NMS

S3 does not need to change when the detector architecture changes.

Keep S3 focused on:

```text
candidate detections
IoU-only NMS false suppression
overlap-aware decision using IoU, center distance, and size similarity
kept adjacent true objects
```

Show it as post-processing / eval-stage refinement, not as a trainable module.

## Names To Use

Use these names consistently:

| Usage | Name |
| --- | --- |
| Public detector name | SAFR-YOLO |
| Current implementation label | P2P4-SelfAttnFR |
| Optional 22M stretch label | P2P4-SelfAttnRF-FR |
| Reasoner | ACE-Reasoner |
| Whole system | CoM3D-ACE |

Avoid these names in candidate / paper figures unless they are selected:

- CBAM
- DCT
- wavelet
- SE
- DynFreq
- Deformable

They can appear in supplementary ablation tables, not in the main detector
architecture figure before selection.

## Prompt Snippet For Redrawing Fig. 2

Use this prompt for a current candidate redraw. After final detector freeze,
replace the candidate branch with the selected combination:

```text
Redraw Main Fig. 2 as a clean YOLO-family detector architecture diagram for
SAFR-YOLO. Show a YOLOv11l-derived backbone, a P2P4 FPN/PAN neck, P2/4, P3/8,
and P4/16 detection heads, and P5/32 as context only. Insert SelfAttnFR before
the detection heads, with pooled-token self-attention and TinyFReLU local
refinement. If the selected model is P2P4-SelfAttnRF-FR, add a small lightweight
dilated RF context branch inside SelfAttnFR, labeled "dilated RF context
(d=2,3 DWConv)". Then show overlap-aware NMS and EvidenceToken output. Use a
white academic computer-vision paper style, blue for detector backbone/neck,
amber for proposed refinement, green for outputs, and no logos or SOTA claims.
```

## Final Freeze Checklist

Before freezing the paper figures:

- Confirm which detector combination is selected for the paper.
- Confirm final 3-seed metrics and parameter count.
- Confirm whether overlap-aware NMS is included in the final main result or only
  in supplementary.
- Update Fig. 2 first.
- Update Fig. 1 detector label only after Fig. 2 is stable.
- Update S1 only if the RF branch becomes part of the final model.
- Leave S2 and S3 mostly unchanged.
- Export final figures as PDF for Overleaf and PNG previews for GitHub.
