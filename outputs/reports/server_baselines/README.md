# Server Baseline Report Bundle

Generated: `2026-06-26T22:36:28+09:00`

This folder is the compact, Git-friendly report bundle for server detector baselines.
Raw datasets, model weights, raw training runs, and caches stay outside Git.

## Current Snapshot

- Recommended next stage: `iterate_proposed_detector`
- Best completed baseline: `YOLOv9m-TinyPersonCornerOriginal AP=0.1997, AP50=0.5291`
- Run status counts: `{"completed": 4}`

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
| 1 | YOLOv9m-TinyPersonCornerOriginal | YOLO | unknown | 2 | preliminary | 0.1997 | 0.5291 | 0.6408 | 0.4943 | 0.5581 | - | - | - |
| 2 | Ours-TinyPersonCornerOriginal | Other | unknown | 2 | preliminary | 0.1675 | 0.4429 | 0.5440 | 0.4224 | 0.4755 | - | - | - |

## Statistical Snapshot

Seed count `3` is preliminary; seed count `5+` is the main statistical setting.

| Metric | Baseline | Candidate | Seeds | Level | Delta | t-test p | Wilcoxon p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| best_AP | YOLOv9m-TinyPersonCornerOriginal | Ours-TinyPersonCornerOriginal | 2 | insufficient_for_pvalue | -0.0323 | - | - |
| best_AP50 | YOLOv9m-TinyPersonCornerOriginal | Ours-TinyPersonCornerOriginal | 2 | insufficient_for_pvalue | -0.0862 | - | - |
| best_F1 | YOLOv9m-TinyPersonCornerOriginal | Ours-TinyPersonCornerOriginal | 2 | insufficient_for_pvalue | -0.0826 | - | - |
| best_recall | YOLOv9m-TinyPersonCornerOriginal | Ours-TinyPersonCornerOriginal | 2 | insufficient_for_pvalue | -0.0720 | - | - |

## Metric Notes

- `AP` is mAP50-95 and is used as the detector accuracy proxy.
- `AP50`, `P` precision, `R` recall, and `F1` are reported alongside AP.
- `FPS` and `latency_ms` appear when validation/inference speed is available.
- `Params` and `GFLOPs` are used to separate nano/small/medium/large comparisons.
- Incomplete, cancelled, or failed runs should be interpreted separately from completed seed summaries.
