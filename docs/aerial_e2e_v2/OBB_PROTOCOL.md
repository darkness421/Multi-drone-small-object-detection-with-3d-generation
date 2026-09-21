# OBB Protocol

## Stored annotation

MMOT per-frame records contain:

`frame,id,x0,y0,x1,y1,x2,y2,x3,y3,confidence,class,visibility`

The eight coordinates are pixel-space quadrilateral corners. The official YOLO
converter preserves the corner order and normalizes each coordinate by image
width/height.

## Canonical state used by B2

B2 converts each quadrilateral to:

`cx, cy, long_side, short_side, sin(2 theta), cos(2 theta)`

`theta` is the long-axis direction canonicalized to `[-pi/2, pi/2)`. The
double-angle representation respects the 180-degree symmetry of a rectangle.
This is deterministic state, not DOS uncertainty.

## Official detector convention

The frozen MMOT detector is an Ultralytics OBB model. Its cached output retains
the four polygon corners. The historical tracking adapter computes the AABB
min/max envelope before BoxMOT. Consequently, the existing B1 tracking metrics
do not demonstrate OBB-aware association.

## Validation requirements

- Polygon area must be positive and finite.
- Corner coordinates must stay in the source image coordinate system.
- Conversion round-trip is checked through polygon IoU, not raw angle equality.
- Orientation error uses the minimum long-axis error modulo pi.
- Near-square boxes require a declared aspect-ratio exclusion or separate
  reporting because their long-axis orientation is unstable.
- OBB mAP must use polygon/rotated IoU. AABB IoU is not a substitute.

## Current gap

Fresh OBB detector validation cannot be rerun because the official detector
checkpoint and full prediction cache are absent. The existing checkpoint
manifest records SHA-256
`6d9f66ed17eb1e29a452d43f223a55efe83959f480c65e596fd288bc966f2b15`;
that file is not currently present.
