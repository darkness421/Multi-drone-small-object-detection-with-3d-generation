# ACCV Submission Execution Plan

Updated: `2026-06-27`

This plan merges the original submission schedule with the current evidence
state. It separates paper-ready claims from pending gates so that the main paper
does not overclaim unfinished 3D or reasoner results.

## Current State

| Track | Status | Current Evidence | Paper Use |
| --- | --- | --- | --- |
| 2D detector main result | fixed | Ours 3-seed VisDrone 1280 result is ready; NMS and input-resolution sweeps are complete. | Main |
| 2D ablation | fixed | Core ablation table, AP/Params trade-off, heatmap/feature activation sheets are ready. | Main + supplementary |
| TinyPerson | closed archive-only | Protocol/class mismatch; corrected diagnostic does not support our main claim. | Exclude by default |
| MarineCity system smoke | smoke-ready | Real-Cesium stage, 3-UAV captures, detector tokens, and cross-view evidence graph are ready. | Main smoke or supplementary |
| MarineCity neural 3D | smoke-ready | RGB/depth/pose, transforms, point-cloud smoke, and three held-out neural-runner metric rows are ready: Nerfacto 12k, Instant-NGP 5k, and Splatfacto/3DGS-style 5k. | Main smoke or supplementary |
| AeroGraph reasoner | pending external validation | Codex-assisted candidates exist; external non-mock replication is not yet complete. | Pending |
| Paper sync/compile | pending full check | GitHub artifacts are updated; full Overleaf/main.tex compile still needs final check. | Paper ops |

## Date Plan

| Date | Main Goal | Concrete Work | Output |
| --- | --- | --- | --- |
| 6/27 | System-level result consolidation | Re-run/refresh MarineCity real-Cesium capture + detector + reasoner smoke; verify actors/UAV cameras/classes; freeze 2D result bundle; lock the 12k Nerfacto, 5k Instant-NGP, and 5k Splatfacto/3DGS-style smoke rows as current paper-safe neural-3D evidence. | Updated simulation dashboard, smoke reports, 3D smoke table, Fig. 1/3 source package candidates |
| 6/28 | System-level result cleanup | Improve object balance/natural placement if needed; collect qualitative panels; prepare 23-prompt non-mock reasoner path. | Paper-ready system smoke table and qualitative panels |
| 6/29 | Full system experiment audit | Re-check detector tables, simulation evidence, reasoner status, 3D runner status; update final Fig. 1/Fig. 3 guidance package for GitHub. | Final experiment audit and figure revision handoff |
| 6/30 | Full draft completion target | Finish main/supp draft skeleton with fixed 2D, system smoke, pending-safe 3D/reasoner wording; add Isaac validation images. | Complete draft for professor review |
| 6/30-7/5 | Main paper writing and revision | Tighten introduction/related work, contribution wording, method, experiments, references, table/figure overflow, equations. | Main paper submission on 7/5 |
| 7/6 | Supplementary polish | Move long ablations, implementation details, Grad-CAM/heatmaps, extra qualitative/failure cases into supplementary. | Supplementary final draft |
| 7/7 | Supplementary submission | Final compile, reference/order check, figure/table path check. | Supplementary submission |

## Work Breakdown

### Main Paper

- Detector comparison table: fixed, use `Ours` as the model name.
- Ablation core table: fixed, keep only main modules and the final selected
  detector path.
- AP/Params trade-off figure: fixed.
- MarineCity system result: include as real-Cesium system smoke/protocol
  validation. Use the Nerfacto, Instant-NGP, and Splatfacto/3DGS-style rows as
  neural-3D runner-family smoke evidence, not as a full optimized
  reconstruction benchmark.
- Figure 1 and Figure 3: update after final MarineCity qualitative package is
  refreshed.

### Supplementary

- YOLO-family full scale table.
- Related-work/model availability details.
- Grad-CAM/feature-activation and ablation heatmaps.
- NMS robustness and input-resolution sensitivity.
- TinyPerson: keep out by default. If mentioned, use only as a limitation or
  protocol-mismatch note, not as a comparative result.
- Failure cases: include person/pedestrian weak detection in current MarineCity
  smoke as a limitation unless fixed by improved placement/capture.

## Remaining Gates

| Priority | Gate | Required To Claim | Next Action |
| --- | --- | --- | --- |
| P0 | Paper-safe 2D bundle | Already ready | Keep frozen; only formatting/table cleanup |
| P1 | Neural 3D result | At least one real runner result or defensible reconstruction sanity result | Done with three runner-family smoke rows; Nerfacto 12k is the current quality row |
| P1 | AeroGraph non-mock | 23-prompt compact non-mock first, then 49-prompt final if time allows | Run/import ChatGPT/Codex/OpenAI/local responses |
| P2 | MarineCity qualitative package | Natural object placement, 3 UAV views, detector overlays, evidence graph panels | Refresh capture/detector/reasoner smoke and update Fig. 1/3 handoff package |
| P2 | Paper QA | Reference order, formula consistency, figure/table overflow, main/supp split | Run final checks after draft assembly |

## Claiming Rules

- Do not claim TinyPerson superiority.
- Do not claim a completed full neural-3D benchmark from the current smoke rows;
  they support system validation and runner-family executability only.
- Do not claim external LLM validation until non-mock response import/check passes.
- It is safe to claim the current MarineCity package as real-Cesium system smoke
  validation with RGB/depth/pose, detector EvidenceTokens, and cross-view graph
  plumbing.
