from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from regr.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_cached_cli_smoke(tmp_path):
    output = tmp_path / "run"
    assert main(
        [
            "--predictions",
            str(ROOT / "examples" / "predictions.jsonl"),
            "--descriptors",
            str(ROOT / "examples" / "descriptors.json"),
            "--method",
            "regr-tg",
            "--output-dir",
            str(output),
        ]
    ) == 0
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "COMPLETE"
    assert manifest["observation_multiset_preserved"] is True
    assert manifest["accepted_edges"] == 1
    assert (output / "refined.jsonl").is_file()


def test_source_checkout_wrapper(tmp_path):
    output = tmp_path / "wrapper-run"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_cached_refinement.py"),
            "--predictions",
            str(ROOT / "examples" / "predictions.jsonl"),
            "--descriptors",
            str(ROOT / "examples" / "descriptors.json"),
            "--method",
            "regr-tg",
            "--output-dir",
            str(output),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["observation_multiset_preserved"] is True
