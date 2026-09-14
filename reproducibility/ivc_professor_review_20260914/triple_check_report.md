# CoM3D-ACE final triple check

Date: 2026-09-14

Paper commit: `7137f6d3d034084576f123ec65907b1b61ab6b5b`

## Pass 1: numbers and frozen artifacts

**PASS**

- `verify_manuscript_numbers.py`: 94/94 source-to-LaTeX checks passed.
- MMOT historical reproduction: 216 metric/count checks; maximum absolute
  floating-point difference `2.842170943040401e-14`.
- M3OT reproduction: 16 sequence/tracker/split checks; metric difference 0 and
  accepted-edge sets exactly matched.
- Reciprocal property audit: 1,989 instances, maximum indegree/outdegree 1/1,
  with zero cycles, strict-time violations, input duplicates, guard rejections,
  or guard/no-guard output differences.
- AFLink audit: 13 overlap contexts and 15 boxes removed by native
  post-remap deduplication; the no-GT validity adapter preserves all boxes.

## Pass 2: method, claims, and professor-review points

**PASS (claim-scope audit), with one deliberately partial figure item.**

- The main table contains the operational None, AFLink+VA, and CoM3D-ACE rows.
  Geometry greedy, Geometry+ReID greedy, partial Hungarian, complete metrics,
  and paired intervals remain in the explicitly linked static-assignment
  appendix.
- The manuscript explicitly reports that Geometry+ReID greedy and partial
  Hungarian attain higher mean IDF1 than historical CoM3D-ACE in all six
  same-input conditions.
- The retained claim is limited to deterministic box-preserving refinement,
  improvements over no refinement and AFLink+VA, and an auditable diagnostic.
- The component guard is described as a defensive assertion, not an active
  accuracy module.
- Confirmation38 is locally pre-specified, not externally preregistered.
- M3OT adverse transfer and its oracle-GT crop-admission limitation are shown.
- Tiny-object prevalence is context, not a scale-stratified superiority claim.
- Figure 1 and Figure 2 files were not modified. Their captions and surrounding
  text scope them as motivation/system context. The requested Figure 1
  temporal before/after replacement itself remains a partial item because the
  author-supplied figure was preserved.

## Pass 3: submission build and layout

**PASS**

- A clean directory with no prior auxiliary files compiled successfully using
  `com3d-ace-latex:20260906` and `latexmk -pdf -interaction=nonstopmode
  -halt-on-error main.tex`.
- Final PDF: 27 pages; all five authors and two corresponding-author marks are
  present.
- Undefined citations/references: 0.
- Overfull boxes: 0.
- Underfull boxes: 4, confined to line wrapping of one long Where2comm URL in
  the bibliography; no clipping or overlap was observed.
- Clean-build and repository-build extracted text SHA-256 are identical:
  `a0b84b9a02ad5735dc81c7164fb8eaad246b2b854b8c5960cbad5452119d3e42`.
- All 14 author-supplied figure files are byte-identical to the pre-edit copy.
- The revised main and static-assignment appendix pages were rendered and
  visually checked for clipping, overlap, and unreadable overflow.

## Submission assessment

The revised manuscript is internally consistent and build-ready. The professor
review materially changed the paper from an implied superiority claim to a
bounded, reproducible refinement-and-diagnostic study. The remaining
unverified items require unavailable external evidence or new protocols: the
exact review PDF identified by SHA-256, source-flight metadata for block
bootstrap, external timestamp evidence for confirmation38, official
GIAOTracker code/weights, and detector-only M3OT transfer. They are disclosed
as limitations and are not represented as completed results.
