#!/usr/bin/env python3
"""Create immutable symlink views for the known-12 and new-38 MMOT subsets."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


LEGACY12 = {
    "data28-1", "data28-2", "data28-3", "data28-4", "data28-5", "data28-6",
    "data30-2", "data30-3", "data30-4", "data30-5", "data30-9", "data30-10",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-root", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-total", type=int, default=50)
    args = parser.parse_args()

    sequences = sorted(path for path in args.full_root.iterdir() if path.is_dir())
    names = {path.name for path in sequences}
    if len(sequences) != args.expected_total:
        raise SystemExit(f"expected {args.expected_total} sequences, found {len(sequences)}")
    missing_legacy = sorted(LEGACY12 - names)
    if missing_legacy:
        raise SystemExit(f"legacy sequence(s) missing: {missing_legacy}")

    rows = []
    for source in sequences:
        split = "legacy12" if source.name in LEGACY12 else "confirmation38"
        destination = args.split_root / split / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            if destination.resolve() != source.resolve():
                raise SystemExit(f"conflicting symlink: {destination}")
        elif destination.exists():
            raise SystemExit(f"refusing to replace existing path: {destination}")
        else:
            destination.symlink_to(source.resolve(), target_is_directory=True)
        npy_count = sum(1 for _ in source.glob("*.npy"))
        txt_count = sum(1 for _ in source.glob("*.txt"))
        if npy_count == 0 or npy_count != txt_count:
            raise SystemExit(f"invalid frame/label pairing in {source}: {npy_count}/{txt_count}")
        rows.append({
            "sequence": source.name,
            "split": split,
            "source": str(source.resolve()),
            "view": str(destination),
            "npy_count": npy_count,
            "txt_count": txt_count,
        })

    counts = {split: sum(row["split"] == split for row in rows) for split in ("legacy12", "confirmation38")}
    if counts != {"legacy12": 12, "confirmation38": 38}:
        raise SystemExit(f"unexpected split counts: {counts}")
    manifest = {
        "status": "COMPLETE",
        "purpose": "Frozen reporting split; no sequence is selected by performance.",
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
        "full_root": str(args.full_root),
        "split_root": str(args.split_root),
        "counts": counts,
        "sequences": rows,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", **counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
