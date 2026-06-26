"""Tests for AeroGraph web-response normalization."""

from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.aerograph_response_validation import validate_response_row
from scripts.normalize_aerograph_web_responses import extract_rows
from scripts.normalize_aerograph_web_responses import normalize_row
from scripts.normalize_aerograph_web_responses import run


def wrapped_response(index: int, object_id: str, predicted_class: str = "car") -> dict[str, object]:
    return {
        "index": index,
        "scenario_id": "S0",
        "object_id": object_id,
        "response_text": {
            "decision": "verified",
            "predicted_class": predicted_class,
            "confidence": 0.82,
            "evidence_clues": ["multi-view support", "geometry consistent"],
            "missing_evidence": "none",
            "recommended_action": "finalize",
        },
    }


class AeroGraphWebNormalizerTest(unittest.TestCase):
    def test_extracts_fenced_jsonl(self) -> None:
        raw = "\n".join(
            [
                "The answer is below.",
                "```jsonl",
                json.dumps(wrapped_response(1, "obj_1")),
                "```",
            ]
        )
        rows = [normalize_row(row) for row in extract_rows(raw)]
        self.assertEqual(len(rows), 1)
        self.assertTrue(validate_response_row(rows[0])["valid"])

    def test_run_merges_multiple_inputs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            (raw_dir / "batch_01.md").write_text(
                "```jsonl\n" + json.dumps(wrapped_response(1, "obj_1")) + "\n```",
                encoding="utf-8",
            )
            (raw_dir / "batch_02.json").write_text(
                json.dumps([wrapped_response(2, "obj_2", "bus")]),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                repo_root=str(root),
                input=["raw"],
                out="normalized.jsonl",
                append_to="manual.jsonl",
                require_valid=True,
                report_json="report.json",
                report_md="report.md",
            )
            report = run(args)
            self.assertEqual(report["normalized_rows"], 2)
            self.assertEqual(report["valid_schema_rows"], 2)
            self.assertEqual(len(report["input_files"]), 2)
            manual_rows = (root / "manual.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(manual_rows), 2)


if __name__ == "__main__":
    unittest.main()
