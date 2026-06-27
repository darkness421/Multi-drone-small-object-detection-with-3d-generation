# Overleaf Sync Status

Updated: `2026-06-28`

## Result

Overleaf sync was blocked because the active experiment repository and the
Overleaf-linked repository are different GitHub repositories.

The Overleaf-linked repository has now been updated directly. The previous
2026-06-27 sync commit was `981d837`; the current full-draft sync is:

- Repository: `darkness421/-ACCV-Multi-drone-small-object-detection-with-3d-generation`
- Branch: `main`
- Pushed commit: `9875dd0 Refresh MarineCity Nerfacto contact sheet`
- Local clean sync worktree: `/tmp/accv-overleaf-sync`

The main experiment repository remains:

- Repository: `darkness421/Multi-drone-small-object-detection-with-3d-generation`
- Branch: `server-baseline-pipeline`
- Latest pushed experiment/status commit: `492186a Add ACCV full draft bundle`

## What To Do In Overleaf

Open Overleaf and run `Sync with GitHub` / pull from GitHub again. It should now
see commit `9875dd0` on the linked GitHub repository. Commit `7674ffb` synced
the full draft bundle, and `9875dd0` refreshes the MarineCity Nerfacto contact
sheet. The pushed `main.tex` loads `sections/full_main_draft_bundle`, so the
current full draft should be visible after sync.

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
