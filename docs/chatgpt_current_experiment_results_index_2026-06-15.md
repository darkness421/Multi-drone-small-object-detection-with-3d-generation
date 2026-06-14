# ChatGPT 5.5 Current Experiment Results Index

Updated: 2026-06-15 KST

Use this file as the entry point when asking ChatGPT 5.5, GPT-5.5 Pro, or another paper-writing assistant to review the current ACCV detector experiments, generate PPT material, or update paper text.

## Start Here

Repository branch:

- `server-baseline-pipeline`

Latest pushed result commits before this index:

- `181cb2a Update live detector paper figures`
- `ecf2481 Add professor meeting PPT brief`

Core instruction for downstream assistants:

> Read this index first, then use the linked tables and figures. Do not mix `640-eval` related-work rows into the main `1280 / 3-seed` detector table. Treat active training runs as provisional. Do not claim speed improvement for the current proposed detector.

## Current Main Detector Result

Main protocol:

- Dataset: VisDrone validation
- Input size: `1280`
- Seeds: `42, 123, 2026`
- Main comparison rule: only completed `1280 / 3-seed` rows belong in the main paper detector table

Current paper-ready leader:

| Method | AP | AP50 | Precision | Recall | F1 | Params | GFLOPs | Seeds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ours: P2P4-SelfAttnFR | 0.3822 | 0.6052 | 0.6732 | 0.5872 | 0.6273 | 20.82M | 109.30 | 42,123,2026 |
| YOLOv11l | 0.3777 | 0.5981 | 0.6666 | 0.5881 | 0.6248 | 25.32M | 87.30 | 123,2026,42 |
| YOLOv12l | 0.3771 | 0.5958 | 0.6698 | 0.5805 | 0.6219 | 26.40M | 89.40 | 123,2026,42 |
| YOLOv8l | 0.3765 | 0.5963 | 0.6695 | 0.5770 | 0.6198 | 43.64M | 165.40 | 123,2026,42 |

Current safe claim:

- Ours is the best completed `1280 / 3-seed` detector in the current table.
- Compared with YOLOv11l, Ours is higher on AP, AP50, and F1 while using fewer parameters.
- Ours uses more GFLOPs than YOLOv11l, so do not claim faster or lower-compute inference yet.

Ours vs YOLOv11l:

- AP: `+0.0045`
- AP50: `+0.0071`
- F1: `+0.0025`
- Params: about `17.8%` lower
- p-values: AP `p=0.0126`, AP50 `p=0.0223`

Important caveat:

- The earlier internal strict target was AP `> 0.3835` with Params `< 25.32M`. The official deduped 3-seed mean for P2P4-SelfAttnFR is `0.3822`, so the stronger wording should be "best confirmed trade-off and statistically higher AP/AP50 than YOLOv11l", not "cleared the 0.3835 AP target."

## Files To Read First

Use these as the main source of truth:

- `outputs/reports/live/figure_update_audit_2026-06-15.md`
- `outputs/reports/live/paper_detector_figures_manifest.md`
- `outputs/reports/final_detector_table_preview.md`
- `outputs/reports/final_detector_table_preview.csv`
- `outputs/reports/final_detector_tables/main_1280_completed_3seed.csv`
- `outputs/reports/detector_rankings/detector_ranking_snapshot.md`
- `outputs/reports/detector_rankings/overall_1280_completed_gated_tradeoff_ranking.csv`
- `outputs/experiments/final_detector_pvalues.csv`

Use this for live/provisional monitoring:

- `outputs/reports/live/training_dashboard.png`

Use this for the professor-meeting PPT:

- `docs/professor_meeting_ppt_brief_2026-06-15.md`
- `outputs/reports/live/professor_meeting_status_20260615.md`
- `outputs/reports/live/professor_meeting_status_20260615.pptx`

## Paper Figure Paths

Main-paper figure candidates:

- `outputs/reports/live/paper_fig01_main_detector_table.png`
- `outputs/reports/live/paper_fig04_ap_ap50_bar_chart.png`
- `outputs/reports/live/paper_fig05_ap_params_scatter.png`
- `outputs/reports/live/paper_fig06_gated_tradeoff_bar.png`
- `outputs/reports/live/paper_fig07_experiment_status_overview.png`

Supplementary or appendix candidates:

- `outputs/reports/live/paper_fig02_yolo_family_scale_table.png`
- `outputs/reports/live/paper_fig03_related_work_pending_table.png`
- `outputs/reports/live/paper_fig08_nms_sweep_top_results.png`
- `outputs/reports/live/supplementary_detector_analysis/figures/ablation_delta_heatmap.png`
- `outputs/reports/live/supplementary_detector_analysis/input_size_sweep_status.md`

Current visual method figures:

- `paper/figures/prof_meeting_fig01_proposed_system_overview.png`
- `paper/figures/fig02_detector_module.png`
- `paper/figures/prof_meeting_fig03_3d_reasoner_flow.png`

## How To Separate Results

Main paper:

- Use only completed `1280 / 3-seed` rows.
- Put Ours vs YOLO-family baselines in the main detector comparison.
- Include AP, AP50, Precision, Recall, F1, Params, and GFLOPs.
- State that Ours improves AP/AP50/F1 and reduces parameter count relative to YOLOv11l.
- Keep NMS, heatmaps, detailed input-size sweeps, and pending related-work consistency rows out of the main detector table unless they become complete and protocol-consistent.
- Avoid long full tables in the main paper. For result figures, prefer compact top-k tables, grouped bar charts, scatter plots, and trade-off plots that fit one column or one page cleanly. Put the exhaustive detector ranking in supplementary/appendix and keep the CSV as the source of truth.

Supplementary:

- Put NMS sweeps, input-size sweep status, Grad-CAM/heatmap ablation, additional qualitative examples, failure cases, hyperparameters, and detailed implementation notes here.
- Put the long full comparison table, all tested YOLO-family variants, and `640-eval` related-work snapshots here until retraining/evaluation is complete under the same `1280 / 3-seed` protocol.

Live dashboard:

- Use only for current monitoring and professor-meeting status.
- Active runs are not final paper rows.

## Related-Work Status

Currently separated from the main table because they are `640-eval` snapshots:

- `CSFPR-RTDETR`
- `LEAF-YOLO-S`
- `LEAF-YOLO-N`

The current main table already includes broad YOLO-family baselines at `1280 / 3-seed`, including nano, small, medium, large, and RT-DETR-L rows. Related-work models should be added to the main table only after protocol-consistent `1280 / 3-seed` results are complete.

## Proposed Detector Structure Summary

Current proposed detector candidate:

- `P2P4-SelfAttnFR`

High-level interpretation for text/figures:

- Multi-scale detection improvement: adds small-object-friendly high-resolution detector paths, especially P2/P4 style feature usage.
- Lightweight enhancement: keeps Params below YOLOv11l while improving AP/AP50/F1.
- Attention/activation direction: uses SelfAttnFR-style enhancement for small, dense, overlapping UAV targets.

Safe wording:

- "The current confirmed detector candidate is P2P4-SelfAttnFR."
- "The final detector name and module composition may still be refined after remaining queued experiments and ablation checks."
- "Single-run P2-CBAM-FR and P2-DCT-FR have higher raw AP, but they are not yet confirmed with the same completed 3-seed protocol."

## Suggested Prompt For ChatGPT 5.5

Copy this prompt when asking another assistant to help with PPT or paper writing:

```text
You are helping prepare an ACCV 2026 paper and professor-meeting PPT for the repository branch server-baseline-pipeline.

First read docs/chatgpt_current_experiment_results_index_2026-06-15.md.
Then read:
- outputs/reports/final_detector_table_preview.md
- outputs/reports/live/figure_update_audit_2026-06-15.md
- outputs/reports/live/paper_detector_figures_manifest.md
- outputs/reports/detector_rankings/detector_ranking_snapshot.md

Use only completed 1280 / 3-seed rows for the main detector comparison.
Do not mix 640-eval related-work snapshots into the main detector table.
Treat active training dashboard rows as provisional.
Do not claim speed improvement because Ours has higher GFLOPs than YOLOv11l.
Avoid long full tables in the main paper figures. Make compact top-k tables or plots for the main paper, and move exhaustive rankings to supplementary.

Current safe detector claim:
Ours: P2P4-SelfAttnFR achieves AP 0.3822, AP50 0.6052, F1 0.6273, Params 20.82M, outperforming YOLOv11l on AP/AP50/F1 with fewer parameters under the completed 1280 / 3-seed protocol.

Please generate a concise PPT/paper summary with:
1. current detector status,
2. main-paper table/figure recommendations,
3. supplementary material separation,
4. remaining experiment queue and caveats.
```

## Quick Checklist Before Using In Paper

- Confirm the paper table uses `outputs/reports/final_detector_tables/main_1280_completed_3seed.csv`.
- Confirm related-work rows are labeled pending or supplementary if still `640-eval`.
- Confirm the final detector figure caption says "current candidate" if the model may still change.
- Confirm the paper does not overclaim speed or compute efficiency.
- Confirm final Overleaf/GitHub update includes only paper-ready tables and figures, while live dashboards remain for monitoring.
