# Professor Meeting PPT Brief

Updated: 2026-06-15 KST

Purpose: give ChatGPT or another slide-generation tool a clean, paper-safe
brief for a professor meeting about the ACCV 2026 project status.

## One-Line Status

We have a strong 2D detector trade-off candidate, `Ours: SAFR-YOLO`,
confirmed under the VisDrone 1280-resolution 3-seed protocol. It currently ranks
first among the completed main-protocol detector results, but the absolute AP
margin is still modest, so the remaining comparison, ablation, and heatmap
evidence are important before freezing the final paper claim.

## Current 2D Detector Result

Protocol: VisDrone val, image size 1280, seeds 42/123/2026.

| Method | AP | AP50 | Precision | Recall | F1 | Params | GFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ours: SAFR-YOLO | 0.3822 | 0.6052 | 0.6732 | 0.5872 | 0.6273 | 20.82M | 109.3 |
| YOLOv11l baseline | 0.3777 | 0.5981 | 0.6666 | 0.5881 | 0.6248 | 25.32M | 87.3 |

Delta vs YOLOv11l:

- AP: +0.0045 absolute.
- AP50: +0.0071 absolute.
- F1: +0.0025 absolute.
- Params: about 17.8% lower.
- GFLOPs: about 25.2% higher because P2/P4 high-resolution paths are more
  expensive.
- Paired t-test: AP p=0.0126, AP50 p=0.0223.

Safe interpretation for the meeting:

- Strongest claim now: better AP/AP50 with fewer parameters than the strongest
  YOLOv11l baseline under the same 3-seed protocol.
- Do not claim a large speed improvement yet.
- Do not overstate the strict internal target: the AP > 0.3835 target is not
  fully cleared by the official deduplicated 3-seed mean yet.
- Best paper framing: small-object-oriented detector with improved
  accuracy/parameter trade-off.

## Top Main-Protocol Ranking Snapshot

All rows below are completed 1280-resolution 3-seed results.

| Rank | Method | AP | AP50 | F1 | Params |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | Ours: SAFR-YOLO | 0.3822 | 0.6052 | 0.6273 | 20.82M |
| 2 | YOLOv11l | 0.3777 | 0.5981 | 0.6248 | 25.32M |
| 3 | YOLOv12l | 0.3771 | 0.5958 | 0.6219 | 26.40M |
| 4 | YOLOv8l | 0.3765 | 0.5963 | 0.6198 | 43.64M |
| 5 | YOLOv26l | 0.3732 | 0.5877 | 0.6136 | 26.19M |

## Current Active Runs

These runs are comparison reinforcement, not proposed-detector search.

- `yolo12s-s42`: epoch 59/100 at last check, best AP 0.3353, AP50 0.5421,
  F1 0.5775, params 9.26M.
- `yolo12s-s123`: epoch 17/100 at last check, best AP 0.3023, AP50 0.4959,
  F1 0.5358, params 9.26M.

Live monitoring file:

- `outputs/reports/live/training_dashboard.png`

## Related-Work Comparison Status

Current related-work rows are separated from the main table because they are
currently 640-eval snapshots, not fully matched 1280/3-seed retraining.

Completed/evaluated snapshots:

- CSFPR-RTDETR: AP 0.3279, AP50 0.5253, params 14.09M, 640 eval.
- LEAF-YOLO-S: AP 0.2810, AP50 0.4820, params 4.28M, 640 eval.
- LEAF-YOLO-N: AP 0.2190, AP50 0.3970, params 1.20M, 640 eval.

Queue/planning:

- Re-evaluate or retrain CSFPR-RTDETR and LEAF-YOLO under a consistent
  1280-resolution protocol where feasible.
- Add at least five related-work models if code/checkpoints/adapters are usable.
- Skip papers without runnable code unless the core idea is lightweight enough to
  implement fairly.

## Proposed System and Model Figures

Use these local figure assets as slide attachments or as references for ChatGPT
image/PPT generation:

- Overall proposed system:
  `paper/figures/prof_meeting_fig01_proposed_system_overview.png`
- Proposed detector/model module:
  `paper/figures/fig02_detector_module.png`
- Planned 3D benchmark + reasoner flow:
  `paper/figures/prof_meeting_fig03_3d_reasoner_flow.png`
- Paper-ready detector table:
  `outputs/reports/live/paper_fig01_main_detector_table.png`
- AP/AP50 comparison chart:
  `outputs/reports/live/paper_fig04_ap_ap50_bar_chart.png`
- AP vs params trade-off chart:
  `outputs/reports/live/paper_fig05_ap_params_scatter.png`

Figure caveat:

- The overall system and 3D/reasoner figures are meeting-ready planning figures.
  They are not final camera-ready ACCV figures.
- `fig02_detector_module.png` is the detector/model figure that should be
  refined after final ablation naming is fixed.

## Remaining Experiments

Detector-side:

- Finish remaining YOLO family n/s/m/l comparison coverage.
- Complete related-work comparison queue with at least five runnable or
  implementable prior models.
- Build the final ablation table:
  - YOLOv11l baseline.
  - P2/P4 high-resolution head only.
  - SelfAttnFR module only if separable.
  - P2/P4 + SelfAttnFR.
  - NMS/post-processing variants.
- Produce heatmaps/Grad-CAM for baseline vs proposed detector.
- Add per-category AP/F1/recall and input-resolution sensitivity to the
  supplementary material.

3D/simulation/reasoner side:

- Start NVIDIA Isaac / marine-city map / multi-drone capture setup after the 2D
  detector queue stabilizes.
- Build the 3D benchmark pipeline from reconstruction + simulation + restoration
  module.
- Run detector-only vs detector+3D vs detector+3D+reasoner comparisons.
- Evaluate the reasoner with decision accuracy, evidence trace, and
  re-observation benefit.

Paper side:

- Main paper: self-contained system, proposed detector, 3D benchmark idea,
  ACE-Reasoner, and key quantitative results.
- Supplementary: ablation details, hyperparameters, dataset details, heatmaps,
  extra qualitative/quantitative results, failure cases, and implementation
  details.
- Keep the main table restricted to consistent 1280/3-seed results.
- Put 640-eval related-work snapshots in a separate table until the fair
  protocol is completed.

## Suggested 10-Slide PPT Structure

1. Title and project goal.
2. Overall proposed system figure.
3. Current one-line status and three contributions.
4. Proposed 2D detector/model figure.
5. Key 2D result vs YOLOv11l.
6. Main detector ranking table.
7. AP/AP50 chart and AP-vs-params trade-off chart.
8. Remaining comparison and ablation queue.
9. 3D benchmark + reasoner plan.
10. Decisions needed from professor.

## ChatGPT PPT Prompt

Use this prompt in ChatGPT when generating the slide deck:

```text
Create a clean academic PowerPoint deck for a professor meeting.
The project is an ACCV 2026 paper on multi-drone marine-city small object
detection, 3D benchmark generation, and ACE-Reasoner.

Audience: computer vision professor. Tone: concise, technical, honest.
Style: white background, minimal color, readable tables, no marketing design.
Use 10 slides.

Important current result:
- Proposed detector: Ours: SAFR-YOLO.
- Protocol: VisDrone val, 1280 image size, 3 seeds 42/123/2026.
- Ours: AP 0.3822, AP50 0.6052, F1 0.6273, Params 20.82M, GFLOPs 109.3.
- YOLOv11l baseline: AP 0.3777, AP50 0.5981, F1 0.6248, Params 25.32M, GFLOPs 87.3.
- Delta vs YOLOv11l: AP +0.0045, AP50 +0.0071, F1 +0.0025.
- Params are 17.8% lower, but GFLOPs are 25.2% higher.
- Paired t-test: AP p=0.0126, AP50 p=0.0223.
- Do not overclaim speed improvement. Say the current strength is accuracy/parameter trade-off.
- Mention that the strict internal AP > 0.3835 target is not fully cleared yet.

Use these figures if attached:
1. Overall proposed system overview.
2. Proposed detector/model module.
3. Detector result table.
4. AP/AP50 comparison chart.
5. AP vs params trade-off chart.
6. 3D benchmark + reasoner flow.

Slide outline:
1. Title and project objective.
2. Overall proposed system.
3. Current status and contributions.
4. Proposed 2D detector/model structure.
5. Key 2D result vs YOLOv11l.
6. Detector ranking table.
7. Trade-off analysis.
8. Remaining 2D experiments: YOLO family, related-work models, ablation, heatmaps.
9. 3D benchmark and reasoner plan.
10. Decisions needed: detector naming/claim, mandatory comparison models, AP vs complexity priority, main/supplement split.

Make the deck professor-meeting friendly:
- Put key numbers large.
- Separate completed 1280/3-seed results from 640-eval related-work snapshots.
- Include caveats in small but visible text.
- End with concrete decisions needed from the professor.
```

## Decisions To Ask

- Can `SAFR-YOLO` be treated as the working proposed detector?
- Which related-work models are mandatory for the comparison section?
- Should the next detector work prioritize a larger AP margin or lower model
  complexity?
- Is the three-contribution structure acceptable:
  1. proposed 2D detector,
  2. 3D marine-city benchmark from reconstruction/simulation/restoration,
  3. reasoner module for final decision and explainability?
- How much main-paper space should be allocated to 2D detector vs 3D benchmark
  vs reasoner?
