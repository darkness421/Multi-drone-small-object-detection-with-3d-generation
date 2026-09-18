# Reproducibility Levels

## Level 1: Algorithm Smoke Test

The synthetic example exercises candidate construction, final REGR selection,
component merging, and observation-preservation checks without external data:

```bash
regr-refine --predictions examples/predictions.jsonl \
  --descriptors examples/descriptors.json --method regr \
  --output-dir outputs/smoke
```

## Level 2: Paper-Number Verification

The repository includes sequence-level MMOT oracle/detector results, scene-level
M3OT results, paired intervals, ablations, link audits, failure categories, and
runtime summaries under `reproducibility/results/final_20260918/` and
`reproducibility/verified_tables/final_20260918/`.

The raw benchmark caches are not redistributed, so exact table regeneration
uses `scripts/summarize_final_results.py` after the three frozen result
directories and AFLink audit CSVs are supplied. The checked-in CSVs permit an
independent audit of every displayed aggregate without those private caches.

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
- M3OT confirmation/retest: upstream inputs are oracle AABBs. Descriptor crops
  are taken directly from tracker boxes without GT identity in inference. The
  seven scenes were examined in earlier diagnostics and are not described as a
  pristine independent test.
- No GT identity enters candidate construction, ranking, motion estimation, or
  final relabeling.

## Unexecuted Evaluations

No M3OT detector-input or VisDrone-MOT result is included. The verified machine
had no functioning CUDA driver, the M3OT common detector-tracklet cache did not
exist, and the local VisDrone-MOT directory was empty. The exact blockers are
recorded in `docs/EXPERIMENT_INVENTORY_20260918.md`; no inferred or placeholder
metrics replace those missing runs.
