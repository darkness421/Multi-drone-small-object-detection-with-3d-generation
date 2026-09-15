# Table 4 versus Table D.16 greedy lineage

The two rows denoted informally by G are not the same implementation.

- Table 4 `Geo.+ReID-G` is `geometry_reid_greedy_guard`: it ranks all gated candidates by cosine distance, then merges components unless their frame sets overlap. It does not enforce one predecessor and one successor at edge selection.
- Table D.16 used `path_g`: it ranks by the normalized controlled cost and enforces at most one outgoing and one incoming edge before component merging.
- The separate controlled-solver table's `Cost-G` is `controlled_cost_greedy`: it ranks all gated candidates by controlled cost and applies only the component-overlap guard. It is also not `path_g`.

Across 803 candidate-bearing MMOT class/tracker instances, Table 4 and D.16 have identical accepted-edge sets in 351 and identical final ID partitions in 433. Across 300 sequence/tracker rows, all three displayed metrics (IDF1, AssA, IDSW) match in 93. The global answer is therefore **not equivalent**.

The D.16 label should be `P-G` (controlled-cost path-constrained greedy), not the Table 4 `Geo.+ReID-G` label.
