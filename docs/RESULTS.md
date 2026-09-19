# Released Result Summary

MMOT HOTA, AssA, and IDF1 are equal-sequence means over 50 sequences; IDSW is
summed. M3OT metrics are first averaged across the four RGB/IR streams of each
physical scene and then across seven scenes; IDSW is summed. Differences are
computed from full-precision rows.

## MMOT Oracle And Detector Inputs

Final REGR improves over no refinement in all six tracker/input conditions.
Against the stronger Geometry+ReID or partial-Hungarian control, however, the
IDF1 differences range only from `-0.021` to `+0.072` percentage points. The
method is therefore reported as near the strong-control envelope, not uniformly
superior. Paired 20,000-resample sequence-bootstrap results are in
`final/paired_idf1.csv`.

## M3OT Oracle Confirmation/Retest

Final REGR reaches 95.472 IDF1 for ByteTrack and 95.418 for OC-SORT. Relative
to the identical temporal rule without candidate-specific motion, the gains are
`+0.656` and `+1.391` points; the latter paired scene interval is above zero.
Relative to partial Hungarian, the differences are `+0.017` and `+0.397`, with
both intervals including zero. These seven scenes were used in earlier
diagnostics, so this is a fixed confirmation/retest rather than untouched
external confirmation.

## Source Files

- `reproducibility/results/final/mmot_oracle/metrics_per_sequence.csv`
- `reproducibility/results/final/mmot_detector/metrics_per_sequence.csv`
- `reproducibility/results/final/m3ot_oracle/metrics_per_scene_group.csv`
- `reproducibility/verified_tables/final/main_comparison.csv`
- `reproducibility/verified_tables/final/ablation.csv`
- `reproducibility/verified_tables/final/guard_link_effect.csv`

## Evaluation Boundary

M3OT detector-input and VisDrone-MOT evaluations are not reported because the
common frozen caches required for same-input comparison were unavailable. The
released tables contain only completed evaluations; no placeholder rows are
used for unexecuted conditions.
