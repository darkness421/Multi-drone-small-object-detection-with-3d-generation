"""Convert UAVDT-style MOT annotations to COCO format."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .common import bbox_area, coco_template, write_json
except ImportError:
    from common import bbox_area, coco_template, write_json


UAVDT_CATEGORIES = [
    {"id": 1, "name": "car"},
    {"id": 2, "name": "truck"},
    {"id": 3, "name": "bus"},
]


def convert_uavdt(sequence_dir: str | Path, annotations_file: str | Path) -> dict[str, object]:
    sequence_dir = Path(sequence_dir)
    rows = Path(annotations_file).read_text(encoding="utf-8").splitlines()
    coco = coco_template(UAVDT_CATEGORIES)
    image_id_by_frame: dict[int, int] = {}
    ann_id = 1
    for row in rows:
        parts = [p.strip() for p in row.split(",")]
        if len(parts) < 7:
            continue
        frame_id = int(float(parts[0]))
        object_id = parts[1]
        x, y, w, h = [float(v) for v in parts[2:6]]
        category_id = int(float(parts[7])) if len(parts) > 7 and parts[7] else 1
        if frame_id not in image_id_by_frame:
            image_id_by_frame[frame_id] = len(image_id_by_frame) + 1
            image_path = sequence_dir / f"{frame_id:06d}.jpg"
            coco["images"].append({"id": image_id_by_frame[frame_id], "file_name": str(image_path), "metadata": {}})
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
                "metadata": {"frame_id": frame_id},
            }
        )
        ann_id += 1
    return coco


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-dir", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(convert_uavdt(args.sequence_dir, args.annotations), args.out)


if __name__ == "__main__":
    main()
