# Strong-linker and component comparison

All cells are equal-sequence mean IDF1 changes in percentage points. MMOT and M3OT held-out are exposed exploratory retests.

| Contrast | M3OT dev | M3OT held-out | MMOT oracle | MMOT detector |
| --- | ---: | ---: | ---: | ---: |
| H+full-V reassign - H | +0.067 | +0.995 | -0.210 | -0.066 |
| P-G+full-V reassign - P-G | +0.152 | +0.000 | -0.160 | -0.020 |
| H+margin-only - H | -0.085 | +0.995 | -0.048 | -0.019 |
| H+motion-only - H | +0.152 | +0.995 | +0.003 | +0.028 |
| H+same-cue soft cost - H | -0.022 | +0.514 | -0.013 | -0.030 |
| H+post-filter - H | +0.114 | +0.443 | -0.274 | -0.086 |
| reassign - post-filter | -0.047 | +0.553 | +0.065 | +0.020 |

## Interpretation

- The full verifier fails the required replication: both strong-linker contrasts worsen on MMOT.
- Motion-only is the least harmful control on MMOT, but its IDF1 confidence intervals include zero and ID switches increase in the all-tracker totals.
- Reassignment is consistently better than post-filtering on MMOT, yet full reassignment still remains below the corresponding standalone Hungarian baseline.
- M3OT held-out gains occur in one of four sequences and were observed after that split had already been inspected; they are not independent confirmation.
- No treatment is promoted to a manuscript method or selected post hoc from these exposed rows.
