# ACCV Detector Comparison Grouping Update - 2026-06-11

## Status

- Current selected detector candidate: `P2P4-SelfAttnFR-s123`.
- Current strongest plain YOLO baseline: `YOLOv11l`.
- Notion connector status: direct update is blocked because the session token is expired. This note is staged for Notion sync after re-authentication.

## Key Result Snapshot

| Group | Model | AP | AP50 | Precision | Recall | F1 | Params | Note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ours | P2P4-SelfAttnFR-s123 | 0.3825 | 0.6061 | 0.6714 | 0.5867 | 0.6262 | 20.82M | selected trade-off candidate |
| Plain YOLO family | YOLOv11l | 0.3777 | 0.5981 | 0.6666 | 0.5881 | 0.6248 | 25.32M | strongest YOLO baseline |
| Plain YOLO family | YOLOv12l | 0.3771 | 0.5958 | 0.6698 | 0.5805 | 0.6219 | 26.40M | 3-seed baseline |
| Plain YOLO family | YOLOv8l | 0.3765 | 0.5963 | 0.6695 | 0.5770 | 0.6198 | 43.64M | 3-seed baseline |
| Generic non-YOLO | RT-DETR-L | 0.3186 | 0.5279 | 0.6127 | 0.5382 | 0.5730 | 32.83M | 1-seed baseline |
| Related-work prior | CSFPR-RTDETR | 0.3279 | 0.5253 | 0.6336 | 0.5145 | 0.5679 | 14.09M | 640-eval |
| Related-work prior | LEAF-YOLO-S | 0.2810 | 0.4820 | 0.5770 | 0.4850 | 0.5270 | 4.28M | 640-eval |

## Table Grouping Rule

- Plain YOLO family baselines: stock YOLO family and scale rows, such as `YOLOv5u`, `YOLOv8`, `YOLOv9`, `YOLOv10`, `YOLO11`, `YOLO12`, and `YOLO26`.
- Generic non-YOLO baselines: stock non-YOLO detectors, such as `RT-DETR-L`.
- Related-work prior models: paper-proposed external detectors, even when their name includes YOLO. Examples include `LEAF-YOLO`, `CSFPR-RTDETR`, `SFFEF-YOLO`, `LSOD-YOLO`, `UAVDet`, and `HF-D-FINE`.
- Ours: the selected proposed detector and final ablation variants.

## Experiment Policy

- Keep the active training queue running; do not interrupt current sessions.
- After the current queue clears, use GPU0 for compact proposed-detector follow-up around `P2P4-SelfAttnFR-s123`.
- Use GPU1 for reviewer-facing comparison coverage: YOLO family scale sweep and runnable related-work prior models.
- Run final 3-seed confirmation only after the detector is frozen. Planned seeds: `42`, `123`, and `2026`.

## Paper Update

- Updated the Overleaf-facing paper section `paper/sections/05_experiments_current_detector_status.tex`.
- The table now separates plain YOLO family baselines, generic non-YOLO baselines, and related-work prior models.
- The text now treats `P2P4-SelfAttnFR-s123` as the selected trade-off candidate, not a fully frozen final model.
