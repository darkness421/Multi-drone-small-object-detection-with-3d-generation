# Idea Bank

Use this file for ideas that are not ready to become implementation tasks yet.

## Detection

- Lightweight YOLO baseline for per-UAV object proposals.
- Add patch-level features for small object preservation.
- Add wavelet stem or multi-frequency branch to improve tiny target representation.

## Multi-UAV Fusion

- Match detections across UAV views using timestamp, camera pose, object class, and projected 3D consistency.
- Fuse object evidence across UAVs before final confidence scoring.
- Use confidence disagreement as a trigger for re-observation.

## Isaac Sim Demo

- Marine City scene with three UAV camera viewpoints.
- Show detection boxes in each UAV camera stream.
- Show a top-down 3D marker for fused object position.
- Display re-observation request when object evidence is uncertain.

## Reasoning

- Use a structured prompt to summarize evidence from multiple UAVs.
- Separate geometric verification from language-model explanation.
- Keep final decision traceable: class, confidence, 3D position, supporting UAVs, and next action.

