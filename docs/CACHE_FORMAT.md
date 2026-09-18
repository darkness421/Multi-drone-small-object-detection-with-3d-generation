# Frozen Cache Format

REGR consumes tracker observations and one descriptor per tracklet. The public
CLI intentionally starts after upstream tracking and descriptor extraction so
that every refiner can receive identical inputs.

## Predictions

`--predictions` accepts JSONL or JSONL.GZ with one observation per line:

```json
{"frame": 17, "id": 4, "x": 120.5, "y": 83.0, "w": 14.0, "h": 9.0, "conf": 0.82, "class_id": 0}
```

- `frame` and `id` are integers.
- `x`, `y`, `w`, and `h` are axis-aligned boxes in native image pixels.
- `conf` is preserved but is not used by the REGR edge rule.
- `class_id` must be constant within a tracklet. Edges are same-class only.
- One identity may occur at most once in a frame.

## Descriptors

`--descriptors` accepts JSON or NPZ. Keys are tracklet IDs and values are
finite, L2-normalized feature vectors of one common dimension.

```json
{"4": [0.12, -0.04, 0.99]}
```

The paper uses 128-dimensional tracklet descriptors from a frozen OpenMMLab
MOT17 ResNet-50 BaseReID checkpoint. Up to the first, middle, and last direct
tracker-box crops are encoded, averaged, and normalized. Missing descriptors
make appearance-dependent edges inadmissible; they are not replaced by zero
vectors.

## Outputs

REGR changes only `id`. The frame, box, confidence, class, and observation
count are checked before a run is reported complete. Candidate distance is in
native pixels, appearance distance is cosine distance, and temporal distance
is in released frame-index units.
