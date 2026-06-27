# ACCV Main Paper vs Supplementary Strategy

Updated: 2026-06-28 KST

## 2026-06-28 Submission Layout Update

The current Overleaf draft must be reorganized so that the conclusion appears
within the ACCV 14-page main-paper limit. If result tables drift beyond the
conclusion or into late pages, keep only the core self-contained results in the
main paper and move supporting material to the supplementary PDF.

Main paper now keeps:

- the compact VisDrone detector comparison table with `Ours` as the final row;
- the compact detector ablation table;
- one AP/parameter or AP/AP50 result figure if space allows;
- the compact MarineCity real-Cesium system-smoke table;
- the compact neural-3D runner-family smoke metric table if it fits;
- one qualitative/system figure built from real MarineCity assets.

Supplementary now receives:

- full YOLO-family scale coverage and detailed related-work protocol tables;
- related-work coverage matrix and citation-only model status;
- Grad-CAM/feature-activation, NMS, input-resolution, and design-search rows;
- real-Cesium capture-source and cross-view graph detail tables;
- AeroGraph prompt schema, reviewed candidate table, and external-provider
  validation checklist until replicated;
- implementation details, hyperparameters, dataset conversion, failure cases,
  and extra qualitative examples.

TinyPerson-style auxiliary stress checks are not part of the active paper claim.
They should not appear in default main/supplementary result artifacts unless the
authors later decide to add a carefully explained limitation note.

Official ACCV 2026 dates:

- Main paper deadline: 2026-07-05
- Supplementary material deadline: 2026-07-08
- Main paper limit: 14 pages including figures and tables

## Core Position

The main paper should not read as a detector leaderboard paper. The strongest
submission story is:

```text
CoM3D-ACE: Cooperative Multi-UAV 3D Ambiguity-Centric Evidence Completion
```

The main claim should be that 2D UAV detections become more useful when they are
converted into a multi-view 3D evidence graph that diagnoses ambiguity, completes
missing evidence, triggers selective re-observation, and optionally uses VLM/LLM
verification only for hard cases.

The detector module is important, but it should be positioned as the front-end
evidence generator and ablation component, not as the only novelty.

## Main Paper Content

The main paper should contain only the minimum content required for reviewers to
understand and trust the contribution.

### Main Paper Must Include

| Section | Main Content | Why It Must Be In Main |
| --- | --- | --- |
| Abstract | Problem, CoM3D-ACE idea, main empirical improvements | Reviewers decide the story early |
| Introduction | Multi-UAV small-object ambiguity, why 2D AP alone is insufficient | Frames the novelty beyond detector AP |
| Related Work | UAV small-object detection, multi-view 3D fusion, VLM/LLM reasoning for UAV | Shows positioning and avoids looking incremental |
| Method Overview | CoM3D-ACE pipeline figure | The central contribution needs one clear system figure |
| Evidence Graph | Nodes, edges, uncertainty, cross-view association | Core technical novelty |
| Ambiguity Diagnosis | false merge/split, occlusion, cross-resolution conflict, missing-view evidence | Explains why the system does more than detection |
| Evidence Completion/Re-observation | targeted view request or confidence repair policy | Turns diagnosis into action |
| Detector Front-end | selected baseline/proposed module summary only | Needed, but should stay compact |
| Dataset/Benchmark Summary | VisDrone/UAVDT plus MarineCity/Isaac overview | Enough for reproducibility without drowning pages |
| Main Experiments | detector table, 3D association, ambiguity resolution, re-observation gain | These prove the claims |
| Main Ablation Summary | compact 4-6 row ablation table | Shows which components matter |
| Qualitative Figure | 2-3 strong visual examples | Essential for perception paper reviewers |
| Limitations | failure cases at a high level | Builds trust and preempts reviewer concerns |

### Main Paper Figure Plan

| Figure | Put In Main? | Content |
| --- | --- | --- |
| Fig. 1 | Yes | Overall CoM3D-ACE pipeline: multi-UAV images -> 2D detections -> 3D evidence graph -> ambiguity diagnosis -> completion/re-observation/VLM |
| Fig. 2 | Yes | Evidence graph construction and ambiguity types |
| Fig. 3 | Yes | Main quantitative results: 3D association/ambiguity/re-observation, not only detector AP |
| Fig. 4 | Yes | Qualitative success cases across multi-view ambiguity |
| Fig. 5 | Maybe | Detector front-end/proposed module schematic if page budget allows |
| Fig. S1+ | Supplement | Extra detector graphs, Grad-CAM, failure cases, prompts, dataset details |

### Main Paper Tables

| Table | Put In Main? | Content |
| --- | --- | --- |
| Table 1 | Yes | Main detector baseline/proposed summary, compressed to best nano/small/medium/large and selected anchors |
| Table 2 | Yes | CoM3D-ACE system comparison: detector-only vs detector+3D graph vs +completion vs +VLM |
| Table 3 | Yes | Main ablation summary: graph, ambiguity diagnosis, re-observation, VLM gate |
| Table 4 | Maybe | UAVDT or cross-dataset validation if strong |
| Table S1-S8 | Supplement | full per-model/per-seed tables, hyperparameters, p-values, all ablations |

## Supplementary Material Content

Supplementary should act as reviewer insurance: everything too long, too
technical, or too exhaustive for the 14-page main paper goes here.

### Supplement Must Include

| Supplement Section | Content | Purpose |
| --- | --- | --- |
| A. Full Experimental Protocol | hardware, software, seeds, deterministic settings, dataset splits | Reproducibility |
| B. Dataset Details | VisDrone/UAVDT conversion, MarineCity scene design, camera poses, weather/occlusion settings | Validates benchmark |
| C. Full Detector Results | all nano/small/medium/large rows, per-seed results, p-values, GFLOPs/Params/FPS | Prevents reviewer complaints about cherry-picking |
| D. Proposed Detector Ablations | SE, CBAM, wavelet stem, partial deformable neck, wavelet+CBAM, full proposed | Shows detector-module exploration |
| E. Hyperparameters | training configs, optimizer, batch, image size, tile settings, graph thresholds | Reproducibility |
| F. Evidence Graph Details | node/edge definitions, score equations, uncertainty terms, association thresholds | Technical depth |
| G. Re-observation Policy Details | selection rule, view scoring, budget limits, stopping criteria | Explains action policy |
| H. VLM/LLM Prompt Details | AeroGraph Reasoner prompt, input fields, output schema, safety/verification rule | Keeps prompt text out of main |
| I. Extra Visual Analysis | Grad-CAM, attention maps, graph overlays, before/after completion | Reviewer intuition |
| J. Failure Cases | dense occlusion, reflective surfaces, extreme scale, cross-view mismatch | Honest limitations |
| K. Additional Qualitative Examples | success/failure panels from multiple scenes | Visual confidence |
| L. Reproducibility Checklist | commands, file paths, model checkpoints, report locations | Submission polish |

### Supplement Figures

| Figure | Content |
| --- | --- |
| S1 | Full detector AP/AP50 chart |
| S2 | Params-vs-AP and GFLOPs-vs-AP |
| S3 | Seed AP distribution |
| S4 | Proposed detector ablation curves |
| S5 | MarineCity scene/camera layout |
| S6 | 3D evidence graph examples |
| S7 | Ambiguity diagnosis examples |
| S8 | Re-observation before/after examples |
| S9 | VLM prompt input/output examples |
| S10 | Failure-case gallery |

## Detector Strategy

The detector result should support the system story. If the proposed detector
does not beat the strongest comparisons by the cutoff date, do not force it as
the main contribution.

### Decision Rule

| Condition | Paper Framing |
| --- | --- |
| Proposed detector beats all comparisons | Present proposed detector as a strong front-end module and include it in main contribution list |
| Proposed detector beats lightweight baseline but not best overall | Frame as efficient evidence front-end; compare system-level gains as main novelty |
| Proposed detector does not beat baselines | Move detector proposal to ablation/supporting module; main contribution becomes ambiguity-centric 3D evidence completion |

### Current Detector Gate

Current status as of 2026-06-01:

- Proposed detector has not yet overwhelmed all comparison models.
- Best old proposed row: Proposed-CBAM-yolo11s.
- Top-3 proposed screening is queued for YOLOv12m, YOLOv10m, and YOLOv9s.
- The paper should not wait too long for detector AP improvements.

## Main vs Supplement Split

### Put In Main

- One compressed detector table.
- One system-level result table.
- One compact ablation table.
- One strong method figure.
- One 3D/evidence graph figure.
- One qualitative success figure.
- Only the most important dataset details.
- Only the best prompt/policy summary.

### Put In Supplement

- All per-seed detector results.
- Large-anchor details.
- Full proposed detector ablations.
- All p-values and statistical-test details.
- Full hyperparameter tables.
- Full dataset conversion details.
- Full MarineCity scene/camera specifications.
- All prompts and output schemas.
- Extra qualitative examples.
- Failure cases.
- Extra graph/Grad-CAM/attention visualizations.

## 32-Day Execution Plan

### Phase 1: Freeze Story And Detector Gate

Dates: 2026-06-01 to 2026-06-07

Goals:

- Finish large-anchor queue.
- Run top-3 proposed detector screening.
- Decide detector framing.
- Start writing Introduction, Related Work, and Method Overview.

Exit criteria:

- One selected detector/front-end policy.
- Main paper figure list frozen.
- Supplement outline created.

### Phase 2: System Experiments

Dates: 2026-06-08 to 2026-06-16

Goals:

- Run detector-to-graph transfer experiments.
- Evaluate association F1, 3D center error, false merge/split, ambiguity resolution.
- Run re-observation gain experiments.
- Generate first full system tables.

Exit criteria:

- Table 2 and Table 3 draft-ready.
- Main qualitative figure candidates selected.

### Phase 3: Supplement Build-Out

Dates: 2026-06-17 to 2026-06-24

Goals:

- Export all detector tables.
- Generate full hyperparameter tables.
- Build dataset/scene/camera documentation.
- Add prompt details and VLM examples.
- Collect failure cases.

Exit criteria:

- Supplement PDF skeleton complete.
- All required appendix figures listed and assigned.

### Phase 4: Main Paper Lock

Dates: 2026-06-25 to 2026-07-02

Goals:

- Compress main paper to 14 pages.
- Finalize figures and tables.
- Polish related work and limitations.
- Ensure main paper stands alone even if reviewers skim supplement.

Exit criteria:

- Main PDF ready for internal review.
- All claims backed by a table/figure or moved to supplement.

### Phase 5: Submission Window

Dates:

- Main paper: 2026-07-03 to 2026-07-05
- Supplement: 2026-07-06 to 2026-07-08

Goals:

- Final PDF checks.
- Anonymity check.
- Reference and formatting check.
- Supplement video/image/code checklist.

## Risk Control

| Risk | Response |
| --- | --- |
| Proposed detector does not beat baselines | Move detector module to supporting ablation; emphasize 3D evidence completion |
| 3D reconstruction methods take too long | Use representative MarineCity scenes and focus on graph/evidence metrics |
| UAVDT validation delays | Keep as supplement or secondary validation |
| Too many experiments | Freeze minimum viable table set by 2026-06-10 |
| Main paper too crowded | Move all full ablations, prompts, per-seed tables, failure cases to supplement |
| Reviewer asks reproducibility | Supplement contains configs, seeds, commands, dataset details |

## Final Recommendation

The main paper should be a clean, system-level ACCV story:

```text
Multi-UAV small-object perception fails not only because detectors miss small
objects, but because evidence is ambiguous across views, scales, and occlusions.
CoM3D-ACE explicitly represents and completes that evidence.
```

The supplement should be the technical vault:

```text
All ablations, full detector comparisons, hyperparameters, dataset details,
prompts, extra visualizations, and failure cases.
```

This split keeps the main paper readable and persuasive while giving reviewers
enough supplementary evidence to trust the system.
