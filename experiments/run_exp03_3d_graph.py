"""Run Exp03: 3D evidence graph.

TODO:
- Lift 2D detections to 3D.
- Build object evidence graph.
- Evaluate graph-centered evidence quality.
"""

from __future__ import annotations

from _runner_utils import run_dummy


if __name__ == "__main__":
    run_dummy("exp03_3d_graph", "configs/experiments/exp03_3d_graph.yaml")

