# M3OT concise failure analysis

The fixed M3OT experiment was reproduced exactly for all 16 split/tracker/sequence
instances (maximum metric difference 0; accepted-edge sets exact). The historical
descriptor protocol is oracle-box diagnostic: tracker observations are admitted to
image crops through IoU >= 0.9 matching to oracle GT before BaseReID encoding.

On the held-out split, the historical rule accepts 0 correct and 7 false links for
ByteTrack and 0 correct and 3 false links for OC-SORT. The candidate universe still
contains 3 and 5 auditable same-actor opportunities. Across those eight
opportunities, 5 are excluded by
the fixed 55-pixel geometry gate, 2
lose the reciprocal incoming comparison, and 1
lose the outgoing comparison.

The common-cost reciprocal diagnostic recovers one correct held-out link for each
tracker and reduces false accepted links to 6 and 2, respectively, but held-out
IDF1 remains below no refinement:

| Tracker | None | Historical | Common-cost reciprocal | Partial Hungarian |
| --- | ---: | ---: | ---: | ---: |
| ByteTrack | 96.77 | 92.77 | 92.89 | 91.86 |
| OC-SORT | 95.39 | 94.84 | 94.92 | 93.96 |

Historical false-link modalities are {'ir': 9, 'rgb': 1}. The casebook records
gap, pixel and normalized displacement, appearance distance, crop area, endpoint
purity, and competing candidates for every audited opportunity and false link.
These results implicate both ranking and cue/domain mismatch; a solver substitution
alone does not establish cross-domain transfer. Redesign should be performed on
development data before any new held-out claim.
