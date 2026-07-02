"""Prepare TinyPerson corner-window annotations as a YOLO dataset.

TinyPerson corner annotations describe crop windows inside the original image.
The regular COCO converter links the full image and therefore mis-scales labels
for these files. This converter materializes each annotated window as its own
image crop and writes crop-local YOLO labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_image_index(raw_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in raw_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            index.setdefault(path.name, path.resolve())
    return index


def yolo_name(image: dict[str, Any], source: Path, image_id: int) -> str:
    corner = image.get("corner") or [0, 0, image.get("width", 0), image.get("height", 0)]
    x1, y1, x2, y2 = [int(round(float(v))) for v in corner]
    return f"{source.stem}_id{image_id}_x{x1}_y{y1}_x{x2}_y{y2}.jpg"


def clip_bbox_xywh(bbox: list[float], width: float, height: float) -> tuple[float, float, float, float] | None:
    x, y, w, h = [float(v) for v in bbox]
    x1 = max(0.0, min(width, x))
    y1 = max(0.0, min(height, y))
    x2 = max(0.0, min(width, x + w))
    y2 = max(0.0, min(height, y + h))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2 - x1, y2 - y1


def to_yolo_line(bbox: tuple[float, float, float, float], width: float, height: float) -> str:
    x, y, w, h = bbox
    cx = (x + w / 2.0) / width
    cy = (y + h / 2.0) / height
    return f"0 {cx:.6f} {cy:.6f} {w / width:.6f} {h / height:.6f}"


def should_skip_ann(ann: dict[str, Any], *, keep_uncertain: bool, keep_ignore: bool) -> bool:
    if not keep_ignore and (ann.get("ignore") or ann.get("iscrowd") or ann.get("logo")):
        return True
    if not keep_uncertain and ann.get("uncertain"):
        return True
    return False


def materialize_crop(source: Path, target: Path, corner: list[Any], width: int, height: int) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return True
    try:
        with Image.open(source) as image:
            rgb = image.convert("RGB")
            x1, y1, x2, y2 = [int(round(float(v))) for v in corner]
            crop = rgb.crop((x1, y1, x2, y2))
            if crop.size != (width, height):
                crop = crop.resize((width, height), Image.BILINEAR)
            crop.save(target, quality=92)
    except Exception:
        return False
    return True


def convert_split(
    split: str,
    coco_json: Path,
    out_dir: Path,
    image_index: dict[str, Path],
    *,
    keep_uncertain: bool,
    keep_ignore: bool,
) -> dict[str, int]:
    payload = load_json(coco_json)
    images = {int(image["id"]): image for image in payload.get("images", [])}
    anns_by_image: dict[int, list[dict[str, Any]]] = {}
    for ann in payload.get("annotations", []):
        anns_by_image.setdefault(int(ann["image_id"]), []).append(ann)

    image_out = out_dir / "images" / split
    label_out = out_dir / "labels" / split
    image_out.mkdir(parents=True, exist_ok=True)
    label_out.mkdir(parents=True, exist_ok=True)

    written_images = 0
    missing_images = 0
    written_boxes = 0
    skipped_boxes = 0
    empty_images = 0

    for image_id, image in sorted(images.items()):
        source_name = Path(str(image.get("file_name", ""))).name
        source = image_index.get(source_name)
        if source is None:
            missing_images += 1
            continue

        width = int(round(float(image.get("width") or 0)))
        height = int(round(float(image.get("height") or 0)))
        corner = image.get("corner") or [0, 0, width, height]
        if width <= 0 or height <= 0:
            x1, y1, x2, y2 = [int(round(float(v))) for v in corner]
            width = max(1, x2 - x1)
            height = max(1, y2 - y1)

        target_name = yolo_name(image, source, image_id)
        target_image = image_out / target_name
        if not materialize_crop(source, target_image, corner, width, height):
            missing_images += 1
            continue

        lines: list[str] = []
        for ann in anns_by_image.get(image_id, []):
            if should_skip_ann(ann, keep_uncertain=keep_uncertain, keep_ignore=keep_ignore):
                skipped_boxes += 1
                continue
            clipped = clip_bbox_xywh(ann.get("bbox", [0, 0, 0, 0]), width, height)
            if clipped is None:
                skipped_boxes += 1
                continue
            lines.append(to_yolo_line(clipped, width, height))

        (label_out / f"{Path(target_name).stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        written_images += 1
        written_boxes += len(lines)
        if not lines:
            empty_images += 1

    return {
        "images": written_images,
        "boxes": written_boxes,
        "empty_images": empty_images,
        "missing_images": missing_images,
        "skipped_boxes": skipped_boxes,
    }


def write_data_yaml(path: Path, out_dir: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"path: {out_dir.as_posix()}",
                "train: images/train",
                "val: images/val",
                "test: images/test",
                "names:",
                "  0: person",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", default="data/raw/TinyPerson")
    parser.add_argument("--out", default="data/processed/tinyperson_corner_original_yolo")
    parser.add_argument(
        "--train-json",
        default="data/raw/TinyPerson/google_drive/tiny_set/annotations/corner/tiny_set_train_with_dense_sw1920_sh1080.json",
    )
    parser.add_argument(
        "--val-json",
        default="data/raw/TinyPerson/google_drive/tiny_set/annotations/corner/task/tiny_set_test_sw1920_sh1080_all.json",
    )
    parser.add_argument(
        "--test-json",
        default="data/raw/TinyPerson/google_drive/tiny_set/annotations/corner/task/tiny_set_test_sw1920_sh1080_all.json",
    )
    parser.add_argument("--data-yaml", default="configs/detector/tinyperson_corner_original_yolo_data.yaml")
    parser.add_argument("--summary", default="outputs/experiments/tinyperson_corner_original/prepare_summary.json")
    parser.add_argument("--keep-uncertain", action="store_true")
    parser.add_argument("--keep-ignore", action="store_true")
    args = parser.parse_args()

    raw_root = Path(args.raw_root)
    out_dir = Path(args.out)
    image_index = build_image_index(raw_root)
    summary: dict[str, Any] = {
        "status": "running",
        "raw_root": raw_root.as_posix(),
        "out": out_dir.as_posix(),
        "class_policy": "collapse_all_categories_to_person",
        "annotation_policy": {
            "corner_windows_materialized": True,
            "keep_uncertain": bool(args.keep_uncertain),
            "keep_ignore": bool(args.keep_ignore),
        },
        "splits": {},
    }

    for split, json_path in [
        ("train", Path(args.train_json)),
        ("val", Path(args.val_json)),
        ("test", Path(args.test_json)),
    ]:
        summary["splits"][split] = {
            "json": json_path.as_posix(),
            **convert_split(
                split,
                json_path,
                out_dir,
                image_index,
                keep_uncertain=args.keep_uncertain,
                keep_ignore=args.keep_ignore,
            ),
        }

    data_yaml = Path(args.data_yaml)
    write_data_yaml(data_yaml, out_dir)
    summary["status"] = "ready"
    summary["data_yaml"] = data_yaml.as_posix()
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
