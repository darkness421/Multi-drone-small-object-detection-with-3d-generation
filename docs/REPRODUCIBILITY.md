# Reproducibility Levels

## Level 1: Algorithm Smoke Test

The synthetic example exercises candidate construction, REGR-TG selection,
component merging, and observation-preservation checks without external data:

```bash
regr-refine --predictions examples/predictions.jsonl \
  --descriptors examples/descriptors.json --method regr-tg \
  --output-dir outputs/smoke
```

## Level 2: Paper-Number Verification

The repository includes MMOT aggregate and sequence-level metrics plus M3OT
development and held-out rows. Verify the headline calculations with:

```bash
python scripts/verify_reported_results.py
```

Regenerate the paper-facing summary CSVs from those result directories with:

```bash
python scripts/summarize_results.py \
  --oracle-dir reproducibility/results/mmot_oracle \
  --detector-dir reproducibility/results/mmot_detector \
  --m3ot-development-dir reproducibility/results/m3ot_development \
  --m3ot-heldout-dir reproducibility/results/m3ot_heldout \
  --output-dir outputs/verified_tables
```

## Level 3: Frozen-Cache Replay

Use `regr-refine` for each tracker/sequence/class cache. The upstream
predictions and descriptors must remain identical across methods. Record the
input hashes and keep each run in a new output directory. Do not select a rule
or threshold from the MMOT test or exposed M3OT held-out results.

## Level 4: Full Dataset Regeneration

Full regeneration additionally requires official MMOT/M3OT data, BoxMOT at the
recorded revision, TrackEval at the recorded revision, the BaseReID checkpoint,
and the original upstream tracker settings. Those third-party assets are not
vendored. The public release candidate currently exposes the refiner and
paper-number audit; dataset-to-cache orchestration remains dependency-gated and
must not be described as a one-command reproduction until it is independently
validated on a clean machine.

## Ground-Truth Use

- MMOT oracle-AABB: GT boxes define upstream inputs; identities are withheld
  from tracking/refinement and used after predictions freeze for metrics and
  post-hoc edge labels.
- MMOT detector: one shared official detector cache is used by all trackers and
  refiners; GT is used for evaluation and post-hoc audit only.
- M3OT transfer: upstream inputs are oracle AABBs. The released transfer-guard
  run uses direct tracker-box descriptor crops without GT crop admission.
- No GT identity enters candidate construction, ranking, motion estimation, or
  final relabeling.
