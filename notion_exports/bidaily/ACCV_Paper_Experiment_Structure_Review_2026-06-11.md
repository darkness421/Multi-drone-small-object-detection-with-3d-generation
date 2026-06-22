# ACCV Paper Experiment Structure Review - 2026-06-11

## Notion Sync Status

- Live Notion connector check still returns `token_expired`.
- This page is staged as the Notion-ready update until the connector token is refreshed.
- Target project page: ACCV multi-drone small-object detection / 3D generation workspace.

## Short Verdict

The experiment structure is directionally correct and paper-ready as a skeleton:

1. Stage 1: 2D evidence generator / detector front end.
2. Stage 2: MarineCity 3D generation, restoration, and evidence graph.
3. Stage 3: selective VLM/LLM reasoner.
4. Stage 4: full system comparison.

This order is good because it prevents the paper from looking like only a YOLO variant paper. The detector result supports the system, while the full claim is about ambiguity-centric multi-UAV evidence completion.

## Current Detector Table Policy

Keep these groups separated in all dashboards, tables, and writing:

| Group | Meaning | Examples |
| --- | --- | --- |
| Ours | selected proposed detector and ablations | P2P4-SelfAttnFR-s123 |
| Plain YOLO family baseline | stock YOLO family scale rows | YOLOv5u/8/9/10/11/12/26 n/s/m/l |
| Generic non-YOLO baseline | stock non-YOLO detector baseline | RT-DETR-L |
| Related-work prior model | paper-proposed external detector | CSFPR-RTDETR, LEAF-YOLO, SFFEF-YOLO, LSOD-YOLO, UAVDet, HF-D-FINE |

Important: `LEAF-YOLO` and `SFFEF-YOLO` are related-work prior models, not plain YOLO family baselines, even though their names contain YOLO.

## Current 2D Status

| Model | AP | AP50 | F1 | Recall | Params | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| P2P4-SelfAttnFR-s123 | 0.3825 | 0.6061 | 0.6262 | 0.5867 | 20.82M | selected trade-off candidate |
| YOLOv11l | 0.3777 | 0.5981 | 0.6248 | 0.5881 | 25.32M | strongest plain YOLO baseline |

P2P4-SelfAttnFR-s123 is meaningful because it improves AP/AP50 over YOLOv11l while reducing parameters by about 17.8%. It is still not final until repeated-seed confirmation is complete.

## Related-Work Resolution Consistency

For CSFPR-RTDETR and LEAF-YOLO:

- `640-eval`: reproduces or checks the released protocol.
- `1280-eval`: should be run next for consistency with our YOLO/proposed protocol.
- `1280-retrain`: heavier reproduction; only do this after deciding it is worth the time, and label it as our retrain rather than the authors' original result.

Recommended next related-work action:

1. Run CSFPR-RTDETR at `1280-eval`.
2. Run LEAF-YOLO-N and LEAF-YOLO-S at `1280-eval`.
3. Keep `640-eval` and `1280-eval` as separate rows in supplementary.
4. Only move a related-work row into the main table if the protocol is clearly matched or clearly labeled.

## Paper Structure Check

Main experiment section is currently organized well:

| Main Stage | Purpose | Status |
| --- | --- | --- |
| Stage 1: 2D Evidence Generator | Proves the detector front end is competitive and efficient | Good; needs 3-seed confirmation and 1280 related-work eval rows |
| Stage 2: 3D Generation and Evidence Graph | Tests whether multi-view 3D evidence improves object-level decisions | Good skeleton; currently placeholders until Isaac/MarineCity experiments |
| Stage 3: LLM/VLM Reasoner | Tests sparse verification for ambiguous hypotheses | Good skeleton; currently placeholders |
| Stage 4: Full System Comparison | Separates detector-only, 3D-only, reasoner-only, and full-system gains | Strong structure; fill after Stage 2/3 experiments |

Supplementary structure is also aligned:

- Full detector leaderboard.
- Per-seed statistics and p-values.
- Full ablations.
- Input-resolution sweep.
- Heat maps / Grad-CAM.
- 3D graph details.
- Prompt/schema details.
- Failure cases.

## Changes Applied To Overleaf

- Updated `sections/05_current_detector_search_status.tex`.
- Updated `tables/table1_main_detector_core.tex`.
- Updated `sections/supp_02_detector_results.tex`.
- Main and supplementary now consistently use `P2P4-SelfAttnFR-s123` as the current selected trade-off candidate.
- Supplementary now explicitly says CSFPR/LEAF need 1280-eval consistency checks before main-table inclusion.

## Next Actions

1. Keep detector queue running until the current candidates finish.
2. Add/launch 1280-eval for CSFPR-RTDETR and LEAF-YOLO.
3. After detector candidate freeze, run 3-seed confirmation with seeds `42`, `123`, and `2026`.
4. Start MarineCity / Isaac 3D experiments after detector comparison is stable.
5. Fill Stage 2 and Stage 3 tables once 3D/reasoner results arrive.
