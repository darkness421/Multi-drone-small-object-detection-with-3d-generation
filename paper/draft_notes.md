# Paper Draft Notes

## Working Title

CoM3D-ACE: Ambiguity-Centric 3D Evidence Completion for Cooperative Multi-UAV Fine-Grained Object Detection in Urban Digital Twins

## Must Finish By Mid-June

- Introduction 1차 완성
- Related Work 1차 완성
- Proposed Method 1차 완성
- Method figure 1차 완성

## Current Paper Patch - 2026-06-16

- Current selected detector candidate: `SAFR-YOLO`.
- Current implementation/run label: `P2P4-SelfAttnFR`.
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
- Related-work detector checks now include 1280-pixel external eval/status rows
  for CSFPR-RTDETR and LEAF-YOLO, with MFFSODNet/UAVDet and other cited UAV
  detectors tracked as pending runnable comparisons until adapters/checkpoints
  are reproducible.
- MarineCity Isaac/Cesium status: Haeundae MarineCity Cesium preview is live on
  port 8093, Isaac Sim 5.1 opens the proxy MarineCity stage on GPU1, and the
  P2P4-SelfAttnFR detector smoke test exports EvidenceTokens, although the
  current proxy visuals are not yet detector-quality validation.
