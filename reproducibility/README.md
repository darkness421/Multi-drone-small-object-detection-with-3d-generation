# Reproducibility Artifacts

This directory contains compact records needed to audit the manuscript's
reported REGR-T and REGR-TG values without redistributing images, checkpoints,
or full prediction caches.

- `protocols/`: immutable method-selection and transfer-guard records.
- `results/`: aggregate and sequence-level metric rows.
- `verified_tables/`: paper-facing summaries and paired confidence intervals.
- `paper_table_map.csv`: manuscript-to-artifact mapping and claim boundaries.

The M3OT held-out rows are explicitly marked as an exposed exploratory retest.
They must not be relabeled as independent confirmation.
