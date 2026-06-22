# UAV Small-Object Same-Dataset Comparison Models

Date: 2026-06-08

Purpose:

- Filter the Notion `Related Research` list by dataset overlap with our detector
  experiments.
- Prioritize comparison models that evaluated UAV or aerial small-object
  detection on `VisDrone`, `UAVDT`, `TinyPerson`, `AI-TOD`, `HIT-UAV`, or
  `DroneVehicle`.
- Keep plain YOLO family baselines separate from prior-art paper models, and
  keep runnable baselines separate from citation-only or adapter-hold papers.

Live Notion note:

- The current chat session's legacy Notion connector still returns an expired
  token. This matrix uses the exported Notion research page plus public source
  checks.

## Main Recommendation

The strongest same-dataset comparison set is:

1. Plain YOLO family baselines: `YOLOv5u/8/9/10/11/12/26` scale rows under our
   exact VisDrone protocol.
2. Generic non-YOLO baselines: stock RT-DETR-style rows when memory and protocol
   are stable.
3. Related-work prior models: `SFFEF-YOLO`, `LSOD-YOLO`, `HF-D-FINE`,
   `CSFPR-RTDETR`, `UAVDet`, `LEAF-YOLO`, `GCL-YOLO`, `SRTSOD-YOLO`, and
   `YOLO11s-UAV`.

Important naming rule:

- A plain YOLO family baseline is a stock family/scale row such as `YOLOv11l`,
  `YOLOv12m`, or `YOLOv8s`.
- A related-work prior model is a detector proposed by another paper. This
  includes models with YOLO in the name, such as `LEAF-YOLO`, `SFFEF-YOLO`, and
  `LSOD-YOLO`; they must not be mixed into the stock YOLO scale sweep.

For the main paper table, use only models we can run fairly or whose official
paper numbers are directly comparable on the same dataset split. Put broader
paper-only comparisons in supplementary.

## Dataset-Overlap Matrix

| Model | From Notion Related Research | Dataset Overlap | Best Use | Runnable Status |
| --- | --- | --- | --- | --- |
| YOLO size baselines | Yes, as baseline family | `VisDrone`, `UAVDT` if converted | Main fair comparison under our protocol | Already running/runnable |
| RT-DETR-L/R18 | Yes, as non-YOLO baseline | `VisDrone`, `UAVDT` if memory permits | Main non-YOLO anchor | Runnable if memory stable |
| SFFEF-YOLO | Yes | `VisDrone2019-DET`, `UAVDT`, `TinyPerson` | Strongest citation for tiny-head / remove-large-head design | Citation/adapter-hold |
| LSOD-YOLO | Yes | `VisDrone2019`, `TinyPerson`, `LEVIR-Ship`, `UAVDT` | Strong lightweight cross-dataset reference | Citation/adapter-hold |
| HF-D-FINE | Yes | `VisDrone`, `AI-TOD`, `UAVDT` | Strong non-YOLO high-resolution tiny-object reference | Adapter-hold |
| CSFPR-RTDETR | Yes | `VisDrone`, `AI-TOD`, `HIT-UAV` | Strong RT-DETR/frequency/P2 reference | Public code, adapter needed |
| UAVDet | Yes | `VisDrone`, `UAVDT`, `DroneVehicle` | Strong CNN-Mamba efficient UAV reference | Adapter-hold |
| LEAF-YOLO | Added from public code check | `VisDrone`, reported `TinyPerson` | Best near-term lightweight external candidate | Public code, YOLOv7-style adapter needed |
| GCL-YOLO | Same-dataset scan | `VisDrone-DET2021`, `UAVDT` | Strong lightweight/P5-removal reference | Citation/possible reproduction |
| SRTSOD-YOLO | Same-dataset scan | `VisDrone`, `UAVDT` | Recent YOLO11 same-dataset reference | Citation/adapter-hold |
| YOLO11s-UAV | Same-dataset scan | `VisDrone-DET2019`, `UAVDT-DET`, `TinyPerson` | Recent YOLO11 same-dataset reference | Citation/adapter-hold |
| Universal YOLO small-object structure | Yes / ACCV support | `VisDrone`, `TinyPerson` | Methodological support for 4x feature map and P2 path | Citation/supporting baseline logic |
| LRDS-YOLO | Yes | `VisDrone` clearly verified | Lightweight YOLO11 UAV reference | Adapter-hold |
| SOD-YOLO | Yes | UAV small-object, VisDrone-oriented record | P2/Soft-NMS direction | Hold until code/weights mature |
| MASF-YOLO | Yes | `VisDrone2019` | YOLO11 UAV multi-scale/attention reference | Hold unless code/checkpoint appears |
| UFO-DETR | Yes | UAV tiny-object/frequency, exact runnable split pending | Frequency-guided DETR citation | Citation/adapter-hold |
| UAVD-Mamba | Yes | Multimodal UAV detection; direct RGB-only fairness unclear | Mamba/SSM related work | Citation unless modality aligns |
| BPD-YOLO | Yes | UAV aerial images; exact same-dataset/run source needs deeper check | Lightweight semantic integration citation | Citation-only |

## Priority For Our Queue

### P0: Must Have Under Our Protocol

- Best YOLO nano/small/medium/large models by measured `AP`, `AP50`, `F1`,
  `Params`, and `GFLOPs`.
- `YOLOv11l`, because our proposed candidates are built around this trade-off.
- `RT-DETR-L/R18` only if memory/code allows a clean completed run.
- Final proposed detector.

### P1: Same-Dataset External Targets

- `LEAF-YOLO`: public repo; best practical lightweight external target.
- `CSFPR-RTDETR`: public source/code pointer; best frequency/RT-DETR target.
- `SFFEF-YOLO`: same datasets and directly supports tiny-head replacement.
- `LSOD-YOLO`: same datasets and strong lightweight cross-layer reference.
- `HF-D-FINE`: same UAV datasets and strong high-resolution non-YOLO reference.
- `UAVDet`: same UAV datasets and strong CNN-Mamba reference.

### P2: Backup / Supplementary Same-Dataset References

- `GCL-YOLO`: useful because it uses `VisDrone-DET2021` and `UAVDT`, removes
  the large prediction head, and reports parameter/FLOP trade-offs.
- `SRTSOD-YOLO` and `YOLO11s-UAV`: useful as recent YOLO11 same-dataset
  references, but only after we confirm code/checkpoint quality.
- `Universal YOLO`: strong citation for 4x/high-resolution feature maps, but not
  a direct required runnable baseline.

## Tested So Far

The following same-dataset external evaluations have already been run from
staged local assets on `VisDrone2019-DET val` at `imgsz=640`.

| Method | P | R | F1 | AP50 | AP | ParamsM | GFLOPs | Speed ms/img | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CSFPR-RTDETR` | 0.6336 | 0.5145 | 0.5679 | 0.5253 | 0.3279 | 14.0892 | 63.9000 | 27.1000 | Staged official checkpoint; frequency/RT-DETR comparison |
| `LEAF-YOLO-S` | 0.5770 | 0.4850 | 0.5270 | 0.4820 | 0.2810 | 4.2840 | 20.9000 | 10.0000 | Staged LEAF small checkpoint |
| `LEAF-YOLO-N` | 0.4800 | 0.4330 | 0.4553 | 0.3970 | 0.2190 | 1.1958 | 5.6000 | 8.9000 | Staged LEAF nano checkpoint |

Important fairness note:

- These are useful paper-facing same-dataset references, but they use the
  external models' `640` evaluation setting. Our strict official table uses
  `1280` for trained YOLO/proposed runs, so keep these in a separate external
  comparison table unless we rerun them under a matched protocol.

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
- SFFEF-YOLO: `VisDrone2019-DET`, `UAVDT`, `TinyPerson`; tiny head replaces
  large head.
- LSOD-YOLO: `VisDrone2019`, `TinyPerson`, `LEVIR-Ship`, `UAVDT`.
- HF-D-FINE: `VisDrone`, `AI-TOD`, `UAVDT`.
- UAVDet: `VisDrone`, `UAVDT`, `DroneVehicle`.
- GCL-YOLO: `VisDrone-DET2021`, `UAVDT`; removes P5/large head and adds shallow
  fusion/prediction head.
- SRTSOD-YOLO: `VisDrone`, `UAVDT`.
- YOLO11s-UAV: `VisDrone-DET2019`, `UAVDT-DET`, `TinyPerson`.
