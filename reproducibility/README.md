# Reproducibility Artifacts

This directory contains compact records needed to audit the reported final
REGR results without redistributing images, checkpoints, or full prediction
caches.

- `protocols/`: immutable method-selection records.
- `results/final/`: sequence- and scene-level metric rows for the final study.
- `results/prior_variants/`: earlier v1/T/TG development and transfer results,
  retained for audit and clearly separated from the selected method.
- `verified_tables/`: reported summaries and paired confidence intervals.
- `verified_tables/prior_variants/`: aggregates for the retained earlier
  variants; these are not final-method claims.
- `paper_table_map.csv`: manuscript-to-artifact mapping and claim boundaries.

The seven M3OT scenes were examined during earlier diagnostics and must not be
relabeled as a pristine independent test.
