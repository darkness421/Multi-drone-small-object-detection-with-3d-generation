"""Run Exp04: ambiguity-centric re-observation.

TODO:
- Diagnose ambiguous object nodes.
- Request recommended next views.
- Evaluate evidence completion success.
"""

from __future__ import annotations

from _runner_utils import run_dummy


if __name__ == "__main__":
    run_dummy("exp04_reobservation", "configs/experiments/exp04_ace_full.yaml")

