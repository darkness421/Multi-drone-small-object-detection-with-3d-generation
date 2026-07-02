# Detector Stage Gate

Recommended next stage: `proceed_to_3d_benchmark`

The best proposed detector meets or exceeds the best overall and best lightweight baselines.

## Selection

- Primary metric: `best_AP_mean`
- Secondary metric: `best_AP50_mean`
- Dataset filter: `all`
- Baseline rows: `6`
- Proposed/candidate rows: `6`
- Lightweight threshold: `15000000` params
- Minimum required delta: `0.0`

| Role | Method | Family | Version | Size | Seeds | Primary | Secondary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall baseline | YOLOv11l | YOLO | v11 | medium | 3 | 0.3776566666666667 | 0.59809 |
| Best lightweight baseline | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Best proposed candidate | ProposedNext-P2TinyFReLU-yolo11l | Other | unknown | unknown | 3 | 0.3823166666666667 | 0.60505 |

## Gate Gaps

| Threshold | Baseline | Candidate | Primary Delta | Secondary Delta |
| --- | --- | --- | --- | --- |
| Best overall baseline | YOLOv11l | ProposedNext-P2TinyFReLU-yolo11l | +0.0047 | +0.0070 |

## Interpretation

- If the recommended stage is `finish_baselines_then_build_proposed`, complete all baseline and comparison sweeps before changing the proposed detector.
- If the recommended stage is `iterate_proposed_detector`, continue ablations on wavelet stem, partial deformable neck, and tiling inference.
- If the recommended stage is `proceed_to_3d_benchmark`, freeze the detector choice and start Marine City multi-angle benchmark and 3D generation experiments.
