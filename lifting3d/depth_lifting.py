"""Depth-based 2D-to-3D object lifting prototype."""

from __future__ import annotations

from typing import Any

import numpy as np


def estimate_object_center_3d(
    bbox_2d: tuple[int, int, int, int],
    depth_map: np.ndarray,
    camera_intrinsics: np.ndarray,
    camera_extrinsics: np.ndarray
) -> dict[str, Any]:
    """Estimate a world-space object center from bbox, depth, intrinsics, and extrinsics."""
    x1, y1, x2, y2 = bbox_2d
    crop = depth_map[y1:y2, x1:x2]
    valid_depth = crop[np.isfinite(crop) & (crop > 0)]
    if valid_depth.size == 0:
        raise ValueError("bbox crop has no valid depth values")

    median_depth = float(np.median(valid_depth))
    depth_std = float(np.std(valid_depth))
    center_u = (x1 + x2) / 2.0
    center_v = (y1 + y2) / 2.0

    fx = float(camera_intrinsics[0, 0])
    fy = float(camera_intrinsics[1, 1])
    cx = float(camera_intrinsics[0, 2])
    cy = float(camera_intrinsics[1, 2])

    x_cam = (center_u - cx) * median_depth / fx
    y_cam = (center_v - cy) * median_depth / fy
    z_cam = median_depth
    point_cam = np.array([x_cam, y_cam, z_cam, 1.0], dtype=float)
    point_world = camera_extrinsics @ point_cam

    uncertainty = depth_std / max(median_depth, 1e-6)
    return {
        "center_3d": point_world[:3].tolist(),
        "depth_statistics": {
            "median": median_depth,
            "std": depth_std,
            "num_valid": int(valid_depth.size)
        },
        "uncertainty": float(uncertainty)
    }


def _synthetic_test() -> None:
    """Run a small synthetic test."""
    depth = np.full((20, 20), 10.0, dtype=float)
    intrinsics = np.array(
        [
            [10.0, 0.0, 10.0],
            [0.0, 10.0, 10.0],
            [0.0, 0.0, 1.0]
        ],
        dtype=float
    )
    extrinsics = np.eye(4, dtype=float)
    result = estimate_object_center_3d((8, 8, 12, 12), depth, intrinsics, extrinsics)
    assert np.allclose(result["center_3d"], [0.0, 0.0, 10.0])
    assert result["depth_statistics"]["num_valid"] == 16
    print("synthetic depth lifting test passed")


if __name__ == "__main__":
    _synthetic_test()

