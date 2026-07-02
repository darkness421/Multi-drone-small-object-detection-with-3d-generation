# ACCV Remaining Gates Queue

Updated: `2026-07-02T16:37:03+09:00`

This queue separates paper-ready evidence from optional gates. Optional rows should not be promoted into a main claim unless their evidence column proves completion.

| Priority | Gate | Status | Evidence | Next Action | Paper Use |
| --- | --- | --- | --- | --- | --- |
| P0 | Detector main claim | `ready` | Ours AP/AP50/F1 0.3822/0.6052/0.6273; params 20.82M; seeds 42,123,2026 | Keep as main VisDrone 1280 3-seed claim; do not mix broad search rows into the main table. | main |
| P1 | MarineCity neural 3D completion metrics | `marinecity_3d_completion_ready` | captures ready=True; dataset ready=True; runner available=True; metric rows=3 | Use the verified Nerfacto and Splatfacto/3DGS-style rows as runner-family system-validation evidence; add longer validation only if time remains. | main_or_supp_validation |
| P3 | Optional AeroGraph external-provider benchmark | `aerograph_external_provider_responses_needed` | manual direct coverage=0/54; reviewed candidate=49/49; provider validation=False | Do not block the current submission. Collect external-provider or local-model responses only if adding a separate LLM benchmark claim. | optional_supp_or_future |
| P2 | MarineCity real-Cesium system validation | `marinecity_system_integration_validation_ready_with_open_final_gates` | tokens=78; actors=['bus', 'car', 'pedestrian', 'person', 'truck', 'van']; open checks=1 | Use as real-Cesium system/protocol validation with graph/action-policy metrics; external provider benchmarking is optional. | main_or_supp_validation |
| P2 | Manuscript/local compile package | `open_main_tex_or_manuscript_package` | local main.tex present=False; latex check=latex_patch_integrity_ok | Keep GitHub paper artifacts and LaTeX patch bundles aligned; full compile verification requires a local main.tex checkout. | paper_ops |

## Immediate Order

1. Keep VisDrone detector results as the main 2D claim: `Ours` in tables, SAFR-YOLO/P2P4-SelfAttnFR in method text.
2. For 3D, use the verified MarineCity RGB/depth/pose package plus Nerfacto and Splatfacto/3DGS-style rows as system-validation evidence; collect longer validation only before claiming a full 3D benchmark.
3. For AeroGraph, keep the current paper claim limited to schema, verifier, and action-policy validation. External-provider or local-model replication is optional supplementary/future evidence.
