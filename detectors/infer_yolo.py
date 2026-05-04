"""YOLO inference entrypoint placeholder.

TODO:
- Load trained detector weights.
- Run per-UAV image inference.
- Save bbox, logits, and crop metadata.
"""

from __future__ import annotations


def planned_inference_output() -> list[str]:
    """Return planned inference outputs."""
    return ["bbox_2d", "class_logits", "crop_path", "uav_id", "timestamp"]


if __name__ == "__main__":
    print(planned_inference_output())

