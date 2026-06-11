# Figure Generation Briefs For GPT-5.5 Pro / Specialist Figure Model

Updated: 2026-06-11 KST

Purpose: give a figure-generation model or Canva artist enough structure to draw
the method figures correctly. These are not decorative prompts. Each figure must
look like a computer-vision paper diagram and must preserve the technical story.

Double-blind rule: do not include university names, lab names, author names,
real logos, real skyline brands, or identifiable map labels. Do not use official
YOLO, NVIDIA, OpenAI, or model-provider logos in the submission figure.

Export rule:

- Editable source: SVG or Canva design.
- Paper export: PDF preferred, PNG backup at 300-600 dpi.
- Text must remain readable at two-column width.
- Use white or very light background. Avoid gradients, decorative blobs, and
  marketing-style illustration.

Recommended palette:

| Role | Color |
| --- | --- |
| 2D detector / proposed | Deep blue |
| 3D geometry / graph | Teal |
| Ambiguity / uncertainty | Amber |
| Verified / completed evidence | Green |
| Failure / rejected action | Muted red |
| Neutral modules | Light gray with dark text |

## Fig. 1: Overall CoM3D-ACE System

### Main Message

Show the whole system path:

```text
multi-UAV observations
-> P2P4-SelfAttnFR 2D evidence generator
-> EvidenceToken
-> 2D-to-3D evidence graph
-> ambiguity diagnosis
-> 3D evidence completion / re-observation
-> graph-grounded SAGE reasoner
-> verified object state
```

### Required Layout

Use a wide two-column pipeline, left to right.

1. Left panel: three UAV camera views.
   - Show small aerial image tiles, not just UAV icons.
   - Each tile should contain tiny object boxes.
   - Add small pose/depth/camera metadata icons beside the tiles.
2. Detector panel: `P2P4-SelfAttnFR 2D Evidence Generator`.
   - Do not draw full YOLO here. Just show it as a subsystem.
   - Output: boxes, class scores, uncertainty, feature descriptor.
3. EvidenceToken panel.
   - Show compact token fields: `bbox`, `class/logits`, `descriptor`,
     `uncertainty`, `pose`, `time`.
4. 3D evidence graph panel.
   - Show camera nodes, observation nodes, object hypothesis nodes.
   - Solid teal edges = matched support.
   - Dashed amber edges = conflict or uncertain association.
5. Ambiguity diagnosis panel.
   - Include entropy, view disagreement, occlusion, missing evidence, crowding.
6. Two right branches:
   - Top: `3D completion / re-observation`.
   - Bottom: `SAGE reasoner`.
7. Final small box: `Verified object state`.
   - class belief, 3D position, uncertainty, final action.

### Exact Prompt

```text
Draw a clean two-column academic computer-vision pipeline figure for a method
called CoM3D-ACE. The figure should show, from left to right: synchronized
multi-UAV image observations with tiny object boxes; a P2P4-SelfAttnFR 2D
evidence generator; compact EvidenceToken outputs containing bbox, class/logits,
feature descriptor, uncertainty, pose, and time; a 2D-to-3D evidence graph with
camera nodes, observation nodes, object hypothesis nodes, teal support edges and
amber conflict edges; ambiguity diagnosis using entropy, view disagreement,
occlusion, missing evidence and crowding; two branches for 3D completion /
re-observation and graph-grounded SAGE reasoner; and a final verified object
state. Use a restrained white-background CV-paper style, thin vector lines,
blue for detector, teal for 3D graph, amber for ambiguity, green for verified
completion. No logos, no institution names, no decorative gradients.
```

### Avoid

- Do not make a marketing hero graphic.
- Do not show the detector as the only main contribution.
- Do not use a generic drone swarm illustration without the evidence graph.

## Fig. 2: Proposed 2D Detector, P2P4-SelfAttnFR

### Main Message

This figure must look like a YOLO-family architecture diagram. It should not be
a simple left-to-right block diagram. It should show backbone, neck, and heads.

Our likely 2D proposed detector is:

```text
YOLOv11l-P2P4 balanced small-object detector
+ P2/P3/P4 detection heads
+ P5/32 used as context only, not as final detect head
+ Lite self-attention neck refinement
+ TinyFReLU spatial/high-frequency activation
+ overlap-aware NMS
```

Use the label:

```text
P2P4-SelfAttnFR
```

Where `SelfAttnFR` means:

```text
pooled-token self-attention neck refinement
+ TinyFReLU spatial/high-frequency gate
```

### Required Layout

Use the standard detector-architecture style:

1. Input crop at left.
2. Backbone column:
   - `Conv P1/2`
   - `C3k2 P2/4`
   - `C3k2 P3/8`
   - `C3k2 P4/16`
   - `SPPF/C2PSA P5/32 context`
3. Neck middle panel:
   - FPN top-down path from P5/P4 to P3 to P2.
   - PAN bottom-up path from P2 to P3 to P4.
   - Clearly label `P2/4`, `P3/8`, `P4/16`.
   - Add a note: `P5/32 is context only`.
4. Proposed refinement block:
   - Place `SelfAttnFR` on the neck outputs before detection heads.
   - Show two internal sub-blocks:
     - `Lite Self-Attention`: pooled-token context for adjacent small objects.
     - `TinyFReLU`: depthwise spatial condition + high-frequency residual.
5. Detection heads:
   - `Detect(P2, P3, P4)`.
   - Do not show P5 as a detection output.
6. Post-processing:
   - `overlap-aware NMS`.
7. Output:
   - EvidenceToken with bbox, class logits, descriptor, uncertainty, pose/time.

### Related-Research Visual Cues To Reflect

These are visual design references from our survey, not necessarily copied
architectures:

- SFFEF-YOLO / GCL-style idea: small-object detectors often reduce reliance on
  coarse large-object heads and emphasize shallow high-resolution heads.
- Universal YOLO / P2-head direction: 4x/8x/16x feature maps are important for
  tiny objects; avoid making stride-32 the main detection branch.
- CSFPR/UFO-style direction: spatial-frequency cues and position relations help
  tiny UAV targets; represent this through SelfAttnFR and TinyFReLU, not by
  adding unrelated modules.
- LEAF/LRDS-style direction: keep the detector efficient and lightweight; do not
  draw a huge transformer replacing the YOLO backbone.

### Exact Prompt

```text
Draw a YOLO-family architecture diagram for a UAV small-object detector named
P2P4-SelfAttnFR. The figure must use a standard backbone-neck-head layout, not a
generic pipeline. On the left, draw an input UAV crop with tiny adjacent object
boxes. Draw a YOLOv11l backbone column with Conv P1/2, C3k2 P2/4, C3k2 P3/8,
C3k2 P4/16, and SPPF/C2PSA P5/32 context. In the middle, draw a P2P4 balanced
FPN/PAN neck: top-down semantic fusion and bottom-up localization fusion. Clearly
show P2/4, P3/8, and P4/16 feature maps as the detection outputs. Mark P5/32 as
"context only, no detection head". Insert a proposed SelfAttnFR refinement block
before the detection heads. Inside SelfAttnFR, show two submodules: Lite
Self-Attention for adjacent-object context, and TinyFReLU spatial/high-frequency
gate. Then draw Detect(P2,P3,P4), overlap-aware NMS, and an EvidenceToken output
with bbox, class logits, feature descriptor, uncertainty, pose/time. Use clean
academic vector style, white background, blue for P2/shallow detail, teal for
P3/P4/neck fusion, amber for SelfAttnFR, green for detection output. Do not use
official YOLO logos or claim SOTA.
```

### Must Show

- Backbone / neck / head separation.
- P2/4, P3/8, P4/16 as final detection heads.
- P5/32 as context only.
- SelfAttnFR insertion point.
- TinyFReLU as part of SelfAttnFR or immediately after neck refinement.
- EvidenceToken output.

### Avoid

- Do not draw a simple row of boxes only.
- Do not show P5/32 as a final detection head.
- Do not include CBAM, DCT, wavelet, DynFreq, or SE as active blocks unless the
  final selected model changes.
- Do not write `best`, `SOTA`, or `outperforms` in the figure.

## Fig. 3: 3D Generation, Restoration, And Evidence Graph

### Main Message

Show why the paper is more than a 2D detector. The 3D module converts multi-view
2D evidence into object-level 3D hypotheses and fills missing or degraded
evidence.

### Required Layout

1. Left: MarineCity multi-view capture.
   - Several UAV views around a coastal urban block.
   - Camera frustums/rays should point toward the same candidate object.
2. Middle-left: 3D generation/restoration.
   - Use neutral labels: `restored view`, `generated support`, `depth/geometry`.
   - Do not overclaim if final generation model is not selected yet.
3. Middle-right: 3D evidence graph.
   - observation nodes, object nodes, support/conflict edges.
   - missing evidence slot filled by generated/restored evidence.
4. Right: verified object state.
   - 3D position, class belief, uncertainty, ambiguity resolved/unresolved.

### Exact Prompt

```text
Draw a clean academic method figure for 3D evidence completion in a cooperative
multi-UAV system. On the left, show multiple UAV camera views of a coastal urban
scene observing the same tiny object from different angles. Draw camera frustums
or rays into a shared 3D space. In the middle, show a 3D generation/restoration
module that restores degraded evidence or generates missing support from
multi-view observations and geometry. Then show a 3D evidence graph with
observation nodes, object hypothesis nodes, teal support edges, amber conflict
edges, and one missing-evidence slot being filled. On the right, show a verified
object state with class belief, 3D position, uncertainty, and next action. Use
teal for geometry and graph, green for completed evidence, amber for ambiguity.
No photorealistic city branding, no real map labels, no institution identity.
```

### Avoid

- Do not make this only a dataset/map figure.
- Do not show impossible 3D reconstruction details before the final model is
  chosen.
- Do not imply real-world flight validation if we only have simulator data.

## Supplementary Method Figure: SAGE Reasoner And Safety Verifier

### Main Message

The LLM/VLM reasoner is sparse, graph-grounded, and verified. It does not
directly control the UAV.

### Required Layout

1. Inputs:
   - ambiguous graph node
   - multi-view crops
   - graph summary
   - geometry residuals
   - allowed actions
2. SAGE prompt builder:
   - protected system rules
   - evidence summary
   - candidate action list
3. VLM/LLM output:
   - constrained JSON schema
   - class, confidence, evidence clues, missing evidence, recommended action
4. Verifier:
   - graph consistency
   - safety/no-fly/battery/communication checks
   - reject unsupported rationale or unsafe action
5. Final action:
   - finalize, reject, verify, re-observe, close/side/neighbor view.

### Exact Prompt

```text
Draw a supplementary method diagram for a graph-grounded VLM/LLM reasoner named
SAGE. The figure should show that only high-ambiguity object hypotheses are sent
to the reasoner. Inputs include an ambiguous graph node, multi-view crops, graph
summary, geometry residuals, and allowed actions. The SAGE prompt builder has
protected system rules, an evidence summary, and a candidate action list. The
VLM/LLM returns a constrained JSON output with class, confidence, evidence clues,
missing evidence, and recommended action. A graph and safety verifier checks
graph consistency, no-fly/battery/communication constraints, and rejects invalid
rationales or unsafe actions. The final action can be finalize, reject, verify,
re-observe, close view, side view, or neighbor confirmation. Use a clean
white-background academic diagram. Use amber for ambiguity, teal for prompt and
graph context, green for accepted output, red for rejected/unsafe output. Do not
show the LLM directly controlling the drone.
```

### Avoid

- Do not draw it as an autonomous flight-command agent.
- Do not include API/vendor logos.
- Do not include real prompt text that could reveal author identity or hidden
  instructions.

## Main vs Supplement Placement

Recommended main paper:

1. Fig. 1 Overall CoM3D-ACE system.
2. Fig. 2 P2P4-SelfAttnFR detector architecture.
3. Fig. 3 3D generation/restoration and evidence graph.

Recommended supplementary:

1. SAGE reasoner and safety verifier detailed figure.
2. Grad-CAM / heat-map figure for baseline vs proposed detector.
3. Full detector leaderboard plots.
4. Extra MarineCity layout, camera poses, qualitative cases, and failure cases.

## Heat-Map Figure Note

The 2D heat-map/Grad-CAM figure should be generated after training from fixed
checkpoints. No retraining is needed. Use the same validation images for:

- YOLOv11l baseline.
- P2P4-SelfAttnFR final proposed detector.
- Optional ablations: P2/P4 only, TinyFReLU only, SelfAttnFR without TinyFReLU.

Main paper should include only 3-4 representative cases. Supplementary should
include tiny object, adjacent/overlap, low contrast, false positive, and false
negative cases.
