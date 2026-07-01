# Overleaf Sync Notes

Updated: `2026-07-02 KST`

The `paper/` folder contains the current Overleaf-ready section bundles, tables, and figures for the CoM3D-ACE submission package.
Markdown notes, README files, local manifests, and runbooks are kept in `docs/` or `outputs/reports/live/`, not in `paper/`.

## Include From Overleaf

From the Overleaf project root, include the prepared bundles:

```latex
% Main-paper result and protocol patch
\input{sections/main_results_patch_bundle}

% Supplementary material
\input{sections/supplementary_patch_bundle}
```

If replacing the full main-paper body, use:

```latex
\input{sections/full_main_draft_bundle}
```

## Sync These Folders

| Folder | Contents |
| --- | --- |
| `sections/` | LaTeX-ready main and supplementary section bundles |
| `tables/` | Main detector, ablation, MarineCity, 3D, and reasoner tables |
| `figures/results/` | Paper-facing detector and MarineCity figures |
| `figures/results/marinecity_system/` | MarineCity qualitative, graph, and neural-3D validation panels |

Do not sync raw runs, datasets, weights, cache folders, or old queue directories into Overleaf.
Do not sync `*.md` or `README*` files into Overleaf. If a script emits a Markdown manifest, keep it under `outputs/reports/live/`.

## Main Paper Priority

Keep the main paper compact:

- detector comparison table: `tables/main_detector_comparison_table`
- detector ablation table: `tables/final_ablation_main_table`
- MarineCity system table: `tables/marinecity_system_scenario_table`
- MarineCity neural-3D validation table: `tables/marinecity_3d_completion_results_table`
- one detector trade-off figure if page budget allows
- one MarineCity qualitative/system figure

Move full inventories, long sweeps, heatmaps, repeated qualitative panels, and implementation details to the supplementary bundle.

## Current Claim Boundaries

- SAFR-YOLO/P2P4-SelfAttnFR is the selected detector candidate under the VisDrone 1280 three-seed protocol.
- MarineCity evidence is a real-Cesium system-validation package.
- Neural-3D results are runner-family validation evidence, not a claim of a completed large-scale 3D reconstruction benchmark.
- AeroGraph/ACE reasoning is reported as graph-grounded schema, verifier, and action-policy validation unless external-provider responses are explicitly imported.

## Validation

Before syncing into Overleaf:

```bash
python scripts/check_latex_patch_integrity.py
python scripts/check_paper_artifact_readiness.py
```

Expected outputs:

- `outputs/reports/live/latex_patch_integrity_check.md`
- `outputs/reports/live/paper_artifact_readiness_check.md`
