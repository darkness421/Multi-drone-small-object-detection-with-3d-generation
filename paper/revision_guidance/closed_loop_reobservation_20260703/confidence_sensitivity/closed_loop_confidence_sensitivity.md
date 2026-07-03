# Closed-loop Re-observation Confidence Sensitivity

This diagnostic tests whether the targeted evidence-update result relies on very low-confidence detector tokens.
It should be used as reviewer-facing sensitivity evidence, not as the main result figure.

| Min conf. | Matched | Resolved | Mean A(loop) | After monitor | After reobserve |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 6 | 6 | 0.775 | 6 | 3 |
| 0.01 | 6 | 6 | 0.775 | 6 | 3 |
| 0.05 | 5 | 5 | 0.795 | 5 | 4 |
| 0.10 | 4 | 4 | 0.813 | 4 | 5 |
| 0.25 | 4 | 4 | 0.809 | 4 | 5 |
| 0.50 | 3 | 3 | 0.815 | 3 | 6 |

Interpretation: the default closed-loop artifact keeps a permissive detector threshold because the re-observation token is used as support evidence, not as a final class decision. Higher thresholds can be reported as a conservative sensitivity check.
