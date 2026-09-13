#!/usr/bin/env python3
"""Verify that a frozen sequence subset is numerically unchanged in a larger run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


KEYS = ("sequence", "tracker", "method")
NUMERIC = (
    "HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW", "FP", "FN", "TP",
    "Frag", "predicted_boxes", "valid_gt_boxes",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path, family: str | None = None) -> dict[tuple[str, ...], dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if family is not None:
        rows = [row for row in rows if row.get("family") == family]
    output = {}
    for row in rows:
        key = tuple(row[item] for item in KEYS)
        if key in output:
            raise RuntimeError(f"Duplicate comparison key: {key}")
        output[key] = row
    return output


def numeric(value: str) -> float | None:
    if value in {"", "None", "nan", "NaN"}:
        return None
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-family", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=0.0)
    args = parser.parse_args()

    reference = load(args.reference)
    candidate = load(args.candidate, args.candidate_family)
    key_match = reference.keys() == candidate.keys()
    maximum = {column: 0.0 for column in NUMERIC}
    mismatches = []
    for key in sorted(reference.keys() & candidate.keys()):
        for column in NUMERIC:
            left, right = numeric(reference[key].get(column, "")), numeric(candidate[key].get(column, ""))
            if left is None or right is None:
                equal = left is right
                difference = None
            else:
                difference = abs(left - right)
                maximum[column] = max(maximum[column], difference)
                equal = difference <= args.tolerance
            if not equal:
                mismatches.append({"key": key, "column": column, "reference": left, "candidate": right})

    payload = {
        "status": "PASS" if key_match and not mismatches else "FAIL",
        "reference": {"path": str(args.reference.resolve()), "sha256": sha256(args.reference), "rows": len(reference)},
        "candidate": {"path": str(args.candidate.resolve()), "sha256": sha256(args.candidate), "family": args.candidate_family, "rows": len(candidate)},
        "key_columns": list(KEYS),
        "numeric_columns": list(NUMERIC),
        "tolerance": args.tolerance,
        "maximum_absolute_difference": maximum,
        "key_sets_match": key_match,
        "mismatches": mismatches,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "rows": len(reference), "mismatches": len(mismatches)}, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
