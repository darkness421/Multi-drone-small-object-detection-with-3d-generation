"""Run Exp01: Single-UAV baseline.

TODO:
- Load detector checkpoint.
- Run single-UAV inference/evaluation.
- Save comparable metrics.
"""

from __future__ import annotations

from _runner_utils import run_dummy


if __name__ == "__main__":
    run_dummy("exp01_single_uav", "configs/experiments/exp01_single_uav.yaml")

