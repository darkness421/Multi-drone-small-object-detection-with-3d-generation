# Server Baseline Report Bundle

Generated: `2026-05-19T12:13:44+09:00`

This folder is the compact, Git-friendly report bundle for server detector baselines.
Raw datasets, model weights, raw training runs, and caches stay outside Git.

## Current Snapshot

- Recommended next stage: `finish_baselines_then_build_proposed`
- Best completed baseline: `YOLOv9s AP=0.3433, AP50=0.5544`
- Run status counts: `{"completed": 33, "incomplete": 4}`

## Files

| File | Purpose |
| --- | --- |
| [Dashboard](figures/server_baseline_dashboard.png) | Main AP/AP50/seed distribution/complexity dashboard |
| [Summary CSV](tables/server_baseline_summary.csv) | Mean/std by method, model size, family, and seed count |
| [Results CSV](tables/server_baseline_results.csv) | Per-run detector metrics and status |
| [P-values CSV](tables/server_baseline_pvalues.csv) | Paired t-test and Wilcoxon comparisons |
| [Stage Gate](stage_gate.md) | Current decision gate for baseline/proposed/3D next stage |

## Top Models

| Rank | Method | Family | Size | Seeds | Level | AP | AP50 | P | R | F1 | FPS | Params | GFLOPs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | YOLOv9s | YOLO | small | 3 | preliminary | 0.3433 | 0.5544 | 0.6362 | 0.5448 | 0.5869 | - | 7.29M | 27.4 |
| 2 | YOLOv8s | YOLO | small | 5 | main | 0.3326 | 0.5398 | 0.6323 | 0.5300 | 0.5767 | - | 11.14M | 28.7 |
| 3 | YOLOv12s | YOLO | small | 5 | main | 0.3318 | 0.5376 | 0.6286 | 0.5280 | 0.5739 | - | 9.26M | 21.5 |
| 4 | YOLOv5su | YOLO | small | 3 | preliminary | 0.3279 | 0.5331 | 0.6261 | 0.5227 | 0.5697 | - | 9.13M | 24.1 |
| 5 | YOLOv11s | YOLO | small | 5 | main | 0.3262 | 0.5291 | 0.6313 | 0.5174 | 0.5687 | - | 9.43M | 21.6 |
| 6 | RT-DETR-L | RT-DETR | medium | 3 | preliminary | 0.3021 | 0.5137 | 0.6024 | 0.5295 | 0.5635 | - | 32.83M | 108.0 |
| 7 | YOLOv12n | YOLO | nano | 3 | preliminary | 0.2938 | 0.4839 | 0.5939 | 0.4776 | 0.5294 | - | 2.57M | 6.5 |
| 8 | YOLOv8n | YOLO | nano | 3 | preliminary | 0.2925 | 0.4812 | 0.5906 | 0.4724 | 0.5249 | - | 3.01M | 8.2 |
| 9 | YOLOv11n | YOLO | nano | 3 | preliminary | 0.2877 | 0.4750 | 0.5864 | 0.4699 | 0.5217 | - | 2.59M | 6.5 |

## Statistical Snapshot

Seed count `3` is preliminary; seed count `5+` is the main statistical setting.

| Metric | Baseline | Candidate | Seeds | Level | Delta | t-test p | Wilcoxon p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| best_AP | YOLOv9s | YOLOv8n | 3 | preliminary | -0.0509 | 0.0003 | 0.2500 |
| best_AP | YOLOv9s | YOLOv11n | 3 | preliminary | -0.0557 | 0.0004 | 0.2500 |
| best_AP | YOLOv9s | YOLOv12n | 3 | preliminary | -0.0496 | 0.0006 | 0.2500 |
| best_AP | YOLOv9s | YOLOv12s | 3 | preliminary | -0.0112 | 0.0015 | 0.2500 |
| best_AP | YOLOv9s | YOLOv11s | 3 | preliminary | -0.0171 | 0.0015 | 0.2500 |
| best_AP | YOLOv9s | YOLOv5su | 3 | preliminary | -0.0155 | 0.0056 | 0.2500 |
| best_AP | YOLOv9s | YOLOv8s | 3 | preliminary | -0.0105 | 0.0219 | 0.2500 |
| best_AP | YOLOv9s | RT-DETR-L | 3 | preliminary | -0.0413 | 0.0576 | 0.2500 |
| best_AP50 | YOLOv9s | YOLOv8n | 3 | preliminary | -0.0732 | 0.0003 | 0.2500 |
| best_AP50 | YOLOv9s | YOLOv12s | 3 | preliminary | -0.0159 | 0.0004 | 0.2500 |
| best_AP50 | YOLOv9s | YOLOv12n | 3 | preliminary | -0.0705 | 0.0012 | 0.2500 |
| best_AP50 | YOLOv9s | YOLOv11s | 3 | preliminary | -0.0261 | 0.0014 | 0.2500 |

## Metric Notes

- `AP` is mAP50-95 and is used as the detector accuracy proxy.
- `AP50`, `P` precision, `R` recall, and `F1` are reported alongside AP.
- `FPS` and `latency_ms` appear when validation/inference speed is available.
- `Params` and `GFLOPs` are used to separate nano/small/medium/large comparisons.
- Incomplete, cancelled, or failed runs should be interpreted separately from completed seed summaries.
