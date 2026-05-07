"""Tests for depth-based 2D-to-3D lifting."""

from __future__ import annotations

import unittest

import numpy as np

from lifting3d.depth_lifting import estimate_object_center_3d


class DepthLiftingTest(unittest.TestCase):
    """Validate synthetic depth lifting."""

    def test_center_lifts_to_expected_world_point(self) -> None:
        depth = np.full((20, 20), 10.0, dtype=float)
        intrinsics = np.array(
            [
                [10.0, 0.0, 10.0],
                [0.0, 10.0, 10.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        extrinsics = np.eye(4, dtype=float)
        result = estimate_object_center_3d((8, 8, 12, 12), depth, intrinsics, extrinsics)
        self.assertEqual(result["depth_statistics"]["num_valid"], 16)
        self.assertTrue(np.allclose(result["center_3d"], [0.0, 0.0, 10.0]))


if __name__ == "__main__":
    unittest.main()

