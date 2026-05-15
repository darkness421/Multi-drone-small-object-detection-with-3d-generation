"""Validate Ultralytics dataset YAML files before starting detector training."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.config import load_config, resolve_path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(slots=True)
class SplitReadiness:
    split: str
    image_dir: str
    label_dir: str
    image_count: int
    label_count: int
    placeholder_count: int
    missing_label_count: int
    ready: bool


@dataclass(slots=True)
class TrainingReadiness:
    data_yaml: str
    dataset_root: str
    ultralytics_available: bool
    ready: bool
    issues: list[str]
    splits: list[SplitReadiness]
    next_action: str


def _dataset_root(config: dict[str, Any], data_yaml: Path) -> Path:
    raw_root = config.get("path", data_yaml.parent)
    root = Path(raw_root)
    if root.is_absolute():
        return root
    return resolve_path(root)


def _split_dir(root: Path, split_value: str | None) -> Path | None:
    if not split_value:
        return None
    split_path = Path(split_value)
    if split_path.is_absolute():
        return split_path
    return root / split_path


def _label_dir_for(image_dir: Path) -> Path:
    parts = list(image_dir.parts)
    for idx, part in enumerate(parts):
        if part.lower() == "images":
            parts[idx] = "labels"
            return Path(*parts)
    return image_dir.parent.parent / "labels" / image_dir.name


def _image_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(child for child in path.rglob("*") if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES)


def _label_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(child for child in path.rglob("*.txt") if child.is_file())


def _is_placeholder(path: Path) -> bool:
    try:
        head = path.read_bytes()[:32]
    except OSError:
        return False
    return head.startswith(b"image_placeholder=")


def inspect_split(root: Path, split: str, split_value: str | None) -> SplitReadiness:
    image_dir = _split_dir(root, split_value) or (root / "images" / split)
    label_dir = _label_dir_for(image_dir)
    images = _image_files(image_dir)
    labels = _label_files(label_dir)
    label_stems = {path.stem for path in labels}
    missing_label_count = sum(1 for image in images if image.stem not in label_stems)
    placeholder_count = sum(1 for image in images if _is_placeholder(image))
    ready = image_dir.exists() and label_dir.exists() and bool(images) and placeholder_count == 0
    return SplitReadiness(
        split=split,
        image_dir=str(image_dir),
        label_dir=str(label_dir),
        image_count=len(images),
        label_count=len(labels),
        placeholder_count=placeholder_count,
        missing_label_count=missing_label_count,
        ready=ready,
    )


def inspect_data_yaml(data_yaml: str | Path) -> TrainingReadiness:
    data_yaml = resolve_path(data_yaml)
    issues: list[str] = []
    if not data_yaml.exists():
        return TrainingReadiness(
            data_yaml=str(data_yaml),
            dataset_root="",
            ultralytics_available=importlib.util.find_spec("ultralytics") is not None,
            ready=False,
            issues=[f"missing data yaml: {data_yaml}"],
            splits=[],
            next_action="convert raw datasets, then rerun training readiness check",
        )

    config = load_config(data_yaml)
    root = _dataset_root(config, data_yaml)
    splits = [
        inspect_split(root, "train", config.get("train")),
        inspect_split(root, "val", config.get("val")),
    ]
    if config.get("test"):
        splits.append(inspect_split(root, "test", config.get("test")))

    if not importlib.util.find_spec("ultralytics"):
        issues.append("ultralytics is not installed in the active Python environment")
    if not root.exists():
        issues.append(f"dataset root does not exist: {root}")
    for split in splits:
        if split.image_count == 0:
            issues.append(f"{split.split} has no images: {split.image_dir}")
        if split.placeholder_count:
            issues.append(f"{split.split} has placeholder images: {split.placeholder_count}")
        if split.missing_label_count:
            issues.append(f"{split.split} images without matching label files: {split.missing_label_count}")

    ready = not issues and all(split.ready for split in splits)
    next_action = "ready: launch the OS-specific detector training script" if ready else "fix issues, then rerun training readiness check"
    return TrainingReadiness(
        data_yaml=str(data_yaml),
        dataset_root=str(root),
        ultralytics_available=importlib.util.find_spec("ultralytics") is not None,
        ready=ready,
        issues=issues,
        splits=splits,
        next_action=next_action,
    )


def print_report(rows: list[TrainingReadiness]) -> None:
    print("Training readiness")
    print("-" * 80)
    for row in rows:
        status = "READY" if row.ready else "NOT READY"
        print(f"{status}: {row.data_yaml}")
        print(f"  root: {row.dataset_root}")
        print(f"  ultralytics: {row.ultralytics_available}")
        for split in row.splits:
            print(
                f"  {split.split}: images={split.image_count}, labels={split.label_count}, "
                f"placeholders={split.placeholder_count}, missing_labels={split.missing_label_count}"
            )
        for issue in row.issues:
            print(f"  issue: {issue}")
        print(f"  next: {row.next_action}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check if Ultralytics detector training can start.")
    parser.add_argument(
        "--data-yaml",
        nargs="+",
        default=["configs/detector/visdrone_yolo_data.yaml", "configs/detector/uavdt_yolo_data.yaml"],
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    rows = [inspect_data_yaml(path) for path in args.data_yaml]
    if args.json:
        print(json.dumps([asdict(row) for row in rows], indent=2))
    else:
        print_report(rows)

    if args.strict and any(not row.ready for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
