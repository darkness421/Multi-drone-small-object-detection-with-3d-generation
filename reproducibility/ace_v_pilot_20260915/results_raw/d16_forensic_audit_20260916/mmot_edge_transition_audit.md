# MMOT verifier edge-transition audit

Labels are post-hoc majority-actor relations from one-to-one same-class GT matching at IoU >= 0.9. Majority ties and unmatched endpoints are retained as unresolved; they are not forced into correct/false counts. GT is not used by linking or verification.

| Input | Tracker | Base | Correct base links rejected | False base links removed | Correct links added by reassignment | False links added by reassignment | Unresolved rejected/added |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| official_detector | bytetrack | H | 3 | 7 | 4 | 3 | 953/357 |
| official_detector | bytetrack | P-G | 1 | 1 | 1 | 0 | 550/27 |
| official_detector | deepocsort | H | 0 | 5 | 1 | 1 | 256/45 |
| official_detector | deepocsort | P-G | 0 | 2 | 0 | 0 | 203/17 |
| official_detector | ocsort | H | 7 | 17 | 3 | 4 | 409/109 |
| official_detector | ocsort | P-G | 2 | 9 | 0 | 1 | 263/8 |
| oracle_aabb | bytetrack | H | 34 | 102 | 28 | 61 | 1703/638 |
| oracle_aabb | bytetrack | P-G | 17 | 53 | 1 | 4 | 1008/46 |
| oracle_aabb | deepocsort | H | 97 | 204 | 24 | 51 | 2/0 |
| oracle_aabb | deepocsort | P-G | 70 | 171 | 9 | 20 | 2/0 |
| oracle_aabb | ocsort | H | 256 | 278 | 43 | 88 | 56/16 |
| oracle_aabb | ocsort | P-G | 143 | 225 | 4 | 6 | 34/1 |

These are edge diagnostics, not independent identity-recovery claims. The mixed final IDF1 results remain authoritative because removing a false edge can also break useful continuity, and adding a locally correct edge need not improve the final trajectory partition.
