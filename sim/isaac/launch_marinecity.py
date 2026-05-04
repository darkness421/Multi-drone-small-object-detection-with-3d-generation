"""Launch the Marine City scene in Isaac Sim.

TODO:
- Locate Isaac Sim executable.
- Load Cesium georeferenced Marine City tiles.
- Attach simulation extensions needed for sensor capture.
"""

from __future__ import annotations


def plan_launch() -> dict[str, str]:
    """Return the planned launch steps without starting Isaac Sim."""
    return {
        "scene": "CoM3D-MarineCity",
        "engine": "NVIDIA Isaac Sim",
        "status": "placeholder",
    }


if __name__ == "__main__":
    print(plan_launch())

