# DOVE-WM CVPR 2027 Preflight

Date: 2026-10-15

## Source Draft

- Title: DOVE-WM: Detection-Oriented Viewpoint World Model for Pixel-Budgeted
  Dense UAV Tiny-Object Perception
- Source PDF SHA-256:
  `6aac5568cac37043665e1b2ee77171e3dee23c6781d3d930a573eee297877943`
- Current evidence status: protocol and method draft. The result tables in the
  supplied PDF are still marked `TBD`, so the draft supports no empirical
  performance claim yet.

## First Executable Gate

The first gate is an asset audit, not model training. Run:

```bash
python scripts/audit_dove_wm_assets.py \
  --capture-root /path/to/isaac_exports \
  --evidence-root /path/to/outputs/evidence \
  --output-dir outputs/experiments/dove_wm_asset_preflight
```

The audit joins candidate camera actions with materialized RGB/depth outputs and
detector evidence. It intentionally does not treat detector predictions as
ground-truth future utility.

## Required Gates

1. Materialize at least two candidate actions per hypothesis with RGB, depth,
   pose, and a stable scene identifier.
2. Define detector-facing outcome targets from audited annotations and a frozen
   detector, including missed-object and false-positive terms.
3. Freeze scene-disjoint train, validation, and test splits before fitting the
   outcome model.
4. Compare DOVE-WM-CF against geometry-only, detector-score, and learned ranking
   baselines under the same action and pixel budget.
5. Start DOVE-WM-Active only after the counterfactual predictor and calibration
   gates pass.

## Current Claim Boundary

Existing MarineCity captures may support a detector-output pipeline pilot. They
do not by themselves establish world-model accuracy, closed-loop benefit,
generalization, or a CVPR-ready benchmark.
