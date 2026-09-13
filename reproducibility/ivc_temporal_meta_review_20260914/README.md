# CoM3D-ACE Temporal Evaluation Snapshot

This directory is the public, path-sanitized snapshot of the frozen temporal
meta-review experiments dated 2026-09-14. It contains compact result tables,
manifests, failed-run records, deterministic visualization scripts, and the
paper-number verification tool. Raw MMOT/M3OT data, detector/ReID weights,
tracker caches, and third-party source trees are intentionally excluded.

## Start here

- `experiment_inventory.md`: datasets, revisions, fixed settings, commands,
  invariants, and blocked comparisons.
- `experiment_report.md`: full results and claim boundaries, including the
  adverse held-out M3OT result.
- `artifact_index.json`: SHA-256 index of this snapshot.
- `results_raw/paper_ready/`: CSV and LaTeX tables generated from frozen rows.
- `paper_verification.json`: 18 passing checks against the compiled paper.

## Environment

The core packages used in the verified environment are pinned in
`requirements-audit.txt`. BoxMOT, TrackEval, the MMOT author code, and official
AFLink were source checkouts at the revisions listed in
`experiment_inventory.md`; install those projects according to their upstream
licenses and instructions. The official datasets and checkpoints must be
obtained from their respective authors.

Set explicit paths before using commands from the inventory:

```bash
export EXPERIMENT_ROOT=/path/to/this/directory
export FROZEN_WORKSPACE=/path/to/checkouts-and-checkpoints
export DATA_CACHE=/path/to/datasets
export RUNS_ROOT=/path/to/reference-runs
export PYTHON_ENV=/path/to/python/environment
```

Historical manifests use angle-bracket path tokens such as
`<FROZEN_WORKSPACE>` and `<DATA_CACHE>`. They document the original command
shape without publishing workstation-specific locations. Historical source
hashes describe the execution copies; `artifact_index.json` hashes this
sanitized snapshot.

## Verification

Regenerate the compact tables from frozen CSVs:

```bash
$PYTHON_ENV/bin/python scripts/generate_temporal_paper_assets.py \
  --experiment-root "$EXPERIMENT_ROOT" \
  --output-dir "$EXPERIMENT_ROOT/results_raw/paper_ready"
```

Validate a compiled manuscript checkout:

```bash
$PYTHON_ENV/bin/python scripts/verify_temporal_paper_numbers.py \
  --experiment-root "$EXPERIMENT_ROOT" \
  --paper-root /path/to/paper \
  --output "$EXPERIMENT_ROOT/paper_verification.json"
```

No failed run contributes a reported metric. GIAOTracker remains unavailable,
and invalid AFLink full-set aggregates remain explicitly unreported.
