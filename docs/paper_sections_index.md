# Paper Section Patches

Updated: `2026-07-02 KST`

This folder stores LaTeX-ready section patches for the Overleaf submission package.

Current files:

| File | Use |
| --- | --- |
| `main_results_patch_bundle.tex` | Overleaf-ready main-paper result/protocol bundle. Include with `\input{sections/main_results_patch_bundle}`. |
| `full_main_draft_bundle.tex` | Overleaf-ready full main-paper draft skeleton. Include with `\input{sections/full_main_draft_bundle}` when replacing the current draft body. |
| `supplementary_patch_bundle.tex` | Overleaf-ready supplementary bundle. Include with `\input{sections/supplementary_patch_bundle}`. |
| `01_introduction_draft.tex` | Draft introduction with conservative contribution wording. |
| `02_related_work_draft.tex` | Draft related-work section using the current UAV detector reference labels. |
| `03_method_draft.tex` | Draft method section for CoM3D-ACE, SAFR-YOLO, EvidenceTokens, 3D graph, and AeroGraph. |
| `04_experiment_protocol_draft.tex` | Draft dataset, metric, and implementation-detail section. |
| `05_experiments_current_detector_status.tex` | Main-paper detector result patch. Keeps only normalized 1280-pixel detector evidence and removes active queue/search-only rows. |
| `06_marinecity_3d_readiness.tex` | Main-paper MarineCity protocol patch. Keeps compact system-validation and neural-3D validation metric tables while avoiding final 3D benchmark/reasoner overclaims. |
| `07_marinecity_qualitative_figure_slots.tex` | Supplementary real-Cesium qualitative figure slots with conservative validation/protocol wording. |
| `08_conclusion_draft.tex` | Draft conclusion with conservative 3D/reasoner limitations. |
| `supp_detector_experiment_inventory.tex` | Supplementary detector inventory for full YOLO scale sweeps, protocol-mismatched related-work checks, and search-only module rows. |
| `supp_marinecity_system_details.tex` | Supplementary MarineCity capture-source, cross-view graph, AeroGraph validation slot, and reporting-split details. |

Important wording rules:

- Treat `SAFR-YOLO` as the selected detector candidate. Use
  `P2P4-SelfAttnFR` only as the implementation/run label for reproducibility
  and ablation metadata.
- Keep Proposed Method wording aligned with the selected SAFR-YOLO detector and
  the completed VisDrone 1280 three-seed protocol.
- Treat MarineCity real-Cesium outputs as system/protocol validation evidence. Do
  not claim a completed 3D reconstruction/restoration benchmark until the
  reasoner response evaluation and completion/restoration experiments are validated.
- Use `AeroGraph Reasoner` for the drone-specialized graph-grounded LLM/VLM
  module. Avoid previous non-drone-specific reasoner labels in paper sections.
- Do not mix 640-pixel related-work evaluations with the main 1280-pixel
  detector comparison table.
- Keep the main-paper conclusion within the 14-page limit. If a table falls
  beyond the conclusion in Overleaf, move it to the supplementary bundle unless
  it is the compact detector, ablation, MarineCity system, or neural-3D validation
  metric table.
- Run `python scripts/check_latex_patch_integrity.py` before syncing to
  Overleaf; the live result is
  `outputs/reports/live/latex_patch_integrity_check.md`.
