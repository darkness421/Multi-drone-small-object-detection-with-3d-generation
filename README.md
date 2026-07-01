# CoM3D-ACE

CoM3D-ACE is the research codebase for **Cooperative Multi-UAV 3D Ambiguity-Centric Evidence Completion**.
The current paper package targets cooperative UAV small-object perception in a Marine City scenario, combining a compact detector, multi-view evidence graphs, neural 3D validation, and ambiguity-aware re-observation reasoning.

## Paper-Facing Status

Updated: `2026-07-02 KST`

The repository is organized around the current ACCV/Overleaf submission package:

- **Detector claim:** `SAFR-YOLO`, implemented as the `P2P4-SelfAttnFR` detector candidate, is the selected detector result.
- **Detector protocol:** VisDrone2019-DET validation, image size 1280, three seeds `42, 123, 2026`.
- **Main result snapshot:** Ours AP `0.3822 +/- 0.0007`, AP50 `0.6052 +/- 0.0012`, F1 `0.6273`, Params `20.82M`, GFLOPs `109.30`.
- **Reference baseline:** YOLOv11l AP `0.3777 +/- 0.0004`, AP50 `0.5981 +/- 0.0011`, F1 `0.6248`, Params `25.32M`.
- **System validation:** MarineCity real-Cesium multi-UAV capture, EvidenceToken generation, cross-view graph construction, neural-3D runner-family validation, and AeroGraph/ACE-style reasoning tables are prepared as paper or supplementary evidence.

Claim boundaries are tracked in [docs/accv_final_submission_readiness_2026-06-30.md](docs/accv_final_submission_readiness_2026-06-30.md).

## Naming

- **CoM3D-ACE:** full cooperative multi-UAV 3D evidence-completion system.
- **SAFR-YOLO:** paper-facing name for the detector contribution.
- **P2P4-SelfAttnFR:** implementation/run label for the selected SAFR-YOLO detector candidate.
- **AeroGraph Reasoner / ACE-Reasoner:** graph-grounded ambiguity and re-observation reasoning module.

Use `SAFR-YOLO` in the main paper. Use `P2P4-SelfAttnFR` only when describing the exact implementation, ablation, or reproducibility metadata.

## Where To Look First

| Path | Purpose |
| --- | --- |
| [docs/overleaf_sync.md](docs/overleaf_sync.md) | What to copy/include in Overleaf |
| [paper/sections/](paper/sections) | LaTeX-ready main and supplementary bundles |
| [paper/tables/](paper/tables) | LaTeX/CSV paper tables |
| [paper/figures/results/](paper/figures/results) | Paper-facing detector and MarineCity figures |
| [outputs/reports/final_detector_table_preview.md](outputs/reports/final_detector_table_preview.md) | Detector comparison snapshot and protocol notes |
| [outputs/reports/README.md](outputs/reports/README.md) | Compact report index |
| [docs/README.md](docs/README.md) | Active documentation index |

Internal queues, raw detector runs, logs, weights, datasets, and cache folders are not part of the paper-facing sync.
Markdown notes and README files are kept outside `paper/`; Overleaf should receive only LaTeX sources, tables, final figures, and required CSV assets.

## Repository Layout

```text
configs/             Experiment, detector, dataset, and simulation configs
data/, datasets/     Dataset converters and small schema/sample files
detectors/           YOLO/RT-DETR wrappers, SAFR-YOLO modules, detector training utilities
evidence/            EvidenceToken generation, crops, uncertainty, and visualization helpers
alignment/           Cross-view and cross-resolution matching costs
graph/               Evidence-graph construction utilities
ambiguity/           Ambiguity scoring and diagnostic helpers
generative3d/        NeRF/Instant-NGP/3DGS runner registry and external-runner interface
simulation/isaac/    MarineCity Isaac/Cesium scene and capture helpers
evaluation/          Detector metrics, seed statistics, ROC-AUC, system/reasoner evaluation
scripts/             Report builders and experiment orchestration scripts
scripts/ubuntu/      Ubuntu/tmux server runners
paper/               Overleaf-ready section, table, and figure assets
outputs/             Small CSV/JSON/PNG summaries only; no raw runs or weights
```

## Overleaf Sync

Use the patch bundles from `paper/sections/`:

```latex
% Main paper result/protocol patch
\input{sections/main_results_patch_bundle}

% Supplementary material
\input{sections/supplementary_patch_bundle}
```

If the Overleaf project needs a full body replacement, use:

```latex
\input{sections/full_main_draft_bundle}
```

Before syncing, run:

```bash
python scripts/check_latex_patch_integrity.py
python scripts/check_paper_artifact_readiness.py
```

Expected live checks:

- `outputs/reports/live/latex_patch_integrity_check.md`
- `outputs/reports/live/paper_artifact_readiness_check.md`

## Reproduce The Detector Tables

The paper table sources are already exported:

- `paper/tables/main_detector_comparison_table.tex`
- `paper/tables/final_ablation_main_table.tex`
- `outputs/reports/final_detector_table_preview.{md,csv,tex}`
- `outputs/reports/final_detector_tables/main_1280_completed_3seed.csv`

To refresh detector summaries from current small CSV artifacts:

```bash
python scripts/build_final_ablation_paper_artifacts.py
python scripts/build_server_report_figures.py
python scripts/check_latex_patch_integrity.py
```

Long training should be launched only through the Ubuntu/tmux scripts in `scripts/ubuntu/`.
Do not commit datasets, weights, raw run directories, cache folders, or large logs.

## Ubuntu Server Entry Points

```bash
cd /home/oem/projects/multi-uav-marine-city
bash scripts/ubuntu/check_env.sh
bash scripts/ubuntu/check_dataset_ready.sh
bash scripts/ubuntu/watch_live_training_scoreboard.sh
```

The main detector training/comparison queues are retained for reproducibility, but the current paper package should rely on completed 1280 three-seed summary tables rather than active queue notes.

## Windows / Isaac Entry Points

Windows and Isaac/Cesium setup instructions are separated from the Ubuntu server workflow:

- [docs/WINDOWS_MARINECITY_ISAAC_SETUP.md](docs/WINDOWS_MARINECITY_ISAAC_SETUP.md)
- [docs/visible_execution_workflow.md](docs/visible_execution_workflow.md)
- [isaac/README.md](isaac/README.md)

## Git Policy

Commit/push targets:

- source code, configs, docs, LaTeX patches
- small CSV/JSON summaries
- paper-facing PNG/PDF figures

Do not commit/push:

- raw datasets
- detector weights
- raw training run folders
- cache folders
- large logs or temporary queue folders
