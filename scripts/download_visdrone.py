"""Download and extract VisDrone2019-DET splits for Windows workflows."""

from __future__ import annotations

import argparse
import shutil
import sys
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from runtime.config import resolve_path


@dataclass(frozen=True)
class VisDroneSplit:
    """Download metadata for one VisDrone2019-DET split."""

    name: str
    url: str
    expected_bytes: int


VISDRONE_SPLITS = [
    VisDroneSplit(
        name="VisDrone2019-DET-train",
        url="https://github.com/ultralytics/yolov5/releases/download/v1.0/VisDrone2019-DET-train.zip",
        expected_bytes=1_549_875_511,
    ),
    VisDroneSplit(
        name="VisDrone2019-DET-val",
        url="https://github.com/ultralytics/yolov5/releases/download/v1.0/VisDrone2019-DET-val.zip",
        expected_bytes=81_638_851,
    ),
    VisDroneSplit(
        name="VisDrone2019-DET-test-dev",
        url="https://github.com/ultralytics/yolov5/releases/download/v1.0/VisDrone2019-DET-test-dev.zip",
        expected_bytes=311_251_787,
    ),
]


def split_file_count(raw_root: Path, split_name: str) -> int:
    split_dir = raw_root / split_name
    if not split_dir.exists():
        return 0
    return sum(1 for path in split_dir.rglob("*") if path.is_file())


def has_extracted_split(raw_root: Path, split_name: str) -> bool:
    split_dir = raw_root / split_name
    return (split_dir / "images").exists() and (split_dir / "annotations").exists() and split_file_count(raw_root, split_name) > 0


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def zip_path_for(download_dir: Path, split: VisDroneSplit) -> Path:
    return download_dir / f"{split.name}.zip"


def existing_zip_is_complete(path: Path, split: VisDroneSplit) -> bool:
    return path.exists() and path.stat().st_size >= int(split.expected_bytes * 0.99)


def download_file(url: str, target: Path, *, expected_bytes: int | None = None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_target = target.with_suffix(target.suffix + ".part")
    downloaded = temp_target.stat().st_size if temp_target.exists() else 0
    headers = {"User-Agent": "CoM3D-ACE-dataset-setup"}
    if downloaded:
        headers["Range"] = f"bytes={downloaded}-"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response, temp_target.open("ab" if downloaded else "wb") as handle:
        total = expected_bytes or int(response.headers.get("Content-Length", "0") or 0) + downloaded
        start = time.time()
        last_print = 0.0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_print >= 2.0:
                percent = (downloaded / total * 100.0) if total else 0.0
                elapsed = max(now - start, 1e-6)
                speed = downloaded / elapsed
                print(
                    f"  {target.name}: {percent:6.2f}% "
                    f"({format_bytes(downloaded)} / {format_bytes(total)}) "
                    f"at {format_bytes(int(speed))}/s",
                    flush=True,
                )
                last_print = now

    if expected_bytes and temp_target.stat().st_size < int(expected_bytes * 0.99):
        raise RuntimeError(f"Incomplete download: {temp_target}")
    if target.exists():
        target.unlink()
    temp_target.rename(target)


def extract_zip(zip_path: Path, raw_root: Path, split_name: str) -> None:
    raw_root.mkdir(parents=True, exist_ok=True)
    if has_extracted_split(raw_root, split_name):
        print(f"Already extracted: {split_name}")
        return
    print(f"Extracting {zip_path.name} -> {raw_root}")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(raw_root)
    if not has_extracted_split(raw_root, split_name):
        nested_candidates = list(raw_root.rglob(split_name))
        for candidate in nested_candidates:
            if candidate.is_dir() and candidate.parent != raw_root:
                target = raw_root / split_name
                if target.exists():
                    shutil.rmtree(target)
                shutil.move(str(candidate), str(target))
                break
    if not has_extracted_split(raw_root, split_name):
        raise RuntimeError(f"Extracted split is missing images/annotations: {raw_root / split_name}")


def prepare_visdrone(
    *,
    download_dir: str | Path = "data/raw/downloads",
    raw_root: str | Path = "data/raw/VisDrone2019-DET",
    skip_download: bool = False,
    skip_extract: bool = False,
) -> list[Path]:
    """Download/extract VisDrone and return expected split directories."""

    download_dir = resolve_path(download_dir)
    raw_root = resolve_path(raw_root)
    split_dirs: list[Path] = []
    for split in VISDRONE_SPLITS:
        split_dir = raw_root / split.name
        split_dirs.append(split_dir)
        if has_extracted_split(raw_root, split.name):
            print(f"Ready: {split.name}")
            continue
        zip_path = zip_path_for(download_dir, split)
        if not existing_zip_is_complete(zip_path, split):
            if skip_download:
                raise FileNotFoundError(f"Missing zip and --skip-download was set: {zip_path}")
            print(f"Downloading {split.name} ({format_bytes(split.expected_bytes)})")
            download_file(split.url, zip_path, expected_bytes=split.expected_bytes)
        else:
            print(f"Using existing zip: {zip_path}")
        if not skip_extract:
            extract_zip(zip_path, raw_root, split.name)
    return split_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and extract VisDrone2019-DET.")
    parser.add_argument("--download-dir", default="data/raw/downloads")
    parser.add_argument("--raw-root", default="data/raw/VisDrone2019-DET")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-extract", action="store_true")
    args = parser.parse_args()

    try:
        split_dirs = prepare_visdrone(
            download_dir=args.download_dir,
            raw_root=args.raw_root,
            skip_download=args.skip_download,
            skip_extract=args.skip_extract,
        )
    except Exception as exc:
        print(f"VisDrone preparation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("VisDrone preparation complete.")
    for split_dir in split_dirs:
        print(f"  {split_dir}")


if __name__ == "__main__":
    main()
