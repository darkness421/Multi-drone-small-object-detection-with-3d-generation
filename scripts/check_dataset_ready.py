"""Server-oriented raw/converted dataset readiness checks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.config import load_config, resolve_path
from scripts.check_training_readiness import inspect_data_yaml


@dataclass(slots=True)
class PathStatus:
    name: str
    path: str
    exists: bool
    file_count: int
    required: bool
    ready: bool
    note: str


def _count(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for child in path.rglob("*") if child.is_file())


def _resolve(value: str) -> Path:
    return resolve_path(Path(value).expanduser())


def inspect_paths(config: str | Path = "configs/paths.ubuntu.yaml") -> list[PathStatus]:
    payload = load_config(config)
    datasets: dict[str, Any] = payload.get("datasets", {})
    specs = [
        ("visdrone_raw", True, "copy VisDrone2019-DET train/val/test-dev folders here before conversion"),
        ("visdrone_yolo", True, "YOLO layout expected: images/{train,val,test} and labels/{train,val,test}"),
        ("visdrone_coco_train", False, "COCO export used by auxiliary analysis"),
        ("visdrone_coco_val", False, "COCO export used by auxiliary analysis"),
        ("uavdt_raw", False, "copy UAVDT raw sequences and annotations here before conversion"),
        ("uavdt_yolo", False, "YOLO layout expected after conversion"),
        ("uavdt_coco", False, "COCO export used by auxiliary analysis"),
    ]
    rows: list[PathStatus] = []
    for key, required, note in specs:
        value = datasets.get(key, "")
        path = _resolve(str(value)) if value else resolve_path("")
        rows.append(
            PathStatus(
                name=key,
                path=str(path),
                exists=bool(value) and path.exists(),
                file_count=_count(path) if value else 0,
                required=required,
                ready=bool(value) and path.exists() and (not required or _count(path) > 0),
                note=note,
            )
        )
    return rows


def print_report(rows: list[PathStatus], data_yamls: list[str]) -> None:
    print("Dataset readiness for Ubuntu server")
    print("-" * 80)
    for row in rows:
        if row.ready:
            status = "OK"
        elif row.required:
            status = "MISSING"
        else:
            status = "optional-missing"
        print(f"{status:16s} {row.name}: {row.path}")
        print(f"  files: {row.file_count}")
        if not row.ready:
            print(f"  next: {row.note}")

    print("")
    print("Ultralytics training YAML checks")
    print("-" * 80)
    for data_yaml in data_yamls:
        readiness = inspect_data_yaml(data_yaml)
        status = "READY" if readiness.ready else "NOT READY"
        print(f"{status}: {readiness.data_yaml}")
        print(f"  root: {readiness.dataset_root}")
        for split in readiness.splits:
            print(
                f"  {split.split}: images={split.image_count}, labels={split.label_count}, "
                f"placeholders={split.placeholder_count}, missing_labels={split.missing_label_count}"
            )
        for issue in readiness.issues:
            print(f"  issue: {issue}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check raw and converted dataset readiness before server training.")
    parser.add_argument("--paths-config", default="configs/paths.ubuntu.yaml")
    parser.add_argument(
        "--data-yaml",
        nargs="+",
        default=["configs/detector/visdrone_yolo_data.yaml", "configs/detector/uavdt_yolo_data.yaml"],
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    rows = inspect_paths(args.paths_config)
    training_rows = [inspect_data_yaml(path) for path in args.data_yaml]
    if args.json:
        print(
            json.dumps(
                {
                    "paths": [asdict(row) for row in rows],
                    "training": [asdict(row) for row in training_rows],
                },
                indent=2,
            )
        )
    else:
        print_report(rows, args.data_yaml)

    required_missing = any(row.required and not row.ready for row in rows)
    training_missing = any(not row.ready for row in training_rows)
    if args.strict and (required_missing or training_missing):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
