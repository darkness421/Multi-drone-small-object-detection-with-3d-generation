# Overleaf Sync Notes

Updated: `2026-06-28 KST`

This folder contains the current ACCV-ready LaTeX patch bundle and paper-facing
figure/table assets. Sync this repository branch into Overleaf, then include
the two bundles from the Overleaf project root:

```latex
% Main paper
\input{sections/main_results_patch_bundle}

% Supplementary material
\input{sections/supplementary_patch_bundle}
```

## Main Paper Priority

Keep the main paper self-contained and within the 14-page ACCV limit:

- detector comparison table: `tables/main_detector_comparison_table`
- detector ablation table: `tables/final_ablation_main_table`
- MarineCity system smoke table: `tables/marinecity_system_scenario_table`
- MarineCity neural-3D smoke metric table: `tables/marinecity_3d_completion_results_table`
- at most one compact detector trade-off figure if page budget allows

Move full inventories, long protocol tables, heat maps, and extra qualitative
figures to the supplementary bundle.

## Fig. 1 / Fig. 3 Revision Assets

Use these folders when revising the final system figures:

- `outputs/reports/live/fig1_fig3_handoff/`
- `paper/figures/results/marinecity_system/`

Recommended current assets:

- Fig. 1 MarineCity multi-UAV source:
  `outputs/reports/live/fig1_fig3_handoff/fig1_map_multiuav_preview.png`
- Fig. 1 UAV view crops:
  `outputs/reports/live/fig1_fig3_handoff/fig1_uav01_rgb.png`,
  `fig1_uav02_rgb.png`, `fig1_uav03_rgb.png`
- Fig. 3 detector preview:
  `paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png`
- Fig. 3 evidence graph:
  `paper/figures/results/marinecity_system/marinecity_crossview_evidence_graph.png`
- Fig. 3 neural-3D smoke evidence:
  `paper/figures/results/marinecity_system/marinecity_nerfacto_eval_contact_sheet.png`,
  `marinecity_instant_ngp_eval_contact_sheet.png`,
  `marinecity_splatfacto_eval_contact_sheet.png`

The current MarineCity results should be described as real-Cesium system/protocol
smoke evidence and runner-family neural-3D smoke evidence, not as a completed
large-scale 3D reconstruction benchmark.

## Validation

Before syncing into Overleaf, run:

```bash
python scripts/check_latex_patch_integrity.py
python scripts/check_paper_artifact_readiness.py
```

The live validation outputs are:

- `outputs/reports/live/latex_patch_integrity_check.md`
- `outputs/reports/live/paper_artifact_readiness_check.md`
