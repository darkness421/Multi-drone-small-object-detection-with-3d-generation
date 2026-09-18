#!/usr/bin/env python3
"""Build deterministic file inventory and checksums for the release tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".pytest_cache", "__pycache__", "outputs"}
GENERATED = {"RELEASE_MANIFEST.json", "SHA256SUMS"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def payload_files() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*"))
        if path.is_file()
        and path.name not in GENERATED
        and not IGNORED_PARTS.intersection(path.relative_to(ROOT).parts)
    ]


def main() -> int:
    files = payload_files()
    manifest = {
        "release_name": "REGR-Aerial-MOT",
        "release_stage": "public-release-candidate",
        "version": "0.1.0",
        "publication_gate": "project license not selected",
        "scope": "within-stream identity-only temporal refinement",
        "payload_file_count": len(files),
        "payload_files": [path.relative_to(ROOT).as_posix() for path in files],
    }
    (ROOT / "RELEASE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    checksum_files = files + [ROOT / "RELEASE_MANIFEST.json"]
    lines = [
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}"
        for path in checksum_files
    ]
    (ROOT / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"indexed {len(files)} payload files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
