from __future__ import annotations

import copy

import numpy as np

from regr.core import resolve_method, select_edges
from regr.graph import build_candidates, refine


def sample_predictions():
    return {
        1: [{"id": 1, "x": 0.0, "y": 0.0, "w": 2.0, "h": 2.0, "class_id": 0}],
        2: [{"id": 1, "x": 1.0, "y": 0.0, "w": 2.0, "h": 2.0, "class_id": 0}],
        4: [{"id": 2, "x": 3.0, "y": 0.0, "w": 2.0, "h": 2.0, "class_id": 0}],
    }


def sample_descriptors():
    return {1: np.asarray([1.0, 0.0]), 2: np.asarray([0.99995, 0.01])}


def test_public_names_resolve_to_frozen_artifact_methods():
    assert resolve_method("regr-v1") == "regr_v1"
    assert resolve_method("regr-t") == "regr_temporal_risk_05"
    assert resolve_method("regr-tg") == "regr_t_reliable_motion_min5"


def test_refinement_changes_only_identity_labels():
    predictions = sample_predictions()
    original = copy.deepcopy(predictions)
    output, audit = refine(predictions, sample_descriptors(), "regr-tg")
    assert predictions == original
    assert audit["observation_multiset_preserved"] is True
    assert audit["duplicate_frame_identity_count"] == 0
    assert output[4][0]["id"] == 1
    assert output[4][0]["x"] == original[4][0]["x"]


def test_sparse_reliable_motion_guard_rejects_inconsistent_edge():
    predictions = {
        1: [{"id": 1, "x": 0.0, "y": 0.0, "w": 2.0, "h": 2.0, "class_id": 0}],
        2: [{"id": 1, "x": 10.0, "y": 0.0, "w": 2.0, "h": 2.0, "class_id": 0}],
        4: [{"id": 2, "x": 0.0, "y": 0.0, "w": 2.0, "h": 2.0, "class_id": 0}],
    }
    descriptors = {1: np.asarray([1.0, 0.0]), 2: np.asarray([1.0, 0.0])}
    candidates = build_candidates(predictions, descriptors)
    proposed, _, details = select_edges("regr-tg", predictions, candidates)
    assert proposed == []
    assert details["motion_coverage"] == 1.0
    assert details["abstained"] is True


def test_candidate_builder_never_links_different_classes():
    predictions = sample_predictions()
    predictions[4][0]["class_id"] = 1
    assert build_candidates(predictions, sample_descriptors()) == []
