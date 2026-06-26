# ACCV Remaining Gates Queue

Updated: `2026-06-26T19:59:43+09:00`

This queue separates paper-ready evidence from pending gates. Do not promote a pending row into a main claim until its evidence column proves completion.

| Priority | Gate | Status | Evidence | Next Action | Paper Use |
| --- | --- | --- | --- | --- | --- |
| P0 | Detector main claim | `ready` | Ours AP/AP50/F1 0.3822/0.6052/0.6273; params 20.82M; seeds 42,123,2026 | Keep as main VisDrone 1280 3-seed claim; do not mix broad search rows into the main table. | main |
| P1 | TinyPerson corrected supplementary check | `comparison_complete` | Ours seed 42 img1280: complete e41 best AP 0.1827/AP50 0.4761; YOLOv9m seed 42 img1280: complete e60 best AP 0.2035/AP50 0.5408 | Corrected 1280 run is complete and Ours is below YOLOv9m; keep this as a supplementary limitation/domain-transfer diagnostic unless we explicitly launch a new TinyPerson-specific adaptation study. | supp_pending |
| P1 | MarineCity neural 3D completion metrics | `marinecity_3d_input_dataset_ready_metrics_pending` | captures ready=True; dataset ready=True; runner available=False; metric rows=0 | Attach/install an upstream NeRF/3DGS/Instant-NGP runner and collect PSNR/SSIM/LPIPS/FPS/runtime rows; placeholders are not paper-valid. | pending_3d |
| P1 | AeroGraph external non-mock reasoner | `aerograph_reviewed_candidate_ready_external_pending` | manual direct coverage=0/49; external replication=False | Collect either compact 23-prompt smoke responses first or full 49-prompt final responses, then import and rebuild the reasoner table. | pending_reasoner |
| P2 | MarineCity real-Cesium system smoke | `marinecity_system_integration_smoke_ready_with_pending_final_gates` | tokens=23; actors=['bus', 'car', 'pedestrian', 'person', 'truck', 'van']; pending=2 | Use as system/protocol validation only; upgrade after neural 3D and external reasoner gates pass. | main_smoke_or_supp |
| P2 | Overleaf/local compile sync | `pending_main_tex_or_overleaf_sync` | local main.tex present=False; latex check=latex_patch_integrity_ok | Keep GitHub/Overleaf patch bundles synced; full compile verification requires the Overleaf project or a local main.tex checkout. | paper_ops |

## Immediate Order

1. TinyPerson corrected 1280 is complete: treat it as supplementary domain-transfer/limitation evidence, not as a main detector win.
2. Keep VisDrone detector results as the main 2D claim: `Ours` in tables, SAFR-YOLO/P2P4-SelfAttnFR in method text.
3. For 3D, use the verified MarineCity RGB/depth/pose package as input and collect real neural metrics before any reconstruction claim.
4. For AeroGraph, run the 23-prompt compact non-mock smoke first if time is tight, then the full 49-prompt final gate for the paper table.
