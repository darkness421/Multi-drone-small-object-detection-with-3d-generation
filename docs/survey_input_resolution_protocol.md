# Survey Input Resolution Protocol

Checked: 2026-06-04

This note records input-resolution evidence from the detector papers already used
in our ACCV survey/paper. The goal is to justify our detector protocol and avoid
mixing results from incompatible image sizes without explanation.

## Main Finding

Most YOLO-family UAV small-object papers use `640 x 640` because it is the
default YOLO/Ultralytics-style setting and gives a manageable speed-memory trade
off. That does not mean `640 x 640` is the strongest small-object protocol.
Several papers in or adjacent to our survey explicitly test larger inputs such as
`1024 x 1024`, `1280 x 1280`, `1333 x 800`, or `1996 x 1996`, and these rows
often improve tiny-object recall at much higher runtime cost.

Our paper should therefore keep `imgsz=1280` as the official high-resolution
detector protocol, then use `960`, `1280`, and `1536` as supplementary
sensitivity checks.

## Confirmed Or Usable Evidence

| Paper or model in our survey | Family | Reported input size evidence | Dataset / context | Protocol implication |
| --- | --- | --- | --- | --- |
| Universal YOLO | YOLO small-object neck / P2-style design | Figure architecture shows `640 x 640`; paper emphasizes replacing stride-32 prediction with stride-4 prediction | VisDrone / TinyPerson style evaluation | Supports our P2/stride-4 design motivation, but not a high-resolution protocol by itself |
| LRDS-YOLO | Lightweight YOLOv11-style UAV detector | Training uses adaptive image size `640 x 640` | VisDrone2019 and HIT-UAV | Typical YOLO-family comparison size |
| LEAF-YOLO | YOLOv7-style lightweight edge detector | Official repo train/test commands use `--img 640 640` or `--img 640` | VisDrone2019-DET | External runnable baseline should first reproduce `640`, then optionally rerun at our `1280` fair protocol |
| CSFPR-RTDETR | RT-DETR UAV detector with spatial-frequency modules | Official repo training command uses `imgsz=640` | VisDrone | Typical DETR/Ultralytics-style UAV setting |
| SOD-YOLO | YOLOv7 small-object branch | Main comparison uses `640 x 640`; paper also reports `1024 x 1024` and compares against TPH-YOLOv5 at `1996 x 1996` | VisDrone validation | Strong evidence that resolution is a real axis and must be reported, not hidden |
| BPD-YOLO | YOLOv8 + P2/L-FPN small-object detector | Table includes `640 x 640`; also BPD-YOLO rows at `1333 x 800` with batch size 1 for memory | VisDrone2019 | High-resolution improves evidence but changes memory/runtime, so report cost |
| RT-UAV-SOD | Real-time transformer-style UAV detector | Implementation fixes input image resolution at `640 x 640` | VisDrone2019-DET and DOTA | Another 640-style realtime reference |
| MFFSODNet | Multi-scale feature fusion UAV detector | A later comparison table reports MFFSODNet at `640 x 640` | VisDrone validation | Usable as secondary evidence; verify original paper before making a primary-source claim |
| YOLOv8 VisDrone resolution study | YOLOv8 systematic evaluation | Compares `640` and `1280`; reports that `1280` improves mAP50 and mAP50-95 over `640` and gives larger gains than adding only P2 | VisDrone2019 | Strong support for keeping high-resolution detector protocol in our paper |

## Still To Verify Before Citation-Level Claims

The following survey entries are important for related work, but I did not find
clear open primary-source input-size lines yet:

- SFFEF-YOLO
- DS-YOLOv5s
- DG-TSOD
- D2A-Detector
- UFO-DETR
- HF-D-FINE
- DFFormer
- DCO-CRSA
- UAVDet
- AFFNet / FG-UNet / GLF-Net, because some are segmentation, rotated-box, or
  multimodal rather than direct horizontal-box VisDrone detector baselines.

For these, the paper should avoid saying they used `640` unless the original PDF,
official code, or a reliable open table confirms it.

## Paper Strategy

Main paper:

- State that our detector front-end is evaluated at `imgsz=1280` because UAV
  tiny objects are strongly resolution-limited.
- Report Params, GFLOPs, FPS/latency, and batch size with every detector row.
- Do not compare our absolute AP directly against literature rows without a note
  that many published rows use `640 x 640` or other resolutions.

Supplementary:

- Add a protocol-alignment table: paper, detector family, dataset, input size,
  batch size if available, and whether the source is paper, official repo, or
  secondary table.
- Add input-size sensitivity: `960`, `1280`, `1536`.
- Add heat maps and qualitative cases showing why small objects fail at lower
  resolution and how P2/TinyFReLU/NMS variants affect adjacent-object cases.

Experiment decision:

- Do not restart all training from `640`.
- Keep the current high-resolution queue.
- If we run external models, use their official `640` command only for
  reproducibility, then add a fair `1280` rerun only for shortlisted models.

## Source URLs

- Universal YOLO ACCV 2024 PDF: https://openaccess.thecvf.com/content/ACCV2024/papers/Hu_A_Universal_Structure_of_YOLO_Series_Small_Object_Detection_Models_ACCV_2024_paper.pdf
- LRDS-YOLO: https://www.nature.com/articles/s41598-025-07021-6
- LEAF-YOLO official repository: https://github.com/highquanglity/LEAF-YOLO
- CSFPR-RTDETR official repository: https://github.com/HuLei-JXNU/CSFPR-RTDETR
- SOD-YOLO: https://www.nature.com/articles/s41598-024-77513-4
- BPD-YOLO: https://www.nature.com/articles/s41598-025-16878-6
- RT-UAV-SOD: https://www.nature.com/articles/s41598-025-22855-w
- Fine-Grained Feature Perception comparison table with MFFSODNet: https://www.mdpi.com/2504-446X/8/5/181
- YOLOv8 VisDrone resolution study: https://www.mdpi.com/2076-3417/16/7/3559
