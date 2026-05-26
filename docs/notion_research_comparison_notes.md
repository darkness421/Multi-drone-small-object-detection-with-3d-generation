# Notion Research Comparison Notes

Source checked: the shared Notion database
`377a56f7685383748586011fd1983a90`, public collection view
`54ba56f7685383b886a28824de7950de`.

Checked on: 2026-05-26.

## What Was Extracted

The database contains 70 rows. The detector-related rows include:

- LRDS-YOLO
- UAVDet: CNN-Mamba hybrid network for UAV small-object detection
- HF-D-FINE: high-resolution feature enhanced D-FINE for UAV tiny objects
- CSFPR-RTDETR: cross spatial-frequency and position relation RT-DETR variant
- UFO-DETR: frequency-guided end-to-end detector for UAV tiny objects
- DFFormer
- Dual-domain attentions for UAV small-object detection
- SFFEF-YOLO
- MFFSODNet
- density-guided/two-stage UAV small-object detection papers
- coarse-fine feature interaction/alignment papers

## Comparison Use

For the paper table, do not run every paper model immediately. The useful
coverage is:

- YOLO version/size baselines: already covered by the server queue.
- Recent YOLO-specialized UAV model: LRDS-YOLO, SOD-YOLO, LSOD-YOLO, or
  MASF-YOLO if runnable.
- Recent non-YOLO model: UAVDet, HF-D-FINE, CSFPR-RTDETR, or UFO-DETR if
  runnable.
- Our proposed model: best top-3 backbone plus the best module ablation.

Recommended external additions after top-3 screening:

1. `LRDS-YOLO` or `SOD-YOLO` as a recent YOLO-family UAV comparison.
2. `HF-D-FINE` or `CSFPR-RTDETR` as a DETR/D-FINE-style comparison.
3. `UAVDet` as a Mamba/CNN hybrid comparison if code or weights are available.

All are currently marked `external_required` in
`configs/experiments/paper_detector_comparison.yaml`.
