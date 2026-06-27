# ACCV Second Draft Review Plan - 2026-06-28

Updated: `2026-06-28 06:30 KST`

## Objective

Prepare the second revised ACCV draft after the nightly MarineCity and neural-3D
refreshes settle. The draft should be Overleaf-syncable through GitHub and
should not expose internal automation or placeholder wording as paper claims.

## Main-Paper Pass

1. Keep the main paper within the 14-page ACCV limit including figures/tables.
2. Keep essential claims in main:
   - SAFR-YOLO / Ours detector comparison.
   - Compact detector ablation.
   - AP/AP50 versus parameter trade-off figure or table.
   - Real-Cesium MarineCity system smoke table.
   - Neural-3D smoke metric table with conservative wording.
3. Move supporting material to supplementary:
   - Full YOLO-family scale inventory.
   - Detailed related-work reproduction status.
   - Grad-CAM/heatmap and NMS/input-resolution checks.
   - Full MarineCity capture-source and cross-view evidence graph details.
   - Prompt schema, provider status, failure cases, and extra qualitative panels.
4. Remove submission-unsafe wording:
   - no internal automation names in paper-facing text;
   - no "candidate" wording in final main result tables unless clearly marked as validation-pending;
   - no TinyPerson superiority claim.

## Simulation / 3D Pass

1. Use the completed S0/S1/S2 real-Cesium viewer160 capture/detector/reasoner
   artifacts as system-protocol evidence.
2. Compare the new 24k Nerfacto row against the existing 12k Nerfacto,
   Instant-NGP 5k, and Splatfacto/3DGS-style 5k rows. The 12k Nerfacto row
   remains the best paper-facing Nerfacto row by PSNR/LPIPS.
3. Refresh:
   - `paper/tables/marinecity_3d_completion_results_table.tex`
   - `outputs/reports/live/marinecity_3d_completion_results_table.md`
   - `outputs/reports/live/marinecity_simulation_dashboard.png`
   - Fig. 1 / Fig. 3 handoff assets if the new qualitative images improve them.

## Overleaf Pass

1. Push final second-draft updates to:
   - experiment repo branch `server-baseline-pipeline`;
   - Overleaf-linked repo `darkness421/-ACCV-Multi-drone-small-object-detection-with-3d-generation`, branch `main`.
2. Confirm Overleaf-linked `main` commit hash after push.
3. In Overleaf, sync with GitHub and verify that `main.tex` loads
   `sections/full_main_draft_bundle`.

## Current Night Queue

| Item | Status |
| --- | --- |
| Overleaf full draft sync | Done: `7674ffb` |
| MarineCity viewer160 S0/S1/S2 rule-based refresh | Done: 3/3 scenarios |
| Nerfacto 24k GPU0 run | Complete; archived as supplemental run log |
| Paper gate loop | Running every 15 minutes |
