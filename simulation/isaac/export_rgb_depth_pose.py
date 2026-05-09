"""Export RGB/depth/pose annotation manifests from Isaac Sim.

This module is intentionally importable outside Isaac Sim. Use --dry-run on a
normal Python environment to validate paths, config loading, and output schema.
Inside Isaac Sim, replace the dry-run frame generator with Replicator/ROS2
capture calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime import load_config, prepare_run_dir, setup_logging
from runtime.config import resolve_path
from simulation.schema import SimFrameAnnotation, SimObjectAnnotation, UAVPose


def make_dry_run_frame(scene_id: str, uav_id: str, timestamp: float = 0.0) -> SimFrameAnnotation:
    return SimFrameAnnotation(
        image_id=f"{scene_id}_{uav_id}_t{timestamp:.2f}",
        uav_id=uav_id,
        timestamp=timestamp,
        camera_intrinsic=[[960.0, 0.0, 640.0], [0.0, 960.0, 360.0], [0.0, 0.0, 1.0]],
        camera_extrinsic=[[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 80.0], [0.0, 0.0, 0.0, 1.0]],
        uav_pose=UAVPose(x=0.0, y=0.0, z=80.0, roll=0.0, pitch=-45.0, yaw=120.0),
        rgb_path=f"images/{scene_id}/{uav_id}_rgb.png",
        depth_path=f"depth/{scene_id}/{uav_id}_depth.npy",
        objects=[
            SimObjectAnnotation(
                object_id="obj_0001",
                class_name="van",
                bbox_2d=[512.0, 331.0, 24.0, 18.0],
                bbox_3d=[0.0, 0.0, 0.0, 4.5, 1.8, 1.7, 0.0],
                visibility=0.62,
                occlusion_level="medium",
                view_angle="side",
                pixel_size=24.0,
                distance=82.3,
                ambiguity_reason="missing_side_view",
                recommended_next_view="closer side view",
            )
        ],
    )


def build_dry_run_manifest(config: dict[str, Any]) -> dict[str, Any]:
    frames = []
    for scene in config.get("scenes", []):
        scene_id = scene["scene_id"]
        for idx in range(int(scene.get("uav_count", 1))):
            frames.append(make_dry_run_frame(scene_id, f"uav_{idx + 1:02d}").to_dict())
    return {
        "dataset": "CoM3D-UAV-Sim",
        "mode": "dry_run",
        "config_name": config.get("name", "isaac_export"),
        "frames": frames,
    }


def write_manifest(manifest: dict[str, Any], out_path: str | Path) -> Path:
    out_path = resolve_path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CoM3D-UAV-Sim RGB/depth/pose manifest.")
    parser.add_argument("--config", default="configs/sim/isaac_export.yaml")
    parser.add_argument("--out", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Generate a schema-valid manifest without Isaac imports.")
    args = parser.parse_args()

    config = load_config(args.config)
    run_dir = prepare_run_dir("isaac_export", output_root=config.get("output_root", "outputs/isaac_exports"))
    logger = setup_logging(run_dir / "logs" / "export.log")
    out_path = Path(args.out) if args.out else run_dir / "manifest.json"

    if args.dry_run:
        manifest = build_dry_run_manifest(config)
        write_manifest(manifest, out_path)
        logger.info("Wrote dry-run Isaac manifest to %s", out_path)
        print(out_path)
        return

    try:
        import omni.replicator.core as rep  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Run this script with Isaac Sim python.bat, or use --dry-run outside Isaac Sim.") from exc

    raise NotImplementedError("Isaac runtime capture is scaffolded; implement Replicator capture calls here.")


if __name__ == "__main__":
    main()

