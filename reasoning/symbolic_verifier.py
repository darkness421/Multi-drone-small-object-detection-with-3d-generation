"""Symbolic checks for geometry and evidence consistency.

TODO:
- Verify 3D consistency between views.
- Check impossible class/context combinations.
- Validate recommended next view constraints.
"""

from __future__ import annotations


def is_uncertain_enough(uncertainty: float, threshold: float = 0.55) -> bool:
    """Return whether uncertainty should trigger re-observation."""
    return uncertainty >= threshold


if __name__ == "__main__":
    print(is_uncertain_enough(0.6))

