# Ambiguity Diagnosis Prompt

You are diagnosing ambiguity for one UAV-detected object in a cooperative Multi-UAV urban digital twin.

## Inputs

- `object_id`
- multi-view crop descriptions
- candidate class logits
- 3D location and size
- view angles
- occlusion level
- surrounding context
- uncertainty

## Task

Determine why the object is ambiguous, what evidence is missing, and which next UAV view should be requested.

## Allowed Ambiguity Types

- `low_resolution`
- `missing_side_view`
- `heavy_occlusion`
- `class_similar_shape`
- `shadow_confusion`
- `road_sea_context_confusion`

## Output

Return valid JSON only.

```json
{
  "object_id": "vehicle_021",
  "candidate_classes": ["van", "ambulance"],
  "ambiguity_type": "missing_side_view",
  "missing_evidence": ["side marking", "roof light bar"],
  "recommended_next_view": {
    "view_type": "right_oblique",
    "altitude": 80,
    "reason": "Side markings and roof light bar are not visible from the current views."
  },
  "need_reobservation": true,
  "explanation": "The nadir view captures only the roof outline, while the oblique view is partially occluded."
}
```

