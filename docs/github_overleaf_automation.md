# GitHub and Overleaf Automation

The experiment runner can be extended with a guarded publish step. The goal is
to keep the 24-hour server work moving while avoiding accidental paper churn.

## Recommended Policy

- Automatically run experiments, collect metrics, and generate tables/figures.
- Automatically export a draft LaTeX snapshot into the Overleaf-linked GitHub
  repository.
- Commit and push only when explicitly enabled.
- Keep code changes human-reviewed. Do not let a failed run rewrite model code
  and relaunch itself without review.

## Export Paper Snapshot

Generate Overleaf-ready files without committing:

```bash
bash scripts/ubuntu/publish_experiment_update.sh
```

This writes into the Overleaf-linked repo, by default:

```text
/tmp/accv-overleaf/tables/auto_detector_results.tex
/tmp/accv-overleaf/sections/auto_experiment_status.tex
/tmp/accv-overleaf/figures/auto/
```

It also inserts this line into `sections/05_results.tex` if it is not already
present:

```latex
\input{sections/auto_experiment_status}
```

## Commit Locally

Commit selected experiment outputs and automation files in the main repo:

```bash
DO_MAIN_COMMIT=1 bash scripts/ubuntu/publish_experiment_update.sh
```

Commit the Overleaf snapshot:

```bash
DO_OVERLEAF_COMMIT=1 bash scripts/ubuntu/publish_experiment_update.sh
```

## Push to GitHub and Overleaf

Push must be explicitly enabled:

```bash
DO_MAIN_COMMIT=1 DO_MAIN_PUSH=1 \
DO_OVERLEAF_COMMIT=1 DO_OVERLEAF_PUSH=1 \
bash scripts/ubuntu/publish_experiment_update.sh
```

After the Overleaf GitHub push, open Overleaf and pull/sync from GitHub. If the
project is configured to auto-sync, the change should appear after the GitHub
sync completes.

## Notion Status Export

Each publish run now also creates a Notion/GitHub status markdown file:

```text
notion_exports/bidaily/ACCV_Bidaily_Update_<timestamp>.md
```

This file summarizes deadline pressure, the current detector gate, active or
recent runs, the detector leaderboard, and the next 48-hour actions. It is safe
to commit because it contains only local result summaries and no tokens.

Generate the paper snapshot plus the Notion-ready markdown without live Notion
append:

```bash
DO_NOTION_EXPORT=1 DO_NOTION_UPDATE=0 bash scripts/ubuntu/publish_experiment_update.sh
```

Append the generated markdown to Notion during the publish step:

```bash
export NOTION_PAGE_ID=<target-page-id-or-url>
export NOTION_TOKEN=<secret-integration-token>
DO_NOTION_EXPORT=1 DO_NOTION_UPDATE=1 bash scripts/ubuntu/publish_experiment_update.sh
```

Do not place `NOTION_TOKEN` in scripts, docs, command history screenshots, or
commit messages.

## Bi-daily Publication Loop

The requested every-other-day update loop is:

```bash
START_IN_TMUX=1 bash scripts/ubuntu/run_bidaily_publication_update.sh
```

Default loop behavior:

- every 48 hours
- generate Overleaf auto tables, status section, and copied result figures
- generate a Notion/GitHub markdown update
- commit and push the scoped main-repo update paths
- commit and push the scoped Overleaf auto snapshot paths
- append to Notion only when `NOTION_TOKEN` and `NOTION_PAGE_ID` are exported

Useful overrides:

```bash
# Dry publication loop: export files only, no commits, no pushes, no live Notion append.
START_IN_TMUX=1 DO_MAIN_COMMIT=0 DO_MAIN_PUSH=0 \
DO_OVERLEAF_COMMIT=0 DO_OVERLEAF_PUSH=0 DO_NOTION_UPDATE=0 \
bash scripts/ubuntu/run_bidaily_publication_update.sh

# Change the cadence for a short smoke test.
START_IN_TMUX=1 INTERVAL_HOURS=1 bash scripts/ubuntu/run_bidaily_publication_update.sh
```

Monitor it with:

```bash
tmux attach -t server-bidaily-publication-update
```

## 24-Hour Operation Pattern

Use this loop manually or as the final step after the orchestrator finishes:

```bash
START_IN_TMUX=1 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh

# After a stage completes and the outputs look reasonable:
DO_MAIN_COMMIT=1 DO_MAIN_PUSH=1 \
DO_OVERLEAF_COMMIT=1 DO_OVERLEAF_PUSH=1 \
bash scripts/ubuntu/publish_experiment_update.sh
```

## Safety Notes

- `DO_MAIN_COMMIT=1` stages only the configured `PUBLISH_PATHS`, not the entire
  dirty worktree.
- `DO_OVERLEAF_COMMIT=1` stages only generated auto files and the results section.
- `DO_*_PUSH=1` should be used only after checking the generated diff.
- Secrets such as Notion tokens should never be placed in commit messages,
  scripts, or command history.
