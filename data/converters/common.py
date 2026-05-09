"""Common COCO conversion helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class ConvertedSample:
    image_path: str
    bbox: list[float]
    category_id: int
    category_name: str
    object_id: str | None = None
    camera_pose: list[float] | None = None
    camera_intrinsic: list[list[float]] | None = None
    camera_extrinsic: list[list[float]] | None = None
    depth_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def coco_template(categories: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "info": {"description": "CoM3D-ACE converted dataset"},
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": list(categories or []),
    }


def write_json(payload: dict[str, Any] | list[Any], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def bbox_area(bbox: list[float]) -> float:
    return max(0.0, float(bbox[2])) * max(0.0, float(bbox[3]))


def image_size(path: str | Path) -> tuple[int | None, int | None]:
    """Return image width/height when OpenCV or PIL is available."""

    path = Path(path)
    try:
        import cv2

        image = cv2.imread(str(path))
        if image is not None:
            height, width = image.shape[:2]
            return int(width), int(height)
    except Exception:
        pass
    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return None, None
