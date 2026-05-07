"""Evidence token schema shared across detector, graph, and policy modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


Vector = list[float]
Matrix = list[list[float]]


@dataclass(slots=True)
class EvidenceToken:
    """One detected object observation from one UAV frame."""

    token_id: str
    image_id: str
    uav_id: str
    timestamp: float
    bbox_2d: Vector
    class_logits: Vector
    confidence: float
    uncertainty: float
    crop_feature: Vector = field(default_factory=list)
    resolution_level: str = "unknown"
    camera_intrinsic: Matrix = field(default_factory=list)
    camera_extrinsic: Matrix = field(default_factory=list)
    uav_pose: Vector = field(default_factory=list)
    depth_value: float | None = None
    class_id: int | None = None
    object_id: str | None = None
    depth_path: str | None = None
    camera_pose_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def bbox_center(self) -> tuple[float, float]:
        x, y, w, h = self.bbox_2d
        return x + w / 2.0, y + h / 2.0

    @property
    def bbox_area(self) -> float:
        return max(0.0, self.bbox_2d[2]) * max(0.0, self.bbox_2d[3])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidenceToken":
        return cls(**payload)

