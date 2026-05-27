"""Convert COCO detection JSON to Ultralytics YOLO folder format."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

try:
    from .common import image_size
except ImportError:
    from common import image_size


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def normalize_bbox_xywh(bbox: list[float], width: float, height: float) -> list[float]:
    x, y, w, h = [float(v) for v in bbox]
    cx = (x + w / 2.0) / width
    cy = (y + h / 2.0) / height
    return [cx, cy, w / width, h / height]


def category_id_to_yolo_index(categories: list[dict[str, Any]]) -> dict[int, int]:
    return {int(category["id"]): idx for idx, category in enumerate(sorted(categories, key=lambda row: int(row["id"])))}


def category_names(categories: list[dict[str, Any]]) -> dict[int, str]:
    return {idx: category["name"] for idx, category in enumerate(sorted(categories, key=lambda row: int(row["id"])))}


def target_image_name(image: dict[str, Any], file_name: Path) -> str:
    """Return the YOLO image filename, allowing converters to avoid collisions."""

    metadata = image.get("metadata") or {}
    yolo_stem = metadata.get("yolo_stem")
    if yolo_stem:
        return f"{yolo_stem}{file_name.suffix}"
    return file_name.name


def _split_for_index(index: int, train_ratio: float, val_ratio: float) -> str:
    bucket = (index * 9973 % 10000) / 10000.0
    if bucket < train_ratio:
        return "train"
    if bucket < train_ratio + val_ratio:
        return "val"
    return "test"


def _write_names_yaml(out_dir: Path, names: dict[int, str]) -> Path:
    data_yaml = out_dir / "data.yaml"
    names_block = "\n".join(f"  {idx}: {name}" for idx, name in names.items())
    data_yaml.write_text(
        "\n".join(
            [
                f"path: {out_dir.as_posix()}",
                "train: images/train",
                "val: images/val",
                "test: images/test",
                "names:",
                names_block,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return data_yaml


def materialize_image(source: Path, target: Path, *, copy_images: bool, link_images: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    if copy_images and source.exists():
        shutil.copy2(source, target)
        return
    if link_images and source.exists():
        try:
            os.link(source, target)
        except OSError:
            try:
                target.symlink_to(source.resolve())
                return
            except OSError:
                pass
        else:
            return
    target.write_text(f"image_placeholder={source}\n", encoding="utf-8")


def _write_yolo_split(
    payload: dict[str, Any],
    out_dir: Path,
    split: str,
    *,
    copy_images: bool,
    link_images: bool,
) -> tuple[int, int]:
    categories = payload.get("categories", [])
    cat_to_idx = category_id_to_yolo_index(categories)
    images = {int(image["id"]): image for image in payload.get("images", [])}
    annotations_by_image: dict[int, list[dict[str, Any]]] = {}
    for ann in payload.get("annotations", []):
        annotations_by_image.setdefault(int(ann["image_id"]), []).append(ann)

    image_count = 0
    label_count = 0
    (out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
    (out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    for image_id, image in sorted(images.items()):
        file_name = Path(image["file_name"])
        width = image.get("width")
        height = image.get("height")
        if width is None or height is None:
            width, height = image_size(file_name)
        if not width or not height:
            width, height = 1, 1

        target_name = target_image_name(image, file_name)
        target_image = out_dir / "images" / split / target_name
        materialize_image(file_name, target_image, copy_images=copy_images, link_images=link_images)

        label_lines = []
        for ann in annotations_by_image.get(image_id, []):
            category_id = int(ann["category_id"])
            if category_id not in cat_to_idx:
                continue
            bbox = normalize_bbox_xywh(ann["bbox"], float(width), float(height))
            label_lines.append(" ".join([str(cat_to_idx[category_id])] + [f"{value:.6f}" for value in bbox]))
        (out_dir / "labels" / split / f"{Path(target_name).stem}.txt").write_text("\n".join(label_lines), encoding="utf-8")
        image_count += 1
        label_count += len(label_lines)
    return image_count, label_count


def convert_coco_to_yolo(
    coco_json: str | Path,
    out_dir: str | Path,
    *,
    copy_images: bool = False,
    link_images: bool = False,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> Path:
    coco_json = Path(coco_json)
    out_dir = Path(out_dir)
    payload = json.loads(coco_json.read_text(encoding="utf-8"))
    names = category_names(payload.get("categories", []))

    for split in ("train", "val", "test"):
        (out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    images = {int(image["id"]): image for image in payload.get("images", [])}
    annotations_by_image: dict[int, list[dict[str, Any]]] = {}
    for ann in payload.get("annotations", []):
        annotations_by_image.setdefault(int(ann["image_id"]), []).append(ann)
    cat_to_idx = category_id_to_yolo_index(payload.get("categories", []))
    for idx, (image_id, image) in enumerate(sorted(images.items())):
        file_name = Path(image["file_name"])
        split = _split_for_index(idx, train_ratio, val_ratio)
        width = image.get("width")
        height = image.get("height")
        if width is None or height is None:
            width, height = image_size(file_name)
        if not width or not height:
            width, height = 1, 1

        target_name = target_image_name(image, file_name)
        target_image = out_dir / "images" / split / target_name
        materialize_image(file_name, target_image, copy_images=copy_images, link_images=link_images)

        label_lines = []
        for ann in annotations_by_image.get(image_id, []):
            category_id = int(ann["category_id"])
            if category_id not in cat_to_idx:
                continue
            bbox = normalize_bbox_xywh(ann["bbox"], float(width), float(height))
            label_lines.append(" ".join([str(cat_to_idx[category_id])] + [f"{value:.6f}" for value in bbox]))
        (out_dir / "labels" / split / f"{Path(target_name).stem}.txt").write_text("\n".join(label_lines), encoding="utf-8")

    return _write_names_yaml(out_dir, names)


def convert_coco_splits_to_yolo(
    split_coco_jsons: dict[str, str | Path],
    out_dir: str | Path,
    *,
    copy_images: bool = False,
    link_images: bool = False,
) -> Path:
    """Convert explicit COCO split files into one Ultralytics YOLO dataset."""

    out_dir = Path(out_dir)
    names: dict[int, str] | None = None
    for split, coco_json in split_coco_jsons.items():
        payload = json.loads(Path(coco_json).read_text(encoding="utf-8"))
        current_names = category_names(payload.get("categories", []))
        if names is None:
            names = current_names
        _write_yolo_split(payload, out_dir, split, copy_images=copy_images, link_images=link_images)

    for split in ("train", "val", "test"):
        (out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)
    return _write_names_yaml(out_dir, names or {})


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert COCO JSON to Ultralytics YOLO format.")
    parser.add_argument("--coco", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--copy-images", action="store_true")
    parser.add_argument("--link-images", action="store_true", help="Hardlink images into the YOLO tree, falling back to symlinks.")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    args = parser.parse_args()
    data_yaml = convert_coco_to_yolo(
        args.coco,
        args.out_dir,
        copy_images=args.copy_images,
        link_images=args.link_images,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
    )
    print(f"Wrote {data_yaml}")


if __name__ == "__main__":
    main()
