# REGR: Reciprocal Evidence-Graph Refinement for Aerial MOT

This repository is the public release candidate for **REGR**, a deterministic
post-tracking method for within-stream aerial multi-object tracking. REGR reads
frozen tracker outputs, builds same-class temporal candidate edges, and changes
only identity labels. It does not add, remove, or interpolate observations.

The release is intentionally narrower than the earlier development project.
It contains the temporal refiner evaluated in the paper, cache-replay tools,
tests, protocol locks, and result tables. It does not present detector design,
cross-camera identity, 3D reconstruction, or active re-observation as evaluated
REGR capabilities.

> Publication gate: the authors have not yet selected a project-level license.
> The source is organized and committed for review, but public redistribution
> remains blocked until `LICENSE-STATUS.md` is resolved.

The intended GitHub repository name is `REGR-Aerial-MOT`. Publication and
repository-transition gates are listed in `GITHUB_RELEASE_CHECKLIST.md`.

## Method Variants

| Public name | Artifact name | Role |
| --- | --- | --- |
| `none` | `no_refinement` | Frozen upstream tracker output |
| `geometry-reid-greedy` | `geometry_reid_greedy_guard` | Strong same-input deterministic control |
| `regr-v1` | `regr_v1` | Geometry-first reciprocal rule |
| `regr-t` | `regr_temporal_risk_05` | Development-selected temporal-risk ranking |
| `regr-tg` | `regr_t_reliable_motion_min5` | REGR-T plus development-frozen reliable-motion abstention |

All variants use the same maximum 30-frame gap, 55-pixel endpoint radius, and
0.30 cosine-distance gate. REGR-T uses a normalized gap weight of 0.05 and a
reciprocal-consensus bonus of 0.005. REGR-TG activates motion abstention only
when fewer than five consensus edges are present and motion is available for at
least 80% of gated edges; the maximum motion-residual/endpoint-distance ratio
is 1.0.

## Reported Scope

On all 50 MMOT test sequences, REGR-TG improves equal-sequence-mean IDF1 over
no refinement in all six tracker/input conditions. The gains are 3.75, 2.93,
and 2.36 percentage points with oracle AABBs and 2.45, 2.11, and 1.01 points
with the shared official detector cache. Five of the six gains exceed 2 points,
and all six paired sequence-bootstrap intervals are above zero.

REGR-T is within 0.055 IDF1 points of Geometry+ReID greedy in every MMOT
condition. Five paired intervals include zero; detector-input ByteTrack is the
only strictly positive interval. This supports near parity under the evaluated
conditions, not uniform superiority.

On four M3OT held-out streams, REGR-TG changes IDF1 from 96.77 to 98.30 for
ByteTrack and from 95.39 to 95.47 for OC-SORT. These streams had been examined
in an earlier failure diagnostic, so the result is exploratory transfer
evidence, not fresh independent confirmation or broad generalization.

Recompute these statements from the released sequence-level CSVs:

```bash
python scripts/verify_reported_results.py
```

## Installation

Core cache replay requires Python 3.10 or newer and NumPy:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

The optional full benchmark environment also uses PyTorch, SciPy, Pillow,
BoxMOT, TrackEval, and the frozen OpenMMLab BaseReID checkpoint. Exact external
revisions and checkpoint hashes are listed in `THIRD_PARTY_NOTICES.md`.

## Quick Smoke Run

The included synthetic example needs no dataset, model weight, or GPU:

```bash
regr-refine \
  --predictions examples/predictions.jsonl \
  --descriptors examples/descriptors.json \
  --method regr-tg \
  --output-dir outputs/smoke
```

The output directory contains:

- `refined.jsonl`: the same observations with final identity labels;
- `accepted_edges.csv` and `rejected_edges.csv`: auditable graph decisions;
- `manifest.json`: method mapping, fixed parameters, input hashes, and
  observation-preservation checks.

The cache schema is documented in `docs/CACHE_FORMAT.md`.

## Tests And Release Audit

```bash
python -m pytest -q
python scripts/verify_reported_results.py
python scripts/check_public_release.py
python scripts/build_release_manifest.py
```

The non-strict audit intentionally reports one warning until a project license
is selected. Before publication, add the approved `LICENSE` and run:

```bash
python scripts/check_public_release.py --strict-publication
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `regr/_artifact_core.py` | Immutable experiment implementation, including development candidates |
| `regr/core.py` | Stable public names for the five reported operating points |
| `regr/graph.py` | Candidate construction, union, and output invariants |
| `regr/cli.py` | Portable cache-replay command |
| `reproducibility/protocols/` | Development/test freeze records |
| `reproducibility/results/` | Released aggregate and sequence-level metrics |
| `reproducibility/verified_tables/` | Paper-facing summary and paired-CI CSVs |
| `scripts/summarize_results.py` | Regenerates paper-facing summaries from result directories |
| `scripts/verify_reported_results.py` | Checks the numerical claims above |
| `tests/` | Algorithm, invariant, CLI, and result-regression tests |
| `ci/github-actions.yml` | CI template; activate it at publication as described in the release checklist |

## Data And Checkpoints

No dataset, tracker cache, image, or checkpoint is redistributed. Obtain MMOT
and M3OT from their official sources and comply with their terms:

- MMOT: https://github.com/Annzstbl/MMOT
- M3OT: https://github.com/M3OT/M3OT

The frozen BaseReID checkpoint used for the paper is documented by source URL
and SHA-256 in `THIRD_PARTY_NOTICES.md`. Store all private or downloaded assets
outside the repository and pass their paths through CLI arguments.

## Reproducibility Boundaries

The checked-in sequence-level CSVs support paper-number verification without
redistributing datasets or tracker caches. Full raw-data regeneration requires
the official datasets, external tracking/evaluation dependencies, and frozen
tracker/descriptor caches. `docs/REPRODUCIBILITY.md` distinguishes cache replay,
metric verification, and full regeneration so that a partial release is not
mistaken for an end-to-end benchmark package.
