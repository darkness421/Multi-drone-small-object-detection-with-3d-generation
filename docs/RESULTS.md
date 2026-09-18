# Released Result Summary

All HOTA, AssA, and IDF1 values are equal-sequence means. IDSW is summed over
the stated sequence set. Differences are computed from full-precision rows.

## MMOT Test-50

REGR-T improves REGR-v1 in all six tracker/input conditions and differs from
Geometry+ReID greedy by at most 0.055 IDF1 percentage points. REGR-TG retains
positive gains over no refinement in all six conditions; five exceed 2 points.
All six paired sequence-bootstrap 95% intervals against no refinement are
above zero.

Source files:

- `reproducibility/results/mmot_oracle/metrics_per_sequence.csv`
- `reproducibility/results/mmot_detector/metrics_per_sequence.csv`
- `reproducibility/verified_tables/mmot_test50_summary.csv`
- `reproducibility/verified_tables/mmot_test50_paired_ci.csv`

## M3OT Transfer

REGR-TG changes held-out IDF1 by +1.53 points for ByteTrack and +0.08 points
for OC-SORT. The four streams were exposed in an earlier failure audit. These
rows support an exploratory frozen-rule retest, not independent confirmation
or broad cross-dataset generalization.

Source files:

- `reproducibility/results/m3ot_development/metrics_per_sequence.csv`
- `reproducibility/results/m3ot_heldout/metrics_per_sequence.csv`
- `reproducibility/verified_tables/m3ot_transfer_summary.csv`
