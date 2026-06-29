# Supplementary Cleanup Audit, 2026-06-30

## Decisions

- Supplementary Fig. 10 is kept as the detector ablation heatmap, but its
  LaTeX include path now explicitly references
  `figures/results/paper_fig10_final_ablation_metric_heatmap.png`.
- The supplementary S2 MarineCity qualitative panel was removed because it is
  byte-identical to the main-paper MarineCity qualitative figure. The
  supplementary material now keeps only the non-duplicated S0/S1 scenario
  panels.
- Table 11 is not required for the current supplementary structure. The active
  supplementary entry point uses `sections/supplementary_patch_bundle.tex` and
  does not include a Table 11 source.
- The `Use` column in the auxiliary Nerfacto sweep table was removed. The
  representative row is now marked by bold formatting and explained in the
  caption instead of using an operations-note column.
- Legacy Overleaf-only `table10_system_stack.tex` no longer contains
  `\pending` markers. It is retained only as a layout-compatible fallback;
  the paper-facing system evidence is the MarineCity validation table set.

## Active Supplementary Inputs

- `sections/supp_detector_experiment_inventory.tex`
- `sections/supp_marinecity_system_details.tex`
- `sections/07_marinecity_qualitative_figure_slots.tex`

## Not Included

- TinyPerson results are excluded from the active main and supplementary paper.
- Duplicate MarineCity S2 qualitative panel is excluded from supplementary.
- Table 11 is not part of the active supplementary source.
