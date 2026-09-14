# Numerical consistency report

## Historical reproduction

The cache-only audit exactly reproduces the historical no-refinement, geometry
greedy, partial-Hungarian, and CoM3D-ACE all-50 rows for both oracle and
official-detector protocols and all three trackers. Maximum
absolute difference across HOTA, AssA, IDF1, IDSW, MOTA, TP, FP, FN, and prediction
count: **2.84217e-14**.

The newly surfaced Geometry+ReID greedy row is computed from the same frozen
candidate/descriptor caches. Its oracle all-50 IDF1 values are 51.80, 46.25, and
83.99 for ByteTrack, OC-SORT, and Deep OC-SORT, matching the manuscript's prior
ablation values after display rounding.

## Aggregation and rounding

- HOTA, AssA, IDF1, and MOTA are equal-sequence means.
- IDSW, FP, FN, and TP are totals over the stated sequence set.
- Delta statements are computed from full-precision CSV values and only then
  rounded for display; they are not recomputed from rounded table entries.
- Paired confidence intervals resample released sequences, with 10,000 replicates
  and seed 20260914.

## Source linkage limit

The exact review-target PDF with SHA-256 `7a04b4d4aa7a6c1f1462aca97a5d9346548c72792c4313b48d0f87756734aab6` is not present on
this machine. The current 23-page source checkout is commit `fa9c4329de036705864fc00ced1d40798a66fa7a` and
its pre-revision local `main.pdf` hash is `88eb435789f41d97425027027878bd2210e2744e265d9825a5b3216ec09bdee8`. The numerical source rows
are fully linked, but byte-for-byte linkage to the named review PDF remains
unverified until that exact PDF is supplied.
