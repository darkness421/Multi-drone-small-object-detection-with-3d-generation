# Experiment Inventory (2026-09-18)

This inventory separates completed cache evaluations from unavailable
data/resource-dependent evaluations. All completed runs write to new result
directories and leave prior paper artifacts unchanged.

| Item | Status | Frozen input | Result or blocker |
| --- | --- | --- | --- |
| A/B development search | Complete | MMOT dev6 and M3OT scene 08 | `reproducibility/protocols/regr_final_selection.json` |
| Final alias equivalence | Complete | Same development caches | Exact metric difference `0.0` for MMOT and M3OT |
| MMOT oracle confirmation | Complete | 50 sequences, 3 trackers | `reproducibility/results/final_20260918/mmot_oracle/metrics_per_sequence.csv` |
| MMOT detector confirmation | Complete | Shared 50-sequence detector cache, 3 trackers | `reproducibility/results/final_20260918/mmot_detector/metrics_per_sequence.csv` |
| M3OT oracle confirmation/retest | Complete | 7 scene groups, 28 streams, 2 trackers | `reproducibility/results/final_20260918/m3ot_oracle/metrics_per_scene_group.csv` |
| Paired bootstrap and link audit | Complete | Above immutable result CSVs | `reproducibility/verified_tables/final_20260918/` |
| Graph-stage runtime | Complete | MMOT oracle cache, 789 class instances | Warm-up 1, timed repeats 3, CPU `perf_counter_ns` |
| M3OT detector-input evaluation | Resource/data wait | No common detector-tracklet cache | GPU unavailable; `nvidia-smi` could not communicate with the driver. A YOLO checkpoint exists, but its M3OT class adapter is unverified. No result was generated. |
| VisDrone-MOT external confirmation | Data wait | Local directory empty | Official test-dev download is not present and no common tracker/descriptor cache exists. No result was generated. |
| Appearance improvement C | Not triggered | Development failure audit | Dominant MMOT losses were fixed-gate removal, competition, and component/order effects; available evidence did not justify changing descriptors. |

## Commands

The public experiment entrypoints are:

```bash
python scripts/run_mmot_confidence_search.py --help
python scripts/run_m3ot_confidence_search.py --help
python scripts/select_regr_ab.py --help
python scripts/summarize_final_results.py --help
python scripts/analyze_link_conditions.py --help
python scripts/profile_regr_final.py --help
```

Dataset and cache paths are CLI arguments and are intentionally not hard-coded
in the release. The immutable run manifests record the exact local commands and
input hashes used for the verified results.
