# Paper Section Patches

This folder stores LaTeX-ready section patches before the Overleaf source is
available in this workspace.

Current files:

| File | Use |
| --- | --- |
| `main_results_patch_bundle.tex` | Overleaf-ready main-paper result/protocol bundle. Include with `\input{sections/main_results_patch_bundle}`. |
| `supplementary_patch_bundle.tex` | Overleaf-ready supplementary bundle. Include with `\input{sections/supplementary_patch_bundle}`. |
| `05_experiments_current_detector_status.tex` | Main-paper detector result patch. Keeps only normalized 1280-pixel detector evidence and removes active queue/search-only rows. |
| `06_marinecity_3d_readiness.tex` | Main-paper MarineCity protocol patch. Keeps compact system-smoke and neural-3D smoke metric tables while avoiding final 3D benchmark/reasoner overclaims. |
| `07_marinecity_qualitative_figure_slots.tex` | Optional main/supplementary real-Cesium qualitative figure slots with safe smoke/protocol wording. |
| `supp_detector_experiment_inventory.tex` | Supplementary detector inventory for full YOLO scale sweeps, protocol-mismatched related-work checks, and search-only module rows. |
| `supp_marinecity_system_details.tex` | Supplementary MarineCity capture-source, cross-view graph, AeroGraph validation slot, and reporting-split details. |

Important wording rule:

- Treat `SAFR-YOLO` as the selected detector candidate. Use
  `P2P4-SelfAttnFR` only as the current implementation/run label unless a later
  repeated-seed run replaces it.
- Keep Proposed Method wording flexible enough to update the candidate name if
  the final compact detector changes.
- Treat MarineCity real-Cesium outputs as system/protocol smoke evidence. Do
  not claim a completed 3D reconstruction/restoration benchmark until the
  external-provider reasoner and completion/restoration experiments are validated.
- Use `AeroGraph Reasoner` for the drone-specialized graph-grounded LLM/VLM
  module. Avoid previous non-drone-specific reasoner labels in paper sections.
- Do not mix 640-pixel related-work evaluations with the main 1280-pixel
  detector comparison table.
- Keep the main-paper conclusion within the 14-page limit. If a table falls
  beyond the conclusion in Overleaf, move it to the supplementary bundle unless
  it is the compact detector, ablation, MarineCity system, or neural-3D smoke
  metric table.
- Run `python scripts/check_latex_patch_integrity.py` before syncing to
  Overleaf; the live result is
  `outputs/reports/live/latex_patch_integrity_check.md`.
