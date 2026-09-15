# M3OT preprocessing control

The historical diagnostic admitted tracker observations to descriptor crops only after one-to-one oracle-GT IoU >= 0.9 matching. The D.16 run crops every valid tracker box directly, without GT crop admission. Both retain oracle-box upstream tracker inputs. None is identical in every sequence/tracker row, confirming the same tracker trajectories; changes below arise from descriptor admission/crops and downstream linking.

| Split | Tracker | Method mapping | Direct - historical IDF1 | Direct - historical AssA | Direct - historical IDSW |
| --- | --- | --- | ---: | ---: | ---: |
| development | bytetrack | controlled_cost_greedy -> cost_g_legacy | +0.032 | +0.025 | -2 |
| development | bytetrack | controlled_cost_partial_hungarian -> cost_h | +0.077 | +0.146 | -4 |
| development | bytetrack | historical_geometry_first_reciprocal -> ace_v1 | +0.010 | -0.025 | -1 |
| development | bytetrack | no_refinement -> no_refinement | +0.000 | +0.000 | +0 |
| development | ocsort | controlled_cost_greedy -> cost_g_legacy | +0.000 | +0.000 | +0 |
| development | ocsort | controlled_cost_partial_hungarian -> cost_h | +0.000 | +0.000 | +0 |
| development | ocsort | historical_geometry_first_reciprocal -> ace_v1 | +0.000 | +0.000 | +0 |
| development | ocsort | no_refinement -> no_refinement | +0.000 | +0.000 | +0 |
| held_out | bytetrack | controlled_cost_greedy -> cost_g_legacy | -0.811 | -1.165 | -1 |
| held_out | bytetrack | controlled_cost_partial_hungarian -> cost_h | -0.811 | -1.165 | -1 |
| held_out | bytetrack | historical_geometry_first_reciprocal -> ace_v1 | -0.811 | -1.165 | -1 |
| held_out | bytetrack | no_refinement -> no_refinement | +0.000 | +0.000 | +0 |
| held_out | ocsort | controlled_cost_greedy -> cost_g_legacy | +0.000 | +0.000 | +0 |
| held_out | ocsort | controlled_cost_partial_hungarian -> cost_h | +0.000 | +0.000 | +0 |
| held_out | ocsort | historical_geometry_first_reciprocal -> ace_v1 | +0.000 | +0.000 | +0 |
| held_out | ocsort | no_refinement -> no_refinement | +0.000 | +0.000 | +0 |

The historical cache has no path-constrained P-G row, so a historical GT-admission P-G comparison is unavailable and is not inferred. H/P-G verifier deltas are reported only within the direct-crop run.
