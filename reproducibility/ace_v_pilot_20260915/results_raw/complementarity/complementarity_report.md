# Frozen-linker complementarity audit

This is a post-hoc GT audit of already frozen edge decisions. It is not a deployable oracle ensemble.

- Source trace rows: 33,466
- Selected-edge disagreements retained: 15,778
- Component co-membership is reported separately because distinct edge sets can induce the same ID partition.
- Unknown labels remain in the coverage count and are excluded only from conditional precision/error.

## ACE-v1 versus Cost-H

| Input | Tracker | Common | v1-only correct/false | H-only correct/false | Edge Jaccard |
|---|---:|---:|---:|---:|---:|
| official_detector | bytetrack | 2199 | 8/10 | 20/13 | 0.459 |
| official_detector | deepocsort | 598 | 0/5 | 4/7 | 0.583 |
| official_detector | ocsort | 1628 | 8/34 | 52/33 | 0.535 |
| oracle_aabb | bytetrack | 3155 | 46/126 | 146/339 | 0.398 |
| oracle_aabb | deepocsort | 749 | 12/185 | 202/232 | 0.543 |
| oracle_aabb | ocsort | 2019 | 59/482 | 887/439 | 0.520 |

## Decision

Across the six input/tracker conditions, v1 has 133 correct edges not selected by Cost-H, while Cost-H has 1311 correct edges not selected by v1.
This confirms edge-level complementarity but does not show that a GT-free verifier can identify the useful subset. ACE-V development therefore proceeds, and its success is judged only by final trajectory metrics against the standalone solvers.

The frozen trace lacks matched-observation and tied-majority counts. That omission is explicit in `link_audit_label_quality.csv`; the new run must rebuild those fields rather than treating unknown edges as errors or successes.
