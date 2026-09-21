# Baseline Results

## B0 detector-only evidence

The completed VisDrone validation result is not an end-to-end tracking result.

| Model | AP50-95 | AP50 | Precision | Recall | F1 | Params | GFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SAFR-YOLO, 3-seed mean | 0.3822 | 0.6052 | 0.6732 | 0.5872 | 0.6273 | 20.82M | 109.30 |

AP_small was not stored in the final compact table and must not be invented.
VisDrone does not supply the required identity labels, so tracking metrics are
not applicable. B0 remains incomplete pending a locked MOT protocol and GPU.

## B1 cache-replayed MMOT result

Input is the official OBB detector cache, converted to AABB envelopes for
standard Deep OC-SORT. These are the no-refinement rows from the exact
50-sequence replay.

| HOTA | DetA | AssA | IDF1 | MOTA | IDSW | Frag | Sequences |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 53.9198 | 45.1068 | 67.0043 | 63.0852 | 49.7763 | 1,370 | 4,881 | 50 |

Counts: 196,194 valid GT boxes, 135,798 predicted boxes, 123,517 TP,
12,281 FP, and 72,677 FN. Aggregation is equal-sequence mean for metrics and
total counts for events. The replay reproduced the frozen source exactly.

Detection AP/OBB mAP cannot be recomputed from the currently retained assets:
the checkpoint and full detector prediction cache are absent. The tracking
result is valid, but it must not be presented as a newly rerun detector result.

## B2

B2 has no scientific accuracy result yet. `tools/run_aerial_e2e_b2_smoke.py`
checks model shapes, a finite joint loss, one optimizer step, registry writing,
and per-sequence provenance on two real MMOT frames. Attempt 02 passed with 40
positive grid cells and a loss change from 3.753854 to 3.436416. The CPU timing
from this two-frame run includes the train step and is not a detector/tracker
latency benchmark. See `B2_SMOKE_TEST_REPORT.md` for the exact scope and paths.

## Baseline gate

- B0: not reproduced end to end; compatible MOT inputs and a working GPU are
  required.
- B1: tracking-cache replay is validated; fresh detector metrics remain blocked
  by the missing official checkpoint and raw detector prediction cache.
- B2: implementation and logging smoke passed; detection and tracking accuracy
  remain unmeasured.

V2-01 must not start until the unavailable B0/B1 assets and GPU gate are
resolved, or the protocol is explicitly revised with a documented substitute.
