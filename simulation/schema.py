"""CoM3D-UAV-Sim annotation schema helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class UAVPose:
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float


@dataclass(slots=True)
class SimObjectAnnotation:
    object_id: str
    class_name: str
    bbox_2d: list[float]
    bbox_3d: list[float] | None = None
    mask: str | None = None
    visibility: float = 1.0
    occlusion_level: str = "none"
    view_angle: str = "unknown"
    pixel_size: float = 0.0
    distance: float = 0.0
    ambiguity_reason: str | None = None
    recommended_next_view: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["class"] = payload.pop("class_name")
        return payload


@dataclass(slots=True)
class SimFrameAnnotation:
    image_id: str
    uav_id: str
    timestamp: float
    camera_intrinsic: list[list[float]]
    camera_extrinsic: list[list[float]]
    uav_pose: UAVPose
    objects: list[SimObjectAnnotation] = field(default_factory=list)
    depth_path: str | None = None
    rgb_path: str | None = None
    scene_id: str = ""
    frame_id: str = ""
    pose_path: str | None = None
    view_angle: str = "unknown"
    altitude_m: float | None = None
    weather: str = "clear"
    lighting: str = "day"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "frame_id": self.frame_id or self.image_id,
            "scene_id": self.scene_id,
            "uav_id": self.uav_id,
            "timestamp": self.timestamp,
            "camera_intrinsic": self.camera_intrinsic,
            "camera_extrinsic": self.camera_extrinsic,
            "uav_pose": asdict(self.uav_pose),
            "depth_path": self.depth_path,
            "rgb_path": self.rgb_path,
            "pose_path": self.pose_path,
            "view_angle": self.view_angle,
            "altitude_m": self.altitude_m,
            "weather": self.weather,
            "lighting": self.lighting,
            "metadata": self.metadata,
            "objects": [obj.to_dict() for obj in self.objects],
        }
