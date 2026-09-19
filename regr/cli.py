"""Command-line replay of REGR on frozen tracklets and descriptors."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from .core import METHODS, PARAMETERS
from .graph import refine
from .io import load_descriptors, load_predictions, write_json, write_predictions


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_edges(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fields:
            return
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--descriptors", type=Path, required=True)
    parser.add_argument("--method", choices=METHODS, default="regr")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    predictions = load_predictions(args.predictions)
    descriptors = load_descriptors(args.descriptors)
    output, audit = refine(predictions, descriptors, args.method)

    write_predictions(args.output_dir / "refined.jsonl", output)
    _write_edges(args.output_dir / "accepted_edges.csv", audit.pop("accepted"))
    _write_edges(args.output_dir / "rejected_edges.csv", audit.pop("rejected"))
    write_json(
        args.output_dir / "manifest.json",
        {
            "status": "COMPLETE",
            "method": args.method,
            "parameters": PARAMETERS,
            "inputs": {
                "predictions": {"path": str(args.predictions), "sha256": sha256(args.predictions)},
                "descriptors": {"path": str(args.descriptors), "sha256": sha256(args.descriptors)},
            },
            **audit,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
