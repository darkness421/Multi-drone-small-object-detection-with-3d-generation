# Reports Index

Last organized: `2026-05-30`

This folder is the small, Git-friendly report area. It should contain only
Markdown, CSV tables, JSON summaries, and compact PNG figures. Raw datasets,
weights, raw training runs, logs, and caches stay outside Git.

## Open First

| Path | Use |
| --- | --- |
| `server_with_proposed/README.md` | Current consolidated detector report for paper writing |
| `detector_experiment_status.md` | Current queue status, dataset readiness, model availability, and next actions |
| `live/README.md` | Live dashboard files generated while tmux training is running |
| `archive/README.md` | Older report bundles and presentation-only assets |

## Current Paper Report

| Path | Contents |
| --- | --- |
| `server_with_proposed/figures/` | Paper-facing plots split by AP/AP50, PR/F1, params, GFLOPs, speed, and seed spread |
| `server_with_proposed/tables/` | Results, summary, and p-value CSVs |
| `server_with_proposed/stage_gate.md` | Current detector stage-gate decision |
| `server_with_proposed/paper_model_availability.md` | Runnable or external-required status for recent comparison models |

## Live Monitoring

`live/` is for active training visibility only. Treat those files as temporary
monitoring artifacts until the collector promotes a clean snapshot into
`server_with_proposed/`.

## Archive

`archive/` holds superseded snapshots and non-current presentation assets. Do
not use archive files as the current paper result unless the README explicitly
points to them.

## Regenerate

```bash
bash scripts/ubuntu/collect_proposed_results.sh
```
