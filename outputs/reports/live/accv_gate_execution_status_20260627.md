# ACCV Gate Execution Status - 2026-06-27

This status file follows the gate-first rule: when a gate finishes, move to the
next gate immediately instead of waiting for the next calendar date.

## Current Snapshot

| Track | Status | Paper Decision |
| --- | --- | --- |
| 2D detector | fixed | Use `Ours` in paper tables; implementation label is SAFR-YOLO/P2P4-SelfAttnFR |
| 2D ablation/statistics | fixed | Main table + supplementary heatmaps/activation/NMS/input-size details |
| Related-work detector coverage | fixed for current draft | Include completed cited rows; keep dependency-blocked rows in supplementary coverage |
| TinyPerson | closed archive-only | Exclude from default main and supplementary; mention only as future/domain-transfer limitation if needed |
| MarineCity real-Cesium smoke | ready | Use as system/protocol validation with real MarineCity captures, UAV views, EvidenceTokens, and graph handoff |
| Neural 3D smoke | ready | Use Nerfacto 12k, Instant-NGP 5k, and Splatfacto/3DGS-style 5k as runner-family smoke rows |
| AeroGraph reasoner | candidate-ready, external pending | Keep 49-prompt Codex-reviewed candidate table; do not claim external-provider validation yet |
| Paper compile/reference QA | next | Full Overleaf `main.tex` reference-order check still needs the actual Overleaf source |

## Evidence That Can Be Claimed Now

- Ours improves AP/AP50 over YOLOv11l under the normalized VisDrone2019-DET
  1280-pixel, three-seed protocol while using fewer parameters.
- Paired-seed AP/AP50 tests against YOLOv11l are available.
- Main detector comparison, ablation, related-work status, and paper figures are
  prepared as LaTeX-ready patches/artifacts.
- Real-Cesium MarineCity system smoke has three UAV views, detector tokens,
  cross-view graph construction, and neural 3D runner-family smoke metrics.

## Claims To Avoid Until Final Validation

- Do not claim TinyPerson superiority.
- Do not call the current neural 3D rows a fully optimized benchmark.
- Do not call AeroGraph externally validated until non-mock provider responses
  are imported and checked.
- Do not claim lower detector compute or faster inference unless profiling
  supports it; the safe detector claim is AP/AP50/parameter efficiency.

## Immediate Queue

1. Assemble the main-paper result patch around the fixed 2D detector, compact
   ablation, AP/Params trade-off, and MarineCity system smoke evidence.
2. Keep long YOLO-family, module-search, Grad-CAM/heatmap, NMS, and coverage
   material in the supplementary patch.
3. Refresh Fig. 1/Fig. 3 handoff only with real-Cesium screenshots, detector
   overlays, neural-3D contact sheets, and evidence-graph assets.
4. Run local patch integrity after every paper artifact update.
5. When the Overleaf source is available locally, check reference order,
   `\cite{}` coverage, table overflow, figure paths, and main/supp duplication.

## 6/27-6/29 Working Targets

| Date | Latest Target | If Finished Early |
| --- | --- | --- |
| 6/27 | Freeze system evidence and begin draft assembly | Move directly to main/supp QA |
| 6/28 | Clean qualitative figure package and supplementary split | Move directly to reference/table/figure QA |
| 6/29 | Full system experiment audit and Fig. 1/Fig. 3 handoff check | Move directly to professor-review draft polish |

