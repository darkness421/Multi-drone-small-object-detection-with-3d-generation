Closed-loop re-observation revision guidance folder

Purpose
This folder is intentionally separate from the ACCV paper source tree.
Do not include these files from the main paper or supplementary LaTeX until a
manual paper revision pass is made.

What this folder contains
1. Korean guidance notes for GPT Pro/manual revision.
2. Candidate LaTeX tables that can be copied into paper/tables after review.
3. Candidate figures copied from the closed-loop re-observation artifact run.
4. CSV/JSON source data for the fresh commanded closed-loop result.
5. Prompt audit and 3D visual audit files for reviewer-facing transparency.

Current claim boundary
The current result is a fresh commanded Isaac/Cesium camera-pose recapture
using graph-generated target poses. It verifies that targeted re-observation
evidence can update graph hypotheses and change actions. It is not a fully
autonomous physical UAV flight/planner benchmark.

Recommended use
1. Read 00_summary_for_gpt_pro_ko.txt first.
2. Use 01_main_paper_revision_map_ko.txt for main-paper edits.
3. Use 02_supplement_revision_map_ko.txt for supplementary edits.
4. Use 04_claim_boundary_and_wording_ko.txt to avoid overclaiming.
5. Use PROMPT_FOR_GPT_PRO_ko.txt when asking GPT Pro to rewrite the paper.

Generated from
outputs/reports/live/closed_loop_reobservation_fresh_20260703/
