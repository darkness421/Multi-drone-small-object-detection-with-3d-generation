# Aerial E2E V2 Baseline Audit

Audit date: 2026-09-21

This audit separates the new end-to-end aerial detection/tracking study from
REGR. REGR is not imported, merged, or used as a training target here.

## Authoritative snapshots

| Item | Verified source | State |
| --- | --- | --- |
| Development repository | `/home/oem/projects/multi-uav-marine-city`, commit `2a033849f1746604db774c95537f0400b5e513a2` | Dirty user worktree; read only |
| Isolated research branch | `/tmp/aerial_e2e_v2_20260921`, branch `research/aerial-e2e-v2-audit-20260921` | New work only |
| BoxMOT | `/mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal/third_party/boxmot_official`, commit `6edfa8ad7dc2f24b19a41c0058fc53d8d2c4e8ec` | Available |
| TrackEval | same workspace, commit `12c8791b303e0a0b50f753af204249e622d0281a` | Available |
| MMOT official source | same workspace, commit `4d365c9eab4cefda058f46cdd821ea06b366bfe4` | Available |

## Located components

1. Previous detector: SAFR-YOLO, implementation label
   `P2P4-SelfAttnFR`. Architecture is defined by
   `configs/detector/yolo11l-p2p4-balanced-v1.yaml` plus
   `lite_self_attention_neck` and `tiny_frelu_neck` patches in
   `detectors/proposed/modules.py`.
2. ByteTrack, OC-SORT, and Deep OC-SORT: pinned BoxMOT implementations.
3. ReID: BaseReID ResNet-50 checkpoint, SHA-256
   `4bf6b63d49235973033c47f77bc9b94a54bdd222bd3f484b4e484aba580254c1`.
4. AABB annotations: VisDrone detection labels and AABB envelope adapters for
   MMOT/M3OT.
5. OBB annotations: MMOT quadrilateral labels and official OBB detector output.
6. Dataset loaders: VisDrone converters under `data/converters/`; MMOT loaders
   and frozen temporal adapters under the reproducibility package.
7. Evaluators: Ultralytics detection metrics and pinned TrackEval HOTA,
   Identity, and CLEAR metrics.
8. Caches: MMOT 50-sequence final tracking metrics are available; full raw
   detector cache and the official OBB checkpoint are not currently available.
9. Visualization: detector, Grad-CAM, evidence graph, and tracking utilities
   exist, but no unified B0/B1/B2 visualizer existed at audit time.

## Baseline status

| ID | Definition | Status | Evidence |
| --- | --- | --- | --- |
| B0 | SAFR-YOLO + standard Deep OC-SORT | Not previously evaluated end to end | Detector checkpoint and detector metrics exist; compatible MOT result/cache does not |
| B1 | Official MMOT YOLO11L-3ch OBB detector + Deep OC-SORT | Cache-replay reproduced | 50 official-test sequences; metrics in `BASELINE_RESULTS.md` |
| B2 | Minimal shared encoder with deterministic OBB and identity heads | Scaffold implemented; scientific training not run | Real MMOT two-frame infrastructure smoke only |

The B0 detector checkpoint is available at the local asset location with
SHA-256 `57b43dc93c7d826ed379b77a1daa1bb398bca0cdf4b40c6c8df1bbaf2c7dd29e`.
Its class vocabulary is VisDrone-specific and must be mapped explicitly before
an MMOT/M3OT tracking claim is permitted.

## Runtime gate

`nvidia-smi` exits 9 and PyTorch `2.11.0+cu128` reports zero CUDA devices.
Large-scale training and fresh detector inference are therefore blocked. Cache
evaluation, CPU unit tests, and the B2 infrastructure smoke remain executable.

## Claim boundary

The existing SAFR detector result and B1 tracker result come from different
detector/data protocols. They must not be combined into a synthetic end-to-end
number. B2 smoke values are implementation checks, not accuracy results.
