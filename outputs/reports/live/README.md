# Live Training Reports

Last organized: `2026-06-25`

This folder is refreshed by active server experiments. Use it to watch training
progress, but do not treat it as the final paper report.

Current live bundle:

- `training_dashboard.png`: active detector queue view.
- `marinecity_simulation_dashboard.png`: Isaac/Cesium simulation status, live-GUI vs automated-capture distinction, and next viewer160 recapture queue.
- `accv_workflow_status_snapshot.md`: compact current-state handoff for
  detector, MarineCity, AeroGraph, and queue gates.
- `accv_research_package_readiness_audit.md`: paper-claim readiness audit that
  separates complete evidence from smoke-test or pending evidence. The tracked
  GitHub copy is `../../docs/accv_research_package_readiness_audit_2026-06-25.md`.
- `paper_artifact_readiness_check.md`: automated existence/stale-claim check
  for main/supplementary paper artifacts and pending gates.
- `latex_patch_integrity_check.md`: automated check for the Overleaf patch
  bundles, including `\input`, figure paths, labels, references, and allowed
  pending rows.
- `paper_fig01_main_detector_table.png`: paper-facing final detector comparison table.
- `paper_fig02_yolo_family_scale_table.png`: YOLO-family scale coverage table.
- `paper_fig03_related_work_status_table.png`: related-work comparison/status table.
- `paper_fig04_ap_ap50_bar_chart.png`: readable AP/AP50 comparison chart.
- `paper_fig05_ap_params_scatter.png`: AP vs. parameter trade-off chart.
- `paper_fig06_gated_tradeoff_bar.png`: final gated trade-off chart.
- `paper_fig08_final_ablation_main_table.png`: completed final detector ablation table for the main paper.
- `paper_fig09_final_ablation_delta_bar.png`: compact ablation delta chart versus YOLOv11l.
- `paper_fig10_final_ablation_metric_heatmap.png`: supplementary ablation heatmap including exploratory modules.
- `paper_fig11_final_detector_feature_activation_heatmap.png`: Grad-CAM-style feature activation heatmap sheet for YOLOv11l, YOLOv9c, and Ours. Use as supplementary qualitative evidence.
- `final_detector_feature_activation_manifest.json`: source metadata for the feature activation heatmap sheet.
- `final_ablation_main_table.csv`: source CSV for the completed main ablation table.
- `supplementary_detector_analysis/final_ablation_supplementary_table.csv`: source CSV for the supplementary ablation table.
- `final_ablation_artifact_manifest.md`: placement guide for the ablation artifacts.
- `marinecity_3d_reasoner_status_2026-06-24.md`: current real-Cesium MarineCity multi-UAV simulation/reasoner status.
- `marinecity_real_capture_benchmark.md`: verified real-Cesium 3-scenario,
  9-frame RGB/depth/pose capture benchmark manifest for the 3D/reasoner handoff.
- `marinecity_real_capture_benchmark_contact_sheet.png`: contact sheet for the
  real-Cesium capture benchmark. Use it as supplementary capture evidence, not
  as a completed NeRF/3DGS result.
- `marinecity_detector_reasoner_smoke.md`: real-Cesium detector-to-reasoner
  smoke report using the current SAFR-YOLO/P2P4-SelfAttnFR weights on the
  verified 3-scenario x 3-UAV captures. It records 23 EvidenceTokens and the
  deterministic AeroGraph mock plumbing result; use this as system validation,
  not as a labeled MarineCity accuracy benchmark.
- `/home/oem/UAV/uav_marinecity/outputs/uavmarine_session_overlay_status_s0.json`: latest live Isaac session-layer overlay status. It confirms `uavmarine.usd` is the real Cesium root layer and the UAV/object layer is non-destructive.
- `../../experiments/marinecity_viewer160_pipeline_status.md`: current viewer160 recapture/detector/reasoner queue status.
- `../../docs/uavmarine_multiuav_scenarios.md`: live Isaac scenario operation guide.
  The latest viewer160 recapture uses UAV camera altitudes
  `uav_01=140 m`, `uav_02=150 m`, and `uav_03=160 m` for S0/S1/S2; keep this
  separate from CesiumGeoreference height.
- `../../reasoning/gpt_model_comparison/gpt54_vs_gpt55_aerograph_comparison.md`: earlier GPT-style AeroGraph smoke comparison on an 8-token set. It is useful as a policy sanity check, but the current non-mock queue should use the 49-prompt pack below.
- `aerograph_reasoner_nonmock_handoff.md`: prompt/input paths and command shapes
  for running the MarineCity AeroGraph Reasoner with Factory, OpenAI, or another
  non-mock provider.
- `../../docs/aerograph_nonmock_collection_plan.md`: tracked runbook for the
  49-prompt non-mock AeroGraph collection gate, acceptance criteria, and paper
  table promotion commands.
- `aerograph_prompt_pack/`: 49 real-Cesium detector-token AeroGraph prompts plus
  a compact 10-prompt sample for GPT/Factory/local LLM non-mock evaluation.
- `aerograph_prompt_pack/aerograph_manual_response_template_sample10.jsonl`:
  manual web-provider response template. Use
  `scripts/import_aerograph_manual_responses.py` to convert Factory/ChatGPT web
  JSON responses into the same CSV/LaTeX artifacts as the CLI runner.
- `aerograph_prompt_pack/aerograph_manual_response_template_all.jsonl`:
  full 49-prompt manual response template for the final non-mock AeroGraph run.
- `aerograph_prompt_pack/web_batches/`: paste-ready 10-prompt Markdown batches
  for Factory/ChatGPT web non-mock AeroGraph evaluation. Collect the JSONL
  responses and import them with `scripts/import_aerograph_manual_responses.py`.
- `aerograph_prompt_pack/aerograph_web_collection_packet.md`: one-file web LLM
  handoff with all batch paths, raw-output targets, promotion commands, and the
  current pending/valid checklist summary.
- `aerograph_prompt_pack/aerograph_web_collection_checklist.csv`: per-prompt
  tracking sheet for the 49 non-mock AeroGraph responses.
- `../../reasoning/aerograph_web_raw_batches/README.md`: drop-folder guide for
  saving Factory/ChatGPT raw batch answers as `batch_01.md` ... `batch_05.md`
  before normalization and import.
- `../../scripts/normalize_aerograph_web_responses.py`: optional cleanup helper
  for web outputs that contain markdown fences, JSON arrays, or prose around
  the AeroGraph JSONL responses.
- `aerograph_prompt_pack/web_batches/README.md`: batch index, required response
  shape, and import commands for the 49-prompt non-mock collection.
- `aerograph_nonmock_readiness_status.md`: current coverage check for manual
  or provider-run non-mock responses, batch-by-batch progress, and paper-table
  promotion readiness.
- `../../reasoning/aerograph_prompt_pack_eval_dryrun_latest/`: structural validation
  that all 49 prompts can be evaluated into JSONL/CSV/LaTeX outputs. This is
  not a non-mock result; it is a provider-readiness check.
- `../../paper/tables/aerograph_reasoner_results_placeholder.tex`: current
  AeroGraph reasoner table slot. It is filled by the transparent
  `Codex-assisted manual LLM review candidate` import for now; replace it with
  Factory/OpenAI/local-LLM output before making a stronger external-provider
  claim.
- `../../scripts/ubuntu/start_aerograph_nonmock_queue.sh`: tmux wrapper for the
  final 49-prompt non-mock AeroGraph run once `OPENAI_API_KEY` or
  `AEROGRAPH_COMMAND` is configured.
- `../../scripts/ubuntu/run_aerograph_plumbing_test.sh`: local runner-path test
  that writes `outputs/reasoning/aerograph_prompt_pack_eval_plumbing_test/` but
  marks it `paper_claim_allowed=false`, so it cannot satisfy the final
  non-mock paper gate.
- `marinecity_system_test_10plus/`: token-level system-test panels, 3 scenario-level panels, reasoner answers, and paper-ready system smoke-test tables.
- `marinecity_capture_quality/`: visual QA ranking for existing real-Cesium
  MarineCity captures, including black/void ratio and top-candidate contact sheet.
- `marinecity_real_capture_crops/`: cropped real-Cesium visual candidates that
  remove tile-boundary void regions for final recapture framing guidance.
- `marinecity_qualitative_gate.md`: full-frame versus crop-only qualitative
  promotion gate. Current status is main-ready for the clean full-frame
  real-Cesium capture.
- `marinecity_clean_recapture_plan.md`: exact 160 m real-Cesium recapture
  runbook, commands, black/void thresholds, and S0/S1/S2 acceptance criteria.

MarineCity system-test quick links:

- `marinecity_system_test_10plus/contact_sheet_token_tests.png`: input-to-detector-to-reasoner test panels.
- `marinecity_system_test_10plus/contact_sheet_3_scenarios.png`: 3 scenario-level multi-UAV summaries.
- `marinecity_system_test_10plus/paper_system_scenario_table.tex`: LaTeX table for the current system smoke-test result.
- `marinecity_system_test_10plus/reasoner_answers_token_tests.md`: image-by-image reasoner answers and artifact paths.
- `../../paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png`: current paper-facing detector-preview sheet from the real-Cesium 3-scenario smoke run.
- `marinecity_real_capture_benchmark_contact_sheet.png`: 3 scenarios x 3 UAV
  real-Cesium RGB capture grid with altitude and depth/void QA metrics.
- `marinecity_capture_quality/marinecity_capture_quality_top8.png`: ranked
  real-Cesium capture candidates for final qualitative recapture planning.
- `marinecity_capture_quality/marinecity_capture_quality_rank.csv`: source visual
  QA metrics.
- `marinecity_real_capture_crops/marinecity_real_capture_crop_top12.png`: top
  16:9 crops from existing real-Cesium captures. These are crop-only candidates,
  not synthetic replacements or final simulation figures.
- `marinecity_real_capture_crops/marinecity_real_capture_crop_candidates.csv`:
  crop boxes and black/void ratios for the candidate sheet.

Archived old live-only files:

- `outputs/reports/archive/live_cleanup_20260621/`: old dashboards, meeting files,
  stale pending/status snapshots, NMS sweep snapshots, and earlier supplementary
  analysis artifacts moved out of the active live folder.
- `outputs/reports/archive/live_nonpaper_20260624/`: previous Isaac/Cesium
  status files, older Fig. 1/Fig. 3 handoff images, smoke-test previews, and
  internal dashboards that are not current paper-facing artifacts.
- `outputs/reports/archive/legacy_marinecity_system_test_11_20260625/`: old
  11-test MarineCity smoke outputs superseded by the current 49 token-level
  real-Cesium viewer160-clean actor-session system-test bundle.

Internal-only proposed detector search figures now live outside this paper-facing
folder at `outputs/reports/internal/proposed_search/`. Do not insert those broad
single-seed search figures into the paper.

After a queue finishes, promote a clean snapshot with:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
```

Continuous ACCV queue entrypoint:

```bash
bash scripts/ubuntu/start_accv_continuous_queue.sh
```

Optional Factory AI supervisor/reasoner hook:

```bash
ENABLE_FACTORY_SUPERVISOR=1 \
FACTORY_COMMAND='<factory command that reads prompt from stdin>' \
bash scripts/ubuntu/start_accv_continuous_queue.sh
```
