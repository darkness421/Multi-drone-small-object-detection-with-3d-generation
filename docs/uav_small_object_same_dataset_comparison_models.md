# UAV Small-Object Same-Dataset Comparison Models

Date: 2026-06-08

Purpose:

- Filter the related-work model list by dataset overlap with our detector
  experiments.
- Prioritize comparison models that evaluated UAV or aerial small-object
  detection on `VisDrone`, `UAVDT`, `TinyPerson`, `AI-TOD`, `HIT-UAV`, or
  `DroneVehicle`.
- Keep plain YOLO family baselines separate from prior-art paper models, and
  keep runnable baselines separate from citation-only or adapter-hold papers.
- Ensure that every detector mentioned in Related Work is explicitly accounted
  for in either a measured table, an adapter/pending row, or a citation-only
  coverage row.

## Main Recommendation

The strongest same-dataset comparison set is:

1. Plain YOLO family baselines: `YOLOv5u/8/9/10/11/12/26` scale rows under our
   exact VisDrone protocol.
2. Generic non-YOLO baselines: stock RT-DETR-style rows when memory and protocol
   are stable.
3. Related-work prior models must be cited in the current manuscript subsection
   `2.1 UAV Small-object Evidence Generation`. Under the current draft this
   means `Universal YOLO`, `MFFSODNet`, `DS-YOLOv5s`, `SFFEF-YOLO`,
   `FMFN-YOLO`, `BPD-YOLO`, `LRDS-YOLO`, `DG-TSOD`, `D2A-Detector`,
   `CSFPR-RTDETR`, `UFO-DETR`, `CFIA`, `HF-D-FINE`, `DFFormer`,
   `RT-UAV-SOD`, and `UAVDet`.

Important naming rule:

- A plain YOLO family baseline is a stock family/scale row such as `YOLOv11l`,
  `YOLOv12m`, or `YOLOv8s`.
- A related-work prior model is a detector proposed by another paper and cited
  in our Related Work section. Models with public code but no current citation,
  such as `LEAF-YOLO`, must stay internal-only until the manuscript explicitly
  cites them.
- Do not drop a related-work model just because it is not runnable today. Mark
  it as `measured`, `pending_adapter`, `pending_assets`, or `citation_only`.

For the main paper table, use only models we can run fairly or whose official
paper numbers are directly comparable on the same dataset split. Put broader
paper-only comparisons in supplementary.

Canonical coverage files:

- `paper/tables/related_work_coverage_matrix.csv`
- `outputs/reports/live/related_work_coverage_matrix.md`

## Dataset-Overlap Matrix

| Model | Source Category | Dataset Overlap | Best Use | Runnable Status |
| --- | --- | --- | --- | --- |
| YOLO size baselines | Stock baseline family | `VisDrone`, `UAVDT` if converted | Main fair comparison under our protocol | Already running/runnable |
| RT-DETR-L/R18 | Stock non-YOLO baseline | `VisDrone`, `UAVDT` if memory permits | Main non-YOLO anchor | Runnable if memory stable |
| Universal YOLO small-object structure | Cited prior | `VisDrone`, `TinyPerson` | Methodological support for 4x feature map and P2 path | Citation/supporting baseline logic |
| MFFSODNet | Cited prior | UAV aerial imagery; VisDrone compatibility to audit | Multi-scale fusion prior | Official repo cloned; scratch 1280 retrain queued |
| DS-YOLOv5s | Cited prior | UAV dense/small object imagery | Dense-scene small-object prior | Citation/adapter-hold |
| SFFEF-YOLO | Cited prior | `VisDrone2019-DET`, `UAVDT`, `TinyPerson` | Strongest citation for tiny-head / remove-large-head design | Citation/adapter-hold |
| FMFN-YOLO | Cited prior | UAV aerial small-object detection | Feature preservation and FPN balancing prior | Citation/adapter-hold |
| HF-D-FINE | Cited prior | `VisDrone`, `AI-TOD`, `UAVDT` | Strong non-YOLO high-resolution tiny-object reference | Adapter-hold |
| CSFPR-RTDETR | Cited prior with code | `VisDrone`, `AI-TOD`, `HIT-UAV` | Strong RT-DETR/frequency/P2 reference | Public code, adapter needed |
| UAVDet | Cited prior | `VisDrone`, `UAVDT`, `DroneVehicle` | Strong CNN-Mamba efficient UAV reference | Adapter-hold |
| LRDS-YOLO | Cited prior | `VisDrone` clearly verified | Lightweight YOLO11 UAV reference | Adapter-hold |
| BPD-YOLO | Cited prior | UAV aerial images; exact same-dataset/run source needs deeper check | Lightweight semantic integration citation | Citation-only |
| DG-TSOD | Cited prior | `VisDrone`, `UAVDT`, `TinyPerson` | Density-guided refinement prior | Citation/adapter-hold |
| D2A-Detector | Cited prior | UAV small-object detection | Dual-domain attention prior | Citation/adapter-hold |
| UFO-DETR | Cited prior | UAV tiny-object/frequency, exact runnable split pending | Frequency-guided DETR citation | Citation/adapter-hold |
| CFIA | Cited prior | UAV object detection | Coarse-fine feature interaction prior | Citation/adapter-hold |
| DFFormer | Cited prior | UAV object detection | Feature scaling and interaction prior | Citation/adapter-hold |
| RT-UAV-SOD | Cited prior | UAV aerial images | Real-time UAV efficiency prior | Citation/adapter-hold |
| LEAF-YOLO | Internal extra check | `VisDrone`, reported `TinyPerson` | Internal sanity check only unless cited later | Public code; exclude from paper-facing related-work table |
| GCL-YOLO / SRTSOD-YOLO / YOLO11s-UAV | Internal extra check | UAV/VisDrone-style datasets | Exclude unless manuscript is revised | Do not queue as paper-facing related work |

## Priority For Our Queue

### P0: Must Have Under Our Protocol

- Best YOLO nano/small/medium/large models by measured `AP`, `AP50`, `F1`,
  `Params`, and `GFLOPs`.
- `YOLOv11l`, because our proposed candidates are built around this trade-off.
- `RT-DETR-L/R18` only if memory/code allows a clean completed run.
- Final proposed detector.

### P1: Same-Dataset External Targets

- `CSFPR-RTDETR`: public source/code pointer; best frequency/RT-DETR target.
- `MFFSODNet`: cited multi-scale fusion model; official repo cloned, zip
  extracted, and scratch 1280 retrain queued after CSFPR.
- `UAVDet`: cited CNN-Mamba efficient UAV detector; official repo candidate
  needs dependency/modality audit before queueing.
- `SFFEF-YOLO`, `FMFN-YOLO`, `DS-YOLOv5s`, and `HF-D-FINE`: cited same-task
  methods; queue only when compatible assets appear.

### P2: Backup / Supplementary Same-Dataset References

- `Universal YOLO`: strong citation for 4x/high-resolution feature maps, but not
  a direct required runnable baseline.
- `BPD-YOLO`, `LRDS-YOLO`, `DG-TSOD`, `D2A-Detector`, `UFO-DETR`, `CFIA`,
  `DFFormer`, and `RT-UAV-SOD`: cited in Sec. 2.1, but citation-only until
  reproducible code/weights are staged.

## Tested So Far

The following same-dataset external evaluations have already been run from
staged local assets on `VisDrone2019-DET val`. These are eval-only rows from
external checkpoints, not our 3-seed training protocol.

| Method | P | R | F1 | AP50 | AP | ParamsM | GFLOPs | Speed ms/img | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CSFPR-RTDETR` | see CSV | see CSV | see CSV | see CSV | see CSV | 14.0892 | 63.9000 | see CSV | 1280 eval-only row collected; prior 640 attempt failed from CUDA/NVML environment issue |
| `LEAF-YOLO-S/N` | see CSV | see CSV | see CSV | see CSV | see CSV | see CSV | see CSV | see CSV | internal-only because LEAF-YOLO is not cited in current Sec. 2.1 |

Important fairness note:

- CSFPR-RTDETR is paper-facing because it is cited in Sec. 2.1. LEAF-YOLO is
  internal-only because it is not cited in the current manuscript. Our strict
  official table uses `1280` and 3 seeds for trained YOLO/proposed runs, so
  external eval-only rows remain separate unless we complete a matched training
  protocol.

## Paper Table Strategy

Main paper:

- Report our own fair runs on `VisDrone2019-DET`: YOLO baselines by size,
  strongest large anchors, RT-DETR if complete, proposed detector.
- Include same-dataset paper rows only if official split/metric is clearly
  comparable or if we rerun them with our pipeline.

Supplementary:

- Add a same-dataset related-work table with `Dataset`, `Metric`, `Params`,
  `GFLOPs`, `Code/Weights`, and `Fairness note`.
- Use `TinyPerson` for a compact stress test: `YOLOv11l`, final proposed model,
  and one architecture-only proposed variant if time allows.

## Source Checks

- CSFPR-RTDETR: `VisDrone`, `AI-TOD`, `HIT-UAV`; public code pointer.
- MFFSODNet: official repository cloned and extracted; no pretrained checkpoint
  found, so the queue uses scratch retraining with an explicit protocol note.
- UAVDet: official repository candidate identified; MMDetection/Mamba and
  modality-fairness audit pending.
- SFFEF-YOLO: `VisDrone2019-DET`, `UAVDT`, `TinyPerson`; tiny head replaces
  large head.
- FMFN-YOLO: feature preservation and multi-scale pyramid balancing prior.
- DS-YOLOv5s: dense and small UAV object detection prior.
- HF-D-FINE: `VisDrone`, `AI-TOD`, `UAVDT`.
- LEAF-YOLO, GCL-YOLO, SRTSOD-YOLO, and YOLO11s-UAV are excluded from the
  paper-facing related-work queue unless the manuscript is revised to cite them.
