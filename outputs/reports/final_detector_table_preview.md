# Final Detector Table Preview

Updated: 2026-06-26T06:05:08+09:00

Reference baseline: YOLOv11l 3-seed mean, AP 0.3777 / AP50 0.5981 / F1 0.6248 / Params 25.32M.
This preview separates completed 1280 3-seed rows, the current 1280 sweep status, single-seed NMS snapshots, and cited related-work rows.

## Main Paper Candidate: Completed 1280 3-Seed Rows

Only completed 1280-resolution 3-seed rows belong in the main detector comparison table. Rows marked as archived are valid completed rows, but they may be refreshed by the current expanded comparison sweep.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Ours final candidate | Ours: P2P4-SelfAttnFR | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3822 +/- 0.0007 | 0.6052 +/- 0.0012 | 0.6732 | 0.5872 | 0.6273 | 20.82 | 109.30 | +0.0045 | deduped latest official seed runs |
| 2 | Cited related work | UAVDet [16] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3812 +/- 0.0013 | 0.6005 +/- 0.0036 | 0.6542 | 0.5899 | 0.6203 | 33.55 | 201.20 | +0.0035 | inspired reproduction from cited UAVDet design; not official checkpoint; 1280, 3-seed |
| 3 | Cited related work | BPD-YOLO [7] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3804 +/- 0.0035 | 0.5986 +/- 0.0027 | 0.6626 | 0.5802 | 0.6187 | 24.53 | 109.50 | +0.0028 | paper-faithful reimplementation; not official checkpoint; 1280, 3-seed |
| 4 | Best YOLO baseline | YOLOv11l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3777 +/- 0.0004 | 0.5981 +/- 0.0011 | 0.6666 | 0.5881 | 0.6248 | 25.32 | 87.30 | +0.0000 | official comparison row |
| 5 | YOLO large | YOLOv12l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3771 +/- 0.0020 | 0.5958 +/- 0.0025 | 0.6698 | 0.5805 | 0.6219 | 26.40 | 89.40 | -0.0006 | official comparison row |
| 6 | YOLO large | YOLOv8l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3765 +/- 0.0003 | 0.5963 +/- 0.0008 | 0.6695 | 0.5770 | 0.6198 | 43.64 | 165.40 | -0.0011 | current 1280 comparison sweep, completed 3-seed |
| 7 | Cited related work | SFFEF-YOLO [4] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3749 +/- 0.0040 | 0.5914 +/- 0.0039 | 0.6540 | 0.5781 | 0.6137 | 20.87 | 108.70 | -0.0027 | paper-faithful reimplementation; not official checkpoint; 1280, 3-seed |
| 8 | YOLO family | YOLOv9c | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3738 +/- 0.0009 | 0.5942 +/- 0.0020 | 0.6641 | 0.5831 | 0.6210 | 25.54 | 103.70 | -0.0039 | current 1280 comparison sweep, completed 3-seed |
| 9 | YOLO large | YOLOv26l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3732 +/- 0.0015 | 0.5877 +/- 0.0010 | 0.6602 | 0.5731 | 0.6136 | 26.19 | 93.20 | -0.0045 | official comparison row |
| 10 | YOLO large | YOLOv10l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3728 +/- 0.0019 | 0.5890 +/- 0.0020 | 0.6677 | 0.5729 | 0.6166 | 25.78 | 127.30 | -0.0049 | official comparison row |
| 11 | YOLO large | YOLOv5lu | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3709 +/- 0.0011 | 0.5897 +/- 0.0017 | 0.6614 | 0.5732 | 0.6141 | 53.17 | 135.30 | -0.0067 | current 1280 comparison sweep, completed 3-seed |
| 12 | YOLO medium | YOLOv9m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3700 +/- 0.0003 | 0.5910 +/- 0.0012 | 0.6708 | 0.5749 | 0.6192 | 20.17 | 77.60 | -0.0077 | current 1280 comparison sweep, completed 3-seed |
| 13 | YOLO medium | YOLOv12m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3668 +/- 0.0008 | 0.5851 +/- 0.0029 | 0.6638 | 0.5663 | 0.6112 | 20.15 | 67.80 | -0.0109 | current 1280 comparison sweep, completed 3-seed |
| 14 | YOLO medium | YOLOv11m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3657 +/- 0.0005 | 0.5846 +/- 0.0012 | 0.6612 | 0.5728 | 0.6138 | 20.06 | 68.20 | -0.0119 | current 1280 comparison sweep, completed 3-seed |
| 15 | YOLO medium | YOLOv26m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3651 +/- 0.0007 | 0.5801 +/- 0.0005 | 0.6525 | 0.5668 | 0.6066 | 21.79 | 74.80 | -0.0126 | current 1280 comparison sweep, completed 3-seed |
| 16 | Cited related work | HF-D-FINE [12] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3619 +/- 0.0129 | 0.5764 +/- 0.0186 | 0.6685 | 0.5555 | 0.6067 | 25.48 | 87.30 | -0.0158 | high-resolution/frequency-detail reproduction; not official D-FINE checkpoint; 1280, 3-seed |
| 17 | YOLO medium | YOLOv8m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3609 +/- 0.0017 | 0.5771 +/- 0.0012 | 0.6593 | 0.5622 | 0.6068 | 25.86 | 79.10 | -0.0168 | current 1280 comparison sweep, completed 3-seed |
| 18 | YOLO medium | YOLOv10m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3546 +/- 0.0006 | 0.5674 +/- 0.0016 | 0.6461 | 0.5530 | 0.5959 | 16.50 | 64.00 | -0.0230 | current 1280 comparison sweep, completed 3-seed |
| 19 | YOLO medium | YOLOv5mu | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3546 +/- 0.0009 | 0.5673 +/- 0.0012 | 0.6564 | 0.5506 | 0.5988 | 25.07 | 64.40 | -0.0230 | current 1280 comparison sweep, completed 3-seed |
| 20 | YOLO small | YOLOv9s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3454 +/- 0.0009 | 0.5573 +/- 0.0011 | 0.6459 | 0.5406 | 0.5886 | 7.29 | 27.40 | -0.0323 | current 1280 comparison sweep, completed 3-seed |
| 21 | YOLO small | YOLOv12s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3338 +/- 0.0015 | 0.5406 +/- 0.0028 | 0.6391 | 0.5253 | 0.5766 | 9.26 | 21.50 | -0.0439 | current 1280 comparison sweep, completed 3-seed |
| 22 | YOLO small | YOLOv8s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3336 +/- 0.0007 | 0.5413 +/- 0.0006 | 0.6335 | 0.5302 | 0.5772 | 11.14 | 28.70 | -0.0440 | current 1280 comparison sweep, completed 3-seed |
| 23 | YOLO small | YOLOv5su | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3300 +/- 0.0024 | 0.5363 +/- 0.0025 | 0.6297 | 0.5236 | 0.5718 | 9.13 | 24.10 | -0.0476 | current 1280 comparison sweep, completed 3-seed |
| 24 | YOLO small | YOLOv11s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3276 +/- 0.0010 | 0.5304 +/- 0.0018 | 0.6295 | 0.5199 | 0.5695 | 9.43 | 21.60 | -0.0500 | current 1280 comparison sweep, completed 3-seed |
| 25 | YOLO small | YOLOv26s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3254 +/- 0.0008 | 0.5263 +/- 0.0001 | 0.6157 | 0.5197 | 0.5636 | 9.96 | 22.50 | -0.0522 | current 1280 comparison sweep, completed 3-seed |
| 26 | YOLO small | YOLOv10s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3247 +/- 0.0018 | 0.5261 +/- 0.0033 | 0.6250 | 0.5160 | 0.5653 | 8.07 | 24.80 | -0.0530 | current 1280 comparison sweep, completed 3-seed |
| 27 | Transformer baseline | RT-DETR-L | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3201 +/- 0.0397 | 0.5355 +/- 0.0450 | 0.6189 | 0.5411 | 0.5773 | 32.83 | 108.00 | -0.0576 | official comparison row |
| 28 | YOLO nano | YOLOv9t | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3043 +/- 0.0018 | 0.4969 +/- 0.0032 | 0.5955 | 0.4905 | 0.5379 | 2.01 | 7.90 | -0.0733 | current 1280 comparison sweep, completed 3-seed |
| 29 | YOLO nano | YOLOv12n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2962 +/- 0.0017 | 0.4868 +/- 0.0020 | 0.5956 | 0.4790 | 0.5309 | 2.57 | 6.50 | -0.0815 | current 1280 comparison sweep, completed 3-seed |
| 30 | YOLO nano | YOLOv8n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2921 +/- 0.0007 | 0.4819 +/- 0.0009 | 0.5817 | 0.4771 | 0.5242 | 3.01 | 8.20 | -0.0856 | current 1280 comparison sweep, completed 3-seed |
| 31 | YOLO nano | YOLOv11n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2879 +/- 0.0015 | 0.4738 +/- 0.0022 | 0.5807 | 0.4703 | 0.5197 | 2.59 | 6.50 | -0.0897 | current 1280 comparison sweep, completed 3-seed |
| 32 | YOLO nano | YOLOv10n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2856 +/- 0.0022 | 0.4703 +/- 0.0039 | 0.5765 | 0.4671 | 0.5160 | 2.71 | 8.40 | -0.0920 | current 1280 comparison sweep, completed 3-seed |
| 33 | YOLO nano | YOLOv5nu | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2835 +/- 0.0006 | 0.4696 +/- 0.0015 | 0.5781 | 0.4597 | 0.5120 | 2.51 | 7.20 | -0.0942 | current 1280 comparison sweep, completed 3-seed |
| 34 | YOLO nano | YOLOv26n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2835 +/- 0.0019 | 0.4673 +/- 0.0027 | 0.5707 | 0.4715 | 0.5164 | 2.51 | 5.80 | -0.0942 | current 1280 comparison sweep, completed 3-seed |
| 35 | Cited related work | CSFPR-RTDETR [11] | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2784 +/- 0.0070 | 0.4431 +/- 0.0094 | 0.5766 | 0.4292 | 0.4921 | 14.09 | 63.90 | -0.0993 | official/staged 1280 3-seed related-work run |
| 36 | Cited related work | MFFSODNet [2] | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.0975 +/- 0.0034 | 0.1830 +/- 0.0070 | 0.6418 | 0.2465 | 0.3562 | 4.54 | 55.10 | -0.2802 | official code scratch retrain; no pretrained checkpoint found |

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

## Cited Related-Work Snapshot

Strict 1280 three-seed related-work runs can be considered for the paper comparison table. External eval-only rows remain separate and must keep their protocol note.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Cited related work | UAVDet [16] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3812 +/- 0.0013 | 0.6005 +/- 0.0036 | 0.6542 | 0.5899 | 0.6203 | 33.55 | 201.20 | +0.0035 | inspired reproduction from cited UAVDet design; not official checkpoint; 1280, 3-seed |
| 2 | Cited related work | BPD-YOLO [7] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3804 +/- 0.0035 | 0.5986 +/- 0.0027 | 0.6626 | 0.5802 | 0.6187 | 24.53 | 109.50 | +0.0028 | paper-faithful reimplementation; not official checkpoint; 1280, 3-seed |
| 3 | Cited related work | SFFEF-YOLO [4] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3749 +/- 0.0040 | 0.5914 +/- 0.0039 | 0.6540 | 0.5781 | 0.6137 | 20.87 | 108.70 | -0.0027 | paper-faithful reimplementation; not official checkpoint; 1280, 3-seed |
| 4 | Cited related work | HF-D-FINE [12] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3619 +/- 0.0129 | 0.5764 +/- 0.0186 | 0.6685 | 0.5555 | 0.6067 | 25.48 | 87.30 | -0.0158 | high-resolution/frequency-detail reproduction; not official D-FINE checkpoint; 1280, 3-seed |
| 5 | Cited related work | CSFPR-RTDETR [11] | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2784 +/- 0.0070 | 0.4431 +/- 0.0094 | 0.5766 | 0.4292 | 0.4921 | 14.09 | 63.90 | -0.0993 | official/staged 1280 3-seed related-work run |
| 6 | Cited related work | MFFSODNet [2] | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.0975 +/- 0.0034 | 0.1830 +/- 0.0070 | 0.6418 | 0.2465 | 0.3562 | 4.54 | 55.10 | -0.2802 | official code scratch retrain; no pretrained checkpoint found |

## Active Queue Note

- YOLO-family nano/small/medium/large sweep rows in this preview are completed 1280-resolution three-seed rows.
- Cited related-work rows with compatible staged runs are completed or explicitly marked with their reproduction/adapter caveat.
- P2P4-SelfAttnFR is deduped by latest official seed run for seeds 42, 123, and 2026.
- External related-work eval-only rows are intentionally separated; strict 1280 3-seed related-work rows are tracked with protocol notes.
