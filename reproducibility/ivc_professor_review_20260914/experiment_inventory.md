# Experiment inventory

## Execution status

| Item | Status | Inputs | Outputs |
| --- | --- | --- | --- |
| P0 source/result linkage | Partial | Current source and frozen CSVs available; named review PDF absent | Manifest, main comparison, consistency report |
| P1 AFLink stage audit | Complete | Frozen official scores/assignments, source commit, checkpoint | Stage CSV, minimal case, native/adapter metrics |
| P2 reciprocal invariant | Complete | All cached MMOT class instances | Property tests and invariant report |
| P3 ranking/solver control | Complete | Frozen tracklets/descriptors; no network rerun | 3,300 sequence rows, 33,466 edge decisions, risk/runtime CSVs |
| P4 M3OT failure diagnostic | Complete | Frozen development/held-out inputs | 80 sequence-method rows and 118 casebook rows |
| P5 paired linker CI | Complete | MMOT per-sequence results | Paired 10,000-resample intervals |
| MMOT source-flight block CI | Not executable | Official release exposes no per-sequence source-flight grouping | No inferred grouping or block CI |
| New detector/tracker/training run | Excluded | Not required for the cache-controlled review | Not run |

## Frozen conditions

- MMOT: all 50 released test sequences, 5,466 frames, oracle AABB and shared
  official-detector conditions, ByteTrack/OC-SORT/Deep OC-SORT.
- Fixed graph gates: gap <= 30 released frames, endpoint distance <= 55 native
  pixels, cosine distance <= 0.30. No threshold was selected from test results.
- Pseudo-RGB for appearance: zero-based bands `[4,2,1]` in RGB order.
- Coverage denominator: source tracklets having at least one strictly later,
  frame-disjoint successor within 30 frames before geometry/appearance gates.
- Ground truth: tracking metrics and post-hoc MMOT edge labels only. M3OT is a
  separate historical oracle-box diagnostic whose crop admission uses IoU >= 0.9
  to oracle GT, as recorded in its manifest.

## Commands

MMOT audit:

```text
/tmp/com3d_professor_review_20260914/scripts/run_cached_solver_audit.py --benchmark-script /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/scripts/run_full50_linker_benchmark.py --workspace /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal --oracle-cache-dir /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e1_direct_full50_v1 --detector-cache-dir /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e3_temporal_full50_v1 --oracle-accepted-links /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e1_direct_full50_v2_equal/results/accepted_links.csv --detector-accepted-links /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e3_temporal_full50_v2_equal/results/accepted_links.csv --family-root legacy12 /mnt/ssd2/meme_comparison/data_cache/accv2026_rebuttal_real_uav/raw/MMOT/extracted/test_meta_review_split/legacy12 --family-root confirmation38 /mnt/ssd2/meme_comparison/data_cache/accv2026_rebuttal_real_uav/raw/MMOT/extracted/test_meta_review_split/confirmation38 --output-dir /tmp/com3d_professor_review_20260914/results_raw/mmot_cached_solver_audit_v1 --repeats 5
```

M3OT diagnostic:

```text
/tmp/com3d_professor_review_20260914/scripts/run_m3ot_linker_diagnostic.py --workspace /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal --val-manifest /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/val_development_manifest.json --val-results /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/val_policy_results_v2.json --test-manifest /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/test_final_manifest.json --test-results /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/test_locked_results.json --checkpoint /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal/assets/reid_r50_6e_mot17-4bf6b63d.pth --output-dir /tmp/com3d_professor_review_20260914/results_raw/m3ot_linker_diagnostic_v2 --device cpu --threads 8
```

Report generation:

```text
python /tmp/com3d_professor_review_20260914/scripts/build_review_reports.py [paths recorded in build_and_results_manifest.json]
```
