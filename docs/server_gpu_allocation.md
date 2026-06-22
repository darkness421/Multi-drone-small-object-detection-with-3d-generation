# Server GPU Allocation

Updated: `2026-06-18`

Use the two RTX 5090 GPUs as separate work lanes so detector experiments do not
block the system-level ACCV experiments.

## Policy

| GPU | Role | Workloads |
| --- | --- | --- |
| GPU0 | Detector lane | VisDrone baselines, comparison models, proposed detector ablations, TinyPerson 640 supplementary stress test, compact UAVDT only if time remains |
| GPU1 | System lane | MarineCity 3D reconstruction, Isaac Sim export/smoke tasks, local VLM/LLM reasoner tests |

## Default Launchers

Detector/proposed lane:

```bash
GPUS=0 bash scripts/ubuntu/train_large_comparison_after_session.sh
GPUS=0 bash scripts/ubuntu/train_top3_proposed_ablation_after_session.sh
GPUS=0 bash scripts/ubuntu/train_proposed_ablation_after_session.sh
bash scripts/ubuntu/start_tinyperson_640_after_2d.sh
```

3D/system lane:

```bash
GPUS=1 bash scripts/ubuntu/train_3d_generators_tmux.sh
CUDA_VISIBLE_DEVICES=1 bash scripts/ubuntu/prepare_marinecity_multiview_benchmark.sh
```

## Practical Rules

- Keep GPU0 busy with detector queues until the baseline/proposed evidence is
  stable enough for the paper.
- After the VisDrone 2D detector queues finish, GPU0 starts the TinyPerson 640
  supplementary stress test: YOLOv11l, final SAFR-YOLO, and one compact P2P4
  ablation first at seed 42.
- Start 3D reconstruction and Isaac/LLM preparation on GPU1 in parallel; do not
  wait for TinyPerson unless GPU1 needs detector weights from that stress test.
- API-based LLM reasoning does not need a GPU. Local VLM/LLM models should be
  pinned to GPU1.
- Do not start detector jobs on GPU1 unless GPU0 is idle and the 3D/system lane
  is intentionally paused.

The machine-readable policy lives in
`configs/experiments/server_gpu_allocation.yaml`.
