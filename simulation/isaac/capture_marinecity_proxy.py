"""Capture RGB and detector GT directly from the MarineCity proxy USD stage."""

from __future__ import annotations

import argparse
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


def _scene_variant_transform(
    variant_index: int, strategy: str = "legacy"
) -> tuple[float, float, float]:
    """Return a deterministic transform without changing legacy captures."""

    if variant_index < 0:
        raise ValueError("variant_index must be non-negative")
    if variant_index == 0:
        return 0.0, 0.0, 0.0
    if strategy == "legacy":
        return (
            float(((variant_index * 17) % 31) - 15),
            float(((variant_index * 7) % 13) - 6),
            float(((variant_index * 11) % 11) - 5),
        )
    if strategy == "balanced":
        return (
            float((variant_index * 47) % 360),
            float(((variant_index * 7) % 23) - 11),
            float(((variant_index * 11) % 29) - 14),
        )
    raise ValueError(f"unknown scene variant strategy: {strategy}")


def _apply_scene_variant(
    stage: Any, variant_index: int, strategy: str = "legacy"
) -> dict[str, float | int | str]:
    """Move the full object layout deterministically between synthetic scenes."""

    from pxr import Gf, UsdGeom

    angle_deg, offset_x, offset_y = _scene_variant_transform(variant_index, strategy)
    for prim_path in ("/World/Objects", "/World/CutoutOverlays"):
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            continue
        xformable = UsdGeom.Xformable(prim)
        xformable.ClearXformOpOrder()
        xformable.AddTranslateOp().Set(Gf.Vec3d(offset_x, offset_y, 0.0))
        xformable.AddRotateZOp().Set(angle_deg)
    return {
        "scene_variant_index": variant_index,
        "scene_variant_strategy": strategy,
        "object_layout_rotation_deg": angle_deg,
        "object_layout_offset_x_m": offset_x,
        "object_layout_offset_y_m": offset_y,
    }


def _open_stage_checked(
    simulation_app: Any,
    context: Any,
    stage_path: Path,
    camera_specs: list[dict[str, Any]],
    attempts: int = 12,
) -> None:
    """Open a freshly written stage after Kit startup and verify its cameras."""

    for attempt in range(1, attempts + 1):
        _wait_updates(simulation_app, 12)
        opened = bool(context.open_stage(str(stage_path)))
        _log(f"stage open attempt {attempt}/{attempts}: opened={opened}")
        if not opened:
            continue

        _wait_updates(simulation_app, 16)
        stage = context.get_stage()
        missing = [
            spec["source_camera_prim"]
            for spec in camera_specs
            if stage is None or not stage.GetPrimAtPath(spec["source_camera_prim"]).IsValid()
        ]
        if not missing:
            return
        _log(f"stage opened but camera prims are not ready: {missing}")

    raise RuntimeError(
        f"failed to open {stage_path} with valid camera prims after {attempts} attempts"
    )


def _jsonable(value: Any) -> Any:
    """Convert Replicator/Numpy values to lossless-enough JSON primitives."""

    import numpy as np

    if isinstance(value, np.ndarray):
        if value.dtype.names:
            return [
                {name: _jsonable(row[name]) for name in value.dtype.names}
                for row in value
            ]
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _capture_direct(
    rep: Any,
    simulation_app: Any,
    render_products: list[Any],
    camera_specs: list[dict[str, Any]],
    out_dir: Path,
    frame_count: int,
    stage: Any,
    scene_variant_count: int = 1,
    scene_variant_strategy: str = "legacy",
) -> dict[str, Any]:
    """Capture data by reading attached annotators instead of relying on writer flushes."""

    import numpy as np
    from PIL import Image

    bundles: list[dict[str, Any]] = []
    for render_product in render_products:
        rgb = rep.AnnotatorRegistry.get_annotator("rgb")
        bbox = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
        camera = rep.AnnotatorRegistry.get_annotator("camera_params")
        rgb.attach(render_product)
        bbox.attach(render_product)
        camera.attach(render_product)
        bundles.append({"rgb": rgb, "bbox": bbox, "camera": camera})

    rep.orchestrator.set_capture_on_play(False)

    records: list[dict[str, Any]] = []
    for frame_index in range(max(frame_count, 1)):
        variant = _apply_scene_variant(
            stage,
            frame_index % max(scene_variant_count, 1),
            strategy=scene_variant_strategy,
        )
        _wait_updates(simulation_app, 4)
        _log(f"direct capture frame {frame_index + 1}/{max(frame_count, 1)}")
        rgba_payloads: list[Any] = []
        for capture_attempt in range(1, 4):
            _log(f"stepping Replicator graph attempt {capture_attempt}/3")
            rep.orchestrator.step(rt_subframes=4)
            _log("Replicator step complete")
            rep.orchestrator.wait_until_complete()
            _wait_updates(simulation_app, 8)
            rgba_payloads = [np.asarray(bundle["rgb"].get_data()) for bundle in bundles]
            shapes = [tuple(payload.shape) for payload in rgba_payloads]
            _log(f"RGB shapes after attempt {capture_attempt}: {shapes}")
            if all(
                payload.ndim == 3 and payload.shape[2] >= 3 and payload.size > 0
                for payload in rgba_payloads
            ):
                break
            _log("render data not ready; advancing Kit before retry")
            _wait_updates(simulation_app, 24)
        else:
            raise RuntimeError(
                "RGB annotators remained empty after three synchronized capture attempts: "
                f"{[tuple(payload.shape) for payload in rgba_payloads]}"
            )

        for camera_index, (spec, bundle, rgba) in enumerate(
            zip(camera_specs, bundles, rgba_payloads)
        ):
            camera_dir = out_dir / "direct" / spec["uav_id"]
            camera_dir.mkdir(parents=True, exist_ok=True)

            _log(f"RGB ready for {spec['uav_id']}: shape={rgba.shape}")
            rgb_path = camera_dir / f"rgb_{frame_index:04d}.png"
            Image.fromarray(rgba[:, :, :3].astype(np.uint8), mode="RGB").save(rgb_path)

            _log(f"reading 2D boxes for {spec['uav_id']}")
            bbox_data = bundle["bbox"].get_data()
            bbox_path = camera_dir / f"bbox2d_tight_{frame_index:04d}.json"
            bbox_path.write_text(
                json.dumps(_jsonable(bbox_data), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            _log(f"reading camera parameters for {spec['uav_id']}")
            camera_data = bundle["camera"].get_data()
            camera_path = camera_dir / f"camera_params_{frame_index:04d}.json"
            camera_path.write_text(
                json.dumps(_jsonable(camera_data), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            data_payload = bbox_data.get("data", []) if isinstance(bbox_data, dict) else bbox_data
            bbox_count = int(len(data_payload))
            records.append(
                {
                    "camera_index": camera_index,
                    "uav_id": spec["uav_id"],
                    "frame_index": frame_index,
                    "rgb_path": str(rgb_path.relative_to(out_dir)),
                    "bbox_path": str(bbox_path.relative_to(out_dir)),
                    "camera_params_path": str(camera_path.relative_to(out_dir)),
                    "rgb_shape": list(rgba.shape),
                    "rgb_min": int(rgba[:, :, :3].min()),
                    "rgb_max": int(rgba[:, :, :3].max()),
                    "rgb_mean": float(rgba[:, :, :3].mean()),
                    "bbox_count": bbox_count,
                    **variant,
                }
            )

    rep.orchestrator.wait_until_complete()
    for bundle in bundles:
        bundle["rgb"].detach()
        bundle["bbox"].detach()
        bundle["camera"].detach()
    _wait_updates(simulation_app, 2)

    expected = len(camera_specs) * max(frame_count, 1)
    rgb_count = len(list((out_dir / "direct").glob("*/rgb_*.png")))
    bbox_count = len(list((out_dir / "direct").glob("*/bbox2d_tight_*.json")))
    camera_count = len(list((out_dir / "direct").glob("*/camera_params_*.json")))
    if (rgb_count, bbox_count, camera_count) != (expected, expected, expected):
        raise RuntimeError(
            "direct capture validation failed: "
            f"expected={expected}, rgb={rgb_count}, bbox={bbox_count}, camera={camera_count}"
        )

    return {
        "expected_camera_frames": expected,
        "rgb_file_count": rgb_count,
        "bbox_file_count": bbox_count,
        "camera_params_file_count": camera_count,
        "records": records,
    }


def capture_proxy(
    config: dict[str, Any],
    out_dir: Path,
    active_gpu: int | None = None,
    frame_count: int = 1,
    scene_variant_count: int = 1,
    scene_variant_strategy: str = "legacy",
) -> dict[str, Any]:
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
            f"objects={stage_summary.get('object_count')} "
            f"cutout_overlays={stage_summary.get('cutout_overlay_count', 0)}"
        )
        write_capture_plan(build_capture_plan(config), out_dir / "capture_plan.json")
        write_replicator_template(config, out_dir / "isaac_replicator_capture_template.py")

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

        _log("opening USD stage")
        context = omni.usd.get_context()
        _open_stage_checked(simulation_app, context, stage_path, camera_specs)
        _log("USD stage and camera prims verified")
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("USD stage unavailable after successful open")

        _log(f"creating {len(camera_specs)} render products at {width}x{height}")
        render_products = [
            rep.create.render_product(
                spec["source_camera_prim"],
                (width, height),
                name=f"rp_{index + 1:02d}",
            )
            for index, spec in enumerate(camera_specs)
        ]

        _log(f"capturing {frame_count} frame(s) through direct annotators")
        direct_summary = _capture_direct(
            rep,
            simulation_app,
            render_products,
            camera_specs,
            out_dir,
            frame_count,
            stage,
            scene_variant_count=scene_variant_count,
            scene_variant_strategy=scene_variant_strategy,
        )
        _log("direct annotator capture complete")

        files = sorted(
            str(path.relative_to(out_dir)) for path in out_dir.rglob("*") if path.is_file()
        )
        summary = {
            "status": "proxy_direct_capture_complete",
            "stage_path": str(stage_path),
            "output_dir": str(out_dir),
            "camera_count": len(camera_specs),
            "frame_count": frame_count,
            "scene_variant_count": scene_variant_count,
            "scene_variant_strategy": scene_variant_strategy,
            "render_resolution": [width, height],
            "capture_cameras": camera_specs,
            "file_count": len(files),
            "files": files[:160],
            "direct_capture": direct_summary,
            "stage_summary": stage_summary,
        }
        (out_dir / "proxy_capture_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        _log(f"wrote validated summary with {len(files)} files")
        return summary
    finally:
        _log("closing SimulationApp")
        simulation_app.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture validated RGB and detector GT from the MarineCity proxy stage."
    )
    parser.add_argument("--config", default="configs/sim/marinecity_isaac_stage1.yaml")
    parser.add_argument("--out-dir", default="/tmp/com3d_isaac_proxy_capture")
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument(
        "--scene-variants",
        type=int,
        default=1,
        help="Deterministic object-layout variants captured as separate frames.",
    )
    parser.add_argument(
        "--scene-variant-strategy",
        choices=("legacy", "balanced"),
        default="legacy",
        help="Keep legacy transforms or use broad 2D translations and rotations.",
    )
    parser.add_argument(
        "--connect-uv",
        choices=("config", "on", "off"),
        default="config",
        help="Override cutout UV wiring for a controlled render A/B test.",
    )
    parser.add_argument(
        "--active-gpu",
        type=int,
        default=(
            int(os.environ["ISAAC_ACTIVE_GPU"])
            if os.environ.get("ISAAC_ACTIVE_GPU")
            else None
        ),
    )
    args = parser.parse_args()

    config = load_config(args.config)
    if args.connect_uv != "config":
        config.setdefault("cutout_overlays", {})["connect_uv"] = args.connect_uv == "on"

    if args.scene_variants < 1:
        parser.error("--scene-variants must be at least 1")
    frame_count = args.scene_variants if args.scene_variants > 1 else args.frames
    summary = capture_proxy(
        config,
        Path(args.out_dir),
        active_gpu=args.active_gpu,
        frame_count=frame_count,
        scene_variant_count=args.scene_variants,
        scene_variant_strategy=args.scene_variant_strategy,
    )
    print(f"Proxy capture status: {summary['status']}")
    print(f"Output dir: {summary['output_dir']}")
    print(f"Files: {summary['file_count']}")


if __name__ == "__main__":
    main()
