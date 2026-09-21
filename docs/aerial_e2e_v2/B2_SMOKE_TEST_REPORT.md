# B2 Minimal Scaffold Smoke Test

## Purpose

This run validates the minimum shared-encoder training path and experiment
registry. It is not a detection or tracking benchmark and is not evidence for
the proposed V2 hypotheses.

## Command

```bash
/home/oem/anaconda3/bin/python tools/run_aerial_e2e_b2_smoke.py \
  --config configs/e2e/b2_minimal_smoke.yaml \
  --output-dir \
  experiments/runs/b2_minimal_mmot_two_frame_smoke_seed42/attempt_02_success
```

## Input and result

- Dataset: MMOT official test sequence `data28-1`.
- Frames: `000001.npy`, `000002.npy`.
- Use: pipeline smoke only; no model or threshold selection.
- Input tensor: `[1, 2, 3, 256, 256]`.
- Output grid: `32 x 32`.
- Positive grid cells: 40.
- Seed: 42.
- Parameters: 66,279.
- Loss before step: 3.7538535595.
- Loss after step: 3.4364159107.
- Device: CPU; CUDA unavailable.
- Status: PASS.

The recorded CPU timing includes forward, backward, optimizer, and validation
forward work. It must not be reported as end-to-end inference FPS.

## Preserved attempts

- Attempt 00 failed at import because direct script execution did not add the
  repository root to `sys.path`.
- Attempt 01 completed model optimization and wrote local metrics, then failed
  while converting a relative config path for the global registry.
- Attempt 02 passed model execution and both global registry writes.

No failed output was deleted. The manifests and partial outputs are retained
under `experiments/runs/b2_minimal_mmot_two_frame_smoke_seed42/`.

## Validation

- Full repository tests: 38 passed.
- Live monitor observed the transition from an empty registry to one
  `smoke_pass` row.
- `nvidia-smi` could not communicate with the NVIDIA driver, so no GPU result
  was produced or inferred.

## Remaining gate

B2 still requires a locked training split, full training, detection evaluation,
tracking evaluation, per-sequence metrics, and efficiency measurement on a
working GPU before it can be compared with B0 or B1.
