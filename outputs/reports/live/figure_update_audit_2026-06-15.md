# Live Figure Update Audit

Updated: 2026-06-15 01:02 KST

This snapshot was regenerated from the current experiment CSV/results artifacts
without launching new training.

## Regenerated Core Artifacts

- `outputs/reports/final_detector_table_preview.csv`
- `outputs/reports/final_detector_table_preview.md`
- `outputs/reports/final_detector_table_preview.tex`
- `outputs/reports/detector_rankings/*.csv`
- `outputs/reports/detector_rankings/detector_ranking_snapshot.md`
- `outputs/experiments/nms_sweep_summary.csv`

## Regenerated Live Figures

- `training_dashboard.png`
- `paper_fig01_main_detector_table.png`
- `paper_fig02_yolo_family_scale_table.png`
- `paper_fig03_related_work_pending_table.png`
- `paper_fig04_ap_ap50_bar_chart.png`
- `paper_fig05_ap_params_scatter.png`
- `paper_fig06_gated_tradeoff_bar.png`
- `paper_fig07_experiment_status_overview.png`
- `paper_fig08_nms_sweep_top_results.png`
- `supplementary_detector_analysis/figures/ablation_delta_heatmap.png`

## Current Main Detector Status

Main protocol is VisDrone validation, 1280 input, 3 seeds.

| Rank | Method | AP | AP50 | F1 | Params | Protocol |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Ours: P2P4-SelfAttnFR | 0.3822 | 0.6052 | 0.6273 | 20.82M | 1280 / 3-seed |
| 2 | YOLOv11l | 0.3777 | 0.5981 | 0.6248 | 25.32M | 1280 / 3-seed |
| 3 | YOLOv12l | 0.3771 | 0.5958 | 0.6219 | 26.40M | 1280 / 3-seed |
| 4 | YOLOv8l | 0.3765 | 0.5963 | 0.6198 | 43.64M | 1280 / 3-seed |

Ours vs YOLOv11l:

- AP: +0.0045
- AP50: +0.0071
- F1: +0.0025
- Params: lower by about 17.8%
- p-values: AP p=0.0126, AP50 p=0.0223

## Notes

- Main comparison figures use completed 1280 / 3-seed rows only.
- Active runs are shown only in `training_dashboard.png`.
- Related-work 640-eval rows remain separated from the main table until 1280
  consistency is complete.
- `paper_fig08_nms_sweep_top_results.png` and the supplementary heatmap are
  supportive/supplementary figures, not final main-paper claims.
