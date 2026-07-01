# Current Workspace Layout

Updated: `2026-07-02 KST`

The workspace is now organized around the paper-facing CoM3D-ACE submission package rather than open-ended detector search.

## Paper-Facing Areas

| Path | Role |
| --- | --- |
| `paper/sections/` | Overleaf-ready LaTeX section bundles |
| `paper/tables/` | LaTeX and CSV paper tables |
| `paper/figures/results/` | Detector and MarineCity paper figures |
| `outputs/reports/` | Compact report index, detector table previews, and figure manifests |
| `outputs/experiments/` | Small CSV/JSON summaries used to build tables and reports |
| `docs/` | Submission-facing docs, setup docs, and internal status notes |

## Keep Internal

| Path | Role |
| --- | --- |
| `outputs/reports/archive/` | Historical reports and stale dashboards |
| `outputs/experiments/archive/` | Historical result snapshots and old queue manifests |
| `outputs/logs/` | Runtime logs; not paper-facing |
| `outputs/detectors/` | Local detector runs and weights; do not push unless only tiny metadata is selected |

## Current Result Sources

- Detector comparison: `outputs/reports/final_detector_table_preview.md`
- Main detector table: `paper/tables/main_detector_comparison_table.tex`
- Main ablation table: `paper/tables/final_ablation_main_table.tex`
- MarineCity figures: `paper/figures/results/marinecity_system/`
- Overleaf instructions: `docs/overleaf_sync.md`

## Cleanup Rule

When in doubt:

1. Keep source code, configs, docs, LaTeX patches, compact CSV/JSON summaries, and final paper figures.
2. Move stale exploratory reports into `archive/`.
3. Do not commit raw datasets, weights, raw training folders, caches, or long logs.
