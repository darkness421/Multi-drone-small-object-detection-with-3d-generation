"""Tests for AeroGraph web collection packet generation."""

from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.build_aerograph_web_collection_packet import build


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class AeroGraphWebCollectionPacketTest(unittest.TestCase):
    def test_packet_marks_valid_and_pending_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompts = [
                {"scenario_id": "S0", "scenario": "s0", "object_id": "obj_1", "candidate_class": "car", "should_reobserve": True},
                {"scenario_id": "S1", "scenario": "s1", "object_id": "obj_2", "candidate_class": "bus", "should_reobserve": True},
            ]
            responses = [
                {
                    "index": 1,
                    "scenario_id": "S0",
                    "object_id": "obj_1",
                    "response_text": {
                        "decision": "verified",
                        "predicted_class": "car",
                        "confidence": 0.9,
                        "evidence_clues": ["consistent views"],
                        "missing_evidence": "none",
                        "recommended_action": "finalize",
                    },
                }
            ]
            manifest = {
                "batch_size": 1,
                "batches": [
                    {"path": "batch1.md", "start_index": 1, "end_index": 1, "count": 1},
                    {"path": "batch2.md", "start_index": 2, "end_index": 2, "count": 1},
                ],
            }
            write_jsonl(root / "prompts.jsonl", prompts)
            write_jsonl(root / "responses.jsonl", responses)
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            args = argparse.Namespace(
                repo_root=str(root),
                prompt_pack="prompts.jsonl",
                web_batch_manifest="manifest.json",
                manual_responses="responses.jsonl",
                out_md="packet.md",
                out_csv="checklist.csv",
                out_json="packet.json",
            )
            report = build(args)
            self.assertEqual(report["prompt_count"], 2)
            self.assertEqual(report["valid_schema_responses"], 1)
            self.assertEqual(report["pending_responses"], 1)
            checklist = (root / "checklist.csv").read_text(encoding="utf-8")
            self.assertIn("valid", checklist)
            self.assertIn("pending", checklist)


if __name__ == "__main__":
    unittest.main()
