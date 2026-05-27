# Server Baseline Report Bundle

Generated: `2026-05-27T22:36:31+09:00`

This folder is the compact, Git-friendly report bundle for server detector baselines.
Raw datasets, model weights, raw training runs, and caches stay outside Git.

## Current Snapshot

- Recommended next stage: `iterate_proposed_detector`
- Best completed baseline: `YOLOv12m AP=0.3669, AP50=0.5848`
- Run status counts: `{"completed": 55, "incomplete": 5}`

## Files

| File | Purpose |
| --- | --- |
| [Dashboard](figures/server_baseline_dashboard.png) | Main AP/AP50/seed distribution/complexity dashboard |
| [Summary CSV](tables/server_baseline_summary.csv) | Mean/std by method, model size, family, and seed count |
| [Results CSV](tables/server_baseline_results.csv) | Per-run detector metrics and status |
| [P-values CSV](tables/server_baseline_pvalues.csv) | Paired t-test and Wilcoxon comparisons |
| [Stage Gate](stage_gate.md) | Current decision gate for baseline/proposed/3D next stage |

## Companion Reports

| File | Purpose |
| --- | --- |
| [Paper Model Availability](paper_model_availability.md) | Runnable/external-required status for recent paper comparison models |
| [Detector Experiment Status](../detector_experiment_status.md) | Queue, dataset readiness, top rows, and next actions |

## Figures

| Figure | Purpose |
| --- | --- |
| [ap_ap50_by_model.png](figures/ap_ap50_by_model.png) | Separated AP and AP50 bar chart |
| [gflops_vs_ap.png](figures/gflops_vs_ap.png) | GFLOPs and AP tradeoff |
| [params_vs_ap.png](figures/params_vs_ap.png) | Parameter-count and AP tradeoff |
| [precision_recall_f1_by_model.png](figures/precision_recall_f1_by_model.png) | Separated precision, recall, and F1 chart |
| [seed_ap_distribution_by_model.png](figures/seed_ap_distribution_by_model.png) | Seed-level AP distribution |
| [server_baseline_dashboard.png](figures/server_baseline_dashboard.png) | Combined overview dashboard for quick monitoring |
| [speed_vs_ap.png](figures/speed_vs_ap.png) | FPS and AP tradeoff, or placeholder until FPS is collected |

## Top Models

| Rank | Method | Family | Size | Seeds | Level | AP | AP50 | P | R | F1 | FPS | Params | GFLOPs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | YOLOv12m | YOLO | medium | 3 | preliminary | 0.3669 | 0.5848 | 0.6646 | 0.5694 | 0.6133 | - | 20.15M | 67.8 |
| 2 | YOLOv10m | YOLO | medium | 3 | preliminary | 0.3539 | 0.5675 | 0.6431 | 0.5573 | 0.5971 | - | 16.50M | 64.0 |
| 3 | YOLOv9s | YOLO | small | 3 | preliminary | 0.3433 | 0.5544 | 0.6362 | 0.5448 | 0.5869 | - | 7.29M | 27.4 |
| 4 | YOLOv8s | YOLO | small | 3 | preliminary | 0.3329 | 0.5401 | 0.6302 | 0.5318 | 0.5768 | - | 11.14M | 28.7 |
| 5 | YOLOv12s | YOLO | small | 3 | preliminary | 0.3322 | 0.5386 | 0.6341 | 0.5268 | 0.5755 | - | 9.26M | 21.5 |
| 6 | YOLOv5su | YOLO | small | 3 | preliminary | 0.3279 | 0.5331 | 0.6261 | 0.5227 | 0.5697 | - | 9.13M | 24.1 |
| 7 | Proposed-CBAM-yolo11s | YOLO | small | 3 | preliminary | 0.3277 | 0.5308 | 0.6278 | 0.5237 | 0.5710 | - | 9.43M | 21.6 |
| 8 | Proposed-Control-yolo11s | YOLO | small | 3 | preliminary | 0.3276 | 0.5304 | 0.6295 | 0.5199 | 0.5695 | - | 9.43M | 21.6 |
| 9 | Proposed-SE-yolo11s | YOLO | small | 3 | preliminary | 0.3275 | 0.5301 | 0.6264 | 0.5175 | 0.5667 | - | 9.43M | 21.6 |
| 10 | Proposed-WaveletStem-yolo11s | YOLO | small | 3 | preliminary | 0.3264 | 0.5280 | 0.6299 | 0.5177 | 0.5682 | - | 9.43M | 21.6 |
| 11 | YOLOv11s | YOLO | small | 3 | preliminary | 0.3262 | 0.5284 | 0.6321 | 0.5162 | 0.5682 | - | 9.43M | 21.6 |
| 12 | YOLOv10s | YOLO | small | 3 | preliminary | 0.3248 | 0.5260 | 0.6239 | 0.5139 | 0.5635 | - | 8.07M | 24.8 |

## Statistical Snapshot

Seed count `3` is preliminary; seed count `5+` is the main statistical setting.

| Metric | Baseline | Candidate | Seeds | Level | Delta | t-test p | Wilcoxon p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| best_AP | YOLOv12m | YOLOv26n | 3 | preliminary | -0.0830 | 0.0000 | 0.2500 |
| best_AP | YOLOv12m | YOLOv8n | 3 | preliminary | -0.0744 | 0.0000 | 0.2500 |
| best_AP | YOLOv12m | Proposed-CBAM-yolo11s | 3 | preliminary | -0.0392 | 0.0000 | 0.2500 |
| best_AP | YOLOv12m | Proposed-SE-yolo11s | 3 | preliminary | -0.0393 | 0.0001 | 0.2500 |
| best_AP | YOLOv12m | YOLOv10n | 3 | preliminary | -0.0830 | 0.0001 | 0.2500 |
| best_AP | YOLOv12m | Proposed-WaveletStem-yolo11s | 3 | preliminary | -0.0405 | 0.0001 | 0.2500 |
| best_AP | YOLOv12m | YOLOv12n | 3 | preliminary | -0.0731 | 0.0002 | 0.2500 |
| best_AP | YOLOv12m | YOLOv11s | 3 | preliminary | -0.0407 | 0.0002 | 0.2500 |
| best_AP | YOLOv12m | YOLOv11n | 3 | preliminary | -0.0792 | 0.0005 | 0.2500 |
| best_AP | YOLOv12m | Proposed-Control-yolo11s | 3 | preliminary | -0.0392 | 0.0005 | 0.2500 |
| best_AP | YOLOv12m | RT-DETR-L | 1 | preliminary | -0.0487 | nan | 1.0000 |
| best_AP | YOLOv12m | YOLOv12s | 3 | preliminary | -0.0347 | 0.0003 | 0.2500 |

## Metric Notes

- `AP` is mAP50-95 and is used as the detector accuracy proxy.
- `AP50`, `P` precision, `R` recall, and `F1` are reported alongside AP.
- `FPS` and `latency_ms` appear when validation/inference speed is available.
- `Params` and `GFLOPs` are used to separate nano/small/medium/large comparisons.
- Incomplete, cancelled, or failed runs should be interpreted separately from completed seed summaries.
