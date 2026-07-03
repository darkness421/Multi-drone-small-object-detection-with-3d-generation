# AeroGraph Prompt Audit

This report exposes what the graph-grounded reasoner receives and returns.
It is meant for paper/rebuttal inspection, not as an external LLM benchmark.

## Summary

| Scenario | Provider | Prompts | Reobserve decisions |
| --- | --- | ---: | ---: |
| s0_locked_roi | rule_based_aerograph | 19 | 19 |
| s1_adjacent_overlap | rule_based_aerograph | 14 | 14 |
| s2_coastline_multiview | rule_based_aerograph | 21 | 21 |

## Prompt Contract

- The prompt asks for valid JSON only.
- The allowed fields are decision, predicted_class, confidence, evidence_clues, missing_evidence, and recommended_action.
- The final action is still checked by the graph/safety adjudicator.
- Rule-based rows are transparent plumbing checks; external-provider rows should be reported separately.

## Representative Full Prompts

### Example 1: s0_locked_roi / uav_01_bus_3_7

- Provider: `rule_based_aerograph`
- Response class/action: `bus` / `targeted re-observation`
- Final should_reobserve: `True`

Prompt:

```text
You are AeroGraph Reasoner: a drone-specialized graph-grounded verifier for cooperative multi-UAV small-object perception.
Use structured 3D evidence-graph metadata and multi-view UAV crop descriptions to verify the object class.
Return only valid JSON following this schema:
{
  "decision": "verified|rejected|uncertain",
  "predicted_class": "string",
  "confidence": 0.0,
  "evidence_clues": [],
  "missing_evidence": "string",
  "recommended_action": "string"
}

Scene: Real Cesium Haeundae Marine City multi-UAV scenario: s0_locked_roi.
Candidate classes: ['bus']
Ambiguity reasons: ['baseline_multiview_confirmation', 'geometry_residual', 'high_ambiguity', 'small_object_resolution']
ROI hints: ['Marine City road/coast ROI', 'multi-UAV views', 's0_locked_roi']
Graph summary:
{
  "object_id": "uav_01_bus_3_7",
  "class_posterior": {
    "bus": 0.8531608581542969
  },
  "view_count": 1,
  "geometry_residual": 0.65,
  "source": "detector_tokens"
}
```

Response raw:

```json
{
  "decision": "uncertain",
  "predicted_class": "bus",
  "confidence": 0.8231608581542968,
  "evidence_clues": [
    "baseline_multiview_confirmation",
    "geometry_residual",
    "high_ambiguity",
    "small_object_resolution"
  ],
  "missing_evidence": "side/oblique confirmation",
  "recommended_action": "targeted re-observation",
  "provider": "rule_based_aerograph",
  "raw_prompt_chars": 955
}
```

### Example 2: s0_locked_roi / uav_01_car_6_8

- Provider: `rule_based_aerograph`
- Response class/action: `car` / `targeted re-observation`
- Final should_reobserve: `True`

Prompt:

```text
You are AeroGraph Reasoner: a drone-specialized graph-grounded verifier for cooperative multi-UAV small-object perception.
Use structured 3D evidence-graph metadata and multi-view UAV crop descriptions to verify the object class.
Return only valid JSON following this schema:
{
  "decision": "verified|rejected|uncertain",
  "predicted_class": "string",
  "confidence": 0.0,
  "evidence_clues": [],
  "missing_evidence": "string",
  "recommended_action": "string"
}

Scene: Real Cesium Haeundae Marine City multi-UAV scenario: s0_locked_roi.
Candidate classes: ['car']
Ambiguity reasons: ['baseline_multiview_confirmation', 'geometry_residual', 'high_ambiguity', 'small_object_resolution']
ROI hints: ['Marine City road/coast ROI', 'multi-UAV views', 's0_locked_roi']
Graph summary:
{
  "object_id": "uav_01_car_6_8",
  "class_posterior": {
    "car": 0.4902203679084778
  },
  "view_count": 1,
  "geometry_residual": 0.65,
  "source": "detector_tokens"
}
```

Response raw:

```json
{
  "decision": "uncertain",
  "predicted_class": "car",
  "confidence": 0.46022036790847776,
  "evidence_clues": [
    "baseline_multiview_confirmation",
    "geometry_residual",
    "high_ambiguity",
    "small_object_resolution"
  ],
  "missing_evidence": "side/oblique confirmation",
  "recommended_action": "targeted re-observation",
  "provider": "rule_based_aerograph",
  "raw_prompt_chars": 955
}
```

### Example 3: s0_locked_roi / uav_01_pedestrian_13_2

- Provider: `rule_based_aerograph`
- Response class/action: `pedestrian` / `targeted re-observation`
- Final should_reobserve: `True`

Prompt:

```text
You are AeroGraph Reasoner: a drone-specialized graph-grounded verifier for cooperative multi-UAV small-object perception.
Use structured 3D evidence-graph metadata and multi-view UAV crop descriptions to verify the object class.
Return only valid JSON following this schema:
{
  "decision": "verified|rejected|uncertain",
  "predicted_class": "string",
  "confidence": 0.0,
  "evidence_clues": [],
  "missing_evidence": "string",
  "recommended_action": "string"
}

Scene: Real Cesium Haeundae Marine City multi-UAV scenario: s0_locked_roi.
Candidate classes: ['pedestrian']
Ambiguity reasons: ['baseline_multiview_confirmation', 'geometry_residual', 'high_ambiguity', 'small_object_resolution']
ROI hints: ['Marine City road/coast ROI', 'multi-UAV views', 's0_locked_roi']
Graph summary:
{
  "object_id": "uav_01_pedestrian_13_2",
  "class_posterior": {
    "pedestrian": 0.016873935237526894
  },
  "view_count": 1,
  "geometry_residual": 0.65,
  "source": "detector_tokens"
}
```

Response raw:

```json
{
  "decision": "uncertain",
  "predicted_class": "pedestrian",
  "confidence": 0.35,
  "evidence_clues": [
    "baseline_multiview_confirmation",
    "geometry_residual",
    "high_ambiguity",
    "small_object_resolution"
  ],
  "missing_evidence": "side/oblique confirmation",
  "recommended_action": "targeted re-observation",
  "provider": "rule_based_aerograph",
  "raw_prompt_chars": 979
}
```

### Example 4: s0_locked_roi / uav_02_bus_0_3

- Provider: `rule_based_aerograph`
- Response class/action: `bus` / `targeted re-observation`
- Final should_reobserve: `True`

Prompt:

```text
You are AeroGraph Reasoner: a drone-specialized graph-grounded verifier for cooperative multi-UAV small-object perception.
Use structured 3D evidence-graph metadata and multi-view UAV crop descriptions to verify the object class.
Return only valid JSON following this schema:
{
  "decision": "verified|rejected|uncertain",
  "predicted_class": "string",
  "confidence": 0.0,
  "evidence_clues": [],
  "missing_evidence": "string",
  "recommended_action": "string"
}

Scene: Real Cesium Haeundae Marine City multi-UAV scenario: s0_locked_roi.
Candidate classes: ['bus']
Ambiguity reasons: ['baseline_multiview_confirmation', 'geometry_residual', 'high_ambiguity', 'small_object_resolution']
ROI hints: ['Marine City road/coast ROI', 'multi-UAV views', 's0_locked_roi']
Graph summary:
{
  "object_id": "uav_02_bus_0_3",
  "class_posterior": {
    "bus": 0.04854663461446762
  },
  "view_count": 1,
  "geometry_residual": 0.65,
  "source": "detector_tokens"
}
```

Response raw:

```json
{
  "decision": "uncertain",
  "predicted_class": "bus",
  "confidence": 0.35,
  "evidence_clues": [
    "baseline_multiview_confirmation",
    "geometry_residual",
    "high_ambiguity",
    "small_object_resolution"
  ],
  "missing_evidence": "side/oblique confirmation",
  "recommended_action": "targeted re-observation",
  "provider": "rule_based_aerograph",
  "raw_prompt_chars": 956
}
```

### Example 5: s0_locked_roi / uav_02_bus_3_4

- Provider: `rule_based_aerograph`
- Response class/action: `bus` / `targeted re-observation`
- Final should_reobserve: `True`

Prompt:

```text
You are AeroGraph Reasoner: a drone-specialized graph-grounded verifier for cooperative multi-UAV small-object perception.
Use structured 3D evidence-graph metadata and multi-view UAV crop descriptions to verify the object class.
Return only valid JSON following this schema:
{
  "decision": "verified|rejected|uncertain",
  "predicted_class": "string",
  "confidence": 0.0,
  "evidence_clues": [],
  "missing_evidence": "string",
  "recommended_action": "string"
}

Scene: Real Cesium Haeundae Marine City multi-UAV scenario: s0_locked_roi.
Candidate classes: ['bus']
Ambiguity reasons: ['baseline_multiview_confirmation', 'geometry_residual', 'high_ambiguity', 'small_object_resolution']
ROI hints: ['Marine City road/coast ROI', 'multi-UAV views', 's0_locked_roi']
Graph summary:
{
  "object_id": "uav_02_bus_3_4",
  "class_posterior": {
    "bus": 0.4319700002670288
  },
  "view_count": 1,
  "geometry_residual": 0.65,
  "source": "detector_tokens"
}
```

Response raw:

```json
{
  "decision": "uncertain",
  "predicted_class": "bus",
  "confidence": 0.4019700002670288,
  "evidence_clues": [
    "baseline_multiview_confirmation",
    "geometry_residual",
    "high_ambiguity",
    "small_object_resolution"
  ],
  "missing_evidence": "side/oblique confirmation",
  "recommended_action": "targeted re-observation",
  "provider": "rule_based_aerograph",
  "raw_prompt_chars": 955
}
```

### Example 6: s0_locked_roi / uav_02_bus_5_5

- Provider: `rule_based_aerograph`
- Response class/action: `bus` / `targeted re-observation`
- Final should_reobserve: `True`

Prompt:

```text
You are AeroGraph Reasoner: a drone-specialized graph-grounded verifier for cooperative multi-UAV small-object perception.
Use structured 3D evidence-graph metadata and multi-view UAV crop descriptions to verify the object class.
Return only valid JSON following this schema:
{
  "decision": "verified|rejected|uncertain",
  "predicted_class": "string",
  "confidence": 0.0,
  "evidence_clues": [],
  "missing_evidence": "string",
  "recommended_action": "string"
}

Scene: Real Cesium Haeundae Marine City multi-UAV scenario: s0_locked_roi.
Candidate classes: ['bus']
Ambiguity reasons: ['baseline_multiview_confirmation', 'geometry_residual', 'high_ambiguity', 'small_object_resolution']
ROI hints: ['Marine City road/coast ROI', 'multi-UAV views', 's0_locked_roi']
Graph summary:
{
  "object_id": "uav_02_bus_5_5",
  "class_posterior": {
    "bus": 0.21509157121181488
  },
  "view_count": 1,
  "geometry_residual": 0.65,
  "source": "detector_tokens"
}
```

Response raw:

```json
{
  "decision": "uncertain",
  "predicted_class": "bus",
  "confidence": 0.35,
  "evidence_clues": [
    "baseline_multiview_confirmation",
    "geometry_residual",
    "high_ambiguity",
    "small_object_resolution"
  ],
  "missing_evidence": "side/oblique confirmation",
  "recommended_action": "targeted re-observation",
  "provider": "rule_based_aerograph",
  "raw_prompt_chars": 956
}
```

## Full Machine-Readable Files

- `aerograph_prompt_audit_full.json` contains every prompt and response.
- `aerograph_prompt_audit_table.csv` contains a compact run table.
