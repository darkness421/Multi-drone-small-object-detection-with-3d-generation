# MarineCity Real-Cesium Detector-to-Reasoner Smoke

- Detector summaries: latest per-scenario `uavmarine_*_viewer160_session_recapture_detector_smoke_conf001` outputs
- Total frames: `9`
- Total evidence tokens: `78`
- Detector contact sheet: `paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png`
- Paper table: `paper/tables/marinecity_system_scenario_table.tex`

| Scenario | UAV views | Tokens | Hypotheses | Re-observe | Classes | Provider |
|---|---:|---:|---:|---:|---|---|
| S0 locked MarineCity ROI | 3 | 26 | 19 | 19 | car=18, bus=6, pedestrian=1, van=1 | rule_based_aerograph |
| S1 adjacent overlap | 3 | 22 | 14 | 14 | car=15, bus=5, pedestrian=2 | rule_based_aerograph |
| S2 coastline multi-view | 3 | 30 | 21 | 21 | car=20, bus=6, pedestrian=3, van=1 | rule_based_aerograph |

Claiming rule: this is a real-Cesium system smoke test, not a labeled MarineCity accuracy benchmark and not a completed 3D reconstruction result.
