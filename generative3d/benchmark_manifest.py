"""Build Marine City multi-angle benchmark manifests."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class BenchmarkFrame:
    scene_id: str
    frame_id: str
    image_path: str
    pose_path: str | None = None
    depth_path: str | None = None
    uav_id: str = ""
    timestamp: float = 0.0
    view_angle: str = "unknown"
    altitude_m: float | None = None
    split: str = "train"
    holdout_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
        "left": "left_oblique",
        "right": "right_oblique",
    }
    return aliases.get(value, value)


def split_for_angle(view_angle: str, val_angles: set[str], test_angles: set[str]) -> tuple[str, str]:
    angle = normalize_view_angle(view_angle)
    if angle in test_angles:
        return "test_unseen_angle", f"held-out angle: {angle}"
    if angle in val_angles:
        return "val", f"validation angle: {angle}"
    return "train", ""


def _frames_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("frames"), list):
            return payload["frames"]
        if isinstance(payload.get("views"), list):
            scene_id = str(payload.get("scene_id", "scene"))
            frames = []
            for idx, view in enumerate(payload["views"]):
                merged = dict(view)
                merged.setdefault("scene_id", scene_id)
                merged.setdefault("frame_id", f"{scene_id}_{idx:04d}")
                merged.setdefault("timestamp", payload.get("timestamp", 0.0))
                frames.append(merged)
            return frames
    raise ValueError("Input manifest must be a list, a dict with frames, or a dict with views.")


def frame_from_row(row: dict[str, Any], *, val_angles: set[str], test_angles: set[str]) -> BenchmarkFrame:
    metadata = dict(row.get("metadata", {}))
    view_angle = normalize_view_angle(row.get("view_angle") or row.get("view_type") or metadata.get("view_angle"))
    split, reason = split_for_angle(view_angle, val_angles, test_angles)
    scene_id = str(row.get("scene_id") or row.get("episode_id") or metadata.get("scene_id") or "scene")
    frame_id = str(row.get("frame_id") or row.get("image_id") or Path(str(row.get("image_path", "frame"))).stem)
    altitude = row.get("altitude_m", row.get("altitude"))
    return BenchmarkFrame(
        scene_id=scene_id,
        frame_id=frame_id,
        image_path=str(row.get("image_path") or row.get("rgb_path") or ""),
        pose_path=row.get("pose_path") or row.get("camera_pose"),
        depth_path=row.get("depth_path"),
        uav_id=str(row.get("uav_id", "")),
        timestamp=float(row.get("timestamp", 0.0)),
        view_angle=view_angle,
        altitude_m=float(altitude) if altitude is not None else None,
        split=split,
        holdout_reason=reason,
        metadata=metadata,
    )


def build_multiview_benchmark(
    input_manifest: str | Path,
    *,
    val_angles: Iterable[str] = ("side_view",),
    test_angles: Iterable[str] = ("rear_oblique", "right_oblique"),
) -> list[BenchmarkFrame]:
    payload = json.loads(Path(input_manifest).read_text(encoding="utf-8"))
    val = {normalize_view_angle(angle) for angle in val_angles}
    test = {normalize_view_angle(angle) for angle in test_angles}
    return [frame_from_row(row, val_angles=val, test_angles=test) for row in _frames_from_payload(payload)]


def summarize_benchmark(frames: list[BenchmarkFrame]) -> dict[str, Any]:
    by_split: dict[str, int] = {}
    by_angle: dict[str, int] = {}
    by_scene: dict[str, int] = {}
    for frame in frames:
        by_split[frame.split] = by_split.get(frame.split, 0) + 1
        by_angle[frame.view_angle] = by_angle.get(frame.view_angle, 0) + 1
        by_scene[frame.scene_id] = by_scene.get(frame.scene_id, 0) + 1
    return {
        "frame_count": len(frames),
        "scene_count": len(by_scene),
        "by_split": dict(sorted(by_split.items())),
        "by_angle": dict(sorted(by_angle.items())),
        "by_scene": dict(sorted(by_scene.items())),
    }


def write_benchmark(frames: list[BenchmarkFrame], out_path: str | Path) -> dict[str, Any]:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summarize_benchmark(frames), "frames": [frame.to_dict() for frame in frames]}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
