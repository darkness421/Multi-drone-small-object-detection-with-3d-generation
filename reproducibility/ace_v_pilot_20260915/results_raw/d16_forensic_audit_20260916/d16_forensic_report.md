# Table D.16 forensic audit report

## Verdict

The D.16 experiments are complete, but their result remains mixed/negative. The fixed full verifier does not establish a solver-agnostic gain: both H and P-G worsen on MMOT. No threshold was selected or changed in this audit.

A concrete naming error was found: D.16's `path_g` is not Table 4's `Geo.+ReID-G`. The D.16 control must be named `P-G` to prevent a false implementation equivalence.

## Requested checks

| Check | Status | Evidence |
| --- | --- | --- |
| D.16 commit/config/commands/results lineage | Partially resolved | Commits, manifests, reconstructed commands, CSV and table paths are recorded; historical stdout/stderr and scheduler IDs were not persisted. |
| Absolute None/v1/H/H+V/P-G/P-G+V by tracker | Resolved | `d16_absolute_metrics_by_tracker.csv`, `d16_absolute_metrics_per_sequence.csv`, and `d16_absolute_results.md`. |
| Verifier equations, units, directions, stage, reassignment | Resolved | `verifier_implementation_audit.md` is traced directly to `ace_v_core.py` and both runners. |
| V-off base reproduction | Resolved | `review_response_20260916/base_off_equivalence.csv`: 1,630/1,630 candidate-bearing solver instances identical. |
| D.16 P-G versus Table 4 G | Resolved as non-equivalent | Only 433/803 candidate-bearing final ID partitions match; see `g_lineage_audit.md`. |
| M3OT GT-admission versus direct crop | Partially resolved | Same tracker outputs verified and v1/H/legacy Cost-G compared. Historical cache has no P-G row, so that cross-preprocessing contrast is unavailable. |
| Margin-only/motion-only/cost-only/post-filter/reassignment | Resolved | `../review_response_20260916/requested_contrasts_per_sequence.csv`, `requested_contrasts_summary.csv`, and `component_comparison_summary.md`. |
| MMOT verifier edge transitions | Partially resolved | Counts are complete under the post-hoc audit labels, but many edges have unmatched/tied endpoints and remain unresolved rather than being treated as GT. |
| Solver-agnostic verifier advantage | Unresolved/unsupported | MMOT IDF1 is negative for both fixed primary contrasts. |

## MMOT all-tracker edge totals

| Input | Base | Correct rejected | False removed | Correct added by reassignment | False added by reassignment | Unresolved rejected/added |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| oracle_aabb | H | 387 | 584 | 95 | 200 | 1761/654 |
| oracle_aabb | P-G | 230 | 449 | 14 | 30 | 1044/47 |
| official_detector | H | 10 | 29 | 8 | 8 | 1618/511 |
| official_detector | P-G | 3 | 12 | 1 | 1 | 1016/52 |

The edge audit explains why lower conditional error is not enough: the verifier removes both correct and false links, while reassignment adds both correct and false alternatives. Final trajectory metrics, not favorable edge subsets, determine the conclusion.

## Manuscript action

Only the confirmed naming issue should change the manuscript: use `P-G` for D.16 and retain Table 4's `Geo.+ReID-G` as a distinct method. The negative D.16 values and limitations remain unchanged.

Control summary source: `../review_response_20260916/component_comparison_summary.md`.
