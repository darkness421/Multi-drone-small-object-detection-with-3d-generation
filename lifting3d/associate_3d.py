"""Associate lifted 3D hypotheses across UAV views.

TODO:
- Match hypotheses by 3D distance and class compatibility.
- Add timestamp-aware association.
- Produce object-level evidence groups.
"""

from __future__ import annotations


def association_key(object_id: str, coarse_class: str) -> str:
    """Return a stable association key placeholder."""
    return f"{coarse_class}:{object_id}"


if __name__ == "__main__":
    print(association_key("vehicle_001", "vehicle"))

