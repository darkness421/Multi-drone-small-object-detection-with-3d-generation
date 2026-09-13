#!/usr/bin/env python3
"""Verify that overlapping detector caches contain identical predictions."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path


def records(path: Path) -> list[dict]:
    output = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            row.pop("family", None)
            output.append(row)
    return output


def canonical_sha(rows: list[dict]) -> str:
    payload = "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-root", type=Path, required=True)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    for old_family in ("data28", "data30"):
        for old_path in sorted((args.old_root / old_family).glob("*.jsonl.gz")):
            new_path = args.new_root / "legacy12" / old_path.name
            if not new_path.is_file():
                raise SystemExit(f"missing overlapping cache: {new_path}")
            old_records = records(old_path)
            new_records = records(new_path)
            rows.append({
                "sequence": old_path.stem.replace(".jsonl", ""),
                "old_family": old_family,
                "row_count_old": len(old_records),
                "row_count_new": len(new_records),
                "canonical_sha_old": canonical_sha(old_records),
                "canonical_sha_new": canonical_sha(new_records),
                "identical_after_family_normalization": old_records == new_records,
            })
    status = "PASS" if len(rows) == 12 and all(row["identical_after_family_normalization"] for row in rows) else "FAIL"
    payload = {
        "status": status,
        "purpose": "Deterministic overlap check; family labels are excluded from comparison.",
        "command": " ".join(sys.argv),
        "script_sha256": file_sha(Path(__file__)),
        "sequence_count": len(rows),
        "sequences": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "sequence_count": len(rows)}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
