# Current Workspace Layout

Updated: `2026-07-02 KST`

The workspace is organized around reproducible CoM3D-ACE implementation work:
detector training, MarineCity simulation, evidence graph construction, neural
3D validation, reasoner evaluation, and compact result summaries.

## Tracked Implementation Areas

| Path | Role |
| --- | --- |
| `configs/` | Dataset, detector, experiment, simulation, and automation configs |
| `detectors/` | Detector runners, wrappers, and proposed modules |
| `evaluation/` | Metric collection, statistics, qualitative analysis, and ROC utilities |
| `generative3d/` | Neural 3D runner registry and external-runner interface |
| `simulation/isaac/` | MarineCity scene construction and capture helpers |
| `scripts/` | Dataset preparation, report building, and experiment orchestration |
| `paper/tables/` | Final table sources used by reports and manuscript builds |
| `paper/figures/results/` | Final detector and MarineCity figure assets |
| `outputs/experiments/` | Small CSV/JSON summaries used to build tables and reports |
| `outputs/reports/` | Compact result reports and final figures |

## Local-Only Or Ignored Areas

| Path | Role |
| --- | --- |
| `outputs/reports/archive/` | Historical reports and stale dashboards |
| `outputs/experiments/archive/` | Historical result snapshots and old queue manifests |
| `outputs/logs/` | Runtime logs |
| `outputs/detectors/` | Local detector runs and weights; do not push unless only tiny metadata is selected |
| `runs/`, `weights/`, `data/raw/` | Large local training and dataset artifacts |

## Current Result Sources

- Detector comparison: `outputs/reports/final_detector_table_preview.md`
- Main detector table: `paper/tables/main_detector_comparison_table.tex`
- Main ablation table: `paper/tables/final_ablation_main_table.tex`
- MarineCity figures: `paper/figures/results/marinecity_system/`

## Cleanup Rule

When in doubt:

1. Keep source code, configs, implementation docs, compact CSV/JSON summaries, and final figures.
2. Move stale exploratory reports into `archive/`.
3. Do not commit raw datasets, weights, raw training folders, caches, or long logs.
