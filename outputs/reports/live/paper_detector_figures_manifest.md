# Paper Detector Figure PNG Manifest

Generated files for LaTeX manuscript insertion. The PNGs intentionally omit large embedded titles because the paper captions carry the figure titles.
Rows with only 640-pixel evaluation are excluded from paper-facing 1280-pixel figures. Blank cells in the YOLO-family scale overview are unselected family-scale combinations, not unfinished paper claims. YOLOv9c is included as the YOLOv9 large-anchor row; YOLOv9e is excluded from the paper-facing comparison because it is outside the target size regime.
Paper-facing detector figures are restricted to final Ours, YOLO-family baselines, final ablations, and related-work comparison/status rows. Broad proposed-search candidates are exported separately under `outputs/reports/internal/proposed_search/` for lab review only.

- `paper_fig01_main_detector_table.png`
- `paper_fig02_yolo_family_scale_table.png`
- `paper_fig03_related_work_status_table.png`
- `paper_fig04_ap_ap50_bar_chart.png`
- `paper_fig05_ap_params_scatter.png`
- `paper_fig06_gated_tradeoff_bar.png`
- `paper_fig07_experiment_status_overview.png`
- `paper_fig08_final_ablation_status_table.png`
- `paper_fig08_final_ablation_main_table.png`
- `paper_fig09_final_ablation_delta_bar.png`
- `paper_fig10_final_ablation_metric_heatmap.png`
- `paper_fig11_final_detector_feature_activation_heatmap.png`

Main-paper recommended:
- `paper_fig01_main_detector_table.png`
- `paper_fig04_ap_ap50_bar_chart.png`
- `paper_fig05_ap_params_scatter.png`
- `paper_fig06_gated_tradeoff_bar.png`
- `paper_fig08_final_ablation_main_table.png`
- `paper_fig08_final_ablation_status_table.png`

Supplementary or appendix recommended:
- `paper_fig02_yolo_family_scale_table.png`
- `paper_fig03_related_work_status_table.png`
- `paper_fig07_experiment_status_overview.png`
- `paper_fig09_final_ablation_delta_bar.png`
- `paper_fig10_final_ablation_metric_heatmap.png`
- `paper_fig11_final_detector_feature_activation_heatmap.png`

Internal-only diagnostics:
- Auxiliary cross-dataset stress-test artifacts are intentionally excluded from this paper-facing figure manifest.
