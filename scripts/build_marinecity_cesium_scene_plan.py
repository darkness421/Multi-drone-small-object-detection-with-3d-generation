"""Build a Cesium/Isaac scene placement plan for MarineCity smoke tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.config import resolve_path


OBJECT_OFFSETS_M = [
    (0.0, 0.0),
    (8.0, 2.5),
    (-7.5, -3.0),
    (14.0, -2.0),
    (-13.0, 4.0),
    (22.0, 1.5),
    (-21.0, -2.5),
    (3.5, 9.0),
    (-4.0, -10.5),
    (18.0, 11.0),
]


def load_yaml(path: str | Path) -> dict[str, Any]:
    with resolve_path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping YAML: {path}")
    return data


def read_json(path: str | Path) -> dict[str, Any]:
    json_path = resolve_path(path)
    if not json_path.exists():
        return {}
    return json.loads(json_path.read_text(encoding="utf-8"))


def build_objects(config: dict[str, Any]) -> list[dict[str, Any]]:
    origin = config.get("scene", {}).get("origin", {})
    classes = list(config.get("objects", {}).get("classes", []))
    if not classes:
        classes = ["sedan", "pickup", "van", "pedestrian"]
    base_height = float(origin.get("height_m", 0.0))
    objects: list[dict[str, Any]] = []
    for idx, class_name in enumerate(classes):
        east_m, north_m = OBJECT_OFFSETS_M[idx % len(OBJECT_OFFSETS_M)]
        objects.append(
            {
                "object_id": f"mc_obj_{idx + 1:03d}",
                "class_name": class_name,
                "asset_placeholder": f"assets/objects/{class_name}.usd",
                "position_enu_m": {
                    "east": round(east_m, 3),
                    "north": round(north_m, 3),
                    "up": 0.0,
                },
                "cesium_height_m": base_height,
                "heading_deg": float((idx * 17) % 360),
                "scale": 1.0 if class_name not in {"pedestrian", "worker"} else 0.75,
                "status": "placeholder_asset",
            }
        )
    return objects


def build_uav_altitude_plan(config: dict[str, Any], capture_plan: dict[str, Any]) -> list[dict[str, Any]]:
    views = capture_plan.get("views", [])
    if views:
        return [
            {
                "frame_id": view.get("frame_id"),
                "scene_id": view.get("scene_id"),
                "uav_id": view.get("uav_id"),
                "altitude_m": view.get("altitude_m"),
                "view_angle": view.get("view_angle"),
                "pose": view.get("uav_pose", {}),
            }
            for view in views[:36]
        ]
    capture = config.get("capture", {})
    altitudes = capture.get("altitudes_m", [140, 150, 160])
    return [
        {
            "uav_id": f"uav_{idx + 1:02d}",
            "altitude_m": altitude,
            "view_angle": "planned",
            "pose": {"z": altitude},
        }
        for idx, altitude in enumerate(altitudes)
    ]


def build_plan(config: dict[str, Any], capture_plan: dict[str, Any]) -> dict[str, Any]:
    scene = config.get("scene", {})
    origin = scene.get("origin", {})
    objects = build_objects(config)
    uav_views = build_uav_altitude_plan(config, capture_plan)
    return {
        "name": "marinecity_cesium_isaac_scene_plan",
        "status": "ready_for_gpu_smoke_test",
        "scene": {
            "name": scene.get("name", "CoM3D-MarineCity"),
            "area": scene.get("area", "Busan Haeundae Marine City"),
            "usd_stage": scene.get("usd_stage", "assets/marinecity/marinecity_base.usd"),
            "cesium_origin": {
                "latitude_deg": origin.get("latitude_deg"),
                "longitude_deg": origin.get("longitude_deg"),
                "height_m": origin.get("height_m"),
            },
        },
        "object_placement": {
            "coordinate_frame": "local ENU meters around Cesium origin",
            "count": len(objects),
            "objects": objects,
        },
        "uav_altitude_and_views": {
            "count": len(uav_views),
            "views": uav_views,
        },
        "smoke_test_steps": [
            "Load Cesium georeferenced MarineCity stage.",
            "Place placeholder vehicle/person/marine objects at ENU offsets.",
            "Spawn 2-4 UAV cameras using planned altitudes and view angles.",
            "Verify object ground height, camera pitch/yaw, RGB/depth/mask export paths.",
            "Export one short multi-view clip before full dataset generation.",
        ],
    }


def write_markdown(plan: dict[str, Any], out_path: str | Path) -> Path:
    out = resolve_path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    scene = plan["scene"]
    lines = [
        "# MarineCity Cesium/Isaac Scene Plan",
        "",
        f"- Status: `{plan['status']}`",
        f"- Scene: {scene['name']} ({scene['area']})",
        f"- USD stage: `{scene['usd_stage']}`",
        f"- Origin: `{scene['cesium_origin']}`",
        f"- Objects: {plan['object_placement']['count']} placeholders",
        f"- UAV views: {plan['uav_altitude_and_views']['count']}",
        "",
        "## Next Smoke Test",
        "",
    ]
    for step in plan["smoke_test_steps"]:
        lines.append(f"- {step}")
    lines.extend(["", "## Object Placement Preview", ""])
    for obj in plan["object_placement"]["objects"][:10]:
        pos = obj["position_enu_m"]
        lines.append(
            f"- `{obj['object_id']}` {obj['class_name']}: "
            f"E={pos['east']}m, N={pos['north']}m, height={obj['cesium_height_m']}m"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/sim/marinecity_windows_export.yaml")
    parser.add_argument("--capture-plan", default="outputs/experiments/marinecity_isaac_capture_plan.json")
    parser.add_argument("--out-json", default="outputs/experiments/marinecity_cesium_scene_plan.json")
    parser.add_argument("--out-md", default="outputs/experiments/marinecity_cesium_scene_plan.md")
    args = parser.parse_args()

    config = load_yaml(args.config)
    capture_plan = read_json(args.capture_plan)
    plan = build_plan(config, capture_plan)

    out_json = resolve_path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md = write_markdown(plan, args.out_md)
    print(json.dumps({"json": str(out_json), "markdown": str(out_md), "status": plan["status"]}, indent=2))


if __name__ == "__main__":
    main()
