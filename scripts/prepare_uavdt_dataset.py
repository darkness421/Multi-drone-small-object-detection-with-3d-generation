"""Prepare UAVDT raw sequences as COCO and Ultralytics YOLO data."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from data.converters.coco_to_yolo import convert_coco_to_yolo
from data.converters.common import write_json
from data.converters.uavdt_to_coco import IMAGE_SUFFIXES, convert_uavdt, merge_coco_sequences
from runtime.config import resolve_path


def maybe_stage_source(source: Path, raw_root: Path) -> None:
    raw_root.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        for child in source.iterdir():
            target = raw_root / child.name
            if target.exists():
                continue
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)
        return
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            archive.extractall(raw_root)
        return
    raise ValueError(f"Unsupported UAVDT source: {source}")


def contains_images(path: Path) -> bool:
    return any(child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES for child in path.iterdir())


def discover_sequence_dirs(images_root: Path) -> list[Path]:
    if not images_root.exists():
        return []
    sequence_dirs = [path for path in images_root.rglob("*") if path.is_dir() and contains_images(path)]
    if contains_images(images_root):
        sequence_dirs.append(images_root)
    return sorted(set(sequence_dirs))


def annotation_candidates(annotations_root: Path, sequence_name: str) -> list[Path]:
    names = [
        f"{sequence_name}.txt",
        f"{sequence_name}_gt.txt",
        f"{sequence_name}_gt_whole.txt",
        f"gt_{sequence_name}.txt",
        f"{sequence_name}/gt.txt",
        f"{sequence_name}/gt/gt.txt",
    ]
    candidates = [annotations_root / name for name in names]
    if annotations_root.exists():
        candidates.extend(
            path
            for path in annotations_root.rglob("*.txt")
            if sequence_name.lower() in path.stem.lower() or path.parent.name.lower() == sequence_name.lower()
        )
    return [path for path in candidates if path.exists()]


def discover_pairs(raw_root: Path) -> list[tuple[str, Path, Path]]:
    images_root = raw_root / "images"
    annotations_root = raw_root / "annotations"
    if not images_root.exists():
        images_root = raw_root
    if not annotations_root.exists():
        annotations_root = raw_root

    pairs: list[tuple[str, Path, Path]] = []
    for sequence_dir in discover_sequence_dirs(images_root):
        sequence_name = sequence_dir.name
        candidates = annotation_candidates(annotations_root, sequence_name)
        if candidates:
            pairs.append((sequence_name, sequence_dir, candidates[0]))
    return pairs


def prepare_uavdt(
    raw_root: Path,
    coco_out: Path,
    yolo_out: Path,
    *,
    copy_images: bool,
    train_ratio: float,
    val_ratio: float,
) -> dict[str, object]:
    pairs = discover_pairs(raw_root)
    if not pairs:
        return {
            "ready": False,
            "raw_root": str(raw_root),
            "sequence_count": 0,
            "message": (
                "No UAVDT image/annotation pairs found. Expected images under "
                "data/raw/UAVDT/images/<sequence>/ and annotations under "
                "data/raw/UAVDT/annotations/<sequence>.txt."
            ),
        }

    payloads = []
    image_id = 1
    ann_id = 1
    for sequence_name, sequence_dir, annotation_file in pairs:
        payload = convert_uavdt(
            sequence_dir,
            annotation_file,
            sequence_name=sequence_name,
            image_id_start=image_id,
            annotation_id_start=ann_id,
        )
        payloads.append(payload)
        image_id += len(payload.get("images", []))
        ann_id += len(payload.get("annotations", []))

    merged = merge_coco_sequences(payloads)
    write_json(merged, coco_out)
    data_yaml = convert_coco_to_yolo(coco_out, yolo_out, copy_images=copy_images, train_ratio=train_ratio, val_ratio=val_ratio)
    return {
        "ready": True,
        "raw_root": str(raw_root),
        "coco_out": str(coco_out),
        "yolo_out": str(yolo_out),
        "data_yaml": str(data_yaml),
        "sequence_count": len(pairs),
        "image_count": len(merged.get("images", [])),
        "annotation_count": len(merged.get("annotations", [])),
        "sequences": [{"name": name, "images": str(seq_dir), "annotations": str(ann)} for name, seq_dir, ann in pairs],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare UAVDT as COCO and YOLO data.")
    parser.add_argument("--source", default="", help="Optional local UAVDT folder or zip to stage into raw-root.")
    parser.add_argument("--raw-root", default="data/raw/UAVDT")
    parser.add_argument("--coco-out", default="data/processed/uavdt_coco.json")
    parser.add_argument("--yolo-out", default="data/processed/uavdt_yolo")
    parser.add_argument("--copy-images", action="store_true")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--summary", default="outputs/experiments/uavdt_prepare_summary.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    raw_root = resolve_path(args.raw_root)
    if args.source:
        maybe_stage_source(resolve_path(args.source), raw_root)

    summary = prepare_uavdt(
        raw_root,
        resolve_path(args.coco_out),
        resolve_path(args.yolo_out),
        copy_images=args.copy_images,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
    )
    summary_path = resolve_path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {summary_path}")
    if args.strict and not summary.get("ready"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
