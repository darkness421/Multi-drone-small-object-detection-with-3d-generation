# ACCV Bi-daily Update - 2026-06-04 11:10 KST

## Deadline
- Main paper due: 2026-07-05 (31 days left).
- Supplementary due: 2026-07-08 (34 days left).

## Current Gate
- Gate not passed yet: best proposed is behind the best comparison by AP 0.0499 and AP50 0.0673.
- Best comparison: YOLOv11l AP 0.3777, AP50 0.5981, F1 0.6248, Params 25.32M, GFLOPs 87.3.
- Best proposed: Proposed-CBAM-yolo11s + cbam_neck AP 0.3277, AP50 0.5308, F1 0.5710, Params 9.43M, GFLOPs 21.6.
- Detector stage gate: finish_baselines_then_build_proposed.
- Proposed overwhelm gate file status: not_yet.

## Active Or Recent Runs
| Method | Seed | Status | Epoch | Best AP | Best AP50 | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| RT-DETR-L | 42 | incomplete | 8.0 / 100 | 0.1063 | 0.2718 | 0.3590 |
| RT-DETR-L | 123 | incomplete | 8.0 / 100 | 0.1248 | 0.2339 | 0.3064 |
| proposed_control_yolo11s | 123 | incomplete | 1.0 / 100 | 0.2152 | 0.3682 | 0.4299 |
| proposed_control_yolo11s | 42 | incomplete | 1.0 / 100 | 0.2179 | 0.3656 | 0.4308 |
| proposed_partial_deformable_neck_yolo11s | 42 | incomplete | 100.0 / 100 | 0.3292 | 0.5308 | 0.5707 |

## Detector Leaderboard
| Rank | Method | Scale | Seeds | AP | AP50 | F1 | Params | GFLOPs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | YOLOv11l | large | 3 | 0.3777 | 0.5981 | 0.6248 | 25.32M | 87.3 |
| 2 | YOLOv12l | large | 3 | 0.3771 | 0.5958 | 0.6219 | 26.40M | 89.4 |
| 3 | YOLOv8l | large | 3 | 0.3765 | 0.5963 | 0.6198 | 43.64M | 165.4 |
| 4 | YOLOv26l | large | 3 | 0.3732 | 0.5877 | 0.6136 | 26.19M | 93.2 |
| 5 | YOLOv10l | large | 3 | 0.3728 | 0.5890 | 0.6166 | 25.78M | 127.3 |
| 6 | YOLOv12m | medium | 3 | 0.3669 | 0.5848 | 0.6133 | 20.15M | 67.8 |
| 7 | YOLOv10m | medium | 3 | 0.3539 | 0.5675 | 0.5971 | 16.50M | 64.0 |
| 8 | YOLOv9s | small | 3 | 0.3433 | 0.5544 | 0.5869 | 7.29M | 27.4 |

## Next 48 Hours
- Keep GPU0 on detector baseline/proposed screening and collect per-epoch AP/AP50/F1.
- Queue YOLOv11l/P2, TinySpatialFReLU, and NMS variants after the current proposed run clears.
- Keep GPU1 reserved for 3D/simulator/reasoner work after the CUDA allocation issue is reset.
- Export paper tables and figures into the Overleaf-linked repository.
- Append this status to Notion when NOTION_TOKEN and NOTION_PAGE_ID are available.

## Updated Artifacts
- GitHub: commit scoped experiment status, automation scripts, Notion exports, and result snapshots.
- Paper: update auto detector table, auto experiment status section, and copied result figures.
- Notion: append this bi-daily update to the project/proposed-method page.
