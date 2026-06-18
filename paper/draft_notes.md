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
- Related-work detector checks now include CSFPR-RTDETR and LEAF-YOLO at
  640-pixel input resolution. Keep these in supplementary material until the
  final comparison table normalizes the protocol.
- MarineCity dry-run readiness is complete at the protocol level: 36 planned
  frames, 4 scenes, 6 view angles, and train/val/unseen-angle test splits of
  19/7/10. This belongs in implementation notes or supplementary material until
  real Isaac/Cesium exports exist.
