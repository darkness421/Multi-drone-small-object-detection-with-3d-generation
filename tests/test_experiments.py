"""Tests for dummy experiment runner utilities."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from experiments._runner_utils import save_dummy_metrics


class ExperimentRunnerTest(unittest.TestCase):
    """Validate dummy metrics structure."""

    def test_save_dummy_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = save_dummy_metrics(
                "exp_test",
                Path("configs/experiments/exp01_single_uav.yaml"),
                Path(tmpdir),
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["experiment_id"], "exp_test")
            self.assertIn("mAP", payload["metrics"])
            self.assertIn("evidence_completion_success", payload["metrics"])


if __name__ == "__main__":
    unittest.main()

