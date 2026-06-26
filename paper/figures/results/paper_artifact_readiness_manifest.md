# Paper Artifact Readiness Manifest

Updated: `2026-06-26 KST`

This manifest is the paper-facing index for current ACCV artifacts. It separates
main-paper-ready items from supplementary items and explicit pending slots.

## Main Paper Ready

| Artifact | Path | Status | Use |
|---|---|---|---|
| Main detector comparison table | `paper/tables/main_detector_comparison_table.tex` | Ready | Compact 1280px three-seed detector comparison |
| Cited related-work detector table | `paper/tables/related_work_detector_status_table.tex` | Ready | Prior UAV detector comparison/status with protocol notes |
| Final detector ablation table | `paper/tables/final_ablation_main_table.tex` | Ready | Main ablation for SAFR-YOLO/P2P4-SelfAttnFR |
| Detector result table figure | `paper/figures/results/paper_fig01_main_detector_table.png` | Ready | Optional compact visual version of detector table |
| AP/AP50 bar chart | `paper/figures/results/paper_fig04_ap_ap50_bar_chart.png` | Ready | Main or supplementary quantitative visual |
| AP vs parameter scatter | `paper/figures/results/paper_fig05_ap_params_scatter.png` | Ready | Trade-off visual |
| Gated trade-off chart | `paper/figures/results/paper_fig06_gated_tradeoff_bar.png` | Ready | Trade-off visual if page budget allows |
| MarineCity system smoke table | `paper/tables/marinecity_system_scenario_table.tex` | Ready with wording limit | Real-Cesium system/protocol smoke-test table |
| MarineCity smoke source CSV | `paper/tables/marinecity_system_token_results.csv` | Ready with wording limit | Source rows for detector-to-reasoner smoke-test table |
| MarineCity real-capture benchmark table | `paper/tables/marinecity_real_capture_benchmark_table.tex` | Ready with wording limit | 3-scenario, 9-frame real-Cesium RGB/depth/pose capture source for the 3D/reasoner handoff |
| MarineCity cross-view evidence graph table | `paper/tables/marinecity_crossview_evidence_graph_table.tex` | Ready with wording limit | 23 real-Cesium EvidenceTokens grouped into 13 smoke-test hypotheses |
| MarineCity detector-preview sheet | `paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png` | Smoke-test ready | Real-Cesium detector preview sheet; use only with system-smoke wording |
| MarineCity qualitative figure slots | `paper/sections/07_marinecity_qualitative_figure_slots.tex` | Ready with wording limit | Optional real-Cesium smoke/protocol figure slots |
| Main result patch bundle | `paper/sections/main_results_patch_bundle.tex` | Ready | Overleaf `\input` bundle for detector + MarineCity protocol sections |
| Supplementary patch bundle | `paper/sections/supplementary_patch_bundle.tex` | Ready | Overleaf `\input` bundle for supplementary detector and MarineCity qualitative slots |
| Paper artifact readiness check | `outputs/reports/live/paper_artifact_readiness_check.md` | Ready | Automated existence and stale-claim audit before Overleaf integration |
| LaTeX patch integrity check | `outputs/reports/live/latex_patch_integrity_check.md` | Ready | Automated `\input`, figure, label, and reference check for patch bundles |

## Supplementary Recommended

| Artifact | Path | Status | Use |
|---|---|---|---|
| YOLO-family scale table | `paper/figures/results/paper_fig02_yolo_family_scale_table.png` | Ready | Full n/s/m/l family coverage |
| Related-work visual table | `paper/figures/results/paper_fig03_related_work_status_table.png` | Ready | Supplementary visual companion to related-work table |
| Experiment status overview | `paper/figures/results/paper_fig07_experiment_status_overview.png` | Ready | Audit/protocol transparency |
| Final ablation delta chart | `paper/figures/results/paper_fig09_final_ablation_delta_bar.png` | Ready | Supplementary ablation visual |
| Final ablation heatmap | `paper/figures/results/paper_fig10_final_ablation_metric_heatmap.png` | Ready | Supplementary heatmap |
| Detector feature activation sheet | `paper/figures/results/paper_fig11_final_detector_feature_activation_heatmap.png` | Ready | Supplementary Fig. S4, Grad-CAM-style qualitative evidence |
| TinyPerson 640 stress-test table | `paper/tables/tinyperson_640_stress_table.tex` | Ready | Supplementary domain-shift diagnostic only |
| TinyPerson eval-size sensitivity table | `paper/tables/tinyperson_eval_imgsz_sweep_table.tex` | Ready | Supplementary input-size diagnostic only |
| TinyPerson eval-size sensitivity figure | `paper/figures/results/paper_fig13_tinyperson_eval_imgsz_sweep.png` | Ready | Supplementary input-size diagnostic only |
| MarineCity scenario contact sheet | `paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png` | Smoke-test ready | Main only if clearly labeled; otherwise supplementary |
| MarineCity real-capture benchmark sheet | `paper/figures/results/marinecity_system/marinecity_real_capture_benchmark_contact_sheet.png` | Capture-source ready | Supplementary capture evidence for the 3-scenario x 3-UAV RGB/depth/pose source |
| MarineCity detector-to-reasoner report | `outputs/reports/live/marinecity_detector_reasoner_smoke.md` | Smoke-test ready | Live report for the 23-token SAFR-YOLO to AeroGraph mock plumbing run |
| MarineCity cross-view evidence graph figure | `paper/figures/results/marinecity_system/marinecity_crossview_evidence_graph.png` | Smoke-test ready | Supplementary graph view of support/conflict/missing-evidence links; not metric 3D reconstruction |
| MarineCity cross-view evidence graph report | `outputs/reports/live/marinecity_crossview_evidence_graph.md` | Smoke-test ready | Live report and source summary for the current cross-view evidence graph |
| AeroGraph real-capture compact prompt pack | `outputs/reports/live/aerograph_real_capture_prompt_pack/manifest.json` | Provider-ready smoke gate | 23 prompts matching the latest real-Cesium detector smoke; use before the full 49-prompt final gate |
| MarineCity token contact sheet | `paper/figures/results/marinecity_system/contact_sheet_token_tests.png` | Smoke-test ready | Supplementary token-level qualitative cases |
| MarineCity capture QA sheet | `paper/figures/results/marinecity_system/marinecity_capture_quality_top8.png` | Review/selection aid | Use to choose final recapture |
| MarineCity crop candidates | `paper/figures/results/marinecity_system/marinecity_real_capture_crop_top12.png` | Review/selection aid | Crop-only framing guidance, not final replacement |
| MarineCity qualitative selection manifest | `paper/figures/results/marinecity_system/marinecity_qualitative_selection_manifest.md` | Ready | Captions and placement rules for current real-Cesium qualitative assets |
| MarineCity qualitative gate | `paper/figures/results/marinecity_system/marinecity_qualitative_gate.md` | Ready | Explicit full-frame-vs-crop promotion gate |
| AeroGraph reviewed candidate table | `paper/tables/aerograph_reasoner_results_placeholder.tex` | Candidate ready | 49-prompt Codex-assisted manual review candidate; external provider replication pending |

## Pending Slots

| Artifact | Path | Current Status | Required Before Claim |
|---|---|---|---|
| AeroGraph external-provider replication | `paper/tables/aerograph_reasoner_results_placeholder.tex` | Candidate table ready; external GPT/Factory/local run pending | Re-run all 49 prompts with selected final provider and rebuild table |
| AeroGraph direct manual/API response file | `outputs/reports/live/aerograph_nonmock_readiness_status.md` | Provider-manifest coverage 49/49; direct manual response file 0/49 | Fill `outputs/reasoning/aerograph_manual_responses.jsonl` or configure provider if replacing the candidate manifest |
| AeroGraph non-mock collection plan | `docs/aerograph_nonmock_collection_plan.md` | Ready | Use as the acceptance gate before promoting the reasoner table |
| AeroGraph real-capture compact non-mock smoke | `outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/` | Prompt batches ready; provider responses pending | Collect 23 valid-schema provider responses to sanity-check the current real-Cesium smoke setting |
| Final 3D completion/restoration result | TBD | Not complete | Run validated NeRF/3DGS/restoration or keep as future/pilot protocol |
| Final MarineCity main qualitative image | `uavmarine_s2_viewer160_session_recapture/frame_002_uav_02_rgb.png` | Qualitative gate says full-frame main ready is true; crop supplementary ready is true | Keep as candidate and re-check during final paper layout review |

## Claiming Rules

- The detector result can be claimed as a completed 1280px three-seed result.
- The MarineCity result can be claimed as a real-Cesium multi-UAV system smoke
  and protocol validation, not as a finished 3D reconstruction benchmark.
- MarineCity crop candidates can support supplementary/framing discussion, but
  should not be used as the main full-frame qualitative figure unless the
  caption explicitly says crop-only.
- The AeroGraph table must remain pending until a complete non-mock provider
  manifest is selected by `scripts/build_aerograph_reasoner_table.py`.
- TinyPerson640 should be used only as supplementary domain-shift/limitation
  evidence. The 640px core-model table now has 18 diagnostic rows
  (six models over seeds 42, 123, and 2026), but AP/AP50 values remain near
  zero, so it should not be used as a main detector claim. The eval-size
  sensitivity table reuses completed TinyPerson checkpoints at 640/960/1280
  and is also supplementary-only.
