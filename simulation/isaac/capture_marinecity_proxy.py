"""Tiny real-capture smoke test for the MarineCity proxy USD stage."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from runtime import load_config
from simulation.isaac.build_marinecity_stage import build_stage
from simulation.isaac.export_rgb_depth_pose import start_isaac_simulation_app, write_replicator_template
from simulation.isaac.marinecity_plan import build_capture_plan, write_capture_plan


def _log(message: str) -> None:
    print(f"[marinecity-capture] {message}", flush=True)


def _wait_updates(simulation_app: Any, count: int = 8) -> None:
    for _ in range(count):
        simulation_app.update()


async def _capture_frames_async(rep: Any, frame_count: int) -> None:
    import omni.kit.app  # type: ignore

    for _ in range(10):
        await omni.kit.app.get_app().next_update_async()
    for _ in range(max(frame_count, 1)):
        await rep.orchestrator.step_async(rt_subframes=16, delta_time=0.0, pause_timeline=False)
    await rep.orchestrator.wait_until_complete_async()
    for _ in range(2):
        await omni.kit.app.get_app().next_update_async()


def capture_proxy(config: dict[str, Any], out_dir: Path, active_gpu: int | None = None, frame_count: int = 1) -> dict[str, Any]:
    _log(f"starting Isaac SimulationApp active_gpu={active_gpu}")
    simulation_app = start_isaac_simulation_app(active_gpu=active_gpu)
    _log("SimulationApp started")
    try:
        _log("importing Replicator and USD modules")
        import omni.replicator.core as rep  # type: ignore
        import omni.usd  # type: ignore

        out_dir.mkdir(parents=True, exist_ok=True)
        stage_path = out_dir / "marinecity_proxy_stage.usda"
        _log(f"building USD stage: {stage_path}")
        stage_summary = build_stage(config, stage_path)
        _log(
            "USD stage built "
            f"objects={stage_summary.get('object_count')} cutout_overlays={stage_summary.get('cutout_overlay_count', 0)}"
        )
        write_capture_plan(build_capture_plan(config), out_dir / "capture_plan.json")
        write_replicator_template(config, out_dir / "isaac_replicator_capture_template.py")

        _log("opening USD stage")
        omni.usd.get_context().open_stage(str(stage_path))
        _log("USD stage open requested; waiting for updates")
        _wait_updates(simulation_app, 12)
        _log("stage update wait complete")

        width = int(config.get("camera", {}).get("width", 1280))
        height = int(config.get("camera", {}).get("height", 720))
        camera_specs = []
        for uav in stage_summary.get("uavs", []):
            x, y, z = uav["pose_xyz_rpy"][:3]
            camera_specs.append(
                {
                    "uav_id": uav["uav_id"],
                    "source_camera_prim": uav["camera_prim"],
                    "capture_position_xyz_m": [float(x), float(y), float(z)],
                }
            )
        _log(f"creating {len(camera_specs)} render products at {width}x{height}")
        render_products = [
            rep.create.render_product(spec["source_camera_prim"], (width, height), name=f"rp_{idx + 1:02d}")
            for idx, spec in enumerate(camera_specs)
        ]

        _log("initializing BasicWriter")
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(
            output_dir=str(out_dir / "replicator"),
            rgb=True,
            distance_to_camera=True,
            bounding_box_2d_tight=True,
            bounding_box_3d=True,
            semantic_segmentation=True,
            instance_segmentation=True,
            camera_params=True,
        )
        _log("attaching writer")
        writer.attach(render_products)
        _log("previewing replicator graph")
        rep.orchestrator.preview()
        _log(f"capturing {frame_count} frame(s)")
        asyncio.get_event_loop().run_until_complete(_capture_frames_async(rep, frame_count))
        _log("capture complete; detaching writer")
        writer.detach()
        _wait_updates(simulation_app, 4)
        _log("final update wait complete")

        files = sorted(str(path.relative_to(out_dir)) for path in out_dir.rglob("*") if path.is_file())
        summary = {
            "status": "proxy_capture_smoke_complete",
            "stage_path": str(stage_path),
            "output_dir": str(out_dir),
            "camera_count": len(camera_specs),
            "frame_count": frame_count,
            "render_resolution": [width, height],
            "capture_cameras": camera_specs,
            "file_count": len(files),
            "files": files[:120],
            "stage_summary": stage_summary,
        }
        (out_dir / "proxy_capture_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"wrote summary with {len(files)} files")
        return summary
    finally:
        _log("closing SimulationApp")
        simulation_app.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a tiny Replicator smoke export from the MarineCity proxy stage.")
    parser.add_argument("--config", default="configs/sim/marinecity_isaac_stage1.yaml")
    parser.add_argument("--out-dir", default="/tmp/com3d_isaac_proxy_capture")
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument(
        "--active-gpu",
        type=int,
        default=int(os.environ["ISAAC_ACTIVE_GPU"]) if os.environ.get("ISAAC_ACTIVE_GPU") else None,
    )
    args = parser.parse_args()

    summary = capture_proxy(load_config(args.config), Path(args.out_dir), active_gpu=args.active_gpu, frame_count=args.frames)
    print(f"Proxy capture status: {summary['status']}")
    print(f"Output dir: {summary['output_dir']}")
    print(f"Files: {summary['file_count']}")


if __name__ == "__main__":
    main()
