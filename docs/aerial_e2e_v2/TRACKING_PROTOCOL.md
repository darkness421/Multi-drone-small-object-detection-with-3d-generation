# Tracking Protocol

## B1 frozen tracker

- Tracker: BoxMOT Deep OC-SORT.
- Detector confidence entering the MMOT detector cache: 0.1.
- Detector NMS IoU: 0.6.
- Detector image size: 1280.
- ReID: precomputed BaseReID ResNet-50 features.
- Deep OC-SORT defaults: detection threshold 0.5, max age 30, minimum hits 3,
  IoU threshold 0.3, delta-t 3, inertia 0.2, embedding weight 0.75,
  fixed-embedding alpha 0.95, adaptive weight 0.5; embedding and CMC enabled.
- Class handling: one independent tracker/evaluator block per official class,
  with disjoint identity namespaces during combined evaluation.
- Frame sampling: every released frame, numeric frame stem preserved.

## State boundary

The historical B1 adapter passes AABB envelopes to Deep OC-SORT. Its Kalman
state is therefore the pinned BoxMOT AABB state, not an oriented state. OBB
orientation is available at detection time but not consumed by the tracker.

## Metrics

TrackEval produces HOTA, DetA, AssA, IDF1, MOTA, IDSW, and Frag. The reported
50-sequence summaries use equal-sequence means for scalar metrics and total
counts for IDSW/Frag/TP/FP/FN. Per-sequence rows remain the primary audit unit.

## B0 lock required before execution

Before a SAFR-YOLO + Deep OC-SORT benchmark is run, freeze:

1. target dataset and split,
2. VisDrone-to-target class mapping,
3. detector confidence and NMS IoU,
4. AABB versus OBB adapter behavior,
5. ReID checkpoint and crop source,
6. tracker YAML and class isolation,
7. evaluator and ignored-region handling.

No current result satisfies all seven items, so B0 remains unavailable rather
than being inferred from separate detector and tracker tables.
