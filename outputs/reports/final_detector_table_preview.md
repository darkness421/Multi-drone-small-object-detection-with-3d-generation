# Final Detector Table Preview

Updated: 2026-06-15T01:02:36+09:00

Reference baseline: YOLOv11l 3-seed mean, AP 0.3777 / AP50 0.5981 / F1 0.6248 / Params 25.32M.
This preview separates completed 1280 3-seed rows, the current 1280 sweep status, single-seed NMS snapshots, and 640 related-work eval rows.

## Main Paper Candidate: Completed 1280 3-Seed Rows

Only completed 1280-resolution 3-seed rows belong in the main detector comparison table. Rows marked as archived are valid completed rows, but they may be refreshed by the current expanded comparison sweep.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Ours final candidate | Ours: P2P4-SelfAttnFR | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3822 +/- 0.0007 | 0.6052 +/- 0.0012 | 0.6732 | 0.5872 | 0.6273 | 20.82 | 109.30 | +0.0045 | deduped latest official seed runs |
| 2 | Best YOLO baseline | YOLOv11l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3777 +/- 0.0004 | 0.5981 +/- 0.0011 | 0.6666 | 0.5881 | 0.6248 | 25.32 | 87.30 | +0.0000 | official comparison row |
| 3 | YOLO large | YOLOv12l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3771 +/- 0.0020 | 0.5958 +/- 0.0025 | 0.6698 | 0.5805 | 0.6219 | 26.40 | 89.40 | -0.0006 | official comparison row |
| 4 | YOLO large | YOLOv8l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3765 +/- 0.0003 | 0.5963 +/- 0.0008 | 0.6695 | 0.5770 | 0.6198 | 43.64 | 165.40 | -0.0011 | official comparison row |
| 5 | YOLO large | YOLOv26l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3732 +/- 0.0015 | 0.5877 +/- 0.0010 | 0.6602 | 0.5731 | 0.6136 | 26.19 | 93.20 | -0.0045 | official comparison row |
| 6 | YOLO large | YOLOv10l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3728 +/- 0.0019 | 0.5890 +/- 0.0020 | 0.6677 | 0.5729 | 0.6166 | 25.78 | 127.30 | -0.0049 | official comparison row |
| 7 | YOLO medium | YOLOv12m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3669 +/- 0.0009 | 0.5848 +/- 0.0033 | 0.6646 | 0.5694 | 0.6133 | 20.15 | 67.80 | -0.0108 | official comparison row |
| 8 | YOLO medium | YOLOv10m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3539 +/- 0.0020 | 0.5675 +/- 0.0028 | 0.6431 | 0.5573 | 0.5971 | 16.50 | 64.00 | -0.0237 | official comparison row |
| 9 | YOLO small | YOLOv9s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3433 +/- 0.0003 | 0.5544 +/- 0.0004 | 0.6362 | 0.5448 | 0.5869 | 7.29 | 27.40 | -0.0343 | official comparison row |
| 10 | YOLO small | YOLOv8s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3329 +/- 0.0030 | 0.5401 +/- 0.0035 | 0.6302 | 0.5318 | 0.5768 | 11.14 | 28.70 | -0.0448 | official comparison row |
| 11 | YOLO small | YOLOv12s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3322 +/- 0.0006 | 0.5386 +/- 0.0007 | 0.6341 | 0.5268 | 0.5755 | 9.26 | 21.50 | -0.0455 | official comparison row |
| 12 | YOLO small | YOLOv5su | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3279 +/- 0.0022 | 0.5331 +/- 0.0040 | 0.6261 | 0.5227 | 0.5697 | 9.13 | 24.10 | -0.0498 | official comparison row |
| 13 | YOLO small | YOLOv11s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3262 +/- 0.0010 | 0.5284 +/- 0.0019 | 0.6321 | 0.5162 | 0.5682 | 9.43 | 21.60 | -0.0515 | official comparison row |
| 14 | YOLO small | YOLOv10s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3248 +/- 0.0020 | 0.5260 +/- 0.0012 | 0.6239 | 0.5139 | 0.5635 | 8.07 | 24.80 | -0.0529 | official comparison row |
| 15 | YOLO small | YOLOv26s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3229 +/- 0.0013 | 0.5229 +/- 0.0025 | 0.6061 | 0.5120 | 0.5551 | 9.96 | 22.50 | -0.0548 | official comparison row |
| 16 | Transformer baseline | RT-DETR-L | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3201 +/- 0.0397 | 0.5355 +/- 0.0450 | 0.6189 | 0.5411 | 0.5773 | 32.83 | 108.00 | -0.0576 | official comparison row |
| 17 | YOLO nano | YOLOv9t | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3043 +/- 0.0018 | 0.4969 +/- 0.0032 | 0.5955 | 0.4905 | 0.5379 | 2.01 | 7.90 | -0.0733 | current 1280 comparison sweep, completed 3-seed |
| 18 | YOLO nano | YOLOv12n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2962 +/- 0.0017 | 0.4868 +/- 0.0020 | 0.5956 | 0.4790 | 0.5309 | 2.57 | 6.50 | -0.0815 | current 1280 comparison sweep, completed 3-seed |
| 19 | YOLO nano | YOLOv8n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2921 +/- 0.0007 | 0.4819 +/- 0.0009 | 0.5817 | 0.4771 | 0.5242 | 3.01 | 8.20 | -0.0856 | current 1280 comparison sweep, completed 3-seed |
| 20 | YOLO nano | YOLOv11n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2879 +/- 0.0015 | 0.4738 +/- 0.0022 | 0.5807 | 0.4703 | 0.5197 | 2.59 | 6.50 | -0.0897 | current 1280 comparison sweep, completed 3-seed |
| 21 | YOLO nano | YOLOv10n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2856 +/- 0.0022 | 0.4703 +/- 0.0039 | 0.5765 | 0.4671 | 0.5160 | 2.71 | 8.40 | -0.0920 | current 1280 comparison sweep, completed 3-seed |
| 22 | YOLO nano | YOLOv5nu | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2835 +/- 0.0006 | 0.4696 +/- 0.0015 | 0.5781 | 0.4597 | 0.5120 | 2.51 | 7.20 | -0.0942 | current 1280 comparison sweep, completed 3-seed |
| 23 | YOLO nano | YOLOv26n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2835 +/- 0.0019 | 0.4673 +/- 0.0027 | 0.5707 | 0.4715 | 0.5164 | 2.51 | 5.80 | -0.0942 | current 1280 comparison sweep, completed 3-seed |

## Current 1280 YOLO-Family Sweep Status

This section shows the newest 202606 comparison sweep. Partial rows are for monitoring only and should not be used as final paper rows until all three seeds complete.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | YOLO small | YOLOv5su | VisDrone val, 1280, partial 2/3 seeds | 123,42 | 0.3266 +/- 0.0022 | 0.5308 +/- 0.0033 | 0.6199 | 0.5231 | 0.5674 | 9.13 | 24.10 | -0.0511 | current 202606 sweep; partial 2/3 seeds; status=incomplete |
| 2 | YOLO nano | YOLOv9t | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.3043 +/- 0.0018 | 0.4969 +/- 0.0032 | 0.5955 | 0.4905 | 0.5379 | 2.01 | 7.90 | -0.0733 | current 202606 sweep; completed 3-seed; status=completed |
| 3 | YOLO nano | YOLOv12n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2962 +/- 0.0017 | 0.4868 +/- 0.0020 | 0.5956 | 0.4790 | 0.5309 | 2.57 | 6.50 | -0.0815 | current 202606 sweep; completed 3-seed; status=completed |
| 4 | YOLO nano | YOLOv8n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2921 +/- 0.0007 | 0.4819 +/- 0.0009 | 0.5817 | 0.4771 | 0.5242 | 3.01 | 8.20 | -0.0856 | current 202606 sweep; completed 3-seed; status=completed |
| 5 | YOLO nano | YOLOv11n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2879 +/- 0.0015 | 0.4738 +/- 0.0022 | 0.5807 | 0.4703 | 0.5197 | 2.59 | 6.50 | -0.0897 | current 202606 sweep; completed 3-seed; status=completed |
| 6 | YOLO nano | YOLOv10n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2856 +/- 0.0022 | 0.4703 +/- 0.0039 | 0.5765 | 0.4671 | 0.5160 | 2.71 | 8.40 | -0.0920 | current 202606 sweep; completed 3-seed; status=completed |
| 7 | YOLO nano | YOLOv5nu | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2835 +/- 0.0006 | 0.4696 +/- 0.0015 | 0.5781 | 0.4597 | 0.5120 | 2.51 | 7.20 | -0.0942 | current 202606 sweep; completed 3-seed; status=completed |
| 8 | YOLO nano | YOLOv26n | VisDrone val, 1280, completed 3-seed | 123,2026,42 | 0.2835 +/- 0.0019 | 0.4673 +/- 0.0027 | 0.5707 | 0.4715 | 0.5164 | 2.51 | 5.80 | -0.0942 | current 202606 sweep; completed 3-seed; status=completed |

## NMS/Postprocessing Snapshot

These rows are useful for the postprocessing/overlap discussion, but they are not yet 3-seed detector-training rows.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3856 | 0.6119 | 0.6626 | 0.6013 | 0.6305 | 24.41 | - | +0.0080 | single-seed eval, conf=0.001, iou=0.55, strict_pass=true |
| 2 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3849 | 0.6080 | 0.6690 | 0.5963 | 0.6306 | 24.41 | - | +0.0073 | single-seed eval, conf=0.001, iou=0.65, strict_pass=true |
| 3 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3849 | 0.6118 | 0.6611 | 0.6032 | 0.6308 | 24.41 | - | +0.0073 | single-seed eval, conf=0.001, iou=0.45, strict_pass=true |
| 4 | Postprocess/NMS snapshot | P2BalV2-FR-s42 + class-aware NMS | VisDrone val, 1280, eval only | 42 | 0.3839 | 0.6086 | 0.6626 | 0.6013 | 0.6305 | 24.41 | - | +0.0063 | single-seed eval, conf=0.01, iou=0.55, strict_pass=true |

## Related-Work Runnable Eval Snapshot

These rows currently use 640-eval settings and should be reported separately from the official 1280 training table unless retrained/evaluated under the same protocol.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Related-work runnable eval | CSFPR-RTDETR | VisDrone2019-DET val, 640-eval | - | 0.3279 | 0.5253 | 0.6336 | 0.5145 | 0.5679 | 14.09 | 63.90 | -0.0498 | Official/staged eval at 640; compare separately from our 1280 trained runs. |
| 2 | Related-work runnable eval | LEAF-YOLO-S | VisDrone2019-DET val, 640-eval | - | 0.2810 | 0.4820 | 0.5770 | 0.4850 | 0.5270 | 4.28 | 20.90 | -0.0967 | Official/staged LEAF eval at 640; compare separately from our 1280 trained runs. |
| 3 | Related-work runnable eval | LEAF-YOLO-N | VisDrone2019-DET val, 640-eval | - | 0.2190 | 0.3970 | 0.4800 | 0.4330 | 0.4553 | 1.20 | 5.60 | -0.1587 | Official/staged LEAF eval at 640; compare separately from our 1280 trained runs. |

## Active Queue Note

- YOLO-family nano sweep is complete in the current 202606 sweep.
- YOLO-family small sweep is currently running; medium and large sweeps are still queued.
- P2P4-SelfAttnFR is deduped by latest official seed run for seeds 42, 123, and 2026.
- 640-eval related-work rows are intentionally separated and should not be mixed into the main 1280 detector ranking.
