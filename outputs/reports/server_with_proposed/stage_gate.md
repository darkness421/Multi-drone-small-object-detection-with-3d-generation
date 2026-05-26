# Detector Stage Gate

Recommended next stage: `iterate_proposed_detector`

The proposed detector does not yet beat the selected baseline thresholds.

## Selection

- Primary metric: `best_AP_mean`
- Secondary metric: `best_AP50_mean`
- Dataset filter: `VisDrone2019-DET`
- Baseline rows: `15`
- Proposed/candidate rows: `4`
- Lightweight threshold: `15000000` params
- Minimum required delta: `0.0`

| Role | Method | Family | Version | Size | Seeds | Primary | Secondary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall baseline | YOLOv12m | YOLO | v12 | medium | 3 | 0.3668766666666667 | 0.58482 |
| Best lightweight baseline | YOLOv9s | YOLO | v9 | small | 3 | 0.3433466666666667 | 0.5544333333333333 |
| Best proposed candidate | Proposed-CBAM-yolo11s | YOLO | v11 | small | 3 | 0.32772 | 0.53078 |

## Interpretation

- If the recommended stage is `finish_baselines_then_build_proposed`, complete all baseline and comparison sweeps before changing the proposed detector.
- If the recommended stage is `iterate_proposed_detector`, continue ablations on wavelet stem, partial deformable neck, and tiling inference.
- If the recommended stage is `proceed_to_3d_benchmark`, freeze the detector choice and start Marine City multi-angle benchmark and 3D generation experiments.
