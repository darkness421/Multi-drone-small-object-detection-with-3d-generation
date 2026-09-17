# REGR reproducibility guide

## 1. What belongs to this manuscript

REGR is the fixed temporal rule stored as `com3d_reciprocal_guard`. It forms same-class forward-time candidate edges, applies a 30-frame gap gate, a 55-pixel endpoint center-distance gate, and a 0.30 cosine-distance gate, and retains reciprocal geometry-first choices. Identity relabeling preserves the observation multiset. This documentation does not introduce a new method or rerun the reported experiments.

The code baseline is commit `2a033849f1746604db774c95537f0400b5e513a2`. The `regr-paper` branch adds a paper-specific entry point to that existing snapshot.

## 2. Where to find the evidence

Paths below are relative to the repository root.

| Manuscript material | Artifact |
| --- | --- |
| Complete MMOT metrics, including AFLink+VA | [main_comparison.csv](../reproducibility/ivc_professor_review_20260914/main_comparison.csv) |
| Paired IDF1 differences | [paired_linker_deltas.csv](../reproducibility/ivc_professor_review_20260914/paired_linker_deltas.csv) |
| Official 50-sequence reporting split | [split manifest](../reproducibility/ivc_temporal_meta_review_20260914/results_raw/e1_full50_split/manifest.json) |
| Tracker configurations and upstream stage counts | [runtime configurations](../reproducibility/ivc_temporal_meta_review_20260914/results_raw/e0/tracker_runtime_configs.json), [stage counts](../reproducibility/ivc_temporal_meta_review_20260914/results_raw/e0/stage_counts.csv) |
| Sequence-level detector-input IDF1 plot | [source data and rendering record](../reproducibility/ivc_professor_review_20260914/evidence/detector_sequence_deltas/) |
| Qualitative success and false-merge examples | [observations, images, and manifest](../reproducibility/ivc_professor_review_20260914/evidence/detector_temporal_cases/) |
| Common-cost controls, component invariants, AFLink stages, and runtime | [MMOT solver audit](../reproducibility/ivc_professor_review_20260914/results_raw/mmot_cached_solver_audit_v1/) |
| Held-out M3OT diagnostic | [M3OT records](../reproducibility/ivc_professor_review_20260914/results_raw/m3ot_linker_diagnostic_v2/) |
| Size statistics, component ablation, and reporting-partition summaries | [generated tables and manifest](../reproducibility/ivc_temporal_meta_review_20260914/results_raw/paper_ready/) |

The earlier temporal snapshot contains native AFLink results that can be invalid under the common-box protocol. Use `main_comparison.csv` from the professor-review snapshot for the final AFLink+VA comparison. Do not substitute its earlier `aflink_official` rows.

Complete same-input comparisons and transfer diagnostics remain part of the record: Geometry+ReID greedy and partial Hungarian have higher mean IDF1 in all six settings, and the fixed rule degrades on held-out M3OT streams. The documented gains concern MMOT relative to no refinement and AFLink+VA.

## 3. Implementation entry points

- [run_full50_linker_benchmark.py](../reproducibility/ivc_temporal_meta_review_20260914/scripts/run_full50_linker_benchmark.py): candidate construction (`build_candidates`), reciprocal selection (`reciprocal`), identity remapping (`apply_union_edges`), and fixed method dispatch (`method_output`).
- [run_mmot_real_detection_temporal_cached.py](../reproducibility/ivc_temporal_meta_review_20260914/scripts/run_mmot_real_detection_temporal_cached.py): detector-input evaluation from shared detections and frozen caches.
- [run_cached_solver_audit.py](../reproducibility/ivc_professor_review_20260914/scripts/run_cached_solver_audit.py): final comparator/AFLink adapter audit, solver controls, and output invariants.
- [run_m3ot_linker_diagnostic.py](../reproducibility/ivc_professor_review_20260914/scripts/run_m3ot_linker_diagnostic.py): held-out transfer diagnostic.

These are research entry points with external workspace and data dependencies, rather than a standalone installed Python package. Consult the [temporal inventory](../reproducibility/ivc_temporal_meta_review_20260914/experiment_inventory.md) and [solver-audit inventory](../reproducibility/ivc_professor_review_20260914/experiment_inventory.md) for the full recorded commands, required arguments, and source revisions. Historical server paths must be replaced by local paths.

## 4. Method names in frozen files

| Manuscript name | Stored key |
| --- | --- |
| No refinement | `no_refinement` |
| Geometry greedy | `geometry_greedy` |
| Geometry+ReID greedy | `geometry_reid_greedy_guard` |
| Partial Hungarian | `geometry_reid_hungarian` |
| AFLink+VA | `aflink_cached_overlap_safe` |
| REGR | `com3d_reciprocal_guard` |

The REGR display label in historical CSVs is `CoM3D-ACE (historical ranking)`. This refers to the same fixed rule, not the project's former detector or static cross-view pipeline. Renaming the stored keys would break existing manifests and analysis scripts, so the mapping is documented here.

## 5. Environment and inputs

The temporal inventory records the BoxMOT, TrackEval, official MMOT, and StrongSORT revisions, and hashes of the BaseReID, detector, and AFLink checkpoints. The [requirements snapshot](../reproducibility/ivc_temporal_meta_review_20260914/requirements-audit.txt) records the numerical environment; it is not a complete installer for the external source workspaces.

MMOT data and pretrained weights must be obtained from their original sources. Full raw datasets, prediction caches, and all external workspaces are not included in this repository. Cached execution commands require those inputs to be generated or supplied at the documented paths. Reading the committed CSVs and manifests does not require new inference.

The MMOT pseudo-RGB policy is zero-based bands `[4, 2, 1]` for RGB, equivalent to `[1, 2, 4]` for BGR. The appearance encoder and all linking thresholds are fixed in the recorded study.

## 6. Verification records

The snapshots retain their original source hashes, output hashes, and manuscript verification reports. They verify the historical manuscript versions named in those records. Their table numbers, names, and source-text checks do not automatically validate a later REGR manuscript layout.

For the current paper, match values by protocol, tracker, method key, and aggregation. HOTA, AssA, and IDF1 are equal-sequence means; IDSW is summed. Each full-test setting contains 50 sequences. Historical PDF copies remain archival.

Repository access was private when this guide was prepared on 2026-09-17. A repository URL in the manuscript does not by itself grant reviewer access; public availability must be checked before describing this as a public code release.
