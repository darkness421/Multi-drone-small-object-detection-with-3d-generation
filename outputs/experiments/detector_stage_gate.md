# Detector Stage Gate

Recommended next stage: `iterate_proposed_detector`

The proposed detector does not yet beat the selected baseline thresholds.

## Selection

- Primary metric: `best_AP_mean`
- Secondary metric: `best_AP50_mean`
- Dataset filter: `TinyPerson`
- Baseline rows: `1`
- Proposed/candidate rows: `1`
- Lightweight threshold: `15000000` params
- Minimum required delta: `0.0`

| Role | Method | Family | Version | Size | Seeds | Primary | Secondary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall baseline | YOLOv9m-TinyPersonCornerOriginal | YOLO | v9 | unknown | 2 | 0.19974999999999998 | 0.5290900000000001 |
| Best lightweight baseline | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Best proposed candidate | Ours-TinyPersonCornerOriginal | Other | unknown | unknown | 2 | 0.167485 | 0.44293 |

## Gate Gaps

| Threshold | Baseline | Candidate | Primary Delta | Secondary Delta |
| --- | --- | --- | --- | --- |
| Best overall baseline | YOLOv9m-TinyPersonCornerOriginal | Ours-TinyPersonCornerOriginal | -0.0323 | -0.0862 |

## Interpretation

- If the recommended stage is `finish_baselines_then_build_proposed`, complete all baseline and comparison sweeps before changing the proposed detector.
- If the recommended stage is `iterate_proposed_detector`, continue ablations on wavelet stem, partial deformable neck, and tiling inference.
- If the recommended stage is `proceed_to_3d_benchmark`, freeze the detector choice and start Marine City multi-angle benchmark and 3D generation experiments.
