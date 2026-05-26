# Experiment Outputs Index

This directory keeps compact CSV/JSON/manifests that are safe to version.
Raw detector runs, weights, datasets, caches, and large logs stay outside Git.

## Current Detector Results

- `server_with_proposed_results.csv`: consolidated detector/proposed result rows.
- `server_with_proposed_summary.csv`: model-level summary table.
- `server_with_proposed_pvalues.csv`: seed statistics and p-values.
- `server_with_proposed_stage_gate.*`: detector stage-gate decision.
- `top3_proposed_ablation_commands.csv`: pending top-3 proposed-module screening queue.

## Current Planning Artifacts

- `marinecity_multiview_benchmark.json`: Marine City multi-view benchmark design.
- `marinecity_isaac_capture_plan.json`: Isaac capture plan.
- `marinecity_isaac_dry_run_manifest.json`: synthetic dry-run manifest.
- `3d_generation_comparison.csv`: 3D reconstruction comparison scaffold.

## Active Runtime Folders

- `server_fresh/`: reproducible server queue manifests and live CSVs for baseline/large-model runs.
- `proposed_ablation_jobs/`: generated proposed-module queue scripts.

## Archive

Superseded smoke tests, initial baseline summaries, and older official snapshots
are collected in `archive/`.
