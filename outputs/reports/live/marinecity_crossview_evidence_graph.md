# MarineCity Cross-View Evidence Graph Smoke

- Status: `marinecity_crossview_evidence_graph_smoke_ready`
- Claim level: `real_cesium_crossview_association_smoke_not_final_3d_reconstruction`
- Source tokens: `/home/oem/projects/multi-uav-marine-city/outputs/evidence/marinecity_real_capture_detector_smoke/evidence_tokens.jsonl`
- Tokens / hypotheses: `23` / `13`
- Multi-view hypotheses: `5`
- Support/conflict/missing edges: `23` / `4` / `20`
- Figure: `/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_crossview_evidence_graph.png`
- Paper table: `/home/oem/projects/multi-uav-marine-city/paper/tables/marinecity_crossview_evidence_graph_table.tex`

Claiming rule: this is real-Cesium detector-token evidence graph smoke evidence. It is not a completed metric 3D reconstruction, NeRF/3DGS result, or non-mock LLM validation.

| Scenario | Hypothesis | Class | Tokens | Views | Mean conf. | Ambiguity | Action |
|---|---|---|---:|---:|---:|---:|---|
| S0 | S0_H000 | bus | 1 | 1 | 0.811 | 0.781 | targeted_reobserve |
| S0 | S0_H001 | bus | 1 | 1 | 0.689 | 0.851 | targeted_reobserve |
| S0 | S0_H002 | car | 1 | 1 | 0.836 | 0.691 | targeted_reobserve |
| S0 | S0_H003 | car | 2 | 1 | 0.781 | 0.756 | targeted_reobserve |
| S0 | S0_H004 | car | 2 | 2 | 0.445 | 0.864 | targeted_reobserve |
| S1 | S1_H005 | bus | 1 | 1 | 0.739 | 0.801 | targeted_reobserve |
| S1 | S1_H006 | bus | 2 | 2 | 0.431 | 0.931 | targeted_reobserve |
| S1 | S1_H007 | car | 2 | 2 | 0.624 | 0.699 | targeted_reobserve |
| S1 | S1_H008 | car | 2 | 1 | 0.786 | 0.750 | targeted_reobserve |
| S1 | S1_H009 | car | 1 | 1 | 0.383 | 1.000 | targeted_reobserve |
| S2 | S2_H010 | bus | 3 | 3 | 0.556 | 0.813 | targeted_reobserve |
| S2 | S2_H011 | car | 2 | 2 | 0.642 | 0.687 | targeted_reobserve |
| S2 | S2_H012 | car | 3 | 1 | 0.649 | 0.867 | targeted_reobserve |
