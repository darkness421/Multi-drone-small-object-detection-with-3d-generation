# Related-Work Code Staging

Date: 2026-06-26

Rule: paper-facing comparison candidates must be cited in the current
`2.1 UAV Small-object Evidence Generation` section. Public-code candidates that
are not cited there are internal-only unless the manuscript is revised.

## Staged Locally

| Model | Sec. 2.1 citation | Local path | Source | Queue status |
| --- | --- | --- | --- | --- |
| CSFPR-RTDETR | `hu2025csfprrtdetr` | `external/CSFPR-RTDETR` | `https://github.com/HuLei-JXNU/CSFPR-RTDETR` | completed 1280 3-seed related-work row |
| MFFSODNet | `jiang2024mffsodnet` | `external/MFFSODNet/tph-yolov5` | `https://github.com/1998Jiang/MFFSODNet` | completed 1280 scratch 3-seed row; no pretrained checkpoint found |
| UAVDet official | `yang2026uavdet` | `external/UAVDet` | `https://github.com/alex-yimingyang/UAVDet` | official adapter hold: MMDetection/Mamba/selective-scan dependency and RGB-only fairness |
| UAVDet-inspired reproduction | `yang2026uavdet` | local YOLO/SSM-style reproduction | local fallback | completed 1280 3-seed row; label as inspired reproduction, not official checkpoint |
| SFFEF-YOLO | `bai2025sffefyolo` | local paper-faithful reproduction | no compatible official checkpoint staged | completed 1280 3-seed row |
| BPD-YOLO | `chao2025bpdyolo` | local paper-faithful reproduction | no compatible official checkpoint staged | completed 1280 3-seed row |
| HF-D-FINE | `hu2026hfdifine` | local high-resolution/frequency-detail reproduction | no compatible D-FINE checkpoint staged | completed 1280 3-seed row |

## Internal-Only / Excluded From Paper-Facing Comparison

| Model | Reason |
| --- | --- |
| LEAF-YOLO-N/S | Not cited in current Sec. 2.1. Existing partial/current runs are internal sanity checks only. |
| DR-YOLO, SOD-YOLO, YOLO11s-UAV, GCL-YOLO, SRTSOD-YOLO | Not cited in current Sec. 2.1. Do not queue as paper-facing related-work comparisons unless Related Work is revised. |

## Current Strict Status

The paper-facing cited related-work detector table is complete for the current
manuscript scope. It now includes six cited rows at the 1280 protocol:
`CSFPR-RTDETR [11]`, `MFFSODNet [2]`, `SFFEF-YOLO [4]`,
`BPD-YOLO [7]`, `HF-D-FINE [12]`, and `UAVDet [16]`.

No additional detector queue should be started by default. Keep GPU0 free unless
paper review finds a missing cited detector row or a targeted re-run is needed.

Live files:

- `outputs/reports/live/training_dashboard.png`
- `outputs/reports/live/paper_fig03_related_work_status_table.png`
- `paper/tables/related_work_detector_experiment_plan.csv`
- `paper/tables/related_work_coverage_matrix.csv`
