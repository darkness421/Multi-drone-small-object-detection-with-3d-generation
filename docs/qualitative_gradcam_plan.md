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
