# Detector Experiment Status

Generated: `2026-05-27T22:36:09+09:00`

This page is the quick navigation point for detector experiments while long server training is running.

## Current Queue

| Order | Session | Role | Action |
| --- | --- | --- | --- |
| 1 | `server-large-comparison` | VisDrone L-size anchors | running |
| 2 | `server-top3-proposed-pending` | top-3 proposed ablation | waits for large comparison |
| 3 | `server-uavdt-comparisons-pending` | UAVDT cross-dataset comparison | waits for large and proposed queues |

## Stage Gate

- Recommended next stage: `iterate_proposed_detector`
- Rationale: The proposed detector does not yet beat the selected baseline thresholds.
- Gate dataset: `VisDrone2019-DET`

## Dataset Readiness

| Dataset | Status | Evidence | Use |
| --- | --- | --- | --- |
| VisDrone2019-DET | ready | configs/detector/visdrone_yolo_data.yaml | primary detector baseline/proposed dataset |
| UAVDT | ready | 40403 images / 763817 boxes | cross-dataset validation after active queues |

## Current Top Detector Rows

| Rank | Method | Dataset | Family | Size | Seeds | Level | AP | AP50 | Recall | F1 | Params | GFLOPs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | YOLOv12m | VisDrone2019-DET | YOLO | medium | 3 | preliminary | 0.3669 | 0.5848 | 0.5694 | 0.6133 | 20.15M | 67.8 |
| 2 | YOLOv10m | VisDrone2019-DET | YOLO | medium | 3 | preliminary | 0.3539 | 0.5675 | 0.5573 | 0.5971 | 16.50M | 64.0 |
| 3 | YOLOv9s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3433 | 0.5544 | 0.5448 | 0.5869 | 7.29M | 27.4 |
| 4 | YOLOv8s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3329 | 0.5401 | 0.5318 | 0.5768 | 11.14M | 28.7 |
| 5 | YOLOv12s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3322 | 0.5386 | 0.5268 | 0.5755 | 9.26M | 21.5 |
| 6 | YOLOv5su | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3279 | 0.5331 | 0.5227 | 0.5697 | 9.13M | 24.1 |
| 7 | Proposed-CBAM-yolo11s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3277 | 0.5308 | 0.5237 | 0.5710 | 9.43M | 21.6 |
| 8 | Proposed-Control-yolo11s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3276 | 0.5304 | 0.5199 | 0.5695 | 9.43M | 21.6 |
| 9 | Proposed-SE-yolo11s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3275 | 0.5301 | 0.5175 | 0.5667 | 9.43M | 21.6 |
| 10 | Proposed-WaveletStem-yolo11s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3264 | 0.5280 | 0.5177 | 0.5682 | 9.43M | 21.6 |
| 11 | YOLOv11s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3262 | 0.5284 | 0.5162 | 0.5682 | 9.43M | 21.6 |
| 12 | YOLOv10s | VisDrone2019-DET | YOLO | small | 3 | preliminary | 0.3248 | 0.5260 | 0.5139 | 0.5635 | 8.07M | 24.8 |

## Paper Comparison Availability

| Model | Family | Group | Size | Runnable Status | Action |
| --- | --- | --- | --- | --- | --- |
| YOLOv10m | YOLO | yolo | medium | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| YOLOv10n | YOLO | yolo | nano | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| YOLOv10s | YOLO | yolo | small | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| CSFPR-RTDETR | RT-DETR | non_yolo | small | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| DR-YOLO | DR-YOLO | yolo | lightweight | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| HF-D-FINE | D-FINE | non_yolo | small | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| LRDS-YOLO | LRDS-YOLO | yolo | lightweight | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| LSOD-YOLO | LSOD-YOLO | yolo | lightweight | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| MASF-YOLO | MASF-YOLO | yolo | small | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| MFR-YOLO | MFR-YOLO | yolo | medium | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| SOD-YOLO | SOD-YOLO | yolo | lightweight | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| TOE-YOLO | TOE-YOLO | yolo | nano | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| UAVDet | UAVDet | non_yolo | lightweight | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| UFO-DETR | DETR | non_yolo | lightweight | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |

## Next Actions

1. Let the active VisDrone large comparison finish.
2. Let the top-3 proposed ablation run on the selected backbones.
3. Run UAVDT cross-dataset comparison from the pending queue.
4. Recollect with `bash scripts/ubuntu/collect_proposed_results.sh` and `bash scripts/ubuntu/collect_cross_dataset_results.sh`.
5. If the proposed gate beats best overall and best lightweight baselines, freeze the detector checkpoint for Isaac Sim and 3D benchmark work.

## Report Links

- `outputs/reports/server_with_proposed/README.md`
- `outputs/reports/server_with_proposed/paper_model_availability.md`
- `outputs/experiments/server_with_proposed_stage_gate.md`
- `docs/notion_research_comparison_notes.md`
