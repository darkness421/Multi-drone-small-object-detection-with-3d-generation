"""Prepare TinyPerson COCO-style annotations as an Ultralytics YOLO dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from data.converters.coco_to_yolo import convert_coco_splits_to_yolo


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("images"), list) and isinstance(payload.get("annotations"), list):
        return payload
    return None


def infer_split(path: Path) -> str | None:
    text = path.as_posix().lower()
    if "train" in text:
        return "train"
    if "val" in text or "valid" in text:
        return "val"
    if "test" in text:
        return "test"
    return None


def build_image_index(raw_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in raw_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            index.setdefault(path.name, path.resolve())
    return index


def ensure_person_categories(payload: dict[str, Any]) -> None:
    if payload.get("categories"):
        return
    category_ids = sorted({int(ann.get("category_id", 1)) for ann in payload.get("annotations", [])})
    if not category_ids:
        category_ids = [1]
    payload["categories"] = [{"id": category_id, "name": "person"} for category_id in category_ids]


def rewrite_image_paths(payload: dict[str, Any], image_index: dict[str, Path]) -> None:
    for image in payload.get("images", []):
        file_name = Path(str(image.get("file_name", "")))
        candidates = [
            file_name,
            image_index.get(file_name.name),
        ]
        resolved = next((Path(candidate) for candidate in candidates if candidate and Path(candidate).exists()), None)
        if resolved is not None:
            image["file_name"] = resolved.resolve().as_posix()


def discover_coco_splits(raw_root: Path) -> dict[str, Path]:
    image_index = build_image_index(raw_root)
    candidates: dict[str, tuple[int, Path]] = {}
    for path in sorted(raw_root.rglob("*.json")):
        payload = load_json(path)
        if payload is None:
            continue
        split = infer_split(path)
        if split is None:
            continue
        score = len(payload.get("images", [])) + len(payload.get("annotations", []))
        old = candidates.get(split)
        if old is None or score > old[0]:
            ensure_person_categories(payload)
            rewrite_image_paths(payload, image_index)
            normalized = path.with_name(f"{path.stem}.normalized_for_yolo.json")
            normalized.write_text(json.dumps(payload), encoding="utf-8")
            candidates[split] = (score, normalized)

    splits = {split: path for split, (_, path) in candidates.items()}
    if "val" not in splits and "test" in splits:
        splits["val"] = splits["test"]
    return splits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", default="data/raw/TinyPerson")
    parser.add_argument("--yolo-out", default="data/processed/tinyperson_yolo")
    parser.add_argument("--summary", default="outputs/experiments/tinyperson_prepare_summary.json")
    args = parser.parse_args()

    raw_root = Path(args.raw_root)
    yolo_out = Path(args.yolo_out)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    splits = discover_coco_splits(raw_root)
    if "train" not in splits or "val" not in splits:
        summary_path.write_text(
            json.dumps(
                {
                    "status": "missing_required_splits",
                    "raw_root": raw_root.as_posix(),
                    "found_splits": {split: path.as_posix() for split, path in splits.items()},
                    "required": ["train", "val"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        raise SystemExit(
            "TinyPerson train/val COCO annotations were not found. "
            f"See {summary_path} after download/extraction."
        )

    data_yaml = convert_coco_splits_to_yolo(splits, yolo_out, link_images=True)
    summary = {
        "status": "ready",
        "raw_root": raw_root.as_posix(),
        "yolo_out": yolo_out.as_posix(),
        "data_yaml": data_yaml.as_posix(),
        "splits": {split: path.as_posix() for split, path in splits.items()},
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
