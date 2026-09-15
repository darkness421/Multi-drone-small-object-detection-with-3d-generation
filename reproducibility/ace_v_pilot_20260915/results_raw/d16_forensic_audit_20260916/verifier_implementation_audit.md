# Verifier implementation audit

## Candidate graph and base cost

Candidates are same-class, strictly forward links with gap <= 30 frames, endpoint-center distance <= 55 pixels, and BaseReID cosine distance <= 0.30. The dimensionless controlled cost is

`c_ij = mean(d_xy / 55 px, d_app / 0.30, gap / 30 frames)`.

## Competition margin

For edge `(i,j)`, the outgoing and incoming alternative costs include a null alternative of 1.0:

`a_out = min(1.0, min_{k != j} c_ik)`, `a_in = min(1.0, min_{k != i} c_kj)`.

`m_out = a_out - c_ij`, `m_in = a_in - c_ij`, and `A = max(0, -min(m_out, m_in))`.

All margin quantities are dimensionless. The margin gate passes when `A <= tau_a`; the selected fixed value is `tau_a=0.10`. Therefore a smaller value is preferred.

## Motion cue

Independent least-squares lines are fitted to x/y box centers over the last up to three source observations and first up to three destination observations. Each side needs at least two distinct frames. The two fits are evaluated at the temporal midpoint. Pixel disagreement is divided by the mean diagonal length of the two endpoint boxes, yielding dimensionless residual `rho`. The motion gate passes when `rho <= tau_m`, with fixed `tau_m=4.0`; smaller is preferred.

For motion-only verification, a missing motion cue passes. For the full verifier, a missing cue passes only when both margins are strictly positive. Thus full-V is:

`A <= 0.10 and (rho <= 4.0 if motion is available else m_out > 0 and m_in > 0)`.

## Application stage

- `post-filter`: run H first and remove selected edges that fail full-V; no reassignment.
- `full reassign`: filter the complete fixed candidate graph with full-V, then rerun the same H or P-G solver.
- `margin-only` and `motion-only`: filter the complete graph by only that cue, then rerun H.
- `same-cue cost-only`: rerun H with `mean(c_ij, min(A/0.10,1), min(rho/8,1))`; missing motion contributes 1. This is a cost control, not the hard verifier.

H is partial Hungarian with 0.5 outgoing and 0.5 incoming null costs. P-G sorts by controlled cost and permits at most one predecessor and one successor. GT is not used by the candidate graph, cue calculation, verifier, or solver.

## Verifier-off invariant

`V_off` returned every candidate and reproduced the corresponding base selection in 1630/1630 cached solver instances.
