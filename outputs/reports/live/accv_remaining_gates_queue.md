# ACCV Remaining Gates Queue

Updated: `2026-06-27T16:35:12+09:00`

This queue separates paper-ready evidence from pending gates. Do not promote a pending row into a main claim until its evidence column proves completion.

| Priority | Gate | Status | Evidence | Next Action | Paper Use |
| --- | --- | --- | --- | --- | --- |
| P0 | Detector main claim | `ready` | Ours AP/AP50/F1 0.3822/0.6052/0.6273; params 20.82M; seeds 42,123,2026 | Keep as main VisDrone 1280 3-seed claim; do not mix broad search rows into the main table. | main |
| P3 | TinyPerson archive-only diagnostic | `closed_archive_only` | Ours seed 42 img1280: complete e41 best AP 0.1827/AP50 0.4761; Ours seed 123 img1280: complete e21 best AP 0.1523/AP50 0.4097; Ours seed 2026 img1280: archived_stopped e5 best AP 0.0890/AP50 0.2569; YOLOv9m seed 42 img1280: complete e60 best AP 0.2035/AP50 0.5408; YOLOv9m seed 123 img1280: complete e36 best AP 0.1960/AP50 0.5174; YOLOv9m seed 2026 img1280: complete e21 best AP 0.1617/AP50 0.4454 | Stop TinyPerson here. Keep existing rows as internal archive/protocol diagnostics only; do not include TinyPerson in the default main or supplementary paper. | internal_archive |
| P1 | MarineCity neural 3D completion metrics | `marinecity_3d_single_runner_smoke_ready` | captures ready=True; dataset ready=True; runner available=False; metric rows=1 | Use the verified single-runner Nerfacto row as system-smoke evidence; add Instant-NGP/3DGS or longer validation only if time remains. | main_smoke_or_supp |
| P1 | AeroGraph external non-mock reasoner | `aerograph_reviewed_candidate_ready_external_pending` | manual direct coverage=0/49; reviewed candidate=49/49; external replication=False | Keep Codex-assisted reviewed candidate visible; collect OpenAI/ChatGPT/local-provider replication before making a final external-provider reasoner claim. | pending_reasoner |
| P2 | MarineCity real-Cesium system smoke | `marinecity_system_integration_smoke_ready_with_pending_final_gates` | tokens=128; actors=['bus', 'car', 'pedestrian', 'person', 'truck', 'van']; pending=2 | Use as system/protocol validation only; upgrade after neural 3D and external reasoner gates pass. | main_smoke_or_supp |
| P2 | Overleaf/local compile sync | `pending_main_tex_or_overleaf_sync` | local main.tex present=False; latex check=latex_patch_integrity_ok | Keep GitHub/Overleaf patch bundles synced; full compile verification requires the Overleaf project or a local main.tex checkout. | paper_ops |

## Immediate Order

1. Close TinyPerson as an internal archive-only diagnostic; do not spend more GPU time or default paper space on it.
2. Keep VisDrone detector results as the main 2D claim: `Ours` in tables, SAFR-YOLO/P2P4-SelfAttnFR in method text.
3. For 3D, use the verified MarineCity RGB/depth/pose package and the available single-runner Nerfacto metric row as system-smoke evidence; collect more runner families only before claiming a full 3D benchmark.
4. For AeroGraph, keep the reviewed candidate visible and collect external OpenAI/ChatGPT/local-provider replication before final reasoner claims.
