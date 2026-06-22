# Final Detector Table Preview

Updated: 2026-06-23T05:00:14+09:00

Reference baseline: YOLOv11l 3-seed mean, AP 0.3777 / AP50 0.5981 / F1 0.6248 / Params 25.32M.
This preview separates completed 1280 3-seed rows, the current 1280 sweep status, single-seed NMS snapshots, and related-work external eval rows.

## Main Paper Candidate: Completed 1280 3-Seed Rows

Only completed 1280-resolution 3-seed rows belong in the main detector comparison table. Rows marked as archived are valid completed rows, but they may be refreshed by the current expanded comparison sweep.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Ours final candidate | Ours: P2P4-SelfAttnFR | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3822 +/- 0.0007 | 0.6052 +/- 0.0012 | 0.6732 | 0.5872 | 0.6273 | 20.82 | 109.30 | +0.0045 | deduped latest official seed runs |
| 2 | Best YOLO baseline | YOLOv11l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3777 +/- 0.0004 | 0.5981 +/- 0.0011 | 0.6666 | 0.5881 | 0.6248 | 25.32 | 87.30 | +0.0000 | official comparison row |
| 3 | YOLO large | YOLOv12l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3771 +/- 0.0020 | 0.5958 +/- 0.0025 | 0.6698 | 0.5805 | 0.6219 | 26.40 | 89.40 | -0.0006 | official comparison row |
| 4 | YOLO large | YOLOv8l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3765 +/- 0.0003 | 0.5963 +/- 0.0008 | 0.6695 | 0.5770 | 0.6198 | 43.64 | 165.40 | -0.0011 | current 1280 comparison sweep, completed 3-seed |
| 5 | YOLO family | YOLOv9c | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3738 +/- 0.0009 | 0.5942 +/- 0.0020 | 0.6641 | 0.5831 | 0.6210 | 25.54 | 103.70 | -0.0039 | current 1280 comparison sweep, completed 3-seed |
| 6 | YOLO large | YOLOv26l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3732 +/- 0.0015 | 0.5877 +/- 0.0010 | 0.6602 | 0.5731 | 0.6136 | 26.19 | 93.20 | -0.0045 | official comparison row |
| 7 | YOLO large | YOLOv10l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3728 +/- 0.0019 | 0.5890 +/- 0.0020 | 0.6677 | 0.5729 | 0.6166 | 25.78 | 127.30 | -0.0049 | official comparison row |
| 8 | YOLO large | YOLOv5lu | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3709 +/- 0.0011 | 0.5897 +/- 0.0017 | 0.6614 | 0.5732 | 0.6141 | 53.17 | 135.30 | -0.0067 | current 1280 comparison sweep, completed 3-seed |
| 9 | YOLO medium | YOLOv9m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3700 +/- 0.0003 | 0.5910 +/- 0.0012 | 0.6708 | 0.5749 | 0.6192 | 20.17 | 77.60 | -0.0077 | current 1280 comparison sweep, completed 3-seed |
| 10 | YOLO medium | YOLOv12m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3668 +/- 0.0008 | 0.5851 +/- 0.0029 | 0.6638 | 0.5663 | 0.6112 | 20.15 | 67.80 | -0.0109 | current 1280 comparison sweep, completed 3-seed |
| 11 | YOLO medium | YOLOv11m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3657 +/- 0.0005 | 0.5846 +/- 0.0012 | 0.6612 | 0.5728 | 0.6138 | 20.06 | 68.20 | -0.0119 | current 1280 comparison sweep, completed 3-seed |
| 12 | YOLO medium | YOLOv26m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3651 +/- 0.0007 | 0.5801 +/- 0.0005 | 0.6525 | 0.5668 | 0.6066 | 21.79 | 74.80 | -0.0126 | current 1280 comparison sweep, completed 3-seed |
| 13 | YOLO medium | YOLOv8m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3609 +/- 0.0017 | 0.5771 +/- 0.0012 | 0.6593 | 0.5622 | 0.6068 | 25.86 | 79.10 | -0.0168 | current 1280 comparison sweep, completed 3-seed |
| 14 | YOLO medium | YOLOv10m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3546 +/- 0.0006 | 0.5674 +/- 0.0016 | 0.6461 | 0.5530 | 0.5959 | 16.50 | 64.00 | -0.0230 | current 1280 comparison sweep, completed 3-seed |
| 15 | YOLO medium | YOLOv5mu | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3546 +/- 0.0009 | 0.5673 +/- 0.0012 | 0.6564 | 0.5506 | 0.5988 | 25.07 | 64.40 | -0.0230 | current 1280 comparison sweep, completed 3-seed |
| 16 | YOLO small | YOLOv9s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3454 +/- 0.0009 | 0.5573 +/- 0.0011 | 0.6459 | 0.5406 | 0.5886 | 7.29 | 27.40 | -0.0323 | current 1280 comparison sweep, completed 3-seed |
| 17 | YOLO small | YOLOv12s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3338 +/- 0.0015 | 0.5406 +/- 0.0028 | 0.6391 | 0.5253 | 0.5766 | 9.26 | 21.50 | -0.0439 | current 1280 comparison sweep, completed 3-seed |
| 18 | YOLO small | YOLOv8s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3336 +/- 0.0007 | 0.5413 +/- 0.0006 | 0.6335 | 0.5302 | 0.5772 | 11.14 | 28.70 | -0.0440 | current 1280 comparison sweep, completed 3-seed |
| 19 | YOLO small | YOLOv5su | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3300 +/- 0.0024 | 0.5363 +/- 0.0025 | 0.6297 | 0.5236 | 0.5718 | 9.13 | 24.10 | -0.0476 | current 1280 comparison sweep, completed 3-seed |
| 20 | YOLO small | YOLOv11s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3276 +/- 0.0010 | 0.5304 +/- 0.0018 | 0.6295 | 0.5199 | 0.5695 | 9.43 | 21.60 | -0.0500 | current 1280 comparison sweep, completed 3-seed |
| 21 | YOLO small | YOLOv26s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3254 +/- 0.0008 | 0.5263 +/- 0.0001 | 0.6157 | 0.5197 | 0.5636 | 9.96 | 22.50 | -0.0522 | current 1280 comparison sweep, completed 3-seed |
| 22 | YOLO small | YOLOv10s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3247 +/- 0.0018 | 0.5261 +/- 0.0033 | 0.6250 | 0.5160 | 0.5653 | 8.07 | 24.80 | -0.0530 | current 1280 comparison sweep, completed 3-seed |
| 23 | Transformer baseline | RT-DETR-L | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3201 +/- 0.0397 | 0.5355 +/- 0.0450 | 0.6189 | 0.5411 | 0.5773 | 32.83 | 108.00 | -0.0576 | official comparison row |
| 24 | YOLO nano | YOLOv9t | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3043 +/- 0.0018 | 0.4969 +/- 0.0032 | 0.5955 | 0.4905 | 0.5379 | 2.01 | 7.90 | -0.0733 | current 1280 comparison sweep, completed 3-seed |
| 25 | YOLO nano | YOLOv12n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2962 +/- 0.0017 | 0.4868 +/- 0.0020 | 0.5956 | 0.4790 | 0.5309 | 2.57 | 6.50 | -0.0815 | current 1280 comparison sweep, completed 3-seed |
| 26 | YOLO nano | YOLOv8n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2921 +/- 0.0007 | 0.4819 +/- 0.0009 | 0.5817 | 0.4771 | 0.5242 | 3.01 | 8.20 | -0.0856 | current 1280 comparison sweep, completed 3-seed |
| 27 | YOLO nano | YOLOv11n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2879 +/- 0.0015 | 0.4738 +/- 0.0022 | 0.5807 | 0.4703 | 0.5197 | 2.59 | 6.50 | -0.0897 | current 1280 comparison sweep, completed 3-seed |
| 28 | YOLO nano | YOLOv10n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2856 +/- 0.0022 | 0.4703 +/- 0.0039 | 0.5765 | 0.4671 | 0.5160 | 2.71 | 8.40 | -0.0920 | current 1280 comparison sweep, completed 3-seed |
| 29 | YOLO nano | YOLOv5nu | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2835 +/- 0.0006 | 0.4696 +/- 0.0015 | 0.5781 | 0.4597 | 0.5120 | 2.51 | 7.20 | -0.0942 | current 1280 comparison sweep, completed 3-seed |
| 30 | YOLO nano | YOLOv26n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2835 +/- 0.0019 | 0.4673 +/- 0.0027 | 0.5707 | 0.4715 | 0.5164 | 2.51 | 5.80 | -0.0942 | current 1280 comparison sweep, completed 3-seed |

## Current 1280 YOLO-Family Sweep Status

This section shows the newest 202606 comparison sweep. Partial rows are for monitoring only and should not be used as final paper rows until all three seeds complete.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | YOLO large | YOLOv8l | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3765 +/- 0.0003 | 0.5963 +/- 0.0008 | 0.6695 | 0.5770 | 0.6198 | 43.64 | 165.40 | -0.0011 | current 202606 sweep; completed 3-seed; status=completed |
| 2 | YOLO family | YOLOv9c | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3738 +/- 0.0009 | 0.5942 +/- 0.0020 | 0.6641 | 0.5831 | 0.6210 | 25.54 | 103.70 | -0.0039 | current 202606 sweep; completed 3-seed; status=completed |
| 3 | YOLO large | YOLOv5lu | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3709 +/- 0.0011 | 0.5897 +/- 0.0017 | 0.6614 | 0.5732 | 0.6141 | 53.17 | 135.30 | -0.0067 | current 202606 sweep; completed 3-seed; status=completed |
| 4 | YOLO medium | YOLOv9m | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3700 +/- 0.0003 | 0.5910 +/- 0.0012 | 0.6708 | 0.5749 | 0.6192 | 20.17 | 77.60 | -0.0077 | current 202606 sweep; completed 3-seed; status=completed |
| 5 | YOLO medium | YOLOv12m | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3668 +/- 0.0008 | 0.5851 +/- 0.0029 | 0.6638 | 0.5663 | 0.6112 | 20.15 | 67.80 | -0.0109 | current 202606 sweep; completed 3-seed; status=completed |
| 6 | YOLO medium | YOLOv11m | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3657 +/- 0.0005 | 0.5846 +/- 0.0012 | 0.6612 | 0.5728 | 0.6138 | 20.06 | 68.20 | -0.0119 | current 202606 sweep; completed 3-seed; status=completed |
| 7 | YOLO medium | YOLOv26m | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3651 +/- 0.0007 | 0.5801 +/- 0.0005 | 0.6525 | 0.5668 | 0.6066 | 21.79 | 74.80 | -0.0126 | current 202606 sweep; completed 3-seed; status=completed |
| 8 | YOLO medium | YOLOv8m | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3609 +/- 0.0017 | 0.5771 +/- 0.0012 | 0.6593 | 0.5622 | 0.6068 | 25.86 | 79.10 | -0.0168 | current 202606 sweep; completed 3-seed; status=completed |
| 9 | YOLO medium | YOLOv10m | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3546 +/- 0.0006 | 0.5674 +/- 0.0016 | 0.6461 | 0.5530 | 0.5959 | 16.50 | 64.00 | -0.0230 | current 202606 sweep; completed 3-seed; status=completed |
| 10 | YOLO medium | YOLOv5mu | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3546 +/- 0.0009 | 0.5673 +/- 0.0012 | 0.6564 | 0.5506 | 0.5988 | 25.07 | 64.40 | -0.0230 | current 202606 sweep; completed 3-seed; status=completed |
| 11 | YOLO small | YOLOv9s | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3454 +/- 0.0009 | 0.5573 +/- 0.0011 | 0.6459 | 0.5406 | 0.5886 | 7.29 | 27.40 | -0.0323 | current 202606 sweep; completed 3-seed; status=completed |
| 12 | YOLO small | YOLOv12s | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3338 +/- 0.0015 | 0.5406 +/- 0.0028 | 0.6391 | 0.5253 | 0.5766 | 9.26 | 21.50 | -0.0439 | current 202606 sweep; completed 3-seed; status=completed |
| 13 | YOLO small | YOLOv8s | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3336 +/- 0.0007 | 0.5413 +/- 0.0006 | 0.6335 | 0.5302 | 0.5772 | 11.14 | 28.70 | -0.0440 | current 202606 sweep; completed 3-seed; status=completed |
| 14 | YOLO small | YOLOv5su | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3300 +/- 0.0024 | 0.5363 +/- 0.0025 | 0.6297 | 0.5236 | 0.5718 | 9.13 | 24.10 | -0.0476 | current 202606 sweep; completed 3-seed; status=completed |
| 15 | YOLO small | YOLOv11s | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3276 +/- 0.0010 | 0.5304 +/- 0.0018 | 0.6295 | 0.5199 | 0.5695 | 9.43 | 21.60 | -0.0500 | current 202606 sweep; completed 3-seed; status=completed |
| 16 | YOLO small | YOLOv26s | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3254 +/- 0.0008 | 0.5263 +/- 0.0001 | 0.6157 | 0.5197 | 0.5636 | 9.96 | 22.50 | -0.0522 | current 202606 sweep; completed 3-seed; status=completed |
| 17 | YOLO small | YOLOv10s | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3247 +/- 0.0018 | 0.5261 +/- 0.0033 | 0.6250 | 0.5160 | 0.5653 | 8.07 | 24.80 | -0.0530 | current 202606 sweep; completed 3-seed; status=completed |
| 18 | YOLO nano | YOLOv9t | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3043 +/- 0.0018 | 0.4969 +/- 0.0032 | 0.5955 | 0.4905 | 0.5379 | 2.01 | 7.90 | -0.0733 | current 202606 sweep; completed 3-seed; status=completed |
| 19 | YOLO nano | YOLOv12n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2962 +/- 0.0017 | 0.4868 +/- 0.0020 | 0.5956 | 0.4790 | 0.5309 | 2.57 | 6.50 | -0.0815 | current 202606 sweep; completed 3-seed; status=completed |
| 20 | YOLO nano | YOLOv8n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2921 +/- 0.0007 | 0.4819 +/- 0.0009 | 0.5817 | 0.4771 | 0.5242 | 3.01 | 8.20 | -0.0856 | current 202606 sweep; completed 3-seed; status=completed |
| 21 | YOLO nano | YOLOv11n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2879 +/- 0.0015 | 0.4738 +/- 0.0022 | 0.5807 | 0.4703 | 0.5197 | 2.59 | 6.50 | -0.0897 | current 202606 sweep; completed 3-seed; status=completed |
| 22 | YOLO nano | YOLOv10n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2856 +/- 0.0022 | 0.4703 +/- 0.0039 | 0.5765 | 0.4671 | 0.5160 | 2.71 | 8.40 | -0.0920 | current 202606 sweep; completed 3-seed; status=completed |
| 23 | YOLO nano | YOLOv5nu | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2835 +/- 0.0006 | 0.4696 +/- 0.0015 | 0.5781 | 0.4597 | 0.5120 | 2.51 | 7.20 | -0.0942 | current 202606 sweep; completed 3-seed; status=completed |
| 24 | YOLO nano | YOLOv26n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2835 +/- 0.0019 | 0.4673 +/- 0.0027 | 0.5707 | 0.4715 | 0.5164 | 2.51 | 5.80 | -0.0942 | current 202606 sweep; completed 3-seed; status=completed |

## NMS/Postprocessing Snapshot

These rows are useful for the postprocessing/overlap discussion, but they are not yet 3-seed detector-training rows.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3856 | 0.6119 | 0.6626 | 0.6013 | 0.6305 | 24.41 | - | +0.0080 | single-seed eval, conf=0.001, iou=0.55, strict_pass=true |
| 2 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3849 | 0.6080 | 0.6690 | 0.5963 | 0.6306 | 24.41 | - | +0.0073 | single-seed eval, conf=0.001, iou=0.65, strict_pass=true |
| 3 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3849 | 0.6118 | 0.6611 | 0.6032 | 0.6308 | 24.41 | - | +0.0073 | single-seed eval, conf=0.001, iou=0.45, strict_pass=true |
| 4 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3839 | 0.6086 | 0.6626 | 0.6013 | 0.6305 | 24.41 | - | +0.0063 | single-seed eval, conf=0.01, iou=0.55, strict_pass=true |

## Related-Work Runnable Eval Snapshot

These rows are external eval-only checkpoints and should be reported separately from the official 1280 3-seed training table unless retrained/evaluated under the same protocol.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Related-work runnable eval | LEAF-YOLO-S | VisDrone2019-DET val, 1280-eval | - | 0.3080 | 0.5210 | 0.5910 | 0.5330 | 0.5605 | 4.28 | 20.90 | -0.0697 | Staged LEAF eval at 1280; external eval-only checkpoint, not our 3-seed training protocol. |
| 2 | Related-work runnable eval | LEAF-YOLO-S | VisDrone2019-DET val, 640-eval | - | 0.2810 | 0.4820 | 0.5770 | 0.4850 | 0.5270 | 4.28 | 20.90 | -0.0967 | Staged LEAF eval at 640; compare separately from our strict 1280 trained runs. |
| 3 | Related-work runnable eval | LEAF-YOLO-N | VisDrone2019-DET val, 1280-eval | - | 0.2510 | 0.4430 | 0.5240 | 0.4610 | 0.4905 | 1.20 | 5.60 | -0.1267 | Staged LEAF eval at 1280; external eval-only checkpoint, not our 3-seed training protocol. |
| 4 | Related-work runnable eval | LEAF-YOLO-N | VisDrone2019-DET val, 640-eval | - | 0.2190 | 0.3970 | 0.4800 | 0.4330 | 0.4553 | 1.20 | 5.60 | -0.1587 | Staged LEAF eval at 640; compare separately from our strict 1280 trained runs. |
| 5 | Related-work runnable eval | CSFPR-RTDETR | VisDrone2019-DET val, 1280-eval | - | 0.0420 | 0.1482 | 0.2805 | 0.1661 | 0.2086 | 14.09 | 63.90 | -0.3357 | Staged CSFPR checkpoint evaluated at 1280; keep separate from trained 3-seed rows because this is an external eval-only checkpoint. |

## Active Queue Note

- YOLO-family nano sweep is complete in the current 202606 sweep.
- YOLO-family small sweep is currently running; medium and large sweeps are still queued.
- P2P4-SelfAttnFR is deduped by latest official seed run for seeds 42, 123, and 2026.
- External related-work eval rows are intentionally separated and should not be mixed into the main 1280 detector ranking.
