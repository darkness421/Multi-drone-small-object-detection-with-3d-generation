# Reports Index

Updated: `2026-07-02 KST`

This directory stores compact experiment summaries and final figures that are small enough to track. It should not contain raw detector runs, weights, datasets, cache folders, or long logs.

## Detector Results

| Path | Use |
| --- | --- |
| `final_detector_table_preview.csv` | Main detector comparison snapshot |
| `final_detector_table_preview.md` | Human-readable detector comparison summary |
| `final_detector_table_preview.tex` | LaTeX detector table source |
| `final_detector_tables/main_1280_completed_3seed.csv` | Main 1280-resolution, three-seed detector source table |
| `final_detector_tables/current_1280_sweep_status.csv` | Sweep status source |
| `detector_rankings/` | Ranked detector result CSVs |

## Live System Reports

| Path | Use |
| --- | --- |
| `live/marinecity_system_integration_check.md` | MarineCity system artifact check |
| `live/marinecity_system_efficiency_report.md` | MarineCity system efficiency summary |
| `live/marinecity_detector_reasoner_smoke.md` | Detector-to-reasoner validation summary |
| `live/marinecity_3d_completion_readiness.md` | Neural 3D readiness gate |
| `live/marinecity_depth_pointcloud_smoke.md` | Depth-fused geometry validation summary |

## Figures

Publication-quality figures are kept either directly in this directory or under `paper/figures/results/`.

Main detector figures:

- `paper_fig01_main_detector_table.png`
- `paper_fig04_ap_ap50_bar_chart.png`
- `paper_fig05_ap_params_scatter.png`
- `paper_fig06_gated_tradeoff_bar.png`
- `paper_fig08_final_ablation_main_table.png`
- `paper_fig09_final_ablation_delta_bar.png`

MarineCity figures:

- `paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png`
- `paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png`
- `paper/figures/results/marinecity_system/marinecity_real_capture_benchmark_contact_sheet.png`
- `paper/figures/results/marinecity_system/marinecity_crossview_evidence_graph.png`

## Reporting Rule

Main comparison rows should come from completed, matched-protocol detector results. Exploratory queue outputs, failed runs, single-seed monitoring rows, and implementation-only checks should stay out of the main detector table.
