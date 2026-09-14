# CoM3D-ACE final triple check

Date: 2026-09-14

Paper commit: `da05de1a1a17e48f66789682c6654fabec1c351d`

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
- The added result figures were rendered from completed frozen outputs. No
  detector, tracker, descriptor, threshold-search, or training run was added.
- A fresh rerun reproduced both figure CSVs and PNGs byte-for-byte. Rasterized
  pages from the regenerated vector PDFs were also byte-identical; PDF container
  hashes differ across runs because of embedded creation metadata.

## Pass 2: method, claims, and professor-review points

**PASS (claim-scope audit).**

- Main Table 2 now has one role: improvement over unchanged tracker output and
  the validated AFLink+VA adapter under identical frozen observations.
- Main Table 4 separately compares alternative temporal tracklet linkers under
  the same inputs. Geometry+ReID greedy and partial Hungarian remain visible
  and have higher mean IDF1 in all six conditions.
- Figure 3 expands the detector-input means into all 50 sequence-level IDF1
  changes. ByteTrack/OC-SORT/Deep OC-SORT improve on 41/45/32 sequences, tie on
  5/3/9, and worsen on 4/2/9; equal-sequence means are +1.65/+1.62/+1.00 pp.
- Figure 4 uses immutable tracker predictions and accepted-link traces. It
  retains one correct CoM3D-ACE edge and one false merge for which partial
  Hungarian selects the correct predecessor. GT is used only for the post-hoc
  one-to-one same-class IoU audit.
- `ID-preserving` was replaced by observation-preserving identity refinement,
  and the former static-assignment wording was corrected to temporal-linker
  comparison. Internal labels were retained to avoid broken references.
- The M3OT gate-development scope and oracle-GT crop-admission diagnostic are
  explicitly separated from MMOT fine-tuning and detector-input claims.
- The contribution remains bounded to deterministic observation-preserving
  refinement, improvements over no refinement and AFLink+VA, and an auditable
  success/failure diagnostic. Universal temporal-linker superiority is not
  claimed.

## Pass 3: submission build and layout

**PASS**

- A clean directory with no prior auxiliary files compiled successfully using
  `com3d-ace-latex:20260906` and `latexmk -pdf -interaction=nonstopmode
  -halt-on-error main.tex`.
- Final PDF: 32 pages; all five authors and two corresponding-author marks are
  present.
- Undefined citations/references: 0.
- Overfull boxes: 0.
- Underfull boxes: 4, confined to line wrapping of one long Where2comm URL in
  the bibliography; no clipping or overlap was observed.
- Final PDF SHA-256: `6bcf768f4a53321ac05fe4b8c344fa5520c829b443039e5d13f5feae555e006f`;
  extracted-text SHA-256:
  `0f14e0291e70becda04c775f2169c46c1b5a149948d7dbac348de8c9a1837c08`.
- Pages containing Figures 1--4 and Tables 2 and 4 were rendered and visually
  checked. Figure 1/2 raster files were not edited in this revision; the new
  result figures have no clipping, overlap, or unreadable overflow.

## Submission assessment

The primary evidence is now visible before the boundary analysis: Table 2 and
Figure 3 establish broad gains over unchanged trajectories and AFLink+VA,
while Figure 4 shows what a verified accepted edge changes in real predictions.
The manuscript also keeps the stronger same-task linkers, a false-merge case,
and adverse M3OT transfer visible. It is internally consistent and build-ready
as a bounded refinement-and-diagnostic study, but it does not establish that
CoM3D-ACE is the most accurate temporal linker.

The remaining unverified items require unavailable external evidence or new
protocols: the exact review PDF identified by SHA-256, source-flight metadata
for block bootstrap, external timestamp evidence for confirmation38, official
GIAOTracker code/weights, and detector-only M3OT transfer. They are not
represented as completed results.
