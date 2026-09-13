#!/usr/bin/env python3
"""Materialize the revision-locked MMOT test split without altering prior data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def sequence_audit(path: Path) -> dict:
    npy = sorted(path.glob("*.npy"))
    txt = sorted(path.glob("*.txt"))
    npy_stems = {item.stem for item in npy}
    txt_stems = {item.stem for item in txt}
    return {
        "npy_count": len(npy),
        "txt_count": len(txt),
        "paired_count": len(npy_stems & txt_stems),
        "unpaired_npy": sorted(npy_stems - txt_stems),
        "unpaired_txt": sorted(txt_stems - npy_stems),
        "valid": bool(npy) and npy_stems == txt_stems,
    }


def find_existing(name: str, expected_size: int, roots: list[Path]) -> Path | None:
    for root in roots:
        candidate = root / name
        if candidate.is_file() and candidate.stat().st_size == expected_size:
            return candidate
    return None


def find_existing_sequence(stem: str, roots: list[Path]) -> Path | None:
    for root in roots:
        candidate = root / stem
        if candidate.is_dir() and sequence_audit(candidate)["valid"]:
            return candidate
    return None


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "curl", "-L", "--fail", "--retry", "8", "--retry-all-errors",
        "--retry-delay", "5", "--continue-at", "-", "--output", str(target), url,
    ]
    subprocess.run(command, check=True)


def extract(archive: Path, target: Path) -> dict:
    if target.exists():
        audit = sequence_audit(target)
        if audit["valid"]:
            return audit
        raise RuntimeError(f"existing extraction is incomplete: {target}")
    temporary = target.parent / f".{target.name}.partial-{os.getpid()}"
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    try:
        subprocess.run(["tar", "-xf", str(archive), "-C", str(temporary)], check=True)
        audit = sequence_audit(temporary)
        if not audit["valid"]:
            raise RuntimeError(f"archive has unmatched NPY/TXT members: {archive}")
        os.replace(temporary, target)
        return audit
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--extract-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--existing-archive-dir", type=Path, action="append", default=[])
    parser.add_argument("--existing-extract-dir", type=Path, action="append", default=[])
    parser.add_argument("--repo", default="Annzstbl/MMOT")
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()

    tree = json.loads(args.tree.read_text(encoding="utf-8"))
    files = sorted(
        (item for item in tree if item.get("type") == "file"
         and item["path"].startswith("test/") and item["path"].endswith(".tar")),
        key=lambda item: item["path"],
    )
    if len(files) != 50:
        raise SystemExit(f"expected 50 test archives, found {len(files)}")

    args.archive_dir.mkdir(parents=True, exist_ok=True)
    args.extract_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "RUNNING",
        "repo": args.repo,
        "revision": args.revision,
        "tree": str(args.tree),
        "test_archive_count_expected": 50,
        "total_bytes_expected": sum(int(item["size"]) for item in files),
        "started_at_unix": time.time(),
        "command": " ".join(sys.argv),
        "sequences": [],
    }
    write_json(args.manifest, payload)

    try:
        for index, item in enumerate(files, start=1):
            name = Path(item["path"]).name
            stem = Path(name).stem
            expected_size = int(item["size"])
            archive = find_existing(name, expected_size, args.existing_archive_dir)
            archive_source = "preserved_existing"
            if archive is None:
                archive = args.archive_dir / name
                if archive.exists() and archive.stat().st_size == expected_size:
                    archive_source = "verified_previous_download"
                else:
                    url = (
                        f"https://huggingface.co/datasets/{quote(args.repo, safe='/')}/resolve/"
                        f"{args.revision}/test/{quote(name)}?download=true"
                    )
                    print(f"[{index:02d}/50] DOWNLOAD {name} {expected_size}", flush=True)
                    download(url, archive)
                    archive_source = "downloaded"
            actual_size = archive.stat().st_size
            if actual_size != expected_size:
                raise RuntimeError(
                    f"size mismatch for {name}: expected {expected_size}, got {actual_size}"
                )

            target = args.extract_dir / stem
            linked_from = None
            if not target.exists():
                existing_sequence = find_existing_sequence(stem, args.existing_extract_dir)
                if existing_sequence is not None:
                    target.symlink_to(existing_sequence, target_is_directory=True)
                    linked_from = str(existing_sequence)
            if target.is_symlink():
                audit = sequence_audit(target)
                extraction = "preserved_existing_symlink"
            else:
                print(f"[{index:02d}/50] EXTRACT  {name}", flush=True)
                audit = extract(archive, target)
                extraction = "new_or_verified_extraction"
            if not audit["valid"]:
                raise RuntimeError(f"invalid extracted sequence: {target}")

            record = {
                "sequence": stem,
                "remote_path": item["path"],
                "expected_size": expected_size,
                "archive_path": str(archive),
                "archive_source": archive_source,
                "archive_sha256": sha256(archive),
                "extracted_path": str(target),
                "extraction": extraction,
                "linked_from": linked_from,
                **audit,
            }
            payload["sequences"].append(record)
            payload["completed_count"] = len(payload["sequences"])
            write_json(args.manifest, payload)
            print(
                f"[{index:02d}/50] VERIFIED {stem} frames={audit['paired_count']} "
                f"sha256={record['archive_sha256'][:12]}",
                flush=True,
            )
    except Exception as error:
        payload["status"] = "FAILED"
        payload["error"] = f"{type(error).__name__}: {error}"
        payload["finished_at_unix"] = time.time()
        write_json(args.manifest, payload)
        raise

    payload["status"] = "COMPLETE"
    payload["finished_at_unix"] = time.time()
    payload["runtime_seconds"] = payload["finished_at_unix"] - payload["started_at_unix"]
    payload["completed_count"] = len(payload["sequences"])
    payload["total_paired_frames"] = sum(row["paired_count"] for row in payload["sequences"])
    write_json(args.manifest, payload)
    print(json.dumps({
        "status": payload["status"],
        "sequences": payload["completed_count"],
        "paired_frames": payload["total_paired_frames"],
        "runtime_seconds": payload["runtime_seconds"],
        "manifest": str(args.manifest),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
