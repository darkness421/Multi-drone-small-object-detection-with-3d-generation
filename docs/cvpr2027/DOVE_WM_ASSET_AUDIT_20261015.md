# DOVE-WM Asset Audit Result

Date: 2026-10-15

## Audited Inputs

- Capture root: `/home/oem/UAV/uav_marinecity/outputs/isaac_exports`
- Detector evidence root:
  `/home/oem/projects/multi-uav-marine-city/outputs/evidence`
- Audit command:

```bash
python scripts/audit_dove_wm_assets.py \
  --capture-root /home/oem/UAV/uav_marinecity/outputs/isaac_exports \
  --evidence-root /home/oem/projects/multi-uav-marine-city/outputs/evidence \
  --output-dir docs/cvpr2027/evidence/dove_wm_asset_preflight_20261015
```

## Result

| Item | Count |
| --- | ---: |
| Sessions with `capture_plan.json` | 30 |
| Planned candidate actions | 117 |
| Actions with materialized RGB | 54 |
| Actions with materialized depth | 54 |
| Hypothesis groups | 21 |
| Groups with at least two candidate actions | 12 |
| Complete multi-action RGB/depth groups | 12 |
| Complete groups with detector evidence for every action | 9 |
| Groups with ground-truth future-outcome labels | 0 |

The existing captures are sufficient to exercise counterfactual tuple loading,
geometry transport, detector-output summarization, and listwise-ranking code on
a small pilot. They are not sufficient to train or validate the proposed world
model because no audited ground-truth future-outcome utility is attached.

Detector evidence also requires care: some complete action groups contain no
prediction matching the requested target class, while other groups have target
class support for only a subset of actions. This can represent a useful miss in
a later annotated benchmark, but without ground truth it cannot be interpreted
as action quality.

## Decision

- Proceed now: counterfactual data loader and detector-output pipeline pilot.
- Blocked pending labels: supervised residual outcome decoder and calibrated
  ranking accuracy.
- Blocked pending scale and split: CVPR benchmark, generalization, and
  closed-loop active-view claims.

The detailed rows are in
`docs/cvpr2027/evidence/dove_wm_asset_preflight_20261015/`.
