# Reports Directory

This directory contains compact, Git-friendly report artifacts only.

## Primary Report

- `server_baselines/README.md` is the main entry point for server detector
  baseline reporting.
- `server_baselines/tables/` contains copied summary/results/p-value CSVs.
- `server_baselines/figures/` contains the dashboard PNG snapshot.
- `server_baselines/stage_gate.*` records the detector stage-gate decision.

## Compatibility Files

- `server_baseline_dashboard.png` is kept at the historical path used by older
  scripts and docs.
- `server_smoke_dashboard.png` is the earlier smoke-test dashboard.
- `live/` is an ignored live-refresh folder used by tmux/browser monitoring.

Regenerate the organized bundle with:

```bash
bash scripts/ubuntu/collect_server_results.sh
```

This should not include raw datasets, weights, raw runs, logs, or caches.
