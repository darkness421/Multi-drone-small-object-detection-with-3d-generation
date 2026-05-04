"""Isaac Replicator writer placeholder.

TODO:
- Convert Isaac annotations to CoM3D-MarineCity JSON.
- Save per-scene evidence JSON files.
- Export COCO-compatible 2D detection labels.
"""

from __future__ import annotations


def writer_name() -> str:
    """Return the planned writer name."""
    return "CoM3DMarineCityWriter"


if __name__ == "__main__":
    print(writer_name())

