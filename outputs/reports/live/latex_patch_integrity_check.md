# LaTeX Patch Integrity Check

Updated: `2026-06-27 13:34:55 KST`
Status: `latex_patch_integrity_ok`

## Summary

- Checked files: `15`
- Missing inputs: `0`
- Missing graphics: `0`
- Duplicate labels: `0`
- Unresolved refs: `0`
- Pending rows needing review: `0`

## Bundles

| bundle | exists | included_file_count | commented_optional_inputs |
| --- | --- | --- | --- |
| paper/sections/main_results_patch_bundle.tex | True | 12 | ['sections/07_marinecity_qualitative_figure_slots'] |
| paper/sections/supplementary_patch_bundle.tex | True | 4 | [] |

## Pending Mentions

| source | line | status | text |
| --- | --- | --- | --- |
| paper/sections/06_marinecity_3d_readiness.tex | 10 | allowed | kept as pending before making a stronger final reasoning claim. |
| paper/sections/06_marinecity_3d_readiness.tex | 34 | allowed | 360, and 3D Gaussian Splatting training remain pending until the external |
| paper/sections/06_marinecity_3d_readiness.tex | 91 | allowed | runner. Therefore, full neural 3D metrics remain a pending experiment rather |
| paper/sections/06_marinecity_3d_readiness.tex | 93 | allowed | Table~\ref{tab:marinecity_3d_completion_results} is kept as a pending-safe |
| paper/sections/06_marinecity_3d_readiness.tex | 94 | allowed | metric slot: it remains visibly pending until verified upstream runner metrics |
| paper/sections/06_marinecity_3d_readiness.tex | 97 | allowed | artifacts, and Table~\ref{tab:aerograph_reasoner_pending} reports the current |
| paper/sections/06_marinecity_3d_readiness.tex | 118 | allowed | remains pending before promoting this to a final reasoning benchmark claim.} |
| paper/sections/06_marinecity_3d_readiness.tex | 119 | allowed | \label{tab:aerograph_reasoner_pending} |
| paper/sections/main_results_patch_bundle.tex | 10 | allowed | % - AeroGraph has a reviewed 49-prompt candidate table; external provider replication remains pending. |
| paper/tables/aerograph_reasoner_results_placeholder.tex | 7 | allowed | Codex-assisted manual LLM review candidate final49 & 49 & 13 & 36 & 0 & Candidate; external replication pending; mismatches=0; source=aerograph_prompt_pack_eval_manual_web \\ |
| paper/tables/marinecity_system_scenario_table.tex | 3 | allowed | \caption{MarineCity multi-UAV system smoke-test results. The current reasoner provider is a deterministic AeroGraph mock; non-mock LLM/VLM validation is marked as pending for the final system study.} |
