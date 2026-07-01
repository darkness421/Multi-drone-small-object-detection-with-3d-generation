# Paper Draft Notes

## Working Title

CoM3D-ACE: Ambiguity-Centric 3D Evidence Completion for Cooperative Multi-UAV Fine-Grained Object Detection in Urban Digital Twins

## Current Paper Patch - 2026-06-27

- Current selected detector: `Ours` in result tables.
- Current implementation/method label: `SAFR-YOLO/P2P4-SelfAttnFR`.
- Contribution wording rule: avoid weak phrasing such as "we study". Use
  "we propose", "we introduce", "we construct", and "we validate" for the
  actual contributions.
- Main detector claim should stay conservative: higher AP/AP50 and fewer
  parameters than YOLOv11l under the normalized 1280-pixel three-seed protocol.
  Do not claim lower compute or faster inference yet because GFLOPs are higher.
- Current experiment section patch:
  `paper/sections/05_experiments_current_detector_status.tex`
- Current MarineCity readiness patch:
  `paper/sections/06_marinecity_3d_readiness.tex`
- Supplementary detector inventory:
  `paper/sections/supp_detector_experiment_inventory.tex`
- Current rough detector structure figure:
  `paper/figures/fig02_detector_module.svg`
- Current detector evidence:
  `SAFR-YOLO` has AP 0.3822 +/- 0.0007 and AP50 0.6052 +/- 0.0012
  across seeds 42, 123, and 2026. YOLOv11l has AP 0.3777 +/- 0.0004 and AP50
  0.5981 +/- 0.0011. The paired-seed p-values are 0.0126 for AP and 0.0223 for
  AP50.
- Detector results should show two paper-facing comparison views: (1) Ours
  versus YOLO-family/transformer baselines under the normalized 1280-pixel,
  three-seed protocol, and (2) related-work reproduction/status rows so prior
  UAV small-object detectors are visibly accounted for.
- Related-work detector checks now include normalized 1280-pixel, three-seed
  rows for CSFPR-RTDETR, MFFSODNet, SFFEF-YOLO, BPD-YOLO, HF-D-FINE, and
  UAVDet. LEAF-YOLO remains internal-only unless it is explicitly cited in the
  manuscript.
- MarineCity Isaac/Cesium status: Isaac Sim 5.1 opens the user-verified real
  Cesium `uavmarine.usd` stage with Google/Cesium tiles visible, and the
  P2P4-SelfAttnFR detector smoke test exports EvidenceTokens for three
  MarineCity scenarios. Treat the current outputs as real-Cesium
  system/protocol smoke evidence.
- MarineCity neural 3D status: three runner-family smoke rows are available on
  the real-Cesium capture package. The current Nerfacto full-res 12k row reports
  PSNR 22.27, SSIM 0.939, LPIPS 0.074, and FPS 0.16; Instant-NGP 5k reports
  PSNR 21.62, SSIM 0.897, LPIPS 0.117; and Splatfacto/3DGS-style 5k reports
  PSNR 19.68, SSIM 0.807, LPIPS 0.170, and FPS 4.56. Use these as
  system-smoke validation, not as a full 3D benchmark.
- AeroGraph status: a 49-prompt schema-check record is available as
  supplementary validation support. External
  OpenAI/ChatGPT/local-provider replication should be imported before promoting
  it as the headline reasoner result.
- Auxiliary cross-dataset stress checks are excluded from the default main and
  supplementary paper unless the protocol is fully aligned with the main
  VisDrone-controlled comparison.
