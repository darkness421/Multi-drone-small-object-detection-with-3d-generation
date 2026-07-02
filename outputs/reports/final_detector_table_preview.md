# Final Detector Table Preview

Updated: 2026-06-28T03:57:11+09:00

Reference baseline: YOLOv11l 3-seed mean, AP 0.3777 / AP50 0.5981 / F1 0.6248 / Params 25.32M.
This preview separates completed 1280 3-seed rows, the current 1280 sweep status, single-seed NMS snapshots, and cited related-work rows.

## Main Paper Candidate: Completed 1280 3-Seed Rows

Only completed 1280-resolution 3-seed rows belong in the main detector comparison table. Rows marked as archived are valid completed rows, but they may be refreshed by the current expanded comparison sweep.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Ours final candidate | Ours | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3822 +/- 0.0007 | 0.6052 +/- 0.0012 | 0.6732 | 0.5872 | 0.6273 | 20.82 | 109.30 | +0.0045 | SAFR-YOLO/P2P4-SelfAttnFR implementation; deduped latest official seed runs |
| 2 | Cited related work | UAVDet [16] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3812 +/- 0.0013 | 0.6005 +/- 0.0036 | 0.6542 | 0.5899 | 0.6203 | 33.55 | 201.20 | +0.0035 | inspired reproduction from cited UAVDet design; not official checkpoint; 1280, 3-seed |
| 3 | Cited related work | BPD-YOLO [7] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3804 +/- 0.0035 | 0.5986 +/- 0.0027 | 0.6626 | 0.5802 | 0.6187 | 24.53 | 109.50 | +0.0028 | paper-faithful reimplementation; not official checkpoint; 1280, 3-seed |
| 4 | Best YOLO baseline | YOLOv11l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3777 +/- 0.0004 | 0.5981 +/- 0.0011 | 0.6666 | 0.5881 | 0.6248 | 25.32 | 87.30 | +0.0000 | official comparison row |
| 5 | YOLO large | YOLOv12l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3771 +/- 0.0020 | 0.5958 +/- 0.0025 | 0.6698 | 0.5805 | 0.6219 | 26.40 | 89.40 | -0.0006 | official comparison row |
| 6 | YOLO large | YOLOv8l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3765 +/- 0.0003 | 0.5963 +/- 0.0008 | 0.6695 | 0.5770 | 0.6198 | 43.64 | 165.40 | -0.0011 | official comparison row |
| 7 | Cited related work | SFFEF-YOLO [4] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3749 +/- 0.0040 | 0.5914 +/- 0.0039 | 0.6540 | 0.5781 | 0.6137 | 20.87 | 108.70 | -0.0027 | paper-faithful reimplementation; not official checkpoint; 1280, 3-seed |
| 8 | YOLO large | YOLOv26l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3732 +/- 0.0015 | 0.5877 +/- 0.0010 | 0.6602 | 0.5731 | 0.6136 | 26.19 | 93.20 | -0.0045 | official comparison row |
| 9 | YOLO large | YOLOv10l | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3728 +/- 0.0019 | 0.5890 +/- 0.0020 | 0.6677 | 0.5729 | 0.6166 | 25.78 | 127.30 | -0.0049 | official comparison row |
| 10 | YOLO medium | YOLOv12m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3669 +/- 0.0009 | 0.5848 +/- 0.0033 | 0.6646 | 0.5694 | 0.6133 | 20.15 | 67.80 | -0.0108 | official comparison row |
| 11 | Cited related work | HF-D-FINE [12] | VisDrone val, 1280, 3-seed | 42,123,2026 | 0.3619 +/- 0.0129 | 0.5764 +/- 0.0186 | 0.6685 | 0.5555 | 0.6067 | 25.48 | 87.30 | -0.0158 | high-resolution/frequency-detail reproduction; not official D-FINE checkpoint; 1280, 3-seed |
| 12 | YOLO medium | YOLOv10m | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3539 +/- 0.0020 | 0.5675 +/- 0.0028 | 0.6431 | 0.5573 | 0.5971 | 16.50 | 64.00 | -0.0237 | official comparison row |
| 13 | YOLO small | YOLOv9s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3433 +/- 0.0003 | 0.5544 +/- 0.0004 | 0.6362 | 0.5448 | 0.5869 | 7.29 | 27.40 | -0.0343 | official comparison row |
| 14 | YOLO small | YOLOv8s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3329 +/- 0.0030 | 0.5401 +/- 0.0035 | 0.6302 | 0.5318 | 0.5768 | 11.14 | 28.70 | -0.0448 | official comparison row |
| 15 | YOLO small | YOLOv12s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3322 +/- 0.0006 | 0.5386 +/- 0.0007 | 0.6341 | 0.5268 | 0.5755 | 9.26 | 21.50 | -0.0455 | official comparison row |
| 16 | YOLO small | YOLOv5su | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3279 +/- 0.0022 | 0.5331 +/- 0.0040 | 0.6261 | 0.5227 | 0.5697 | 9.13 | 24.10 | -0.0498 | official comparison row |
| 17 | YOLO small | YOLOv11s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3262 +/- 0.0010 | 0.5284 +/- 0.0019 | 0.6321 | 0.5162 | 0.5682 | 9.43 | 21.60 | -0.0515 | official comparison row |
| 18 | YOLO small | YOLOv10s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3248 +/- 0.0020 | 0.5260 +/- 0.0012 | 0.6239 | 0.5139 | 0.5635 | 8.07 | 24.80 | -0.0529 | official comparison row |
| 19 | YOLO small | YOLOv26s | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3229 +/- 0.0013 | 0.5229 +/- 0.0025 | 0.6061 | 0.5120 | 0.5551 | 9.96 | 22.50 | -0.0548 | official comparison row |
| 20 | Transformer baseline | RT-DETR-L | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.3201 +/- 0.0397 | 0.5355 +/- 0.0450 | 0.6189 | 0.5411 | 0.5773 | 32.83 | 108.00 | -0.0576 | official comparison row |
| 21 | YOLO nano | YOLOv12n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2938 +/- 0.0020 | 0.4839 +/- 0.0047 | 0.5939 | 0.4776 | 0.5294 | 2.57 | 6.50 | -0.0839 | official comparison row |
| 22 | YOLO nano | YOLOv8n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2925 +/- 0.0014 | 0.4812 +/- 0.0026 | 0.5906 | 0.4724 | 0.5249 | 3.01 | 8.20 | -0.0852 | official comparison row |
| 23 | YOLO nano | YOLOv11n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2877 +/- 0.0021 | 0.4750 +/- 0.0056 | 0.5864 | 0.4699 | 0.5217 | 2.59 | 6.50 | -0.0900 | official comparison row |
| 24 | YOLO nano | YOLOv26n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2838 +/- 0.0003 | 0.4668 +/- 0.0011 | 0.5780 | 0.4625 | 0.5138 | 2.51 | 5.80 | -0.0938 | official comparison row |
| 25 | YOLO nano | YOLOv10n | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2838 +/- 0.0016 | 0.4666 +/- 0.0021 | 0.5667 | 0.4697 | 0.5136 | 2.71 | 8.40 | -0.0938 | official comparison row |
| 26 | Cited related work | CSFPR-RTDETR [11] | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.2784 +/- 0.0070 | 0.4431 +/- 0.0094 | 0.5766 | 0.4292 | 0.4921 | 14.09 | 63.90 | -0.0993 | official/staged 1280 3-seed related-work run |
| 27 | Cited related work | MFFSODNet [2] | VisDrone val, 1280, 3-seed | 123,2026,42 | 0.0975 +/- 0.0034 | 0.1830 +/- 0.0070 | 0.6418 | 0.2465 | 0.3562 | 4.54 | 55.10 | -0.2802 | official code scratch retrain; no pretrained checkpoint found |

## Current 1280 YOLO-Family Sweep Status

This section shows the newest 202606 comparison sweep. Partial rows are for monitoring only and should not be used as final paper rows until all three seeds complete.

| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |

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
- `Ours` denotes the SAFR-YOLO/P2P4-SelfAttnFR implementation, deduped by latest official seed run for seeds 42, 123, and 2026.
- External related-work eval-only rows are intentionally separated; strict 1280 3-seed related-work rows are tracked with protocol notes.
