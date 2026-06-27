# Overleaf Sync Status

Updated: `2026-06-27`

## Result

Overleaf sync was blocked because the active experiment repository and the
Overleaf-linked repository are different GitHub repositories.

The Overleaf-linked repository has now been updated directly:

- Repository: `darkness421/-ACCV-Multi-drone-small-object-detection-with-3d-generation`
- Branch: `main`
- Pushed commit: `981d837 Update ACCV paper results for Overleaf`
- Local clean sync worktree: `/tmp/accv-overleaf-sync`

The main experiment repository remains:

- Repository: `darkness421/Multi-drone-small-object-detection-with-3d-generation`
- Branch: `server-baseline-pipeline`
- Latest pushed experiment/status commit: `eae7e8c Document gate-first ACCV execution status`

## What To Do In Overleaf

Open Overleaf and run `Sync with GitHub` / pull from GitHub again. It should now
see commit `981d837` on the linked GitHub repository.

Local full PDF compilation was not run because this server environment does not
currently provide `latexmk`, `pdflatex`, or `xelatex`. The local patch integrity
checks should still be run from this repository before and after paper edits.

## Continuous Queue

Use the queue runner below to keep paper-gate artifacts refreshed:

```bash
bash scripts/ubuntu/run_accv_paper_gate_queue.sh
```

For a detached repeated queue:

```bash
tmux new-session -d -s accv-paper-gate-queue \
  'cd /home/oem/projects/multi-uav-marine-city && QUEUE_LOOP=1 QUEUE_MAX_ITER=0 QUEUE_INTERVAL_SEC=900 bash scripts/ubuntu/run_accv_paper_gate_queue.sh'
```

The queue refreshes:

- LaTeX patch integrity
- Paper artifact readiness
- MarineCity 3D completion readiness
- AeroGraph non-mock readiness
- External provider/runner capability status
- AeroGraph table placeholders
- MarineCity simulation dashboard
- Live detector dashboard
- ACCV workflow snapshot
- ACCV remaining gates queue

It does not fabricate completed 3D/reasoner claims. Pending gates remain
pending in the output files until real evidence is available.
