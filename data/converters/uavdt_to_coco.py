"""Convert UAVDT-style MOT annotations to COCO format."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

try:
    from .common import bbox_area, coco_template, image_size, write_json
except ImportError:
    from common import bbox_area, coco_template, image_size, write_json


UAVDT_CATEGORIES = [
    {"id": 1, "name": "car"},
    {"id": 2, "name": "truck"},
    {"id": 3, "name": "bus"},
]


IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp")


def _frame_candidates(sequence_dir: Path, frame_id: int) -> Iterable[Path]:
    stems = [
        f"img{frame_id:06d}",
        f"img{frame_id:05d}",
        f"{frame_id:06d}",
        f"{frame_id:05d}",
        str(frame_id),
    ]
    for stem in stems:
        for suffix in IMAGE_SUFFIXES:
            yield sequence_dir / f"{stem}{suffix}"


def find_frame_image(sequence_dir: Path, frame_id: int) -> Path:
    for candidate in _frame_candidates(sequence_dir, frame_id):
        if candidate.exists():
            return candidate
    suffix = str(frame_id)
    for candidate in sequence_dir.iterdir() if sequence_dir.exists() else []:
        if candidate.suffix.lower() in IMAGE_SUFFIXES and candidate.stem.lstrip("img").lstrip("0") == suffix:
            return candidate
    return sequence_dir / f"img{frame_id:06d}.jpg"


def parse_category_id(parts: list[str]) -> int:
    # UAVDT MOT-style rows commonly store category at index 8 after
    # out-of-view and occlusion flags. Older local notes used index 7.
    candidates = []
    if len(parts) > 8:
        candidates.append(parts[8])
    if len(parts) > 7:
        candidates.append(parts[7])
    for value in candidates:
        try:
            category_id = int(float(value))
        except ValueError:
            continue
        if category_id in {1, 2, 3}:
            return category_id
    return 1


def convert_uavdt(
    sequence_dir: str | Path,
    annotations_file: str | Path,
    *,
    sequence_name: str | None = None,
    image_id_start: int = 1,
    annotation_id_start: int = 1,
) -> dict[str, object]:
    sequence_dir = Path(sequence_dir)
    sequence_name = sequence_name or sequence_dir.name
    rows = Path(annotations_file).read_text(encoding="utf-8").splitlines()
    coco = coco_template(UAVDT_CATEGORIES)
    image_id_by_frame: dict[int, int] = {}
    ann_id = annotation_id_start
    for row in rows:
        parts = [p.strip() for p in row.split(",")]
        if len(parts) < 7:
            continue
        frame_id = int(float(parts[0]))
        object_id = parts[1]
        x, y, w, h = [float(v) for v in parts[2:6]]
        category_id = parse_category_id(parts)
        if frame_id not in image_id_by_frame:
            image_id_by_frame[frame_id] = image_id_start + len(image_id_by_frame)
            image_path = find_frame_image(sequence_dir, frame_id)
            width, height = image_size(image_path)
            coco["images"].append(
                {
                    "id": image_id_by_frame[frame_id],
                    "file_name": str(image_path),
                    "width": width,
                    "height": height,
                    "metadata": {
                        "sequence": sequence_name,
                        "frame_id": frame_id,
                        "yolo_stem": f"{sequence_name}_{image_path.stem}",
                    },
                }
            )
        coco["annotations"].append(
            {
                "id": ann_id,
                "image_id": image_id_by_frame[frame_id],
                "category_id": category_id,
                "bbox": [x, y, w, h],
                "area": bbox_area([x, y, w, h]),
                "iscrowd": 0,
                "object_id": object_id,
                "camera_pose": None,
                "depth_path": None,
                "metadata": {"sequence": sequence_name, "frame_id": frame_id},
            }
        )
        ann_id += 1
    return coco


def merge_coco_sequences(sequence_payloads: Iterable[dict[str, object]]) -> dict[str, object]:
    merged = coco_template(UAVDT_CATEGORIES)
    for payload in sequence_payloads:
        merged["images"].extend(payload.get("images", []))
        merged["annotations"].extend(payload.get("annotations", []))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-dir", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(convert_uavdt(args.sequence_dir, args.annotations), args.out)


if __name__ == "__main__":
    main()
