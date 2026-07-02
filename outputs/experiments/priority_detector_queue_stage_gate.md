# Detector Stage Gate

Recommended next stage: `run_baseline_sweep`

No completed baseline summary rows were found.

## Selection

- Primary metric: `best_AP_mean`
- Secondary metric: `best_AP50_mean`
- Dataset filter: `all`
- Baseline rows: `0`
- Proposed/candidate rows: `16`
- Lightweight threshold: `15000000` params
- Minimum required delta: `0.0`

| Role | Method | Family | Version | Size | Seeds | Primary | Secondary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall baseline | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Best lightweight baseline | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Best proposed candidate | ProposedP2FR-CBAM-yolo11l | Other | unknown | unknown | 1 | 0.38481 | 0.60793 |

## Gate Gaps

_No proposed candidate gap is available yet._

## Interpretation

- If the recommended stage is `finish_baselines_then_build_proposed`, complete all baseline and comparison sweeps before changing the proposed detector.
- If the recommended stage is `iterate_proposed_detector`, continue ablations on wavelet stem, partial deformable neck, and tiling inference.
- If the recommended stage is `proceed_to_3d_benchmark`, freeze the detector choice and start Marine City multi-angle benchmark and 3D generation experiments.
