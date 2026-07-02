# Experiment Outputs Index

Updated: `2026-07-02 KST`

This directory keeps small CSV/JSON/manifests that are safe to version. It is not a raw-run storage area.

## Paper-Facing Detector Results

| Path | Use |
| --- | --- |
| `server_with_proposed_results.csv` | Consolidated detector/proposed result rows |
| `server_with_proposed_summary.csv` | Model-level detector summary |
| `server_with_proposed_pvalues.csv` | Seed statistics and p-values |
| `server_with_top3_proposed_results.csv` | Top proposed-candidate comparison rows |
| `server_with_yolov11_p2_next_results.csv` | YOLOv11/P2 follow-up result rows |
| `final_p2p4_selfattnfr_ablation_results.csv` | Final SAFR-YOLO/P2P4-SelfAttnFR ablation rows |
| `final_p2p4_selfattnfr_ablation_summary.csv` | Final ablation summary table |
| `server_baseline_results.csv` | Baseline detector result rows |
| `server_baseline_summary.csv` | Baseline detector summary table |

## MarineCity And 3D Validation

| Path | Use |
| --- | --- |
| `marinecity_real_capture_benchmark.csv` | Real-Cesium MarineCity capture benchmark rows |
| `marinecity_multiview_benchmark.json` | Multi-view benchmark design/manifest |
| `marinecity_viewer160_pipeline_status.csv` | Viewer160 capture pipeline status |
| `marinecity_isaac_capture_plan.json` | Isaac/Cesium capture plan |
| `3d_generation/` | Small neural-3D manifests and validation figures |

## Archive

Superseded smoke tests, old server queues, generated job scripts, and stale live CSVs belong under `archive/`.
Do not use archived rows as current paper evidence unless they are explicitly promoted into `outputs/reports/` or `paper/`.

## Do Not Store Here

- raw datasets
- `best.pt` / `last.pt` weights
- full Ultralytics run folders
- raw logs
- cache folders
