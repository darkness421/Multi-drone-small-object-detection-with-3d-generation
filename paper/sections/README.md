# Paper Section Patches

This folder stores LaTeX-ready section patches before the Overleaf source is
available in this workspace.

Current files:

| File | Use |
| --- | --- |
| `05_experiments_current_detector_status.tex` | Main-paper detector result patch. Keeps only normalized 1280-pixel detector evidence and removes active queue/search-only rows. |
| `06_marinecity_3d_readiness.tex` | Main-paper 3D benchmark protocol patch. Avoids treating dry-run placeholder counts as final dataset evidence. |
| `supp_detector_experiment_inventory.tex` | Supplementary detector inventory for full YOLO scale sweeps, protocol-mismatched related-work checks, and search-only module rows. |

Important wording rule:

- Treat `SAFR-YOLO` as the selected detector candidate. Use
  `P2P4-SelfAttnFR` only as the current implementation/run label unless a later
  repeated-seed run replaces it.
- Keep Proposed Method wording flexible enough to update the candidate name if
  the final compact detector changes.
- Treat MarineCity dry-run numbers as protocol validation only until the real
  Isaac/Cesium RGB/depth/annotation export is generated.
- Do not mix 640-pixel related-work evaluations with the main 1280-pixel
  detector comparison table.
