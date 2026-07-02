# Server GPU Allocation

Updated: `2026-06-20`

Use the two RTX 5090 GPUs as separate work lanes so detector experiments do not
block the system-level ACCV experiments.

## Policy

| GPU | Role | Workloads |
| --- | --- | --- |
| GPU0 | Detector lane | Final 2D ablations, runnable related-work 1280 comparisons, final detector heatmap/qualitative preparation, then corrected TinyPerson corner/original-window core-model check |
| GPU1 | Detector/system lane | Finish any active 2D jobs first; after related-work/heatmap completion, run MarineCity 3D reconstruction, Isaac Sim export/smoke tasks, and local VLM/LLM reasoner tests |

## Default Launchers

Detector/proposed lane:

```bash
SESSION=related-work-consistency-1280 bash scripts/ubuntu/start_related_work_consistency_retrain_queue.sh
bash scripts/ubuntu/start_final_detector_heatmaps_after_related_work.sh
bash scripts/ubuntu/start_tinyperson_corner_original_queue.sh
```

3D/system lane:

```bash
GPUS=1 bash scripts/ubuntu/train_3d_generators_tmux.sh
CUDA_VISIBLE_DEVICES=1 bash scripts/ubuntu/prepare_marinecity_multiview_benchmark.sh
```

## Practical Rules

- Finish the current 2D ablation queue first.
- Then finish runnable related-work 1280 experiments that can be fairly run
  from staged code/checkpoints.
- After related-work 1280 is complete, prepare final detector heatmap and
  qualitative comparison panels for YOLOv11l, YOLOv9c, and Ours.
- Only after those detector-side evidence tasks finish, split the GPUs:
  GPU0 runs the corrected TinyPerson corner/original-window core-model check,
  while GPU1 runs Isaac/3D/reasoner simulation.
- API-based LLM reasoning does not need a GPU. Local VLM/LLM models should be
  pinned to GPU1.
- TinyPerson is supplementary and core-model only by default. Use the corrected
  crop-window protocol, 1280 input, and a narrow Ours-vs-strong-baseline check.
  Do not run broad TinyPerson ablations or related-work rows unless we
  explicitly promote that result.

The machine-readable policy lives in
`configs/experiments/server_gpu_allocation.yaml`.
