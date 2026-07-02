# CoM3D-ACE

CoM3D-ACE is a cooperative multi-UAV perception research codebase for small-object detection, multi-view evidence construction, neural 3D validation, and ambiguity-aware re-observation in a MarineCity-style UAV scenario.

The repository is organized for reproducible implementation work: detector training/evaluation, simulation capture utilities, evidence graph construction, 3D reconstruction runners, and compact experiment summaries.

## Implemented Components

| Area | Implementation |
| --- | --- |
| Detector training | Ultralytics YOLO/RT-DETR wrappers, VisDrone/TinyPerson/UAVDT-oriented configs, tmux queue scripts |
| Proposed detector | SAFR-YOLO / `P2P4-SelfAttnFR` modules and ablation configs |
| Evaluation | Metric collection, seed summaries, p-values, detector tables, ROC/qualitative/activation utilities |
| Evidence graph | EvidenceToken generation, cross-view grouping, support/conflict/missing-evidence links |
| 3D validation | MarineCity RGB/depth/pose export, Nerfacto/Instant-NGP/3DGS-style runner registry, depth point-cloud checks |
| Reasoning | AeroGraph/ACE-style rule and prompt interfaces for ambiguity diagnosis and re-observation decisions |
| Simulation | Isaac/Cesium MarineCity scene setup, multi-UAV camera capture helpers, Windows and Ubuntu separated workflows |

## Current Detector Snapshot

The main completed detector protocol is VisDrone2019-DET validation at image size `1280` with seeds `42`, `123`, and `2026`.

| Method | AP | AP50 | F1 | Params | GFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| SAFR-YOLO / P2P4-SelfAttnFR | `0.3822 +/- 0.0007` | `0.6052 +/- 0.0012` | `0.6273` | `20.82M` | `109.30` |
| YOLOv11l reference | `0.3777 +/- 0.0004` | `0.5981 +/- 0.0011` | `0.6248` | `25.32M` | `109.10` |

Primary detector result files:

- `outputs/reports/final_detector_table_preview.csv`
- `outputs/reports/final_detector_table_preview.md`
- `outputs/reports/final_detector_tables/main_1280_completed_3seed.csv`
- `outputs/experiments/final_p2p4_selfattnfr_ablation_summary.csv`

## Repository Layout

```text
configs/             Dataset, detector, experiment, simulation, and automation configs
data/, datasets/     Dataset converters and lightweight schema/sample files
detectors/           YOLO/RT-DETR runners, SAFR-YOLO modules, detector wrappers
evaluation/          Metric collection, statistics, ROC-AUC, qualitative and activation analysis
evidence/            EvidenceToken generation, crops, uncertainty, visualization helpers
alignment/           Cross-view and cross-resolution matching costs
graph/               Evidence graph construction utilities
ambiguity/           Ambiguity scoring and diagnostic helpers
generative3d/        Neural 3D runner registry and external runner interface
simulation/isaac/    MarineCity Isaac/Cesium scene and capture utilities
scripts/             Report builders, preparation scripts, and experiment orchestration
scripts/ubuntu/      Ubuntu/tmux server runners and live monitoring helpers
paper/               Publication tables and final figure assets
outputs/             Small CSV/JSON/PNG summaries only; no raw runs or weights
```

## Setup And Checks

Ubuntu server:

```bash
cd /home/oem/projects/multi-uav-marine-city
bash scripts/ubuntu/check_env.sh
bash scripts/ubuntu/check_dataset_ready.sh
```

Python module checks:

```bash
python -m scripts.check_env
python -m py_compile detectors/train_yolo.py detectors/ultralytics_runner.py evaluation/collect_detector_metrics.py
```

Windows/Isaac setup is documented separately:

- `docs/WINDOWS_MARINECITY_ISAAC_SETUP.md`
- `isaac/README.md`

## Detector Experiments

Baseline and proposed detector runs are launched through tmux scripts so long jobs remain visible and resumable:

```bash
bash scripts/ubuntu/train_visdrone_baselines_tmux.sh
bash scripts/ubuntu/train_proposed_ablation_after_session.sh
bash scripts/ubuntu/watch_live_training_scoreboard.sh
```

Result collection and tables:

```bash
bash scripts/ubuntu/collect_server_results.sh
python scripts/build_final_ablation_paper_artifacts.py
python scripts/build_server_report_figures.py
```

## MarineCity / 3D / Reasoner Workflow

The MarineCity stack uses real or simulated multi-UAV captures, detector outputs, evidence graph construction, and 3D validation artifacts.

Key entry points:

- `simulation/isaac/marinecity_plan.py`
- `simulation/isaac/export_rgb_depth_pose.py`
- `scripts/export_marinecity_neural3d_dataset.py`
- `scripts/build_marinecity_depth_pointcloud_smoke.py`
- `scripts/check_marinecity_system_integration.py`
- `scripts/build_marinecity_detector_reasoner_smoke_artifacts.py`

Compact outputs are stored under:

- `outputs/experiments/3d_generation/`
- `outputs/reports/live/marinecity_*`
- `paper/figures/results/marinecity_system/`

## Git Policy

Commit and push:

- source code
- configs
- documentation needed to run the implementation
- compact CSV/JSON summaries
- final PNG/PDF figures and LaTeX/CSV publication tables

Do not commit or push:

- raw datasets
- detector weights or checkpoints
- raw training run directories
- cache folders
- large logs
- temporary queue folders
