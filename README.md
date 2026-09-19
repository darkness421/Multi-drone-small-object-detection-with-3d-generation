# REGR: Reciprocal Evidence-Graph Refinement for Aerial MOT

This repository contains the reference implementation of **REGR**, a deterministic
post-tracking method for within-stream aerial multi-object tracking. REGR reads
frozen tracker outputs, builds same-class temporal candidate edges, and changes
only identity labels. It never adds, removes, or interpolates observations.

The implementation contains the final refiner, cache-replay tools, frozen
protocols, tests, and result tables. Detector design, cross-camera identity, 3D
reconstruction, and active re-observation are outside the evaluated scope.

## Final Method

The public method name is `regr`; `regr_final` is the corresponding frozen
implementation name. It was selected on the pre-registered MMOT development
subset and M3OT scene 08 before confirmation evaluation.

1. Candidate edges have a gap of 1--30 frames, endpoint distance at most 55
   native-image pixels, cosine distance at most 0.30, equal class, and no
   overlapping frame support.
2. The deterministic temporal score is cosine distance plus
   `0.05 * gap / 30`, with a 0.005 bonus for geometry/appearance reciprocal
   consensus.
3. Source-forward and destination-backward motion are fit from three endpoint
   observations using their actual frame indices. Holdout error, fit RMSE,
   velocity variation, support, and temporal span form a candidate-specific
   confidence in `[0, 1]`. Two-point tracklets are uninformative.
4. The motion guard activates only when reciprocal consensus is sparse
   (`< 5` edges) and at least 80% of gated candidates have confidence at least
   0.50. When active, only reliable candidates whose mean bidirectional
   residual exceeds one geometric-mean endpoint box diagonal are rejected;
   unreliable motion does not force acceptance or rejection.
5. Remaining edges are greedily merged in temporal-score order. A merge that
   would place the same output identity twice in one frame is rejected.

`regr/configs/regr_final.json` is the canonical parameter record. Earlier
`regr-v1`, `regr-t`, and `regr-tg` remain available for reproducing the reported
ablations and are not presented as three current methods.

## What The Evaluation Supports

All values below come from frozen upstream outputs and are reported as
equal-sequence means for MMOT and equal-scene means after four-stream averaging
for M3OT.

- On MMOT oracle inputs, final REGR changes IDF1 from 47.44 to 51.87 for
  ByteTrack, 42.96 to 46.25 for OC-SORT, and 81.49 to 84.00 for Deep OC-SORT.
  Against each tracker's stronger Geometry+ReID/partial-Hungarian control, the
  differences are `+0.072`, `-0.000`, and `-0.004` percentage points.
- On the shared MMOT detector cache, final REGR changes IDF1 from 38.32 to
  41.11, 36.46 to 38.75, and 63.09 to 64.15. Differences from the stronger
  control are `+0.008`, `-0.012`, and `-0.021` points. The OC-SORT paired
  interval is slightly negative; the other strong-control intervals include
  zero.
- On seven M3OT oracle scene groups, final REGR reaches 95.47 IDF1 with
  ByteTrack and 95.42 with OC-SORT. This is `+0.656` and `+1.391` points over
  the same temporal rule without candidate-specific motion, but only `+0.017`
  and `+0.397` over the stronger partial-Hungarian control; those latter
  intervals include zero.

These results support observation-preserving gains over no refinement and a
reduction of the prior M3OT transfer failure while preserving near-parity with
strong MMOT controls. They do **not** establish universal superiority over
assignment baselines or broad cross-dataset generalization. The seven M3OT
scenes were used in earlier diagnostics and are a fixed confirmation/retest,
not a pristine independent test. M3OT detector-input and VisDrone-MOT results
are not claimed because the required common caches were unavailable in the
verified environment.

Reported aggregates, paired intervals, ablations, accepted-link audits,
failure categories, and phase timings are under
`reproducibility/verified_tables/final/`.

## Installation

Core final-method replay requires Python 3.10 or newer and NumPy:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Install the optional evaluation dependencies when running partial-Hungarian
controls or the full benchmark adapters:

```bash
python -m pip install -e '.[evaluation,dev]'
```

The external benchmark environment additionally uses BoxMOT, TrackEval, and a
frozen OpenMMLab BaseReID checkpoint. Exact external revisions and checkpoint
hashes are documented in `THIRD_PARTY_NOTICES.md`.

## Quick Smoke Run

The included synthetic example needs no dataset, checkpoint, or GPU:

```bash
regr-refine \
  --predictions examples/predictions.jsonl \
  --descriptors examples/descriptors.json \
  --method regr \
  --output-dir outputs/smoke
```

The output directory contains:

- `refined.jsonl`: unchanged observations with final identity labels;
- `accepted_edges.csv` and `rejected_edges.csv`: auditable graph decisions;
- `manifest.json`: method mapping, fixed parameters, input hashes, and
  observation-preservation checks.

The cache schema is documented in `docs/CACHE_FORMAT.md`.

## Verification

```bash
python -m pytest -q
python scripts/check_public_release.py
python scripts/verify_reported_results.py
```

The release audit reports one warning until the authors add an approved
project-level `LICENSE`. Use strict mode before announcing an open-source release:

```bash
python scripts/check_public_release.py --strict-publication
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `regr/confidence.py` | Final motion-confidence rule, development controls, and ablations |
| `regr/core.py` | Stable public method names and final `regr` entrypoint |
| `regr/graph.py` | Candidate construction, component-safe merging, and output invariants |
| `regr/cli.py` | Portable cache-replay command |
| `regr/configs/regr_final.json` | Frozen final parameters and selection provenance |
| `reproducibility/protocols/` | Development/confirmation freeze records |
| `reproducibility/verified_tables/final/` | Verified reported CSVs and manifests |
| `scripts/run_*_confidence_search.py` | MMOT/M3OT cache evaluation entrypoints |
| `scripts/summarize_results.py` | Aggregate, paired-CI, and link-effect generation |
| `scripts/summarize_prior_variants.py` | Retained v1/T/TG summary generation |
| `scripts/profile_regr_final.py` | Exact-output graph-phase profiling |
| `tests/` | Algorithm, invariant, CLI, and result-regression tests |

## Data And Checkpoints

No dataset, tracker cache, image, or checkpoint is redistributed. Obtain MMOT
and M3OT from their official sources and comply with their terms:

- MMOT: https://github.com/Annzstbl/MMOT
- M3OT: https://github.com/M3OT/M3OT
- VisDrone: https://github.com/VisDrone/VisDrone-Dataset

Store private/downloaded assets outside the repository and pass their paths to
the experiment scripts. Ground-truth identity is used only for development
metric selection, final evaluation, and post-hoc edge audit; it never enters
candidate construction, motion confidence, ranking, or relabeling.

## Reproducibility Boundary

The checked-in sequence-level CSVs support paper-number verification without
redistributing datasets or tracker caches. Full dataset-to-cache regeneration
requires official data, external tracking/evaluation dependencies, and frozen
tracker/descriptor caches. `docs/REPRODUCIBILITY.md` distinguishes smoke replay,
paper-number verification, cache replay, and full regeneration.

## License

No project-level license has been granted yet. Source availability does not by
itself grant permission to copy, modify, or redistribute the software. The
authors will add the approved license before announcing an open-source release.
