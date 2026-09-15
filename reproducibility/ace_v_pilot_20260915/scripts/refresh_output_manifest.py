#!/usr/bin/env python3
"""Refresh hashes in an existing ACE-V output manifest after lossless compression."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest_stream(handle) -> str:
    value = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        value.update(block)
    return value.hexdigest()


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return digest_stream(handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    manifest_path = args.output_dir / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    outputs = {}
    for path in sorted(args.output_dir.iterdir()):
        if not path.is_file() or path.name == "manifest.json":
            continue
        if path.name == "accepted_link_audit.csv" and (path.with_suffix(path.suffix + ".gz")).is_file():
            continue
        record = {"bytes": path.stat().st_size, "sha256": digest(path)}
        if path.suffix == ".gz":
            with gzip.open(path, "rb") as handle:
                record["uncompressed_sha256"] = digest_stream(handle)
        outputs[path.name] = record
    payload["outputs"] = outputs
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"refreshed {len(outputs)} outputs in {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
