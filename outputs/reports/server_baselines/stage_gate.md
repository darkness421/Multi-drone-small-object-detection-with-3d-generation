# Detector Stage Gate

Recommended next stage: `finish_baselines_then_build_proposed`

Baseline/comparison models are being established; proposed detector rows are not present yet.

## Selection

- Primary metric: `best_AP_mean`
- Secondary metric: `best_AP50_mean`
- Dataset filter: `all`
- Baseline rows: `9`
- Proposed/candidate rows: `0`
- Lightweight threshold: `15000000` params
- Minimum required delta: `0.0`

| Role | Method | Family | Version | Size | Seeds | Primary | Secondary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall baseline | YOLOv9s | YOLO | v9 | small | 3 | 0.3433466666666667 | 0.5544333333333333 |
| Best lightweight baseline | YOLOv9s | YOLO | v9 | small | 3 | 0.3433466666666667 | 0.5544333333333333 |
| Best proposed candidate | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Interpretation

- If the recommended stage is `finish_baselines_then_build_proposed`, complete all baseline and comparison sweeps before changing the proposed detector.
- If the recommended stage is `iterate_proposed_detector`, continue ablations on wavelet stem, partial deformable neck, and tiling inference.
- If the recommended stage is `proceed_to_3d_benchmark`, freeze the detector choice and start Marine City multi-angle benchmark and 3D generation experiments.
