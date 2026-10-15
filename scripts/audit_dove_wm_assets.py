#!/usr/bin/env python3
"""Inventory captured candidate actions for the DOVE-WM research track."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dove_wm.asset_audit import audit_assets, write_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture-root",
        type=Path,
        required=True,
        help="Root containing session directories and capture_plan.json files.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        help="Optional root containing detector evidence_tokens.jsonl files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Destination for summary.json and CSV inventories.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = audit_assets(args.capture_root, args.evidence_root)
    paths = write_audit(audit, args.output_dir)
    result = {
        "summary": audit["summary"],
        "written_files": [str(path) for path in paths],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
