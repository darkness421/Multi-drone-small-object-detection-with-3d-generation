"""Spawn UAV camera rigs in Isaac Sim.

TODO:
- Create UAV prims.
- Attach RGB/depth cameras.
- Register synchronized timestamps.
"""

from __future__ import annotations


def planned_uav_ids(count: int) -> list[str]:
    """Return deterministic UAV ids."""
    return [f"UAV_{index + 1}" for index in range(count)]


if __name__ == "__main__":
    print(planned_uav_ids(3))

