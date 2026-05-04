"""Object token representation for 3D evidence graph input.

TODO:
- Define feature fields from crops, geometry, logits, and context.
- Add serialization helpers.
- Connect tokens to graph nodes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectToken:
    """Minimal object token placeholder."""
    object_id: str
    coarse_class: str
    center_3d: tuple[float, float, float]
    uncertainty: float


if __name__ == "__main__":
    print(ObjectToken("vehicle_001", "vehicle", (0.0, 0.0, 0.0), 0.1))

