"""Tests for dummy experiment runner utilities."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from detectors.roc_auc import class_names, label_path_for_image, read_present_classes
from experiments._runner_utils import save_dummy_metrics
from evaluation.seed_statistics import compare_seed_csvs


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

    def test_compare_seed_csvs_pairs_matching_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baseline = root / "baseline.csv"
            candidate = root / "candidate.csv"
            baseline.write_text("seed,AP\n0,0.1\n1,0.2\n2,0.3\n", encoding="utf-8")
            candidate.write_text("seed,AP\n0,0.2\n1,0.31\n2,0.39\n", encoding="utf-8")
            summary = compare_seed_csvs(baseline, candidate, "AP")
            self.assertEqual(summary["paired_seeds"], [0, 1, 2])
            self.assertAlmostEqual(summary["delta_candidate_minus_baseline"]["mean"], 0.1)

    def test_roc_auc_helpers_follow_yolo_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            image_path = root / "images" / "val" / "frame001.jpg"
            label_path = root / "labels" / "val" / "frame001.txt"
            label_path.parent.mkdir(parents=True)
            label_path.write_text("2 0.5 0.5 0.1 0.1\n0 0.5 0.5 0.1 0.1\n", encoding="utf-8")

            self.assertEqual(class_names({"names": {"10": "ten", "2": "two"}}), ["two", "ten"])
            self.assertEqual(label_path_for_image(image_path), label_path)
            self.assertEqual(read_present_classes(label_path, 4), [1, 0, 1, 0])


if __name__ == "__main__":
    unittest.main()
