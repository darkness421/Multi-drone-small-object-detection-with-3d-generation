# CoM3D-ACE professor-review audit

This directory is the reproducibility package for the 2026-09-14
professor-review response. It reuses frozen MMOT/M3OT tracklets, descriptors,
and evaluator inputs. It does not retrain a detector or tracker, select a test
threshold, or overwrite historical outputs.

## Contents

- `experiment_inventory.md`: executable inventory, frozen conditions, and full
  commands.
- `build_and_results_manifest.json`: source revisions, input paths, hashes, and
  result linkage.
- `results_raw/mmot_cached_solver_audit_v1/`: per-sequence solver results,
  AFLink stages, edge decisions, property tests, risk--coverage, and runtime.
- `results_raw/m3ot_linker_diagnostic_v2/`: exact historical reproduction,
  alternative linkers, and edge-level failure cases.
- `main_comparison.csv`, `paired_linker_deltas.csv`, and the other root CSVs:
  paper-facing aggregates derived from the raw outputs.
- `professor_review_resolution.md`: the required seven-part review response.
- `triple_check_report.md`: final numerical, claim-scope, and clean-build audit.
- `manuscript_number_verification.{md,json}`: 94 source-to-LaTeX checks.
- `scripts/`: the executed audit, report, M3OT diagnostic, and manuscript
  verification entry points.
- `paper/`: the compiled revised manuscript and its verification manifest.

## Verification

The paper numbers can be checked without rerunning detector or tracker inference:

```bash
python scripts/verify_manuscript_numbers.py \
  --report-root /path/to/ivc_professor_review_20260914 \
  --paper-root /path/to/com3d_ace_ivc_overleaf_sync
```

The revised manuscript was compiled in the frozen LaTeX image with:

```bash
docker run --rm -v "$PWD:/work" -w /work \
  com3d-ace-latex:20260906 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

See `experiment_inventory.md` for the exact MMOT and M3OT analysis commands.
Absolute paths in that file identify the frozen server artifacts used for this
audit; they are provenance records, not portable defaults.

## Interpretation boundary

The historical CoM3D-ACE ranking improves mean IDF1 over no refinement and the
box-preserving AFLink adapter in all six MMOT input/tracker conditions. It does
not outperform Geometry+ReID greedy or partial Hungarian mean IDF1. The
common-cost control and held-out M3OT result are diagnostic limitations and
must not be relabeled as a selected replacement method or omitted from claims.
