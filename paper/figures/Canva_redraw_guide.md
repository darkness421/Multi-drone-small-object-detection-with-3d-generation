# Canva redraw guide for revised CoM3D-ACE figures

## Naming to use consistently
- System: **CoM3D-ACE**
- Detector / proposed model: **WavePD-YOLO**
- Benchmark dataset: **MarineCity-MUAV**
- Downstream loop: **ACE-ReObs** or **ACE-ReObs Loop**

## Global drawing rule
Use four clean colors only: blue = simulation/data, green = detector, purple = 3D evidence, orange/yellow = ambiguity/LLM/re-observation. Keep every arrow outside dense text areas.

## Figure 1 arrow fix
The previous red dashed loop was unclear because it crossed the bottom message. In the revised version, draw the feedback as one external dashed orange elbow arrow:

LLM re-observation command -> down -> left along the outside bottom corridor -> up into Stage 2 "new view input".

Label it: **Active re-observation feedback to Stage 2**.
Do not connect the dashed arrow to the key-message box.

## Figure 2
Keep it detector-only. Do not include LLM, 3D reconstruction, or benchmark details. The main visual should be:
Input UAV image -> Wavelet Stem -> YOLO Backbone -> Partial Deformable Neck -> Detection Head -> boxes/classes/confidence/evidence token.
Patch/Tiling Inference should be a dashed optional branch below the input and should rejoin before the detector.

## Figure 3
This figure should only explain the benchmark/dataset. Left: Isaac Sim/Cesium coastal city with multi-UAV camera frustums. Middle: controllable factors. Right: exported dataset components and labels.

## Figure 4
Combine downstream components into one loop:
Weather-degraded images -> Weather restoration -> 3D reconstruction model bank -> Object-aware 3D evidence completion -> Ambiguity scorer -> Selective LLM reasoner -> final decision OR re-observation command.
The re-observation loop should be a clear dashed orange arrow from the command back to the input/new UAV view.
