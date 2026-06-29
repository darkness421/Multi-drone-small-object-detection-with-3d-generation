# ACCV Remaining Gates Queue

Updated: `2026-06-30T03:34:56+09:00`

This queue separates paper-ready evidence from open gates. Do not promote an open-gate row into a main claim until its evidence column proves completion.

| Priority | Gate | Status | Evidence | Next Action | Paper Use |
| --- | --- | --- | --- | --- | --- |
| P0 | Detector main claim | `ready` | Ours AP/AP50/F1 0.3822/0.6052/0.6273; params 20.82M; seeds 42,123,2026 | Keep as main VisDrone 1280 3-seed claim; do not mix broad search rows into the main table. | main |
| P1 | MarineCity neural 3D completion metrics | `marinecity_3d_completion_ready` | captures ready=True; dataset ready=True; runner available=True; metric rows=3 | Use the verified Nerfacto and Splatfacto/3DGS-style rows as runner-family system-validation evidence; add longer validation only if time remains. | main_or_supp_validation |
| P1 | AeroGraph external-provider reasoner | `aerograph_external_provider_responses_needed` | manual direct coverage=0/54; reviewed candidate=49/49; provider validation=False | Keep the reviewed candidate internal; collect OpenAI/ChatGPT/local-provider responses before making a final provider-backed reasoner claim. | open_reasoner_gate |
| P2 | MarineCity real-Cesium system validation | `marinecity_system_integration_validation_ready_with_open_final_gates` | tokens=78; actors=['bus', 'car', 'pedestrian', 'person', 'truck', 'van']; open checks=1 | Use as system/protocol validation only; upgrade after neural 3D and external reasoner gates pass. | main_or_supp_validation |
| P2 | Overleaf/local compile sync | `open_main_tex_or_overleaf_sync` | local main.tex present=False; latex check=latex_patch_integrity_ok | Keep GitHub/Overleaf patch bundles synced; full compile verification requires the Overleaf project or a local main.tex checkout. | paper_ops |

## Immediate Order

1. Keep VisDrone detector results as the main 2D claim: `Ours` in tables, SAFR-YOLO/P2P4-SelfAttnFR in method text.
2. For 3D, use the verified MarineCity RGB/depth/pose package plus Nerfacto and Splatfacto/3DGS-style rows as system-validation evidence; collect longer validation only before claiming a full 3D benchmark.
3. For AeroGraph, keep the reviewed candidate internal and collect external OpenAI/ChatGPT/local-provider replication before final reasoner claims.
