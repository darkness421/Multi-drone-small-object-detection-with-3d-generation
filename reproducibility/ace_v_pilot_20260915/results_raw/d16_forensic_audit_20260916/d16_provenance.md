# Table D.16 provenance

- Experiment implementation and immutable result artifacts: `9cd5fb8c319e40cb3f25b469f0bf8dbb8e63bc0b`.
- Review-pack and LaTeX table generator: `a98cac208fc1638966202ac8658356b78ccf753f` (`scripts/build_review_response.py`).
- Manuscript commit that includes Table D.16: `20fa424e51420e0aa20c3dfc4edeeda81096dd71`.
- Frozen configuration: `reproducibility/ace_v_pilot_20260915/protocol_freeze.yaml`.
- Selected development configuration: `results_raw/m3ot_direct_crop_v1/selected_config.json` (`tau_a=0.10`, `tau_m=4.0`).
- MMOT sequence results: `results_raw/mmot_full50_v1/hybrid_results_per_sequence.csv`.
- M3OT sequence results: `results_raw/m3ot_direct_crop_v1/hybrid_results_per_sequence.csv`.
- Table generator output: `results_raw/review_response_20260916/paper_table_ace_v_strong_linker.tex`.
- Reconstructed non-overwriting commands: `results_raw/review_response_20260916/reproduction_commands.md`.

## Execution record

- MMOT manifest status `COMPLETE`, runtime `461.358 s`, result hashes recorded in `results_raw/mmot_full50_v1/manifest.json`.
- M3OT manifest status `COMPLETE`, runtime `175.341 s`, result hashes recorded in `results_raw/m3ot_direct_crop_v1/manifest.json`.
- The exact historical shell strings, scheduler IDs, and stdout/stderr logs for these two runs were not persisted. They cannot be truthfully supplied after the fact. The manifest parameters and current CLI contracts reconstruct executable commands, but those commands are not represented as historical logs.
- No experiment is currently running, and this forensic audit does not rerun either experiment.

## LaTeX linkage

- Manuscript table path: `/home/oem/projects/deepfake/Ourmethod/_checkpoint/meme_comparison/workspace/com3d_ace_ivc_overleaf_sync/ivc_tables/temporal/ace_v_strong_linker.tex`.
- Current generated/table SHA-256: `5e5b9d4480306841d1fae230ae180e100127c33f0f7783cf6dd3b2887728c391` / `5e5b9d4480306841d1fae230ae180e100127c33f0f7783cf6dd3b2887728c391`.
- Byte-identical: `True`.
