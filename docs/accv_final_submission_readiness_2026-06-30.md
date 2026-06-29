# ACCV Submission Readiness Snapshot

Updated: 2026-06-30 KST

## Submission-Ready Claims

- **2D detector:** SAFR-YOLO is ready as the main detector claim. The paper-facing result uses the normalized VisDrone2019-DET 1280-pixel, three-seed protocol with comparison tables, ablation tables, heatmaps, and trade-off figures.
- **MarineCity system validation:** The real-Cesium MarineCity stage is ready as a system-validation claim. The current evidence includes three UAV views, 140--160 m camera altitude, 78 detector EvidenceTokens, 17 graph-level object hypotheses, support/conflict/missing-evidence edges, and action counts for finalize/monitor/reject/re-observation.
- **3D handoff validation:** The neural-3D handoff is ready as runner-family validation, not as a full benchmark claim. Nerfacto, Instant-NGP, and Splatfacto/3DGS-style rows provide PSNR/SSIM/LPIPS/runtime evidence on the exported real-Cesium capture split.
- **AeroGraph reasoner:** The submission-ready claim is limited to graph-grounded schema, verifier, and action-policy validation. External-provider LLM benchmarking remains optional and must not be described as completed unless provider responses are collected and imported.

## Paper Placement

- **Main paper:** compact detector comparison, compact ablation, AP/parameter trade-off, MarineCity qualitative real-Cesium figure, MarineCity 3D validation table, and ambiguity-aware system-efficiency table.
- **Supplementary:** full detector inventory, full ablation, module figures, additional heatmaps, related-work coverage details, cross-view evidence graph, capture-source details, re-observation policy ablation, 3D sweep details, and reasoner schema/verifier validation summary.

## Important Claim Boundaries

- Do not claim a full large-scale 3D reconstruction benchmark.
- Do not claim autonomous UAV control.
- Do not claim completed external-provider AeroGraph benchmarking.
- Do not use fake/proxy city wording for the final MarineCity evidence. The paper-facing system evidence is from the saved real-Cesium MarineCity stage.

## Optional Follow-Up

- External OpenAI/ChatGPT/local-provider response replication for AeroGraph can be added later as supplementary evidence.
- Longer neural-3D runs can strengthen the 3D result but are not required for the current system-validation claim.
- TinyPerson remains auxiliary and should not be mixed into the main VisDrone claim unless retrained and analyzed under a clean, dataset-specific protocol.
