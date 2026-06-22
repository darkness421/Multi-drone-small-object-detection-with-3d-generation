# 24h Experiment Orchestrator

This document describes the safe 24-hour automation lane for the ACCV experiments.
The orchestrator does not invent new methods or modify code by itself. It chains
approved experiment queues, waits for tmux sessions to finish, collects results,
builds stage-gate reports, and optionally pushes status to Notion.

## What It Automates

- Wait for the active large detector comparison session to finish.
- Collect the large detector results, summary CSV, p-values, dashboard, report
  bundle, detector stage gate, and proposed-overwhelm gate.
- Start or wait for the top-3 YOLO + proposed-module screening queue.
- Collect combined baseline/proposed results across the current large baseline,
  top-3 proposed screening, top-3 main run, and legacy proposed ablation roots.
- Optionally run and collect UAVDT cross-dataset experiments.
- Optionally run and collect 3D generation experiments after the 3D benchmark
  manifest and runner are ready.
- Optionally build an auto-research agenda from the latest performance gap.
- Optionally export a draft paper snapshot into the Overleaf-linked GitHub repo.

## What It Does Not Automate

- It does not automatically edit detector code after a failure.
- It does not change the proposed module definition without review.
- It does not pick the final paper claim until the stage-gate outputs support it.
- It does not enable UAVDT or 3D by default, because those depend on dataset
  readiness and the real 3D runner boundary.

This keeps the experiments reproducible. Failures should be inspected, fixed,
committed, and then resumed with the same orchestrator.

## Main Command

Start the full default detector lane in tmux:

```bash
START_IN_TMUX=1 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

Attach:

```bash
tmux attach -t server-24h-orchestrator
```

The orchestrator log is written under:

```text
outputs/logs/orchestrator/<run_id>/orchestrator.log
```

## Default Detector Flow

The default flow is:

```text
server-large-comparison finishes
  -> collect large detector results
  -> start/wait server-top3-proposed-screening
  -> collect combined baseline + proposed results
```

Important outputs:

```text
outputs/experiments/server_fresh/large_20260524_140922/server_baseline_results.csv
outputs/experiments/server_fresh/large_20260524_140922/server_baseline_summary.csv
outputs/experiments/server_fresh/large_20260524_140922/server_baseline_stage_gate.md
outputs/experiments/server_fresh/large_20260524_140922/proposed_overwhelm_gate.md

outputs/experiments/server_with_proposed/server_with_proposed_results.csv
outputs/experiments/server_with_proposed/server_with_proposed_summary.csv
outputs/experiments/server_with_proposed/server_with_proposed_stage_gate.md
outputs/experiments/server_with_proposed/proposed_overwhelm_gate.md

outputs/reports/server_fresh_baselines/large_20260524_140922/README.md
outputs/reports/server_with_proposed/README.md
```

## Optional UAVDT

Enable after the UAVDT dataset is prepared:

```bash
START_IN_TMUX=1 ENABLE_UAVDT=1 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

If UAVDT is not ready, the optional stage fails without stopping the detector
main lane unless `CONTINUE_ON_OPTIONAL_FAILURE=0` is set.

## Optional 3D Generation

Enable after the Marine City multi-view benchmark manifest and real 3D runner are
ready:

```bash
START_IN_TMUX=1 ENABLE_3D=1 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

Default 3D inputs and outputs:

```text
outputs/experiments/marinecity_multiview_benchmark.json
outputs/experiments/3d_generation/
outputs/experiments/3d_generation_comparison.csv
```

## Optional Notion Status

If `NOTION_TOKEN` and `NOTION_PAGE_ID` are already exported in the shell, enable:

```bash
START_IN_TMUX=1 ENABLE_NOTION=1 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

Do not paste tokens into command history. Export secrets in a private shell or
use a local environment file that is not committed.

## Optional GitHub and Overleaf Publish Step

Export the latest table/figure snapshot to the Overleaf-linked repo after the
orchestrator completes:

```bash
START_IN_TMUX=1 ENABLE_PUBLISH=1 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

Commit and push are still off by default. To enable both main-repo and Overleaf
pushes after checking the policy in `docs/github_overleaf_automation.md`:

```bash
START_IN_TMUX=1 ENABLE_PUBLISH=1 \
DO_MAIN_COMMIT=1 DO_MAIN_PUSH=1 \
DO_OVERLEAF_COMMIT=1 DO_OVERLEAF_PUSH=1 \
bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

## Optional Auto Research Agenda

Generate a research agenda after result collection:

```bash
START_IN_TMUX=1 ENABLE_AUTO_RESEARCH=1 bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

This produces:

```text
outputs/research/auto_research_agenda.md
outputs/research/auto_research_agenda.csv
```

## Useful Overrides

```bash
POLL_SECONDS=120
ENABLE_TOP3=0
ENABLE_UAVDT=1
ENABLE_3D=1
CONTINUE_ON_OPTIONAL_FAILURE=0
LARGE_SESSION=server-large-comparison
TOP3_SESSION=server-top3-proposed-screening
COMBINED_DETECTOR_ROOTS=path_a,path_b,path_c
```

GPU1 baseline extension:

```bash
bash scripts/ubuntu/start_gpu1_baseline_extension.sh
```

When a separate GPU1 baseline session is running, restart or launch the
orchestrator with both wait sessions and roots:

```bash
BASELINE_WAIT_SESSIONS=server-large-comparison,server-gpu1-baseline-extension \
EXTRA_BASELINE_ROOTS=outputs/detectors/server_fresh_baselines/<gpu1_run_id> \
START_IN_TMUX=1 ENABLE_AUTO_RESEARCH=1 \
bash scripts/ubuntu/run_24h_experiment_orchestrator.sh
```

## Recovery Pattern

1. Attach to the orchestrator tmux session and inspect the latest stage log.
2. Fix the failing dataset/config/code boundary manually.
3. Restart the orchestrator with the same command.
4. Completed top-3 jobs are skipped by default through `SKIP_COMPLETED=1`.

This makes the server behave like a 24-hour experiment operator while preserving
paper-grade traceability.
