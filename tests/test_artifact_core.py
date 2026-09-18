from __future__ import annotations

import numpy as np

from regr import _artifact_core as core


def edge(source, destination, appearance, geometry, gap):
    return {
        "earlier": source,
        "later": destination,
        "cosine_distance": appearance,
        "endpoint_center_distance_pixels": geometry,
        "controlled_cost": (geometry / 55.0 + appearance / 0.30 + gap / 30.0) / 3.0,
        "gap": gap,
    }


def test_motion_ratio_guard_rejects_inconsistent_extrapolation():
    predictions = {
        1: [{"id": 1, "x": 0.0, "y": 0.0, "w": 2.0, "h": 2.0}],
        2: [{"id": 1, "x": 10.0, "y": 0.0, "w": 2.0, "h": 2.0}],
        4: [{"id": 2, "x": 0.0, "y": 0.0, "w": 2.0, "h": 2.0}],
    }
    proposed, _, details = core.select(
        "regr_t_motion_ratio_100",
        predictions,
        [edge(1, 2, 0.05, 10.0, 2)],
    )
    assert proposed == []
    assert details["motion_ratio_max"] == 1.0


def test_reliable_motion_guard_falls_back_without_motion():
    predictions = {
        1: [{"id": 1, "x": 0.0, "y": 0.0, "w": 2.0, "h": 2.0}],
        2: [{"id": 2, "x": 5.0, "y": 0.0, "w": 2.0, "h": 2.0}],
    }
    proposed, _, details = core.select(
        "regr_t_reliable_motion_min5",
        predictions,
        [edge(1, 2, 0.05, 5.0, 1)],
    )
    assert [core.edge_id(item) for item in proposed] == [(1, 2)]
    assert np.isclose(details["motion_coverage"], 0.0)
    assert details["abstained"] is False
