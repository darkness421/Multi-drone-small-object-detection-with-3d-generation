"""Convert CoM3D-MarineCity annotation JSON to COCO and evidence JSON.

TODO:
- Add full category registry.
- Validate multi-view input schema.
- Preserve links to Isaac sensor outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CATEGORY_NAME_TO_ID = {
    "sedan": 1,
    "pickup": 2,
    "van": 3,
    "ambulance": 4,
    "police_car": 5,
    "truck": 6,
    "pedestrian": 7,
    "worker": 8,
    "small_boat": 9,
    "debris": 10
}


def load_json(path: Path) -> Any:
    """Load JSON from a path."""
    return json.loads(path.read_text(encoding="utf-8"))


def image_record(image_id: int, view: dict[str, Any]) -> dict[str, Any]:
    """Create a minimal COCO image record."""
    return {
        "id": image_id,
        "file_name": view["image_path"],
        "width": view.get("width", 0),
        "height": view.get("height", 0),
        "uav_id": view.get("uav_id"),
        "view_type": view.get("view_type")
    }


def annotation_record(annotation_id: int, image_id: int, item: dict[str, Any], view: dict[str, Any]) -> dict[str, Any]:
    """Create a COCO annotation record from one object view."""
    x1, y1, x2, y2 = view["bbox_2d"]
    width = max(0, x2 - x1)
    height = max(0, y2 - y1)
    return {
        "id": annotation_id,
        "image_id": image_id,
        "category_id": CATEGORY_NAME_TO_ID.get(item["fine_class"], 0),
        "bbox": [x1, y1, width, height],
        "area": width * height,
        "iscrowd": 0,
        "object_id": item["object_id"]
    }


def convert(input_data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert a CoM3D-MarineCity annotation to COCO and evidence JSON."""
    images: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    annotation_id = 1

    for image_id, view in enumerate(input_data.get("views", []), start=1):
        images.append(image_record(image_id, view))
        annotations.append(annotation_record(annotation_id, image_id, input_data, view))
        annotation_id += 1

    categories = [
        {"id": category_id, "name": name}
        for name, category_id in sorted(CATEGORY_NAME_TO_ID.items(), key=lambda item: item[1])
    ]
    coco = {
        "images": images,
        "annotations": annotations,
        "categories": categories
    }
    evidence = {
        "scene_id": input_data.get("scene_id"),
        "object_id": input_data.get("object_id"),
        "uav_group": input_data.get("uav_group", []),
        "views": input_data.get("views", []),
        "location_3d": input_data.get("location_3d"),
        "ambiguity_type": input_data.get("ambiguity_type"),
        "missing_evidence": input_data.get("missing_evidence", []),
        "recommended_next_view": input_data.get("recommended_next_view", {}),
        "occlusion_level": input_data.get("occlusion_level"),
        "difficulty": input_data.get("difficulty")
    }
    return coco, evidence


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Convert MarineCity annotations to COCO.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-coco", type=Path, required=True)
    parser.add_argument("--out-evidence", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    """Run conversion from the command line."""
    args = parse_args()
    coco, evidence = convert(load_json(args.input))
    args.out_coco.parent.mkdir(parents=True, exist_ok=True)
    args.out_evidence.parent.mkdir(parents=True, exist_ok=True)
    args.out_coco.write_text(json.dumps(coco, indent=2), encoding="utf-8")
    args.out_evidence.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"wrote {args.out_coco} and {args.out_evidence}")


if __name__ == "__main__":
    main()

