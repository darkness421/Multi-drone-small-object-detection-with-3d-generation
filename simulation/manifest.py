"""Simple manifest schema for Isaac/Cesium multi-UAV episodes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SimulationFrame:
    image_path: str
    uav_id: str
    timestamp: float
    depth_path: str | None = None
    camera_intrinsic: list[list[float]] = field(default_factory=list)
    camera_extrinsic: list[list[float]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

