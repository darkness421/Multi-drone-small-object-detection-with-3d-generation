"""Loader for custom CoM3D multi-view JSON annotations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .common import bbox_area, coco_template, write_json
except ImportError:
    from common import bbox_area, coco_template, write_json


def load_com3d(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "samples" in payload:
        return list(payload["samples"])
    if isinstance(payload, list):
        return payload
    return [payload]


def com3d_to_coco(path: str | Path) -> dict[str, Any]:
    samples = load_com3d(path)
    category_by_name: dict[str, int] = {}
    coco = coco_template()
    ann_id = 1
    image_id = 1
    for sample in samples:
        for obj in sample.get("objects", [sample]):
            cls_name = obj.get("fine_class") or obj.get("coarse_class") or "object"
            category_by_name.setdefault(cls_name, len(category_by_name) + 1)
            for view in obj.get("views", sample.get("views", [])):
                bbox = view.get("bbox_2d")
                if bbox is None:
                    continue
                coco["images"].append(
                    {
                        "id": image_id,
                        "file_name": view.get("image_path", ""),
                        "camera_intrinsic": view.get("camera_intrinsic"),
                        "camera_extrinsic": view.get("camera_extrinsic"),
                        "camera_pose": view.get("camera_pose"),
                        "depth_path": view.get("depth_path"),
                        "metadata": {
                            "scene_id": sample.get("scene_id"),
                            "uav_id": view.get("uav_id"),
                            "timestamp": sample.get("timestamp", view.get("timestamp")),
                        },
                    }
                )
                coco["annotations"].append(
                    {
                        "id": ann_id,
                        "image_id": image_id,
                        "category_id": category_by_name[cls_name],
                        "bbox": bbox,
                        "area": bbox_area(bbox),
                        "iscrowd": 0,
                        "object_id": obj.get("object_id"),
                        "camera_pose": view.get("camera_pose"),
                        "depth_path": view.get("depth_path"),
                        "metadata": {
                            "ambiguity_type": obj.get("ambiguity_type"),
                            "missing_evidence": obj.get("missing_evidence", []),
                            "location_3d": obj.get("location_3d"),
                        },
                    }
                )
                ann_id += 1
                image_id += 1
    coco["categories"] = [{"id": idx, "name": name} for name, idx in sorted(category_by_name.items(), key=lambda x: x[1])]
    return coco


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(com3d_to_coco(args.input), args.out)


if __name__ == "__main__":
    main()
