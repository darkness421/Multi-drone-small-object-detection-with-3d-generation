# Professor-review experiment status

Generated from committed result CSVs without rerunning the experiment or changing the manuscript.

## Status

| Requested item | Status | Evidence |
| --- | --- | --- |
| Hungarian alone vs Hungarian + evidence verifier | 완료 | `cost_h` vs `cost_h_full_reassign` |
| Geometry+ReID greedy alone vs greedy + same verifier | 완료 | `path_g` vs `path_g_full_reassign` |
| Margin-only / motion-only / same-cue cost-only | 완료 | Three component methods in per-sequence CSV |
| Post-filter-only vs verification then reassignment | 완료 | `cost_h_full_postfilter` vs `cost_h_full_reassign` |
| M3OT direct tracker-box crop control | 완료 (범위 제한) | Crop admission is GT-free; upstream detections remain oracle boxes |

Implementation commit: `9cd5fb8c319e40cb3f25b469f0bf8dbb8e63bc0b`.
Frozen config: `reproducibility/ace_v_pilot_20260915/protocol_freeze.yaml`.
The historical shell command, scheduler job ID, and stdout/stderr log were not persisted. This is a provenance gap; no job is currently running. The COMPLETE manifests retain input/output hashes, runtime, environment, and selected configuration.
Recorded runtime: MMOT 461.358 s; M3OT 175.341 s.

## Primary result

| Input | H+V - H IDF1 | G+V - G IDF1 |
| --- | ---: | ---: |
| M3OT development | +0.067 pp | +0.152 pp |
| M3OT exposed held-out | +0.995 pp | +0.000 pp |
| MMOT oracle AABB | -0.210 pp | -0.160 pp |
| MMOT official detector | -0.066 pp | -0.020 pp |

The verifier does not produce a solver-agnostic improvement: MMOT worsens for both primary contrasts, and M3OT held-out improves only for Hungarian while tying greedy. These are exposed exploratory retests, not fresh confirmation.

## Base-off check

All 1630 cached solver instances reproduced exactly with `V_off`: 1630/1630 identical.

## Artifact map

- Sequence-level requested contrasts: `requested_contrasts_per_sequence.csv`
- Aggregate deltas and component comparisons: `requested_contrasts_summary.csv`
- Readable component summary: `component_comparison_summary.md`
- CSV-generated Appendix table: `paper_table_ace_v_strong_linker.tex`
- Machine-readable five-item status table: `experiment_status.csv`
- Verifier-off cached equivalence: `base_off_equivalence.csv`
- M3OT crop-admission scope: `m3ot_preprocessing_control.csv`
- Commands recoverable from manifest parameters: `reproduction_commands.md`
- Review disposition: `professor_review_resolution.md`
