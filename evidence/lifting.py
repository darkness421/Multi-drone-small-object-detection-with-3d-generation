"""2D-to-3D lifting utilities for bbox/depth/camera geometry."""

from __future__ import annotations

from typing import Sequence

import numpy as np


def lift_bbox_center_to_world(
    bbox_2d: Sequence[float],
    depth_map: np.ndarray | None,
    camera_intrinsic: Sequence[Sequence[float]],
    camera_extrinsic: Sequence[Sequence[float]],
    *,
    depth_value: float | None = None,
) -> dict[str, object]:
    """Back-project the bbox center into world coordinates."""

    if len(bbox_2d) != 4:
        raise ValueError("bbox_2d must be [x, y, width, height]")
    x, y, w, h = [float(v) for v in bbox_2d]
    u = x + w / 2.0
    v = y + h / 2.0

    if depth_value is None:
        if depth_map is None:
            raise ValueError("Either depth_map or depth_value is required")
        x0 = max(0, int(np.floor(x)))
        y0 = max(0, int(np.floor(y)))
        x1 = min(depth_map.shape[1], int(np.ceil(x + w)))
        y1 = min(depth_map.shape[0], int(np.ceil(y + h)))
        patch = depth_map[y0:y1, x0:x1]
        valid = patch[np.isfinite(patch) & (patch > 0)]
        if valid.size == 0:
            raise ValueError("No valid depth value inside bbox")
        depth = float(np.median(valid))
        depth_std = float(np.std(valid))
    else:
        depth = float(depth_value)
        depth_std = 0.0

    k = np.asarray(camera_intrinsic, dtype=float)
    t_cw = np.asarray(camera_extrinsic, dtype=float)
    if k.shape != (3, 3):
        raise ValueError("camera_intrinsic must be 3x3")
    if t_cw.shape != (4, 4):
        raise ValueError("camera_extrinsic must be 4x4 camera-to-world transform")

    ray_camera = np.linalg.inv(k) @ np.array([u, v, 1.0], dtype=float)
    point_camera = ray_camera * depth
    point_world = t_cw @ np.array([point_camera[0], point_camera[1], point_camera[2], 1.0])
    uncertainty = float(depth_std + 1.0 / max(w * h, 1.0))

    return {
        "center_3d": point_world[:3].tolist(),
        "center_pixel": [u, v],
        "depth": depth,
        "depth_statistics": {"median": depth, "std": depth_std},
        "uncertainty": uncertainty,
    }


def lift_bbox_corners_to_world(
    bbox_2d: Sequence[float],
    depth: float,
    camera_intrinsic: Sequence[Sequence[float]],
    camera_extrinsic: Sequence[Sequence[float]],
) -> list[list[float]]:
    x, y, w, h = [float(v) for v in bbox_2d]
    corners = ([x, y], [x + w, y], [x + w, y + h], [x, y + h])
    return [
        lift_bbox_center_to_world([u, v, 0.0, 0.0], None, camera_intrinsic, camera_extrinsic, depth_value=depth)[
            "center_3d"
        ]
        for u, v in corners
    ]

