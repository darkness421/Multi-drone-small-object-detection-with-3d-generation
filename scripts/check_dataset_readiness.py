"""Check whether configured dataset roots are ready for conversion/training."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.config import configured_dataset_roots


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(slots=True)
class DatasetReadiness:
    name: str
    ready: bool
    missing: list[str]
    existing: dict[str, str]
    counts: dict[str, int]
    next_action: str


def _count_files(path: Path, suffixes: Iterable[str] | None = None) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    suffixes = {suffix.lower() for suffix in suffixes} if suffixes is not None else None
    total = 0
    for child in path.rglob("*"):
        if child.is_file() and (suffixes is None or child.suffix.lower() in suffixes):
            total += 1
    return total


def _required_fields(name: str, fields: dict[str, Path] | None = None) -> tuple[str, ...]:
    if name == "visdrone":
        fields = fields or {}
        if "train_images" in fields:
            return ("train_images", "train_annotations", "val_images", "val_annotations")
        return ("images", "annotations")
    if name == "uavdt":
        return ("sequence_dir", "annotations")
    if name == "aitod":
        return ("annotations",)
    return tuple()


def _count_field(field: str, path: Path) -> int:
    if field in {"images", "sequence_dir"}:
        return _count_files(path, IMAGE_SUFFIXES)
    if field == "annotations":
        return _count_files(path, {".txt", ".json", ".xml"})
    return _count_files(path)


def inspect_dataset(name: str, fields: dict[str, Path]) -> DatasetReadiness:
    required = _required_fields(name, fields)
    missing = [field for field in required if not fields.get(field, Path()).exists()]
    existing = {field: str(path) for field, path in fields.items() if path.exists()}
    counts = {field: _count_field(field, path) for field, path in fields.items() if path.exists()}
    ready = not missing

    if ready:
        next_action = "ready: run scripts\\01_convert_datasets.bat"
    else:
        needed = ", ".join(missing)
        next_action = f"copy or configure missing raw dataset paths: {needed}"

    return DatasetReadiness(
        name=name,
        ready=ready,
        missing=missing,
        existing=existing,
        counts=counts,
        next_action=next_action,
    )


def inspect_all(config: str | Path = "configs/dataset_roots.yaml") -> list[DatasetReadiness]:
    roots = configured_dataset_roots(config)
    return [inspect_dataset(name, fields) for name, fields in roots.items()]


def print_table(rows: list[DatasetReadiness]) -> None:
    print("Dataset readiness")
    print("-" * 80)
    for row in rows:
        status = "READY" if row.ready else "MISSING"
        print(f"{row.name:10s} {status:8s} {row.next_action}")
        for field, count in row.counts.items():
            print(f"  - {field}: {count}")
        for field in row.missing:
            print(f"  - missing: {field}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check configured dataset roots before conversion/training.")
    parser.add_argument("--config", default="configs/dataset_roots.yaml")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any required path is missing.")
    args = parser.parse_args()

    rows = inspect_all(args.config)
    if args.json:
        print(json.dumps([asdict(row) for row in rows], indent=2))
    else:
        print_table(rows)

    if args.strict and any(not row.ready for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
