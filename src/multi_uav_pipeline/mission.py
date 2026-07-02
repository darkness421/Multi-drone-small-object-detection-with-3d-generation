"""Mission data structures for synchronized multi-UAV observation."""

from dataclasses import dataclass
from pathlib import Path

from .geo import EnuPose


@dataclass(frozen=True)
class CameraConfig:
    width: int
    height: int
    fov_deg: float


@dataclass(frozen=True)
class UavConfig:
    uav_id: str
    start_pose: EnuPose
    camera: CameraConfig


@dataclass(frozen=True)
class MissionConfig:
    name: str
    frame_rate_hz: int
    output_dir: Path
    uavs: tuple[UavConfig, ...]
