# REGR: Reciprocal Evidence-Graph Refinement for Aerial Multi-Object Tracking

This branch contains the code and experiment records associated with the REGR manuscript. REGR is a deterministic post-tracking refinement method: it links compatible frozen tracklets through reciprocal predecessor-successor selection and changes only their identity labels. Boxes, classes, confidence scores, and observation counts are preserved.

## Start here

- [Reproducibility guide](docs/REGR_REPRODUCIBILITY.md): implementation entry points, manuscript-to-artifact mapping, dependencies, and historical method names.
- [Complete MMOT comparison](reproducibility/ivc_professor_review_20260914/main_comparison.csv): all six linkers, three upstream trackers, and both input conditions.
- [Paired comparisons](reproducibility/ivc_professor_review_20260914/paired_linker_deltas.csv): sequence-bootstrap differences.
- [Qualitative evidence](reproducibility/ivc_professor_review_20260914/evidence/detector_temporal_cases/): observations and provenance for the success/failure examples.

## Paper scope

The evaluation uses all 50 MMOT test sequences with frozen ByteTrack, OC-SORT, and Deep OC-SORT outputs, under common oracle AABBs and one shared official detector cache. REGR improves mean IDF1 over no refinement and AFLink with a box-preserving validity adapter in all six settings. Complete comparisons and the held-out M3OT diagnostic are retained in the experiment records.

The current manuscript concerns within-stream temporal identity refinement. Earlier detector, static cross-view, 3D, and re-observation experiments belong to the project's history and are outside this paper's contribution.

## Version and naming

This `regr-paper` branch starts from experiment commit `2a033849f1746604db774c95537f0400b5e513a2` on `server-baseline-pipeline`. The REGR documentation update preserves the recorded algorithms, thresholds, and results. The later `ace-v-pilot-20260915` branch is a separate exploratory study.

The frozen result key `com3d_reciprocal_guard` identifies the rule called **REGR** in the manuscript. Historical filenames and CSV labels remain unchanged so that hashes and result provenance remain traceable. See the guide for all comparator names.

## Access and dependencies

This documentation was prepared on 2026-09-17 while the repository was private. Anonymous access requires a public release. Raw datasets, full tracker/detector caches, pretrained checkpoints, and third-party source checkouts are not bundled; their revisions and hashes are recorded in the reproducibility directories.

For the former project overview, see the [archived README](docs/archive/CoM3D_ACE_README.md).
