# Reports Index

This directory contains compact, Git-friendly report artifacts only. Start with
`server_with_proposed/README.md` unless you are intentionally checking live
training output or an archived run.

## Current Report

- `server_with_proposed/README.md`: current consolidated detector report.
- `server_with_proposed/tables/`: results, summary, and p-value CSVs.
- `server_with_proposed/figures/`: paper-facing plots split by metric.
- `server_with_proposed/stage_gate.*`: current detector stage-gate decision.

## Live Monitoring

- `live/`: live-refresh dashboard and figures for the active tmux training run.
  These are useful for monitoring, not for final reporting.

## Presentation

- `progress_ppt/com3d_ace_progress_plan_20260526.pptx`: current progress deck.
- `progress_ppt_assets/`: figures used by the progress deck.

## Archive

- `archive/`: superseded report bundles kept for traceability.

Regenerate the organized detector report with:

```bash
bash scripts/ubuntu/collect_proposed_results.sh
```

This should not include raw datasets, weights, raw runs, logs, or caches.
