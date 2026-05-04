"""Run Exp02: 2D fusion baseline.

TODO:
- Fuse per-view 2D detections.
- Compare with single-UAV baseline.
- Save fusion metrics.
"""

from __future__ import annotations

from _runner_utils import run_dummy


if __name__ == "__main__":
    run_dummy("exp02_2d_fusion", "configs/experiments/exp02_2d_fusion.yaml")

