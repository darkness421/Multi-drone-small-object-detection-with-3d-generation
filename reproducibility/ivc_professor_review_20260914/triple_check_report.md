# CoM3D-ACE final triple check

Date: 2026-09-14

Paper commit: `51a93e0a7dca9c99d2115c87162de3fd167130de`

## Pass 1: numbers and frozen artifacts

**PASS**

- `verify_manuscript_numbers.py`: 100/100 source-to-LaTeX checks passed.
- Frozen MMOT result reproduction: 216 metric/count checks; maximum absolute
  floating-point difference `2.842170943040401e-14`.
- M3OT reproduction: 16 sequence/tracker/split checks; metric difference 0 and
  accepted-edge sets exactly matched.
- Reciprocal property audit: 1,989 instances, maximum indegree/outdegree 1/1,
  with zero cycles, strict-time violations, input duplicates, guard rejections,
  or guard/no-guard output differences.
- AFLink audit: 13 overlap contexts and 15 boxes removed by native
  post-remap deduplication; the no-GT validity adapter preserves all boxes.

## Pass 2: method, claims, and professor-review points

**PASS (claim-scope audit).**

- The main Table 2 contains None, Geometry greedy, Geometry+ReID greedy,
  partial Hungarian, AFLink+VA, and CoM3D-ACE under the same frozen-tracklet
  inputs. HOTA/AssA detail remains in Appendix B.
- The former Table B.10 ranking-versus-assignment diagnostic is now main
  Table 4 with its original label retained. Appendix Table B.10 now reports
  paired intervals against both static controls and AFLink+VA.
- The manuscript explicitly reports that Geometry+ReID greedy and partial
  Hungarian attain higher mean IDF1 than fixed CoM3D-ACE in all six
  same-input conditions, while every AFLink+VA interval favors CoM3D-ACE.
- The retained claim is limited to deterministic box-preserving refinement,
  improvements over no refinement and AFLink+VA, and an auditable diagnostic.
- The component guard is described as a defensive assertion, not an active
  accuracy module.
- Confirmation38 is locally pre-specified, not externally preregistered.
- Table C.12 defines conditional link error over auditable accepted links,
  reports the auditable share, and retains unknown links in coverage.
- The six-point appearance-gate grid is linked as a descriptive artifact, not
  a test-selected operating point.
- M3OT adverse transfer and the exact oracle-GT descriptor-crop admission,
  scoring, and post-hoc label uses are shown.
- Tiny-object prevalence is context, not a scale-stratified superiority claim.
- Figure 1 now connects poorly resolved aerial targets to within-stream
  temporal identity fragmentation. Figure 2 shows only the evaluated path:
  frozen tracker outputs, EvidenceToken adaptation, candidate construction,
  linker comparison, ID-only relabeling, and improvement/failure audit.

## Pass 3: submission build and layout

**PASS**

- A clean directory with no prior auxiliary files compiled successfully using
  `com3d-ace-latex:20260906` and `latexmk -pdf -interaction=nonstopmode
  -halt-on-error main.tex`.
- Final PDF: 28 pages; all five authors and two corresponding-author marks are
  present.
- Undefined citations/references: 0.
- Overfull boxes: 0.
- Underfull boxes: 4, confined to line wrapping of one long Where2comm URL in
  the bibliography; no clipping or overlap was observed.
- Clean-build and repository-build extracted text SHA-256 are identical:
  `35a4977eb50e816a6fff25a4a667ab5c0b06a9805f9bd55f4e3092b19701570f`.
- Figure 1 and Figure 2 were intentionally replaced to match the evaluated
  temporal task; the remaining figure files were not changed in this revision.
- Pages containing Figures 1--2 and Tables 2, 4, B.10, C.12--C.13, and D.14
  were rendered and visually checked for clipping, overlap, and unreadable
  overflow.

## Submission assessment

The revised manuscript is internally consistent and build-ready. The professor
review materially changed the paper from an implied superiority claim to a
bounded, reproducible refinement-and-diagnostic study. Strong same-task
baselines and the adverse M3OT result remain visible. The remaining
unverified items require unavailable external evidence or new protocols: the
exact review PDF identified by SHA-256, source-flight metadata for block
bootstrap, external timestamp evidence for confirmation38, official
GIAOTracker code/weights, and detector-only M3OT transfer. They are disclosed
as limitations and are not represented as completed results.
