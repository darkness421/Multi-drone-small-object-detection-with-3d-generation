"""Tests for the dummy end-to-end evidence pipeline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipelines.run_dummy_evidence_pipeline import run_pipeline


class DummyEvidencePipelineTest(unittest.TestCase):
    """Validate pipeline output files and graph structure."""

    def test_pipeline_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outputs = run_pipeline(
                Path("datasets/converters/dummy_marinecity_input.json"),
                Path(tmpdir),
            )
            for path in outputs.values():
                self.assertTrue(Path(path).exists())

            graph = json.loads(Path(outputs["evidence_graph"]).read_text(encoding="utf-8"))
            self.assertEqual(graph["graph_type"], "CoM3D object evidence graph")
            self.assertEqual(graph["nodes"][0]["object_id"], "vehicle_021")
            self.assertEqual(graph["nodes"][0]["ambiguity_type"], "van_vs_ambulance")


if __name__ == "__main__":
    unittest.main()

