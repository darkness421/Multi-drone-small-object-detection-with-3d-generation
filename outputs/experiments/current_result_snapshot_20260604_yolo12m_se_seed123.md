# Current Result Snapshot: ProposedTop3-SE-yolo12m seed123

Saved at: 2026-06-04 15:36 KST

Run directory:
`outputs/detectors/server_top3_proposed_ablation/20260604_101321_proposed_se_neck_yolo12m_visdrone_top3_seed123`

Reason for stopping:
The run plateaued by epoch 55/100 and remained below the strongest baseline.

Best checkpoint:
`outputs/detectors/server_top3_proposed_ablation/20260604_101321_proposed_se_neck_yolo12m_visdrone_top3_seed123/ultralytics/weights/best.pt`

Raw results:
`outputs/detectors/server_top3_proposed_ablation/20260604_101321_proposed_se_neck_yolo12m_visdrone_top3_seed123/ultralytics/results.csv`

## Metrics

| Metric | Value |
| --- | ---: |
| Best epoch | 51 |
| Best AP | 0.36520 |
| Best AP50 | 0.58131 |
| Best F1 | 0.61077 |
| Latest completed epoch | 55 |
| Latest AP | 0.36364 |
| Latest AP50 | 0.57853 |
| Latest F1 | 0.60653 |
| Params | 20.15M |
| GFLOPs | 67.8 |

## Gate Context

| Model | AP | AP50 | F1 | Params | GFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| YOLOv11l baseline | 0.37766 | 0.59809 | 0.62475 | 25.32M | 87.3 |
| YOLOv12m baseline | 0.36688 | 0.58482 | 0.61330 | 20.15M | 67.8 |
| ProposedTop3-SE-yolo12m seed123 | 0.36520 | 0.58131 | 0.61077 | 20.15M | 67.8 |

Decision:
Do not continue this run. Move GPU0 to the YOLOv11l + P2/TinyFReLU proposed detector search.
