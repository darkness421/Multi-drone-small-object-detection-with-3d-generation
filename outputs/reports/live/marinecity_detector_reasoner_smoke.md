# MarineCity Real-Cesium Detector-to-Reasoner Smoke

- Detector summary: `outputs/evidence/marinecity_real_capture_detector_smoke/detector_smoke_summary.json`
- Total frames: `9`
- Total evidence tokens: `23`
- Detector contact sheet: `paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png`
- Paper table: `paper/tables/marinecity_system_scenario_table.tex`

| Scenario | UAV views | Tokens | Hypotheses | Re-observe | Classes | Provider |
|---|---:|---:|---:|---:|---|---|
| S0 locked MarineCity ROI | 3 | 7 | 7 | 7 | car=5, bus=2 | mock_symbolic_aerograph |
| S1 adjacent overlap | 3 | 8 | 8 | 8 | car=5, bus=3 | mock_symbolic_aerograph |
| S2 coastline multi-view | 3 | 8 | 8 | 8 | car=5, bus=3 | mock_symbolic_aerograph |

Claiming rule: this is a real-Cesium system smoke test, not a labeled MarineCity accuracy benchmark and not a completed 3D reconstruction result.
