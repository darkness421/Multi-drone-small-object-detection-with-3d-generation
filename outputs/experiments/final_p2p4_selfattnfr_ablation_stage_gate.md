# Detector Stage Gate

Recommended next stage: `iterate_proposed_detector`

The proposed detector does not yet beat the selected baseline thresholds.

## Selection

- Primary metric: `best_AP_mean`
- Secondary metric: `best_AP50_mean`
- Dataset filter: `all`
- Baseline rows: `25`
- Proposed/candidate rows: `7`
- Lightweight threshold: `15000000` params
- Minimum required delta: `0.0`

| Role | Method | Family | Version | Size | Seeds | Primary | Secondary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall baseline | yolov9e | Other | unknown | large | 1 | 0.38643 | 0.61393 |
| Best lightweight baseline | YOLOv9s | YOLO | v9 | small | 3 | 0.3454 | 0.5573433333333333 |
| Best proposed candidate | ProposedSize-P2P4BalancedSelfAttnTinyFReLU-yolo11l | Other | unknown | unknown | 3 | 0.3822425 | 0.6053975 |

## Gate Gaps

| Threshold | Baseline | Candidate | Primary Delta | Secondary Delta |
| --- | --- | --- | --- | --- |
| Best overall baseline | yolov9e | ProposedSize-P2P4BalancedSelfAttnTinyFReLU-yolo11l | -0.0042 | -0.0085 |
| Best lightweight baseline | YOLOv9s | ProposedSize-P2P4BalancedSelfAttnTinyFReLU-yolo11l | +0.0368 | +0.0481 |

## Interpretation

- If the recommended stage is `finish_baselines_then_build_proposed`, complete all baseline and comparison sweeps before changing the proposed detector.
- If the recommended stage is `iterate_proposed_detector`, continue ablations on wavelet stem, partial deformable neck, and tiling inference.
- If the recommended stage is `proceed_to_3d_benchmark`, freeze the detector choice and start Marine City multi-angle benchmark and 3D generation experiments.
