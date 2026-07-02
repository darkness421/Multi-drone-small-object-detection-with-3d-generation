# Current Work Status

Updated: `2026-07-02T16:39:50+09:00`

This file mirrors the active work shown in `training_dashboard.png`. Active work now focuses on the VisDrone detector claim, MarineCity simulation, neural-3D validation metrics, AeroGraph reasoner replication, and paper cleanup.

| Work Item | Status | Detail | Latest Event |
| --- | --- | --- | --- |
| ACCV paper gate queue | `monitoring` | refreshes manuscript gates, 3D/AeroGraph readiness, and dashboards | run_20260702_163850.log; finished_at=2026-07-02T16:38:55+09:00 |
| Neural-3D 80k | `done` | Nerfacto full-res 80k reinforcement completed; compare before promotion | metric row: outputs/experiments/3d_generation/nerfstudio_native_runs/marinecity_nerfacto_fullres80k_20260629_afternoon_20260629_1608_fullres80k_metric_row.json |
| Isaac/Cesium map | `done` | Real MarineCity Cesium ROI captured for S0/S1/S2 with viewer160 profile | real Cesium captures 3/3; next paper-quality recapture should reduce tile/backface artifacts |
| Multi-UAV YOLO test | `done` | P2P4-SelfAttnFR inference + 3D evidence/reasoner validation ran on S0/S1/S2 viewer160 captures | 78 EvidenceTokens; bus:17, car:53, pedestrian:6, van:2; rule-based reasoner 3/3 |
