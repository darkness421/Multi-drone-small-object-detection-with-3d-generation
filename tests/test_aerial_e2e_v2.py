from pathlib import Path

import numpy as np
import torch

from aerial_e2e_v2 import B2Scaffold, B2Targets, compute_b2_loss
from aerial_e2e_v2.mmot_smoke import canonical_long_axis
from aerial_e2e_v2.registry import RESULT_COLUMNS, append_result


def test_b2_shapes_and_finite_loss():
    model = B2Scaffold(num_classes=3, embedding_dim=8)
    frames = torch.rand(1, 2, 3, 64, 64)
    outputs = model(frames)
    assert outputs.objectness_logits.shape == (1, 2, 1, 8, 8)
    objectness = torch.zeros_like(outputs.objectness_logits)
    objectness[:, :, :, 2, 3] = 1
    class_ids = torch.full((1, 2, 8, 8), -1, dtype=torch.long)
    class_ids[:, :, 2, 3] = 1
    box_state = torch.zeros((1, 2, 8, 8, 6))
    box_state[:, :, 2, 3] = torch.tensor([0.4, 0.3, 0.1, 0.05, 0.0, 1.0])
    identity_ids = torch.full((1, 2, 8, 8), -1, dtype=torch.long)
    identity_ids[:, :, 2, 3] = 7
    losses = compute_b2_loss(outputs, B2Targets(objectness, class_ids, box_state, identity_ids))
    assert all(torch.isfinite(value) for value in losses.values())


def test_long_axis_angle_is_pi_periodic():
    points = np.asarray([[0, 0], [4, 0], [4, 2], [0, 2]], dtype=np.float32)
    _, _, width, height, theta = canonical_long_axis(points)
    assert width == 4
    assert height == 2
    assert abs(theta) < 1e-6


def test_registry_has_required_columns_and_appends(tmp_path: Path):
    required = {"experiment_id", "OBB_mAP", "HOTA", "config_path", "git_commit"}
    assert required.issubset(RESULT_COLUMNS)
    destination = tmp_path / "results.csv"
    append_result(destination, {"experiment_id": "smoke", "status": "pass"})
    text = destination.read_text(encoding="utf-8")
    assert "experiment_id" in text
    assert "smoke" in text
