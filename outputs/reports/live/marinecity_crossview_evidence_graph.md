# MarineCity Cross-View Evidence Graph Smoke

- Status: `marinecity_crossview_evidence_graph_smoke_ready`
- Claim level: `real_cesium_crossview_association_smoke_not_final_3d_reconstruction`
- Source tokens: `/home/oem/projects/multi-uav-marine-city/outputs/evidence/marinecity_viewer160_combined_detector_smoke/evidence_tokens.jsonl`
- Tokens / hypotheses: `78` / `17`
- Multi-view hypotheses: `8`
- Support/conflict/missing edges: `78` / `11` / `25`
- Figure: `/home/oem/projects/multi-uav-marine-city/outputs/reports/live/marinecity_crossview_evidence_graph.png`
- Paper table: `/home/oem/projects/multi-uav-marine-city/paper/tables/marinecity_crossview_evidence_graph_table.tex`

Claiming rule: this is real-Cesium detector-token evidence graph smoke evidence. It is not a completed metric 3D reconstruction, NeRF/3DGS result, or external-provider LLM validation.

| Scenario | Hypothesis | Class | Tokens | Views | Mean conf. | Ambiguity | Action |
|---|---|---|---:|---:|---:|---:|---|
| S0 | S0_H000 | bus | 6 | 2 | 0.263 | 0.884 | targeted_reobserve |
| S0 | S0_H001 | car | 8 | 2 | 0.193 | 0.911 | targeted_reobserve |
| S0 | S0_H002 | car | 9 | 1 | 0.232 | 1.000 | targeted_reobserve |
| S0 | S0_H003 | car | 1 | 1 | 0.019 | 1.000 | reject |
| S0 | S0_H004 | pedestrian | 1 | 1 | 0.017 | 1.000 | reject |
| S0 | S0_H005 | van | 1 | 1 | 0.029 | 1.000 | reject |
| S1 | S1_H006 | bus | 5 | 2 | 0.328 | 0.813 | targeted_reobserve |
| S1 | S1_H007 | car | 9 | 1 | 0.270 | 1.000 | targeted_reobserve |
| S1 | S1_H008 | car | 6 | 2 | 0.190 | 0.908 | targeted_reobserve |
| S1 | S1_H009 | pedestrian | 2 | 1 | 0.013 | 1.000 | reject |
| S2 | S2_H010 | bus | 4 | 3 | 0.578 | 0.693 | monitor |
| S2 | S2_H011 | bus | 2 | 1 | 0.022 | 1.000 | reject |
| S2 | S2_H012 | car | 9 | 2 | 0.183 | 0.911 | targeted_reobserve |
| S2 | S2_H013 | car | 11 | 2 | 0.206 | 0.904 | targeted_reobserve |
| S2 | S2_H014 | pedestrian | 1 | 1 | 0.015 | 1.000 | reject |
| S2 | S2_H015 | pedestrian | 2 | 2 | 0.010 | 0.979 | targeted_reobserve |
| S2 | S2_H016 | van | 1 | 1 | 0.011 | 1.000 | reject |
