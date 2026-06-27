# Nightly Execution Status - 2026-06-28

Updated: `2026-06-28 06:30 KST`

## Overleaf Sync

- Overleaf-linked repository: `darkness421/-ACCV-Multi-drone-small-object-detection-with-3d-generation`
- Branch: `main`
- Latest pushed commit: `7674ffb Sync ACCV full draft bundle for Overleaf`
- Main entry point now loads: `\input{sections/full_main_draft_bundle}`
- Validation: LaTeX patch integrity passed in the main experiment repository before sync.

## Running Queues

| Session | Purpose | Resource | Status |
| --- | --- | --- | --- |
| `accv-nightly-marinecity-0628` | Refresh MarineCity viewer160 S0/S1/S2 reasoner outputs from detector tokens | Isaac container / CPU detector reuse | Complete: 3/3 scenarios, 0 failed |
| `accv-nightly-nerfacto-24k-gpu0` | Longer native Nerfacto smoke run for MarineCity neural-3D evidence | GPU0 | Complete; retained 12k as best paper row |
| `accv-nightly-paper-gate-loop-0628` | Refresh paper readiness, dashboards, workflow status every 15 min | CPU | Running |

## Current Plan

1. Use the existing Nerfacto 12k row as the paper-facing best row: PSNR 22.76,
   SSIM 0.941, LPIPS 0.070.
2. Keep the completed 24k row as a supplemental run log only because it did not
   improve PSNR/LPIPS over the 12k row.
3. Refresh paper-facing 3D table, MarineCity dashboard, and Fig. 1/Fig. 3 handoff assets.
4. Prepare the second revised draft tonight after the updated 3D artifacts settle.

## Notes

- Docker Nerfstudio image is not used for RTX 5090 because its CUDA/tiny-cuda-nn build does not support `sm_120`.
- Native `marinecity-nerfstudio` environment detects RTX 5090 correctly with PyTorch `2.11.0+cu128`.
- TinyPerson remains auxiliary only and should not be used as a main-paper claim unless explicitly promoted later.
- `paper/tables/marinecity_3d_completion_results_table.tex` and
  `paper/figures/results/marinecity_system/marinecity_nerfacto_eval_contact_sheet.png`
  were refreshed after the 24k run, with the table reverted to the best verified
  12k Nerfacto row.
