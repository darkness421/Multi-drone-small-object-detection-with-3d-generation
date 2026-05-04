"""Convert 2D bbox measurements into a camera frustum placeholder.

TODO:
- Compute frustum rays for bbox corners.
- Intersect rays with depth or ground plane.
- Export frustum evidence to object tokens.
"""

from __future__ import annotations


def bbox_center(bbox_2d: tuple[float, float, float, float]) -> tuple[float, float]:
    """Return bbox center from x1, y1, x2, y2."""
    x1, y1, x2, y2 = bbox_2d
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


if __name__ == "__main__":
    print(bbox_center((0, 0, 10, 20)))

