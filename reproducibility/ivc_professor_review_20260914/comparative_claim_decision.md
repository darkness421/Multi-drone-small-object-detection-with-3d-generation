# Comparative claim decision

## Decision

The completed cache-controlled audit does **not** support presenting the historical
geometry-first CoM3D-ACE row as the most accurate or risk-optimal MMOT linker. It
does support a narrower claim: the deterministic, box-preserving refiner improves
equal-sequence means over no refinement under all six upstream/input conditions,
while exposing reproducible assignment behavior and explicit transfer limits.

## Full-50 complete comparison

| Input | Tracker | Refiner | HOTA | AssA | IDF1 | IDSW |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Oracle AABB | ByteTrack | None | 44.20 | 44.69 | 47.44 | 20,056 |
| Oracle AABB | ByteTrack | Geometry greedy | 45.60 | 46.97 | 51.02 | 15,484 |
| Oracle AABB | ByteTrack | Geometry+ReID greedy | 45.89 | 47.47 | 51.80 | 15,064 |
| Oracle AABB | ByteTrack | Partial Hungarian | 45.55 | 46.90 | 50.78 | 16,462 |
| Oracle AABB | ByteTrack | AFLink + common validity adapter | 44.30 | 44.88 | 47.70 | 20,025 |
| Oracle AABB | ByteTrack | CoM3D-ACE (historical ranking) | 45.19 | 46.34 | 49.72 | 17,511 |
| Oracle AABB | OC-SORT | None | 44.92 | 51.43 | 42.96 | 6,119 |
| Oracle AABB | OC-SORT | Geometry greedy | 45.90 | 53.68 | 45.41 | 4,122 |
| Oracle AABB | OC-SORT | Geometry+ReID greedy | 46.31 | 54.55 | 46.25 | 3,481 |
| Oracle AABB | OC-SORT | Partial Hungarian | 46.26 | 54.45 | 46.19 | 3,547 |
| Oracle AABB | OC-SORT | AFLink + common validity adapter | 45.14 | 51.92 | 43.33 | 6,082 |
| Oracle AABB | OC-SORT | CoM3D-ACE (historical ranking) | 45.92 | 53.64 | 45.25 | 4,441 |
| Oracle AABB | Deep OC-SORT | None | 81.32 | 82.06 | 81.49 | 1,962 |
| Oracle AABB | Deep OC-SORT | Geometry greedy | 82.58 | 84.52 | 83.69 | 1,294 |
| Oracle AABB | Deep OC-SORT | Geometry+ReID greedy | 82.82 | 84.98 | 83.99 | 1,149 |
| Oracle AABB | Deep OC-SORT | Partial Hungarian | 82.79 | 84.93 | 84.00 | 1,174 |
| Oracle AABB | Deep OC-SORT | AFLink + common validity adapter | 81.54 | 82.48 | 81.93 | 1,919 |
| Oracle AABB | Deep OC-SORT | CoM3D-ACE (historical ranking) | 82.60 | 84.54 | 83.67 | 1,377 |
| Official detector | ByteTrack | None | 34.65 | 42.29 | 38.32 | 10,324 |
| Official detector | ByteTrack | Geometry greedy | 35.64 | 44.14 | 40.76 | 7,908 |
| Official detector | ByteTrack | Geometry+ReID greedy | 35.79 | 44.49 | 41.10 | 7,711 |
| Official detector | ByteTrack | Partial Hungarian | 35.58 | 44.11 | 40.56 | 8,405 |
| Official detector | ByteTrack | AFLink + common validity adapter | 34.73 | 42.45 | 38.53 | 10,297 |
| Official detector | ByteTrack | CoM3D-ACE (historical ranking) | 35.40 | 43.75 | 39.97 | 8,935 |
| Official detector | OC-SORT | None | 35.89 | 47.62 | 36.46 | 4,263 |
| Official detector | OC-SORT | Geometry greedy | 36.51 | 49.40 | 38.14 | 2,959 |
| Official detector | OC-SORT | Geometry+ReID greedy | 36.80 | 50.12 | 38.76 | 2,585 |
| Official detector | OC-SORT | Partial Hungarian | 36.77 | 49.97 | 38.74 | 2,668 |
| Official detector | OC-SORT | AFLink + common validity adapter | 36.02 | 47.95 | 36.69 | 4,240 |
| Official detector | OC-SORT | CoM3D-ACE (historical ranking) | 36.53 | 49.24 | 38.09 | 3,204 |
| Official detector | Deep OC-SORT | None | 53.92 | 67.00 | 63.09 | 1,370 |
| Official detector | Deep OC-SORT | Geometry greedy | 54.25 | 67.71 | 64.01 | 1,008 |
| Official detector | Deep OC-SORT | Geometry+ReID greedy | 54.34 | 67.92 | 64.15 | 942 |
| Official detector | Deep OC-SORT | Partial Hungarian | 54.36 | 67.95 | 64.17 | 957 |
| Official detector | Deep OC-SORT | AFLink + common validity adapter | 54.00 | 67.16 | 63.33 | 1,342 |
| Official detector | Deep OC-SORT | CoM3D-ACE (historical ranking) | 54.31 | 67.84 | 64.08 | 1,046 |

Geometry+ReID greedy and partial Hungarian exceed historical CoM3D-ACE IDF1 in all
six conditions. The paired intervals below compare the proposed row directly with
the strongest relevant linkers rather than only with no refinement.

| Input | Tracker | Comparator | Delta IDF1 [95% CI] | W/T/L |
| --- | --- | --- | ---: | ---: |
| Oracle AABB | ByteTrack | Geometry+ReID greedy | -2.08 [-2.69, -1.53] | 0/7/43 |
| Oracle AABB | ByteTrack | Partial Hungarian | -1.07 [-1.37, -0.79] | 1/8/41 |
| Oracle AABB | ByteTrack | AFLink + common validity adapter | +2.02 [+1.58, +2.51] | 46/4/0 |
| Oracle AABB | OC-SORT | Geometry+ReID greedy | -1.00 [-1.38, -0.66] | 1/8/41 |
| Oracle AABB | OC-SORT | Partial Hungarian | -0.93 [-1.36, -0.57] | 3/8/39 |
| Oracle AABB | OC-SORT | AFLink + common validity adapter | +1.92 [+1.44, +2.47] | 45/3/2 |
| Oracle AABB | Deep OC-SORT | Geometry+ReID greedy | -0.32 [-0.50, -0.15] | 4/21/25 |
| Oracle AABB | Deep OC-SORT | Partial Hungarian | -0.33 [-0.51, -0.17] | 3/22/25 |
| Oracle AABB | Deep OC-SORT | AFLink + common validity adapter | +1.74 [+0.96, +2.73] | 39/8/3 |
| Official detector | ByteTrack | Geometry+ReID greedy | -1.14 [-1.85, -0.60] | 5/11/34 |
| Official detector | ByteTrack | Partial Hungarian | -0.60 [-0.82, -0.40] | 2/12/36 |
| Official detector | ByteTrack | AFLink + common validity adapter | +1.43 [+1.05, +1.86] | 43/5/2 |
| Official detector | OC-SORT | Geometry+ReID greedy | -0.68 [-1.01, -0.41] | 2/12/36 |
| Official detector | OC-SORT | Partial Hungarian | -0.66 [-0.99, -0.40] | 1/12/37 |
| Official detector | OC-SORT | AFLink + common validity adapter | +1.40 [+1.05, +1.77] | 44/3/3 |
| Official detector | Deep OC-SORT | Geometry+ReID greedy | -0.06 [-0.14, +0.01] | 7/24/19 |
| Official detector | Deep OC-SORT | Partial Hungarian | -0.09 [-0.19, +0.01] | 4/27/19 |
| Official detector | Deep OC-SORT | AFLink + common validity adapter | +0.75 [+0.38, +1.22] | 32/9/9 |

## Ranking-versus-solver control

| Input | Tracker | Method | IDF1 | IDSW | Coverage | Known error |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Oracle AABB | ByteTrack | CoM3D-ACE (historical ranking) | 49.72 | 17,511 | 36.6% | 44.6% |
| Oracle AABB | ByteTrack | Common-cost greedy | 51.54 | 14,929 | n/a | n/a |
| Oracle AABB | ByteTrack | Common-cost reciprocal | 50.30 | 16,710 | 39.8% | 43.2% |
| Oracle AABB | ByteTrack | Partial Hungarian | 50.78 | 16,462 | 54.0% | 52.9% |
| Oracle AABB | OC-SORT | CoM3D-ACE (historical ranking) | 45.25 | 4,441 | 37.9% | 35.1% |
| Oracle AABB | OC-SORT | Common-cost greedy | 46.14 | 3,501 | n/a | n/a |
| Oracle AABB | OC-SORT | Common-cost reciprocal | 45.88 | 3,828 | 42.1% | 21.2% |
| Oracle AABB | OC-SORT | Partial Hungarian | 46.19 | 3,547 | 49.5% | 25.6% |
| Oracle AABB | Deep OC-SORT | CoM3D-ACE (historical ranking) | 83.67 | 1,377 | 26.1% | 39.2% |
| Oracle AABB | Deep OC-SORT | Common-cost greedy | 83.96 | 1,185 | n/a | n/a |
| Oracle AABB | Deep OC-SORT | Common-cost reciprocal | 84.02 | 1,242 | 27.4% | 29.0% |
| Oracle AABB | Deep OC-SORT | Partial Hungarian | 84.00 | 1,174 | 32.7% | 35.3% |
| Official detector | ByteTrack | CoM3D-ACE (historical ranking) | 39.97 | 8,935 | 34.4% | 29.7% |
| Official detector | ByteTrack | Common-cost greedy | 40.97 | 7,604 | n/a | n/a |
| Official detector | ByteTrack | Common-cost reciprocal | 40.42 | 8,491 | 37.2% | 24.8% |
| Official detector | ByteTrack | Partial Hungarian | 40.56 | 8,405 | 47.5% | 28.8% |
| Official detector | OC-SORT | CoM3D-ACE (historical ranking) | 38.09 | 3,204 | 35.4% | 38.9% |
| Official detector | OC-SORT | Common-cost greedy | 38.66 | 2,635 | n/a | n/a |
| Official detector | OC-SORT | Common-cost reciprocal | 38.55 | 2,825 | 39.0% | 31.6% |
| Official detector | OC-SORT | Partial Hungarian | 38.74 | 2,668 | 45.4% | 33.4% |
| Official detector | Deep OC-SORT | CoM3D-ACE (historical ranking) | 64.08 | 1,046 | 21.7% | 32.3% |
| Official detector | Deep OC-SORT | Common-cost greedy | 64.17 | 945 | n/a | n/a |
| Official detector | Deep OC-SORT | Common-cost reciprocal | 64.23 | 979 | 22.1% | 28.8% |
| Official detector | Deep OC-SORT | Partial Hungarian | 64.17 | 957 | 26.1% | 32.4% |

At the unchanged 0.30 gate, common-cost reciprocal selection improves IDF1 and has
both higher accepted-link coverage and lower known-link error than historical
geometry-first CoM3D-ACE in all six conditions. This diagnoses geometry-first
ranking as a material limitation; it does not license renaming the post-hoc
common-cost variant as the submitted method.

Solver-only timing favors reciprocal assignment modestly in several conditions,
but the absolute difference from Hungarian is small compared with candidate
construction and especially descriptor extraction. Consequently, runtime does not
provide a strong end-to-end selection basis for the historical rule.
