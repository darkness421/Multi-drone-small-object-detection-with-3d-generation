"""Capture RGB, depth, segmentation, bbox, and pose outputs.

TODO:
- Configure Isaac sensor capture.
- Save synchronized per-UAV frames.
- Write camera pose JSON files.
"""

from __future__ import annotations


def planned_modalities() -> list[str]:
    """Return sensor modalities planned for CoM3D-MarineCity."""
    return ["rgb", "depth", "segmentation", "bbox", "camera_pose"]


if __name__ == "__main__":
    print(planned_modalities())

