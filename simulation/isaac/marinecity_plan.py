"""Marine City multi-UAV capture planning helpers.

The functions in this module do not import Isaac Sim. They create a deterministic
capture plan that can be validated on Windows with normal Python, then consumed
by an Isaac/Replicator runtime script later.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.config import resolve_path
from simulation.schema import SimFrameAnnotation, SimObjectAnnotation, UAVPose


@dataclass(slots=True)
class PlannedUAVView:
    scene_id: str
    frame_id: str
    image_id: str
    uav_id: str
    timestamp: float
    altitude_m: float
    view_angle: str
    weather: str
    lighting: str
    object_density: str
    uav_pose: UAVPose
    camera_intrinsic: list[list[float]]
    camera_extrinsic: list[list[float]]
    rgb_path: str
    depth_path: str
    pose_path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_frame(self, objects: list[SimObjectAnnotation]) -> SimFrameAnnotation:
        return SimFrameAnnotation(
            image_id=self.image_id,
            frame_id=self.frame_id,
            scene_id=self.scene_id,
            uav_id=self.uav_id,
            timestamp=self.timestamp,
            camera_intrinsic=self.camera_intrinsic,
            camera_extrinsic=self.camera_extrinsic,
            uav_pose=self.uav_pose,
            objects=objects,
            rgb_path=self.rgb_path,
            depth_path=self.depth_path,
            pose_path=self.pose_path,
            view_angle=self.view_angle,
            altitude_m=self.altitude_m,
            weather=self.weather,
            lighting=self.lighting,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["uav_pose"] = asdict(self.uav_pose)
        return payload


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_/-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "item"


def normalize_view_angle(value: str | None) -> str:
    if not value:
        return "unknown"
    value = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "top": "nadir",
        "top_down": "nadir",
        "front": "front_oblique",
        "rear": "rear_oblique",
        "side": "side_view",
        "sideview": "side_view",
        "left": "left_oblique",
        "right": "right_oblique",
        "close": "close_oblique",
        "close_up": "close_oblique",
    }
    return aliases.get(value, value)


def _as_list(value: Any, default: list[Any]) -> list[Any]:
    if value is None:
        return default
    if isinstance(value, list):
        return value
    return [value]


def _camera_intrinsic(config: dict[str, Any]) -> list[list[float]]:
    camera = config.get("camera", {})
    width = float(camera.get("width", 1920))
    height = float(camera.get("height", 1080))
    focal = float(camera.get("focal_px", min(width, height)))
    return [[focal, 0.0, width / 2.0], [0.0, focal, height / 2.0], [0.0, 0.0, 1.0]]


def _pose_for_view(index: int, count: int, altitude: float, view_angle: str, radius_scale: float) -> UAVPose:
    angle_rad = (2.0 * math.pi * index / max(count, 1)) + math.radians(20.0)
    radius = max(altitude * radius_scale, 20.0)
    if view_angle == "nadir":
        pitch = -90.0
        radius = max(radius * 0.2, 5.0)
    elif "side" in view_angle:
        pitch = -18.0
        radius *= 1.2
    elif "rear" in view_angle or "front" in view_angle or "left" in view_angle or "right" in view_angle:
        pitch = -35.0
    else:
        pitch = -45.0
    x = radius * math.cos(angle_rad)
    y = radius * math.sin(angle_rad)
    yaw = math.degrees(math.atan2(-y, -x))
    return UAVPose(x=round(x, 3), y=round(y, 3), z=round(altitude, 3), roll=0.0, pitch=round(pitch, 3), yaw=round(yaw, 3))


def _extrinsic_from_pose(pose: UAVPose) -> list[list[float]]:
    # Placeholder world-to-camera matrix. The Isaac runtime should replace this
    # with calibrated camera extrinsics from camera_params.
    return [
        [1.0, 0.0, 0.0, pose.x],
        [0.0, 1.0, 0.0, pose.y],
        [0.0, 0.0, 1.0, pose.z],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _sample_objects(scene: dict[str, Any], classes: list[str], ambiguity_pairs: list[list[str]]) -> list[SimObjectAnnotation]:
    density = str(scene.get("object_density", scene.get("density", "medium")))
    count = {"sparse": 1, "medium": 2, "dense": 3}.get(density, 2)
    objects: list[SimObjectAnnotation] = []
    for idx in range(count):
        class_name = classes[idx % len(classes)] if classes else "car"
        pair = ambiguity_pairs[idx % len(ambiguity_pairs)] if ambiguity_pairs else [class_name, class_name]
        objects.append(
            SimObjectAnnotation(
                object_id=f"obj_{idx + 1:04d}",
                class_name=class_name,
                bbox_2d=[512.0 + idx * 42.0, 331.0 + idx * 19.0, 24.0 + idx * 3.0, 18.0 + idx * 2.0],
                bbox_3d=[float(idx), 0.0, 0.0, 4.5, 1.8, 1.7, 0.0],
                visibility=max(0.35, 0.72 - idx * 0.12),
                occlusion_level="medium" if idx else "low",
                view_angle="planned",
                pixel_size=24.0 + idx * 3.0,
                distance=82.3 + idx * 8.0,
                ambiguity_reason=f"{pair[0]}_vs_{pair[1]}",
                recommended_next_view="closer side view",
            )
        )
    return objects


def build_capture_plan(config: dict[str, Any]) -> list[PlannedUAVView]:
    capture = config.get("capture", {})
    altitudes = [float(v) for v in _as_list(capture.get("altitudes_m"), [60.0, 100.0])]
    view_angles = [normalize_view_angle(str(v)) for v in _as_list(capture.get("view_angles"), ["nadir", "front_oblique", "side_view"])]
    timestamps = [float(v) for v in _as_list(capture.get("timestamps"), [0.0])]
    weather_values = [str(v) for v in _as_list(capture.get("weather"), ["clear"])]
    lighting_values = [str(v) for v in _as_list(capture.get("lighting"), ["day"])]
    radius_scale = float(capture.get("radius_scale", 0.9))
    intrinsic = _camera_intrinsic(config)

    views: list[PlannedUAVView] = []
    for scene in config.get("scenes", []):
        scene_id = slugify(str(scene.get("scene_id") or scene.get("id") or "scene"))
        uav_count = int(scene.get("uav_count", capture.get("default_uav_count", 3)))
        density = str(scene.get("object_density", scene.get("density", "medium")))
        for ts_idx, timestamp in enumerate(timestamps):
            weather = weather_values[ts_idx % len(weather_values)]
            lighting = lighting_values[ts_idx % len(lighting_values)]
            for uav_idx in range(uav_count):
                altitude = altitudes[uav_idx % len(altitudes)]
                view_angle = view_angles[uav_idx % len(view_angles)]
                uav_id = f"uav_{uav_idx + 1:02d}"
                frame_id = f"{scene_id}_{uav_id}_t{ts_idx:03d}_{view_angle}"
                pose = _pose_for_view(uav_idx, uav_count, altitude, view_angle, radius_scale)
                views.append(
                    PlannedUAVView(
                        scene_id=scene_id,
                        frame_id=frame_id,
                        image_id=frame_id,
                        uav_id=uav_id,
                        timestamp=timestamp,
                        altitude_m=altitude,
                        view_angle=view_angle,
                        weather=weather,
                        lighting=lighting,
                        object_density=density,
                        uav_pose=pose,
                        camera_intrinsic=intrinsic,
                        camera_extrinsic=_extrinsic_from_pose(pose),
                        rgb_path=f"images/{scene_id}/{frame_id}_rgb.png",
                        depth_path=f"depth/{scene_id}/{frame_id}_depth.npy",
                        pose_path=f"poses/{scene_id}/{frame_id}_pose.json",
                        metadata={
                            "scene_description": scene.get("description", ""),
                            "weather": weather,
                            "lighting": lighting,
                            "object_density": density,
                            "view_angle": view_angle,
                            "altitude_m": altitude,
                        },
                    )
                )
    return views


def build_dry_run_manifest(config: dict[str, Any]) -> dict[str, Any]:
    classes = list(config.get("objects", {}).get("classes", []))
    ambiguity_pairs = list(config.get("objects", {}).get("ambiguity_pairs", []))
    views = build_capture_plan(config)
    frames = []
    for view in views:
        objects = _sample_objects({"object_density": view.object_density}, classes, ambiguity_pairs)
        frames.append(view.to_frame(objects).to_dict())
    return {
        "dataset": config.get("dataset_name", "CoM3D-MarineCity"),
        "mode": "dry_run",
        "config_name": config.get("name", "isaac_export"),
        "summary": summarize_plan(views),
        "frames": frames,
    }


def summarize_plan(views: list[PlannedUAVView]) -> dict[str, Any]:
    by_scene: dict[str, int] = {}
    by_angle: dict[str, int] = {}
    by_weather: dict[str, int] = {}
    by_altitude: dict[str, int] = {}
    for view in views:
        by_scene[view.scene_id] = by_scene.get(view.scene_id, 0) + 1
        by_angle[view.view_angle] = by_angle.get(view.view_angle, 0) + 1
        by_weather[view.weather] = by_weather.get(view.weather, 0) + 1
        alt_key = f"{view.altitude_m:g}m"
        by_altitude[alt_key] = by_altitude.get(alt_key, 0) + 1
    return {
        "planned_frame_count": len(views),
        "scene_count": len(by_scene),
        "by_scene": dict(sorted(by_scene.items())),
        "by_view_angle": dict(sorted(by_angle.items())),
        "by_weather": dict(sorted(by_weather.items())),
        "by_altitude": dict(sorted(by_altitude.items())),
    }


def write_capture_plan(views: list[PlannedUAVView], out_path: str | Path) -> Path:
    out = resolve_path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summarize_plan(views), "views": [view.to_dict() for view in views]}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out

