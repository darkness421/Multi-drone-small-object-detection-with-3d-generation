# Detector-input result-figure audit

The two paper-facing result figures were regenerated from completed frozen
artifacts. No detector, tracker, descriptor network, threshold search, or
training run was performed.

## Sequence-level quantitative figure

Source: `detector_input_temporal_per_sequence.csv` from the full 50-sequence
official-detector evaluation. Each plotted value is
`IDF1(CoM3D-ACE) - IDF1(no refinement)` for the same sequence and frozen
tracker output.

| Tracker | Mean delta IDF1 (pp) | Improved | Tied | Worsened |
| --- | ---: | ---: | ---: | ---: |
| ByteTrack | +1.65 | 41 | 5 | 4 |
| OC-SORT | +1.62 | 45 | 3 | 2 |
| Deep OC-SORT | +1.00 | 32 | 9 | 9 |

The exact 150 paired rows, source hash, fixed sequence order, and full-precision
means are stored in `evidence/detector_sequence_deltas/`.

## Qualitative link audit

The displayed boxes and local IDs come from the immutable detector-input
tracker caches. Dashed GT labels are assigned after linking by one-to-one
same-class matching at IoU >= 0.9.

- Correct edge: `data49-2`, OC-SORT, car. CoM3D-ACE accepts local tracklet
  `3 -> 28`; both endpoint tracklets have modal actor 2 with purity 1.0.
  The displayed observations at frames 10, 22, and 35 each match actor 2 at
  IoU 0.91 or above. CoM3D-ACE changes the displayed output IDs from
  `3 / 1 / 28` to `3 / 1 / 3`; this is a correct edge, not complete recovery
  of all three fragments. Partial-H instead produces `3 / 1 / 1`.
- Failure edge: `data37-10`, ByteTrack, car. CoM3D-ACE accepts `99 -> 123`,
  whose modal actor labels are 16 and 14. Partial-H instead accepts the correct
  same-actor edge `49 -> 123`. The displayed observations at frames 90, 102,
  and 136 all pass the same one-to-one IoU audit.

The case manifest records exact accepted-edge fields, output-root replay,
per-sequence deltas, source paths and hashes, crop coordinates, and the limited
post-hoc role of GT. The failure is retained in both the artifact and paper.

## Re-render check

Both scripts were rerun from the recorded inputs after manuscript integration.
The CSV and PNG outputs were byte-identical to the archived copies. Rasterizing
the regenerated vector PDFs also produced byte-identical page images; the PDF
containers themselves embed run-time metadata and therefore are not expected
to have identical file hashes across invocations.
