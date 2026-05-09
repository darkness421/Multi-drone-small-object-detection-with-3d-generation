"""Crop extraction utilities for object evidence patches."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np


def clamp_bbox_xywh(bbox: Sequence[float], width: int, height: int) -> tuple[int, int, int, int]:
    x, y, w, h = [float(v) for v in bbox]
    x0 = max(0, min(width, int(round(x))))
    y0 = max(0, min(height, int(round(y))))
    x1 = max(0, min(width, int(round(x + w))))
    y1 = max(0, min(height, int(round(y + h))))
    return x0, y0, max(x0, x1), max(y0, y1)


def extract_crop(image_path: str | Path, bbox_2d: Sequence[float], out_path: str | Path | None = None) -> np.ndarray:
    """Extract a crop from image+bbox, optionally saving it to disk."""

    image_path = Path(image_path)
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python is required for crop extraction") from exc

    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    height, width = image.shape[:2]
    x0, y0, x1, y1 = clamp_bbox_xywh(bbox_2d, width, height)
    crop = image[y0:y1, x0:x1].copy()
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), crop)
    return crop

