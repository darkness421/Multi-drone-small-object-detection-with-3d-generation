"""Convert VisDrone DET annotations to COCO format.

Expected VisDrone row:
<bbox_left>,<bbox_top>,<bbox_width>,<bbox_height>,<score>,<object_category>,<truncation>,<occlusion>
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .common import bbox_area, coco_template, image_size, write_json
except ImportError:
    from common import bbox_area, coco_template, image_size, write_json


VISDRONE_CATEGORIES = [
    {"id": 1, "name": "pedestrian"},
    {"id": 2, "name": "people"},
    {"id": 3, "name": "bicycle"},
    {"id": 4, "name": "car"},
    {"id": 5, "name": "van"},
    {"id": 6, "name": "truck"},
    {"id": 7, "name": "tricycle"},
    {"id": 8, "name": "awning-tricycle"},
    {"id": 9, "name": "bus"},
    {"id": 10, "name": "motor"},
]


def convert_visdrone(image_dir: str | Path, annotation_dir: str | Path) -> dict[str, object]:
    image_dir = Path(image_dir)
    annotation_dir = Path(annotation_dir)
    coco = coco_template(VISDRONE_CATEGORIES)
    ann_id = 1
    for image_id, image_path in enumerate(sorted(image_dir.glob("*")), start=1):
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        width, height = image_size(image_path)
        coco["images"].append(
            {"id": image_id, "file_name": str(image_path), "width": width, "height": height, "metadata": {}}
        )
        anno_path = annotation_dir / f"{image_path.stem}.txt"
        if not anno_path.exists():
            continue
        for line in anno_path.read_text(encoding="utf-8").splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 6:
                continue
            x, y, w, h = [float(v) for v in parts[:4]]
            category_id = int(float(parts[5]))
            if category_id <= 0:
                continue
            coco["annotations"].append(
                {
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": [x, y, w, h],
                    "area": bbox_area([x, y, w, h]),
                    "iscrowd": 0,
                    "object_id": None,
                    "camera_pose": None,
                    "depth_path": None,
                    "metadata": {"truncation": parts[6] if len(parts) > 6 else None, "occlusion": parts[7] if len(parts) > 7 else None},
                }
            )
            ann_id += 1
    return coco


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(convert_visdrone(args.images, args.annotations), args.out)


if __name__ == "__main__":
    main()
