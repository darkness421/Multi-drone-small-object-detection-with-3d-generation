# Server Progress

## 2026-05-15

Baseline infrastructure stage.

Completed:

- Added Ubuntu path config in `configs/paths.ubuntu.yaml`.
- Added Ubuntu environment and dataset readiness wrappers.
- Added tmux scripts for two-GPU VisDrone baseline queues and paired runs.
- Added result collectors for server baseline result CSV, summary CSV, and p-value CSV.
- Added detector ROC-AUC utilities separated from future ambiguity ROC-AUC.
- Added dashboard, qualitative examples, and Grad-CAM preparation entrypoints.
- Added proposed small-object perception module skeleton and config.
- Added Marine City multi-angle benchmark and 3D generative model comparison scaffolds.
- Added LLM-assisted final adjudicator and ablation evaluation scaffolds.
- Added Ubuntu VisDrone dataset preparation scripts for staging/downloading, conversion, and preflight.

Not run:

- No long detector training was started.
- No dataset copy or weight download was performed.

Next:

1. Run environment and dataset checks on the Ubuntu server.
2. Launch preliminary 3-seed baseline sweep in tmux.
3. Collect CSV/PNG summaries.
4. Extend top models to 5 seeds for main statistical analysis.
5. Add the proposed module to the best overall or best lightweight baseline.
6. Build Marine City multi-angle benchmark splits for 3D generation and reasoner ablations.
