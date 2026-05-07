"""Convert CoM3D-MarineCity annotation JSON to COCO and evidence JSON.

TODO:
- Add batch conversion for full dataset folders.
- Add segmentation and bbox3d export after Isaac Replicator integration.
- Add optional official COCO validation once dependencies are allowed.
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
    "rescue_vehicle": 7,
    "pedestrian": 8,
    "worker": 9,
    "small_boat": 10,
    "debris": 11
}

REQUIRED_TOP_LEVEL = (
    "scene_id",
    "timestamp",
    "uav_group",
    "object_id",
    "coarse_class",
    "fine_class",
    "ambiguity_type",
    "missing_evidence",
    "recommended_next_view",
    "views",
    "location_3d",
    "occlusion_level",
    "difficulty",
)

REQUIRED_VIEW_FIELDS = (
    "uav_id",
    "view_type",
    "altitude",
    "image_path",
    "depth_path",
    "bbox_2d",
    "camera_pose",
    "width",
    "height",
)


def load_json(path: Path) -> Any:
    """Load JSON from a path."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_annotation(input_data: dict[str, Any]) -> None:
    """Validate required CoM3D-MarineCity annotation fields."""
    for key in REQUIRED_TOP_LEVEL:
        if key not in input_data:
            raise ValueError(f"missing required top-level field: {key}")
    if input_data["fine_class"] not in CATEGORY_NAME_TO_ID:
        raise ValueError(f"unknown fine_class: {input_data['fine_class']}")
    if not isinstance(input_data["views"], list) or not input_data["views"]:
        raise ValueError("views must be a non-empty list")
    if len(input_data["location_3d"]) != 3:
        raise ValueError("location_3d must have exactly 3 values")
    for view_index, view in enumerate(input_data["views"]):
        for key in REQUIRED_VIEW_FIELDS:
            if key not in view:
                raise ValueError(f"view {view_index} missing required field: {key}")
        if len(view["bbox_2d"]) != 4:
            raise ValueError(f"view {view_index} bbox_2d must have exactly 4 values")
        x1, y1, x2, y2 = view["bbox_2d"]
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"view {view_index} bbox_2d has invalid coordinates")
        if view["width"] <= 0 or view["height"] <= 0:
            raise ValueError(f"view {view_index} width/height must be positive")


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
    validate_annotation(input_data)
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
        "coarse_class": input_data.get("coarse_class"),
        "fine_class": input_data.get("fine_class"),
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
    parser.add_argument("--out-coco", type=Path)
    parser.add_argument("--out-evidence", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run conversion from the command line."""
    args = parse_args()
    input_data = load_json(args.input)
    validate_annotation(input_data)
    if args.validate_only:
        print(f"valid annotation: {args.input}")
        return
    if args.out_coco is None or args.out_evidence is None:
        raise SystemExit("--out-coco and --out-evidence are required unless --validate-only is used")
    coco, evidence = convert(input_data)
    args.out_coco.parent.mkdir(parents=True, exist_ok=True)
    args.out_evidence.parent.mkdir(parents=True, exist_ok=True)
    args.out_coco.write_text(json.dumps(coco, indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_evidence.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out_coco} and {args.out_evidence}")


if __name__ == "__main__":
    main()
