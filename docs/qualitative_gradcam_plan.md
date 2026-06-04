# Qualitative And Grad-CAM Plan

## Goal

Compare detector behavior on the same VisDrone images across baseline models and
the later proposed module.

## Detection Qualitative Examples

Output directory:

- `outputs/qualitative/detection_examples/`

Planned cases:

- correct detections
- false positives
- false negatives
- class confusion

Command scaffold:

```bash
bash scripts/ubuntu/make_qualitative_examples.sh \
  data/processed/visdrone_yolo/images/val \
  outputs/detectors/server_baselines/.../weights/best.pt
```

## Grad-CAM / Attention

Output directory:

- `outputs/qualitative/gradcam/`

YOLO-family plan:

- use the same image set for every model
- target the final neck feature map or detection-head pre-logit feature
- save original, prediction overlay, heatmap, and blended heatmap

RT-DETR plan:

- keep separate from YOLO Grad-CAM
- visualize decoder attention or selected feature maps when the RT-DETR baseline
  checkpoint is finalized

Current scaffold:

```bash
bash scripts/ubuntu/run_gradcam_examples.sh weight1.pt weight2.pt -- image1.jpg image2.jpg
```

The scaffold records a `gradcam_run_plan.json`. Full heatmap generation is a
TODO after the selected model internals are fixed.

## Supplementary Ablation Heat Maps

For the supplementary material, include two heat-map styles:

- Quantitative ablation delta heatmap: rows are detector module variants, columns
  are AP, AP50, recall, and F1 deltas against the matching control run.
- Qualitative Grad-CAM/attention panels: same validation images for the baseline,
  P2/TinyFReLU, NMS-tuned variant, and final proposed detector.

Recommended cases:

- tiny true positive recovered by the proposed detector
- adjacent-object case where standard NMS suppresses one target
- false negative caused by low contrast or blur
- false positive near dense marine-city background clutter

Build current quantitative heat-map artifacts from collected CSVs:

```bash
python -m scripts.build_supplementary_detector_analysis
```

Expected outputs:

```text
outputs/reports/supplementary_detector/ablation_delta_heatmap.csv
outputs/reports/supplementary_detector/figures/ablation_delta_heatmap.png
outputs/reports/supplementary_detector/input_size_sweep.csv
outputs/reports/supplementary_detector/figures/input_size_ap_ap50.png
outputs/reports/supplementary_detector/figures/input_size_efficiency.png
```

## High-Resolution Input Pixel-Size Sweep

This is supplementary-only unless it becomes central to the final claim. The
official detector protocol remains high-resolution (`imgsz=1280`). The goal is
to answer whether the proposed detector still helps around that high-resolution
operating point, rather than switching the paper to a 640 crop protocol.

Pilot sweep:

```bash
WAIT_FOR=server-top3-proposed-screening \
GPUS=0 SEEDS=42 \
bash scripts/ubuntu/train_input_size_sweep.sh
```

Default input sizes:

```text
960, 1280, 1536
```

Report AP, AP50, recall, F1, FPS, latency, Params, and GFLOPs. Keep `1280` as
the official row; use `960` and `1536` as supplementary sensitivity checks.
