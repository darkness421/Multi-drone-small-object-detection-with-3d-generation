# MarineCity Closed-loop Re-observation Evidence Update

This package is a review-response artifact. It does not edit the paper tree.

## Protocol

- Before state: 78-token viewer160 real-Cesium evidence graph.
- Routed set: hypotheses whose graph action is `targeted_reobserve`.
- Re-observation evidence: fresh commanded Isaac/Cesium targeted camera-pose recapture, matched to the missing UAV direction, scenario, and class.
- Graph update: insert the matched EvidenceToken into the hypothesis and recompute the closed-loop action.
- Scope: Fresh camera poses are generated from the graph target plan and recaptured in Isaac/Cesium; this supports closed-loop camera-pose/evidence-update validation, not autonomous physical drone flight.

## Summary

- Routed hypotheses: `9`
- Matched re-observation tokens: `6`
- Resolved from re-observe to monitor/finalize/reject: `6`
- Mean A(o) before: `0.923`
- Mean raw A(o) after token insertion: `0.901`
- Mean closed-loop A(o) after missing-evidence completion: `0.775`
- Before action counts: `{'targeted_reobserve': 9}`
- After action counts: `{'monitor': 6, 'targeted_reobserve': 3}`

## Generated Figures

- `figures/closed_loop_ambiguity_before_after.png`
- `figures/closed_loop_summary_card.png`
- `figures/closed_loop_action_distribution.png`
- `figures/closed_loop_outcomes_by_scenario.png`
- `closed_loop_contact_sheet.png`

## Paper-strengthening Text Candidates

1. Add a short subsection titled `Closed-loop re-observation evidence update` after the MarineCity routing result.
2. State that the original graph routes 9 ambiguous hypotheses to targeted re-observation, and the fresh commanded Isaac/Cesium targeted camera-pose recapture provides matching evidence for 6 of them.
3. Report the before/after trend: the matched subset moves from targeted re-observation to monitor under the closed-loop score, reducing mean ambiguity over routed cases.
4. Be careful with claim scope: Fresh camera poses are generated from the graph target plan and recaptured in Isaac/Cesium; this supports closed-loop camera-pose/evidence-update validation, not autonomous physical drone flight.
5. Use unresolved cases as honest failure cases: missing-view recapture did not always produce a same-class token, so the policy keeps those hypotheses under re-observation.

## Per-hypothesis Table

| Hyp. | Scenario | Class | Before views | Missing UAV | Before A | Reobs token | After views | After A(loop) | After action | Outcome |
|---|---|---|---:|---|---:|---|---:|---:|---|---|
| S0_H000 | S0 | bus | 2 | uav_03 | 0.884 | reobs_s0_s0_h000_uav_03_rgb:0:5 | 3 | 0.719 | monitor | resolved_to_monitor |
| S0_H001 | S0 | car | 2 | uav_03 | 0.911 | - | 2 | 0.911 | targeted_reobserve | unresolved_no_matching_reobservation_token |
| S0_H002 | S0 | car | 1 | uav_01,uav_03 | 1.000 | reobs_s0_s0_h002_uav_01_rgb:0:4 | 2 | 0.703 | monitor | resolved_to_monitor |
| S1_H006 | S1 | bus | 2 | uav_03 | 0.813 | reobs_s1_s1_h006_uav_03_rgb:0:2 | 3 | 0.657 | monitor | resolved_to_monitor |
| S1_H007 | S1 | car | 1 | uav_01,uav_03 | 1.000 | reobs_s1_s1_h007_uav_01_rgb:0:5 | 2 | 0.703 | monitor | resolved_to_monitor |
| S1_H008 | S1 | car | 2 | uav_03 | 0.908 | - | 2 | 0.908 | targeted_reobserve | unresolved_no_matching_reobservation_token |
| S2_H012 | S2 | car | 2 | uav_03 | 0.911 | reobs_s2_s2_h012_uav_03_rgb:0:6 | 3 | 0.738 | monitor | resolved_to_monitor |
| S2_H013 | S2 | car | 2 | uav_01 | 0.904 | reobs_s2_s2_h013_uav_01_rgb:0:1 | 3 | 0.659 | monitor | resolved_to_monitor |
| S2_H015 | S2 | pedestrian | 2 | uav_02 | 0.979 | - | 2 | 0.979 | targeted_reobserve | unresolved_no_matching_reobservation_token |
