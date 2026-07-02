# Paper Model Availability

Source config: `configs/experiments/paper_detector_comparison.yaml`

This file separates runnable comparison candidates, GitHub-backed candidates that need adapters/checkpoints, and no-code papers that should be passed for full reproduction.

- Runnable or queue-check candidates: `4`
- GitHub-backed but adapter/checkpoint-needed candidates: `5`
- Passed for full reproduction because no public GitHub/code is staged: `11`
- Total candidates: `22`

## Recommendation

Run models with public GitHub/code and staged assets first. If code exists but the format differs, build only the adapter needed for fair evaluation.
Pass no-code/no-weight papers for full reproduction, but keep simple transferable mechanisms such as NMS, activation, wavelet/DCT, attention, and P2-head changes as lightweight ablations inside our proposed detector.
For the paper-specific comparison row, prioritize `CSFPR-RTDETR`, `LEAF-YOLO`, and `DR-YOLO` before lower-priority generic or modality-mismatched models.

## Candidate Table

| Model | Family | Group | Size | Status | Runnable | Action |
| --- | --- | --- | --- | --- | --- | --- |
| YOLOv10n | YOLO | yolo | nano | ultralytics_available_check | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| YOLOv10s | YOLO | yolo | small | already_in_queue | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| YOLOv10m | YOLO | yolo | medium | already_in_queue | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| LRDS-YOLO | LRDS-YOLO | yolo | lightweight | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| BPD-YOLO | BPD-YOLO | yolo | lightweight | citation_only_until_code | citation_only_until_code | Do not queue yet; cite the paper or stage compatible code/weights first. |
| SFFEF-YOLO | SFFEF-YOLO | yolo | lightweight | citation_only_until_code | citation_only_until_code | Do not queue yet; cite the paper or stage compatible code/weights first. |
| SOD-YOLO | SOD-YOLO | yolo | lightweight | external_required | github_code_needs_adapter_or_checkpoint | Prioritize this candidate: stage repo/checkpoint or build a small adapter before running. |
| DR-YOLO | DR-YOLO | yolo | lightweight | external_required | github_code_needs_adapter_or_checkpoint | Prioritize this candidate: stage repo/checkpoint or build a small adapter before running. |
| LSOD-YOLO | LSOD-YOLO | yolo | lightweight | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| GCL-YOLO | GCL-YOLO | yolo | lightweight | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| SRTSOD-YOLO | SRTSOD-YOLO | yolo | lightweight | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| YOLO11s-UAV | YOLO11 | yolo | small | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| MASF-YOLO | MASF-YOLO | yolo | small | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| TOE-YOLO | TOE-YOLO | yolo | nano | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| MFR-YOLO | MFR-YOLO | yolo | medium | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| UAVDet | UAVDet | non_yolo | lightweight | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| HF-D-FINE | D-FINE | non_yolo | small | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| CSFPR-RTDETR | RT-DETR | non_yolo | small | external_required | local_weight_found | Queue after active VisDrone/proposed jobs if the adapter matches the current trainer. |
| UFO-DETR | DETR | non_yolo | lightweight | external_required | pass_no_public_github | Pass full reproduction for now; only test simple transferable mechanisms as our own ablations. |
| LEAF-YOLO | LEAF-YOLO | yolo | nano_lightweight | external_required | github_code_needs_adapter_or_checkpoint | Prioritize this candidate: stage repo/checkpoint or build a small adapter before running. |
| UAVD-Mamba | Mamba | non_yolo | lightweight | external_required | github_code_needs_adapter_or_checkpoint | Prioritize this candidate: stage repo/checkpoint or build a small adapter before running. |
| RF-DETR-B | RF-DETR | non_yolo | base | external_required | github_code_needs_adapter_or_checkpoint | Prioritize this candidate: stage repo/checkpoint or build a small adapter before running. |
