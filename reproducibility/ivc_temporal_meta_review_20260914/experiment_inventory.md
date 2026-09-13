# CoM3D-ACE Temporal Meta-Review Experiment Inventory

Date: 2026-09-14

This inventory covers only the frozen post-tracking tracklet-refinement study
requested in the A-plan. Existing development results were preserved. New
outputs are represented in this reproducibility snapshot and were not written
into historical result directories.

## Status vocabulary

- `verified`: provenance or implementation was inspected and checked.
- `implemented-not-run`: executable code exists but was not run.
- `running`: a process is currently active.
- `complete-not-in-paper`: computation and validation are complete, but the
  result has not yet been incorporated into the manuscript.
- `complete-in-paper`: computation, validation, and manuscript incorporation
  are complete.
- `blocked`: an external dependency needed for a fair experiment is absent.

## Experiment status

| Item | Status | Evidence |
|---|---|---|
| E0 channel and input audit | verified | `results_raw/e0/channel_audit.json`, `input_manifest.csv` |
| E0 evaluator sanity tests | verified | `results_raw/e0/evaluator_sanity_tests.json` |
| E0 tracker/runtime audit | verified | `results_raw/e0/tracker_runtime_configs.json`, `stage_counts.csv` |
| E1 corrected legacy-12 pilot | complete-not-in-paper | `results_raw/e1_direct_12_v1/` |
| E1 MMOT official test-50, oracle AABB | complete-in-paper | `results_raw/e1_direct_full50_v2_equal/`; Table 2 |
| E1 official AFLink comparison | complete-in-paper | Tables 2, 3, and B.10; invalid outputs remain N/A |
| E1 GIAOTracker global linker | blocked | `results_raw/e1_giao_availability/manifest.json` |
| E2 temporal ablation | complete-in-paper | `results_raw/e1_direct_full50_v2_equal/results/temporal_ablation.csv`; Table 5 |
| E2 fixed-gate error/coverage | complete-in-paper | `results_raw/e2_error_coverage_direct_full50_v1/`; Fig. 2 and Table B.10 |
| E2 M3OT development/held-out diagnostic | complete-in-paper | `results_raw/e2_m3ot_failure_attempt2/`; Table 6 |
| E2 native object-size audit | complete-in-paper | `results_raw/derived/e1_direct_full50_v2_equal_sizes/`; Table 7 |
| E2 ReID and graph runtime | complete-in-paper | `results_raw/e2_runtime_reid_full50_v1/`, `e2_runtime_graph_full50_v1/`; Table 8 |
| E3 MMOT official detector inference | complete-in-paper | `results_raw/e3_detector_full50_v1/`; Table 3 input cache |
| E3 detector-input temporal evaluation | complete-in-paper | `results_raw/e3_temporal_full50_v2_equal/`; Table 3 |
| Paper-ready tables and key numbers | complete-in-paper | `results_raw/paper_ready/manifest.json`; eight generated LaTeX tables |
| Actual-prediction qualitative evidence | complete-in-paper | `evidence/temporal_link_examples_full50/manifest.json`; Fig. 3 |

No experiment process is running.

The manuscript incorporation was checked by
`scripts/verify_temporal_paper_numbers.py`: all eight result tables are
byte-identical to generated tables, and all 18 source/PDF checks pass. The
post-A PDF and verification record are indexed under `evidence/paper_after_A/`
and `paper_verification.json`.

## Frozen data and reporting split

- Dataset: official MMOT test release, Hugging Face revision
  `57dfe1521ee2efa31813cd0065d437d498f0d710`.
- Release contents used: 50 test archives, 5,466 paired NPY/annotation frames,
  47,256,545,280 bytes before extraction.
- Reporting split: 12 sequences already evaluated before this meta-review
  (`legacy12`) and the remaining 38 (`confirmation38`). The split manifest says
  explicitly that no sequence was selected by performance.
- Split membership is in the `sequences` array of
  `results_raw/e1_full50_split/manifest.json`.
- The 50-sequence oracle protocol contains 196,194 annotated AABBs after the
  official OBB-to-AABB conversion and basic validity checks.

The raw NPY arrays are HWC `uint8` with eight spectral bands. The corrected
pseudo-RGB path uses one-based bands 5, 3, and 2, or zero-based `[4,2,1]` for
PIL RGB. The official tracker path's BGR `[1,2,4]` selection is equivalent
after its internal conversion. The former local scripts' `[:, :, :3]` policy
was not equivalent and was superseded for all appearance-based results here.

## Frozen models and code

| Component | Revision or SHA-256 |
|---|---|
| BoxMOT | `6edfa8ad7dc2f24b19a41c0058fc53d8d2c4e8ec` |
| TrackEval | `12c8791b303e0a0b50f753af204249e622d0281a` |
| MMOT official code | `4d365c9eab4cefda058f46cdd821ea06b366bfe4` |
| BaseReID ResNet-50 checkpoint | `4bf6b63d49235973033c47f77bc9b94a54bdd222bd3f484b4e484aba580254c1` |
| Official MMOT YOLO11L-3ch checkpoint | `6d9f66ed17eb1e29a452d43f223a55efe83959f480c65e596fd288bc966f2b15` |
| Official AFLink checkpoint | `b35cbeddd3acc48fece820bd640640e6bfb1f5fbf570aa79af26c6a38958daa4` |
| StrongSORT/AFLink repository | `ee995076da5083e28d0da1f885297df62705ebd7` |

The ReID model is a fixed OpenMMLab MOT17 BaseReID model. Three crops
(first/middle/last when available) are resized to 128 x 256, encoded, L2
normalized, and averaged per tracklet. It was not trained or adapted on MMOT
or M3OT evaluation identities.

The detector is the checkpoint distributed by the MMOT authors for their
train/test benchmark protocol. It was run once at 1280-pixel input,
confidence 0.1, and NMS IoU 0.6. The resulting 193,977 detections over 5,466
frames, including one zero-detection frame, were cached and shared by every
tracker/refiner comparison.

## Fixed temporal policy

- Maximum non-overlapping temporal gap: 30 frames.
- Endpoint center-distance gate: 55 pixels.
- Appearance cosine-distance gate: 0.30.
- Proposed selection: mutual lexicographic nearest successor/predecessor,
  then ascending appearance distance, temporal gap, and stable IDs.
- Merge constraint: union only when the two components have disjoint frame
  supports. Unmatched tracklets remain unchanged.
- Partial Hungarian control: mean of normalized geometry, appearance, and gap
  costs with a dummy unmatched cost of 1.0.
- AFLink official settings: `thrT=(0,30)`, `thrS=75`, `thrP=0.05`.

All methods receive the same frozen upstream tracklets. Linking changes only
identity labels: it does not interpolate boxes, alter scores/classes, or add
detections. Ground-truth identity is read only for the final evaluator and
post-hoc link audits.

## Tracker adapters

Each fine-grained MMOT class is processed by an independent tracker instance.
Frames retain their released numeric order and no intermediate frame is
skipped. Full details and source hashes are in
`results_raw/e0/tracker_runtime_configs.json`.

- ByteTrack: BoxMOT defaults including detection threshold 0.45, match
  threshold 0.8, buffer 25, min hits 3, max age 30, and IoU threshold 0.3.
- OC-SORT: threshold 0.3, max age 30, min hits 3, IoU threshold 0.3,
  `delta_t=3`, inertia 0.2, and `use_byte=false`.
- Deep OC-SORT: BoxMOT configuration and fixed precomputed ReID embeddings;
  exact YAML and adapter overrides are embedded in the audit JSON.

These are the historical BoxMOT AABB adapters used by CoM3D-ACE, not the
rotated trackers or runtime thresholds from the MMOT authors' native code.

## Principal commands

The private execution manifests preserved fully expanded commands and script
hashes. This public snapshot replaces workstation-specific path prefixes with
documented angle-bracket tokens. The same commands can be expressed portably
by setting:

```bash
EXP=/path/to/ivc_temporal_meta_review_20260913
DATA=/path/to/mmot/test_meta_review_split
WORKSPACE=/path/to/frozen/accv2026_rebuttal
PY=/path/to/environments/accv_m3ot/bin/python
```

Oracle-AABB full-50 comparison:

```bash
$PY $EXP/scripts/run_full50_linker_benchmark.py \
  --workspace "$WORKSPACE" \
  --reid-checkpoint "$WORKSPACE/assets/reid_r50_6e_mot17-4bf6b63d.pth" \
  --aflink-root "$EXP/third_party/StrongSORT" \
  --aflink-checkpoint "$EXP/assets/AFLink_epoch20.pth" \
  --tracker-cache-dir "$EXP/results_raw/e1_direct_full50_v1" \
  --descriptor-cache-dir "$EXP/results_raw/e1_direct_full50_v1" \
  --family-root legacy12 "$DATA/legacy12" \
  --family-root confirmation38 "$DATA/confirmation38" \
  --trackers bytetrack ocsort deepocsort --device cuda:0 \
  --batch-size 128 --aflink-batch-size 512 --skip-pooled-aggregate \
  --output-dir "$EXP/results_raw/e1_direct_full50_v2_equal"
```

Detector-input comparison:

```bash
$PY $EXP/scripts/run_mmot_real_detection_temporal_cached.py \
  --benchmark-script "$EXP/scripts/run_full50_linker_benchmark.py" \
  --workspace "$WORKSPACE" \
  --detection-dir "$EXP/results_raw/e3_detector_full50_v1" \
  --detector-manifest "$EXP/results_raw/e3_detector_full50_v1/detector_checkpoint_manifest.json" \
  --reid-checkpoint "$WORKSPACE/assets/reid_r50_6e_mot17-4bf6b63d.pth" \
  --aflink-root "$EXP/third_party/StrongSORT" \
  --aflink-checkpoint "$EXP/assets/AFLink_epoch20.pth" \
  --tracker-cache-dir "$EXP/results_raw/e3_temporal_full50_v1" \
  --descriptor-cache-dir "$EXP/results_raw/e3_temporal_full50_v1" \
  --family-root legacy12 "$DATA/legacy12" \
  --family-root confirmation38 "$DATA/confirmation38" \
  --trackers bytetrack ocsort deepocsort --device cuda:0 \
  --batch-size 128 --aflink-batch-size 512 --skip-pooled-aggregate \
  --output-dir "$EXP/results_raw/e3_temporal_full50_v2_equal"
```

Derived statistics use 10,000 paired sequence-bootstrap resamples with seed
20260914. The reporting unit is the sequence: HOTA/AssA/IDF1 are
equal-sequence means, whereas IDSW/FP/FN are summed counts.

## Validation and invariants

- Perfect-prediction and globally permuted-ID evaluator tests return
  HOTA/IDF1/MOTA 100 and IDSW 0.
- Stored historical no-refinement metrics reproduce exactly.
- Refined outputs preserve the `(frame, box, confidence, class)` multiset.
- Proposed outputs contain no duplicate identity within one frame.
- Legacy-12 rows embedded in both full-50 runs match the standalone runs at
  absolute tolerance zero across 180 rows each.
- AFLink created duplicate same-frame identities in 9 oracle variants and 4
  detector-input variants. Those sequence-dependent aggregates remain N/A;
  they were not silently repaired.

## Recorded failed runs

- `logs/e0_attempt_1_failure.json`: constructor-only tracker attribute.
- `logs/e1_aflink_checkpoint_download_attempt1_failure.json`: absent output
  directory before download.
- `logs/e1_direct_full50_v1_incomplete.json`: complete caches, impractical
  optional pooled-HOTA aggregation; stopped and rerun with equal-sequence
  reporting.
- `logs/e3_temporal_full50_v1_incomplete.json`: same pooled-aggregation issue
  after complete detector-input caches.
- `logs/e2_error_coverage_attempt1_failure.json`: wrong Python environment
  lacked `lap`.
- `logs/e2_error_coverage_attempt2_manifest_failure.json`: all CSVs complete,
  final source-manifest hash absent; Cartesian product was validated before a
  recovery manifest was written.
- `logs/e2_m3ot_failure_attempt1.json`: TrackEval omitted from `PYTHONPATH`.
- `logs/e4_qualitative_attempt1_failure.json`: incorrect result-method label.
- `logs/e4_paper_assets_attempts_failure.json`: table-source, N/A JSON, and
  stale-interpreter-path corrections before the final table manifest.

No failed attempt contributed a reported metric.

## Blocked and deliberately unperformed work

GIAOTracker is `blocked`: the authors' public repository states that release
of the implementation is not planned, and the learned GIModel plus executable
global-link stage and compatible weights are unavailable. A locally invented
partial approximation was not labeled as official GIAOTracker.

No threshold was selected from MMOT test identities, no new detector was
trained, no M3OT held-out sweep was run, and no adverse sequence was removed.
The descriptive error/coverage sweep does not replace the fixed 0.30 operating
point.
