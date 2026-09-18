# Final REGR Experiment Report (2026-09-18)

## Selection

The initial pre-registered A/B search did not beat the strong-baseline envelope
on both development datasets. A limited eight-point stage-2 search therefore
held the temporal order fixed and isolated candidate-specific motion gating.
The pre-specified max-min rule selected
`s2_t_cond_w3_scale_c50_r100`, now exposed as `regr`/`regr_final`:

- MMOT development delta versus the per-tracker strong envelope: `+0.0714 pp`;
- M3OT development delta: `+0.1279 pp`;
- minimum delta: `+0.0714 pp`.

The chosen rule uses a three-observation bidirectional fit, object-scale
normalization, confidence threshold 0.50, normalized residual threshold 1.0,
and conditional graph activation. The alias was verified to reproduce the
selected configuration exactly before confirmation evaluation.

## Confirmation Results

Final IDF1 and differences from the stronger same-input Geometry+ReID or
partial-Hungarian control are:

| Panel | Tracker | Final IDF1 | Delta vs strong control (pp) |
| --- | --- | ---: | ---: |
| MMOT oracle | ByteTrack | 51.872 | +0.072 |
| MMOT oracle | OC-SORT | 46.250 | -0.000 |
| MMOT oracle | Deep OC-SORT | 83.997 | -0.004 |
| MMOT detector | ByteTrack | 41.112 | +0.008 |
| MMOT detector | OC-SORT | 38.752 | -0.012 |
| MMOT detector | Deep OC-SORT | 64.151 | -0.021 |
| M3OT oracle | ByteTrack | 95.472 | +0.017 |
| M3OT oracle | OC-SORT | 95.418 | +0.397 |

The method is therefore near the strong-control envelope on MMOT, not uniformly
above it. On M3OT, candidate-specific motion improves the same temporal method
without motion by `+0.656 pp` (ByteTrack) and `+1.391 pp` (OC-SORT). The paired
scene bootstrap interval is above zero for the latter comparison only. Strong
partial Hungarian remains statistically tied at seven-scene resolution.

## What The Guard Changes

Against the identical temporal rule without motion, the M3OT guard removes 26
false and 8 correct accepted links for ByteTrack, and 54 false and 12 correct
links for OC-SORT. Subsequent component ordering adds 1 correct/3 false and
9 correct/6 false links, respectively. This supports transfer-error suppression
but also shows that the guard is not a correctness oracle.

Always-on motion improves M3OT point estimates but lowers all six MMOT
tracker/input IDF1 values. Conditional activation is therefore the selected
single fixed rule. A matched-score Hungarian control scores higher on M3OT but
was lower on MMOT development, so it was not selected after viewing
confirmation results.

## Failure Audit

On MMOT dev6, 139 post-hoc correct opportunities were removed by fixed gates,
29 lost to a competing false edge, and 101 lost to component/order effects;
only two false candidates were removed by the selected guard. On M3OT scene 08,
the guard removed eight false and one correct candidate. These counts motivated
candidate-specific motion but did not provide sufficient evidence to alter the
appearance descriptor, so optional improvement C was not run.

## Scope

The supported claim is observation-preserving improvement over no refinement,
near-parity with strong MMOT controls, and reduced prior M3OT transfer failure
under oracle inputs. M3OT detector-input and unused VisDrone-MOT confirmation
remain unexecuted because common frozen caches were unavailable and the verified
machine had no working CUDA driver. No placeholder values were created.
