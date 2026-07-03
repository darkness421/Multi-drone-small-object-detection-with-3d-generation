"""Build a fresh Isaac/Cesium targeted re-observation camera plan.

The plan is generated from the current viewer160 cross-view evidence graph.
Each hypothesis routed to ``targeted_reobserve`` gets one fresh camera frame
from a missing UAV direction. The output is consumed by
``simulation/isaac/capture_realcities_multiuav.py --camera-plan``.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "outputs/graphs/marinecity_viewer160_crossview_evidence_graph/hypotheses.json"
DEFAULT_OUT = ROOT / "outputs/experiments/marinecity_targeted_reobservation_plan_20260703.json"
DEFAULT_SPLIT_DIR = ROOT / "outputs/experiments/marinecity_targeted_reobservation_plan_20260703"

BASE_EYES = {
    "uav_01": [8.0, -2.0, 140.0],
    "uav_02": [-2.0, 3.0, 150.0],
    "uav_03": [18.0, -15.0, 160.0],
}
BASE_TARGET = [-22.0, -13.0, 15.0]


def normalize_xy(dx: float, dy: float) -> tuple[float, float]:
    norm = math.hypot(dx, dy)
    if norm <= 1e-9:
        return 1.0, 0.0
    return dx / norm, dy / norm


def camera_eye_for_target(uav_id: str, target: list[float], *, radius_m: float) -> list[float]:
    base_eye = BASE_EYES[uav_id]
    ux, uy = normalize_xy(base_eye[0] - BASE_TARGET[0], base_eye[1] - BASE_TARGET[1])
    return [float(target[0] + ux * radius_m), float(target[1] + uy * radius_m), float(base_eye[2])]


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    hypotheses: list[dict[str, Any]] = json.loads(args.graph.read_text(encoding="utf-8"))
    frames: list[dict[str, Any]] = []
    routed = [h for h in hypotheses if h.get("recommended_action") == "targeted_reobserve"]
    for index, hyp in enumerate(routed, start=1):
        missing = list(hyp.get("missing_uav_ids") or [])
        if not missing:
            continue
        uav_id = str(missing[0])
        center = list(hyp.get("center_scene_units") or [0.0, 0.0, 0.0])
        target = [float(center[0]), float(center[1]), float(args.target_z)]
        eye = camera_eye_for_target(uav_id, target, radius_m=args.radius_m)
        frame_id = f"reobs_{hyp['scenario_short'].lower()}_{hyp['hypothesis_id'].lower()}_{uav_id}"
        frames.append(
            {
                "frame_id": frame_id,
                "frame_index": index,
                "image_id": frame_id,
                "hypothesis_id": hyp["hypothesis_id"],
                "scenario_short": hyp["scenario_short"],
                "scenario_id": str(hyp.get("scenario_id", "")),
                "class_name": str(hyp.get("class_name", "")),
                "uav_id": uav_id,
                "requested_missing_uav_ids": missing,
                "before_uav_ids": list(hyp.get("uav_ids") or []),
                "before_view_count": int(hyp.get("view_count", 0) or 0),
                "before_ambiguity": float(hyp.get("ambiguity_score", 0.0) or 0.0),
                "before_action": str(hyp.get("recommended_action", "")),
                "target_scene_units": target,
                "camera_position": eye,
                "altitude_m": float(eye[2]),
                "look_at_target": target,
                "view_angle": "targeted_reobservation_missing_view",
                "weather": "clear",
                "lighting": "day",
            }
        )
    plan = {
        "status": "marinecity_targeted_reobservation_plan_ready",
        "source_graph": str(args.graph),
        "frame_count": len(frames),
        "radius_m": args.radius_m,
        "target_z": args.target_z,
        "base_camera_profile": "viewer160",
        "claim_boundary": "Fresh Isaac/Cesium capture plan for targeted missing-view re-observation.",
        "frames": frames,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.split_dir:
        args.split_dir.mkdir(parents=True, exist_ok=True)
        for scenario_short in sorted({str(frame["scenario_short"]) for frame in frames}):
            scenario_frames = [frame for frame in frames if frame["scenario_short"] == scenario_short]
            scenario_plan = dict(plan)
            scenario_plan["status"] = "marinecity_targeted_reobservation_scenario_plan_ready"
            scenario_plan["scenario_short"] = scenario_short
            scenario_plan["frame_count"] = len(scenario_frames)
            scenario_plan["frames"] = scenario_frames
            scenario_out = args.split_dir / f"targeted_reobservation_plan_{scenario_short}.json"
            scenario_out.write_text(json.dumps(scenario_plan, indent=2, ensure_ascii=False), encoding="utf-8")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MarineCity targeted re-observation camera plan.")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--split-dir", type=Path, default=DEFAULT_SPLIT_DIR)
    parser.add_argument("--radius-m", type=float, default=45.0)
    parser.add_argument("--target-z", type=float, default=15.0)
    args = parser.parse_args()
    print(json.dumps(build_plan(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
