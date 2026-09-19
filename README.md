# REGR: Reciprocal Evidence-Graph Refinement for Aerial MOT

REGR is a deterministic post-processing method for aerial multi-object
tracking. It builds temporal candidate edges from frozen tracker observations
and tracklet descriptors, then updates identity labels without adding,
removing, or interpolating detections.

This repository contains the implementation, fixed method configurations,
command-line interface, tests, and a small synthetic smoke example. Datasets,
images, checkpoints, tracker caches, generated figures, and experiment outputs
are not included.

## Installation

REGR requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e '.[dev]'
```

Optional benchmark adapters require the evaluation dependencies:

```bash
python -m pip install -e '.[evaluation,dev]'
```

## Input

The prediction input is JSONL or compressed JSONL. Each observation requires
`frame`, `id`, `class_id`, `x`, `y`, `w`, and `h`; `conf` is retained when
present. Coordinates use native-image pixels.

Tracklet descriptors are supplied as JSON or NPZ, keyed by tracklet ID. Every
tracklet used for appearance comparison must have one descriptor vector.

## Run

The included example requires no external data, checkpoint, or GPU:

```bash
regr-refine \
  --predictions examples/predictions.jsonl \
  --descriptors examples/descriptors.json \
  --method regr \
  --output-dir outputs/smoke
```

The command writes refined observations, accepted and rejected edge audits,
and a manifest containing parameters, input hashes, and invariant checks. It
refuses to overwrite a non-empty output directory.

The public method names are `none`, `geometry-reid-greedy`, `regr`,
`regr-v1`, `regr-t`, and `regr-tg`. The default `regr` parameters are stored
in `regr/configs/regr_final.json`.

## Verification

```bash
python -m pytest -q
python scripts/check_public_release.py
```

`check_public_release.py --strict-publication` also requires a project-level
license. The license has not yet been selected, so redistribution permission
is not granted by this repository alone.

## External Assets

MMOT, M3OT, BoxMOT, TrackEval, and pretrained ReID weights must be obtained
from their official sources under their respective terms. No third-party data,
images, code checkout, or model weight is redistributed here. Recorded external
revisions and the descriptor checkpoint hash are listed in `NOTICE`.
