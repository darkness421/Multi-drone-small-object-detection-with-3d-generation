# Paper Model Availability

Source config: `configs/experiments/paper_detector_comparison.yaml`

This file separates runnable comparison candidates from models that still need external code, adapters, or checkpoints.

- Runnable or queue-check candidates: `3`
- External-asset blocked candidates: `11`
- Total candidates: `14`

## Recommendation

Use the already queued YOLO/RT-DETR family as the primary reproducible comparison set.
For the paper-specific comparison row, add only 2-3 external models after local weights/adapters are staged:
`LRDS-YOLO` or another YOLO-specialized UAV model, one DETR/D-FINE family model, and optionally `UAVDet`.

## Candidate Table

| Model | Family | Group | Size | Status | Runnable | Action |
| --- | --- | --- | --- | --- | --- | --- |
| YOLOv10n | YOLO | yolo | nano | ultralytics_available_check | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| YOLOv10s | YOLO | yolo | small | already_in_queue | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| YOLOv10m | YOLO | yolo | medium | already_in_queue | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| LRDS-YOLO | LRDS-YOLO | yolo | lightweight | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| SOD-YOLO | SOD-YOLO | yolo | lightweight | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| DR-YOLO | DR-YOLO | yolo | lightweight | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| LSOD-YOLO | LSOD-YOLO | yolo | lightweight | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| MASF-YOLO | MASF-YOLO | yolo | small | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| TOE-YOLO | TOE-YOLO | yolo | nano | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| MFR-YOLO | MFR-YOLO | yolo | medium | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| UAVDet | UAVDet | non_yolo | lightweight | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| HF-D-FINE | D-FINE | non_yolo | small | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| CSFPR-RTDETR | RT-DETR | non_yolo | small | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
| UFO-DETR | DETR | non_yolo | lightweight | external_required | blocked_external_assets | Stage compatible code/checkpoint first; do not count as executed comparison yet. |
