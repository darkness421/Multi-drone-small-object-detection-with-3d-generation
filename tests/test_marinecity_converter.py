"""Tests for CoM3D-MarineCity annotation conversion."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from datasets.converters.marinecity_to_coco import convert, validate_annotation


FIXTURE = Path("datasets/converters/dummy_marinecity_input.json")


class MarineCityConverterTest(unittest.TestCase):
    """Validate MarineCity converter behavior."""

    def test_dummy_annotation_is_valid(self) -> None:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        validate_annotation(data)

    def test_convert_outputs_coco_and_evidence(self) -> None:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        coco, evidence = convert(data)
        self.assertEqual(len(coco["images"]), 2)
        self.assertEqual(len(coco["annotations"]), 2)
        self.assertEqual(coco["annotations"][0]["category_id"], 4)
        self.assertEqual(evidence["ambiguity_type"], "van_vs_ambulance")


if __name__ == "__main__":
    unittest.main()

