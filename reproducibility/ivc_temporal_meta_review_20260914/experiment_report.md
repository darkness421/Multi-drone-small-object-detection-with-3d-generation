# CoM3D-ACE A-Plan Experiment Report

Date: 2026-09-14

## Decision

The defensible contribution is a deterministic post-tracking tracklet
refinement layer for aerial MOT. On the full official MMOT test set, the fixed
CoM3D-ACE rule consistently improves each frozen upstream tracker over no
refinement under both oracle AABB and official detector inputs. The result is
also positive on the previously unseen `confirmation38` partition.

The method is not the strongest refiner in this study. Geometry+ReID partial
Hungarian is stronger for OC-SORT and Deep OC-SORT, and simple geometry
greedy is stronger for ByteTrack. A geometry+ReID greedy ablation is stronger
still in several rows. The component-overlap guard is inactive on the MMOT
outputs. Held-out M3OT transfer is negative. These results rule out universal,
state-of-the-art, calibrated-risk, and domain-general claims.

## Protocol correction and relation to the previous manuscript

The former local MMOT scripts treated raw bands 1, 2, and 3 as RGB. The MMOT
paper and active official tracking loaders establish the pseudo-RGB channels
as bands 5, 3, and 2. All new appearance-based results use zero-based
`[4,2,1]` as RGB. The old 12-sequence temporal numbers therefore remain in
the historical archive but are superseded for this manuscript.

The corrected 12-sequence equal-sequence results already changed the evidence:

| Upstream | No refinement IDF1 | CoM3D-ACE IDF1 | Delta | IDSW change |
|---|---:|---:|---:|---:|
| ByteTrack | 44.11 | 46.05 | +1.95 | 2,760 to 2,362 |
| OC-SORT | 37.45 | 40.19 | +2.74 | 1,556 to 1,063 |
| Deep OC-SORT | 69.84 | 71.68 | +1.84 | 286 to 167 |

The A-plan expands this to all 50 official test sequences and applies all
three trackers to the same sequence set. Consequently, the previous abstract
claims based on two 12-sequence trackers and one 6-sequence pooled protocol
must not be carried into the revised paper.

## Full MMOT test: oracle AABB input

Scores are equal-sequence means over 50 sequences. IDSW is summed over the
same sequences.

| Upstream | Refiner | HOTA | AssA | IDF1 | IDSW |
|---|---|---:|---:|---:|---:|
| ByteTrack | None | 44.20 | 44.69 | 47.44 | 20,056 |
|  | Geometry greedy | **45.60** | **46.97** | **51.02** | **15,484** |
|  | Partial Hungarian | 45.55 | 46.90 | 50.78 | 16,462 |
|  | CoM3D-ACE | 45.19 | 46.34 | 49.72 | 17,511 |
| OC-SORT | None | 44.92 | 51.43 | 42.96 | 6,119 |
|  | Geometry greedy | 45.90 | 53.68 | 45.41 | 4,122 |
|  | Partial Hungarian | **46.26** | **54.45** | **46.19** | **3,547** |
|  | CoM3D-ACE | 45.92 | 53.64 | 45.25 | 4,441 |
| Deep OC-SORT | None | 81.32 | 82.06 | 81.49 | 1,962 |
|  | Geometry greedy | 82.58 | 84.52 | 83.69 | 1,294 |
|  | Partial Hungarian | **82.79** | **84.93** | **84.00** | **1,174** |
|  | CoM3D-ACE | 82.60 | 84.54 | 83.67 | 1,377 |

Relative to no refinement, CoM3D-ACE changes IDF1 by +2.28, +2.29, and
+2.18 points and IDSW by -2,545, -1,678, and -585 for ByteTrack, OC-SORT,
and Deep OC-SORT, respectively. Detection metrics remain effectively fixed,
as expected from an ID-only refiner.

Official AFLink cannot be summarized over all 50 oracle sequences under the
predeclared invariant policy because at least one output is invalid for 2, 3,
and 4 sequences for ByteTrack, OC-SORT, and Deep OC-SORT, respectively. Those
aggregates are N/A rather than repaired post hoc.

## Full MMOT test: official detector input

The same official YOLO11L-3ch detections are shared by all methods.

| Upstream | Refiner | HOTA | AssA | IDF1 | IDSW |
|---|---|---:|---:|---:|---:|
| ByteTrack | None | 34.65 | 42.29 | 38.32 | 10,324 |
|  | Geometry greedy | **35.64** | **44.14** | **40.76** | **7,908** |
|  | Partial Hungarian | 35.58 | 44.11 | 40.56 | 8,405 |
|  | CoM3D-ACE | 35.40 | 43.75 | 39.97 | 8,935 |
| OC-SORT | None | 35.89 | 47.62 | 36.46 | 4,263 |
|  | Geometry greedy | 36.51 | 49.40 | 38.14 | 2,959 |
|  | Partial Hungarian | **36.77** | **49.97** | **38.74** | **2,668** |
|  | CoM3D-ACE | 36.53 | 49.24 | 38.09 | 3,204 |
| Deep OC-SORT | None | 53.92 | 67.00 | 63.09 | 1,370 |
|  | Geometry greedy | 54.25 | 67.71 | 64.01 | 1,008 |
|  | Partial Hungarian | **54.36** | **67.95** | **64.17** | **957** |
|  | AFLink | 54.00 | 67.16 | 63.33 | 1,342 |
|  | CoM3D-ACE | 54.31 | 67.84 | 64.08 | 1,046 |

Relative to no refinement, CoM3D-ACE changes IDF1 by +1.65, +1.62, and
+1.00 points and IDSW by -1,389, -1,059, and -324. This is the practical
detector-to-tracker-to-refiner result; it must remain distinct from the
oracle-AABB diagnostic. AFLink is fully valid only for Deep OC-SORT in this
input condition.

## Frozen confirmation-38 result

The 38 sequences outside the previously evaluated 12 were not used to alter
the method or thresholds. Paired bootstrap intervals use 10,000 sequence
resamples and seed 20260914.

| Input | Upstream | Delta IDF1 [95% CI] | Delta IDSW | Improved / tied / worsened |
|---|---|---:|---:|---:|
| Oracle | ByteTrack | +2.38 [1.85, 2.99] | -2,147 | 38 / 0 / 0 |
| Oracle | OC-SORT | +2.15 [1.54, 2.84] | -1,185 | 37 / 0 / 1 |
| Oracle | Deep OC-SORT | +2.29 [1.37, 3.57] | -466 | 31 / 4 / 3 |
| Detector | ByteTrack | +1.71 [1.20, 2.26] | -1,142 | 33 / 1 / 4 |
| Detector | OC-SORT | +1.51 [1.07, 2.04] | -759 | 36 / 0 / 2 |
| Detector | Deep OC-SORT | +1.10 [0.48, 2.00] | -268 | 27 / 5 / 6 |

Every interval is above zero, but this confirms improvement only over the
unchanged upstream output, not superiority over the stronger refiners.

## Component ablation and comparator result

Under oracle AABBs on all 50 sequences:

- Geometry reciprocal already yields IDF1 49.62/45.08/83.63 for
  ByteTrack/OC-SORT/Deep OC-SORT.
- Adding fixed ReID yields 49.72/45.25/83.67.
- Adding the component-overlap guard changes no MMOT metric or IDSW count.
  The guard is a validity constraint but is empirically inactive here.
- Geometry+ReID greedy reaches 51.80/46.25/83.99, exceeding CoM3D-ACE for
  all three trackers in IDF1.
- Partial Hungarian reaches 50.78/46.19/84.00, also exceeding CoM3D-ACE.

The proposal's supported advantage is therefore deterministic conservative
reciprocal refinement over no refinement, with explicit unmatched outputs and
a validity guard. The experiments do not establish an accuracy advantage over
the strongest global assignment controls.

## Error/coverage audit

The fixed source-tracklet denominator is the set with at least one temporally
admissible non-overlapping successor within 30 frames. Error is measured only
among accepted links with auditable post-hoc GT identities. At the fixed
0.30 gate:

| Upstream | Refiner | Coverage | Auditable-link error | IDF1 |
|---|---|---:|---:|---:|
| ByteTrack | CoM3D-ACE | 36.6% | 44.6% | 49.72 |
|  | Partial Hungarian | 54.0% | 52.9% | 50.78 |
| OC-SORT | CoM3D-ACE | 37.9% | 35.1% | 45.25 |
|  | Partial Hungarian | 49.5% | 25.6% | 46.19 |
| Deep OC-SORT | CoM3D-ACE | 26.1% | 39.2% | 83.67 |
|  | Partial Hungarian | 32.7% | 35.3% | 84.00 |

For ByteTrack, 3,909 CoM3D-ACE accepted links lack a sufficiently pure
post-hoc endpoint identity and are excluded from the error denominator; the
coverage denominator still includes them. The sweep is descriptive and was
not used to choose a test threshold. These rates are not calibrated risks or
formal abstention guarantees.

## M3OT transfer failure

The fixed policy improves the four development sequences but degrades the
four held-out sequences:

| Split | Upstream | IDF1 baseline to refined | IDSW baseline to refined | Correct/false accepted links |
|---|---|---:|---:|---:|
| Development | ByteTrack | 96.89 to 98.49 | 20 to 10 | 10 / 3 |
| Development | OC-SORT | 96.10 to 98.26 | 21 to 9 | 12 / 5 |
| Held-out | ByteTrack | 96.77 to 92.77 | 6 to 6 | 0 / 7 |
| Held-out | OC-SORT | 95.39 to 94.84 | 5 to 5 | 0 / 3 |

The held-out streams contain only three and five correct fragment
opportunities for ByteTrack and OC-SORT; all ten admitted links are false,
nine on IR and one on RGB. This is a post-hoc association, not proof that
modality alone caused the failure. No M3OT test-specific exception or retuned
gate was introduced.

## Small-object evidence and efficiency

Of 196,194 MMOT oracle boxes, 53.4% have area below `32^2` pixels, 45.9% lie
between `32^2` and `96^2`, and 43.1% have a short side below 16 pixels. Median
short side is 21 pixels. This supports retaining “aerial small-object” as a
dataset characteristic, not a claim that the refiner itself is a detector.

On an RTX 5090 with batch 128, frozen BaseReID extraction plus the in-memory
graph costs approximately 46.9 ms/frame for ByteTrack, 24.5 ms/frame for
OC-SORT, and 24.5 ms/frame for Deep OC-SORT over 5,466 frames. Graph-only
time is 7.99, 2.09, and 1.21 seconds in total, respectively; appearance
extraction dominates. The shared detector inference is separately measured at
226.15 seconds, about 41.4 ms/frame. These are offline replay measurements,
not a flight-system latency claim.

## Qualitative evidence

The new panel uses actual frozen predictions, not GT boxes presented as
predictions:

- Correct accepted link: confirmation38 `data41-1`, bus, ByteTrack, local IDs
  1 to 3, frames 56 to 58, post-hoc actor 18 at purity 1.0.
- False accepted link: confirmation38 `data24-1`, car, Deep OC-SORT, local IDs
  40 to 48, frames 393 to 397, different post-hoc actors.

The raw MMOT imagery is displayed with the corrected pseudo-RGB bands and is
unaltered except deterministic crops, boxes, and labels.

## Manuscript incorporation

The manuscript was narrowed to:

`CoM3D-ACE: Reciprocal Evidence-Graph Tracklet Refinement for Aerial Multi-Object Tracking`

The revised paper includes the full-50 oracle and detector tables, the frozen
confirmation-38 deltas, component ablation, error/coverage curve, adverse M3OT
transfer, object-size distribution, runtime, and actual-prediction
success/failure panel. MarineCity static association, BuckTales, SAFR-YOLO,
and simulated follow-up routing are not used as evidence for this temporal
contribution. Generated tables were compared byte-for-byte with the manuscript
inputs, and repeated headline deltas were recomputed from full-precision frozen
rows before display rounding.

## Remaining limitations and blocked comparison

- Official GIAOTracker global-link reproduction is blocked by unavailable
  released implementation/weights; no substitute is reported as GIAO.
- AFLink's official output violates the no-duplicate-identity-per-frame
  invariant in some sequences, preventing several full-set aggregate rows.
- The method does not beat the strongest controlled greedy/Hungarian refiner.
- MMOT confirmation is positive, but held-out M3OT transfer is negative.
- Error/coverage values are descriptive and uncalibrated.
- The study evaluates within-stream temporal identity, not global cross-UAV
  identity or autonomous re-observation.

The exact source paths, commands, hashes, and all failed-run records are in
`experiment_inventory.md` and the per-run manifests.
