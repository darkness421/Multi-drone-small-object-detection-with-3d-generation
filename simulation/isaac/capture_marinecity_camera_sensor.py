"""Direct camera-sensor capture for the MarineCity proxy USD stage.

This path bypasses Replicator BasicWriter and saves RGB/depth/bbox data from
Isaac's Camera sensor API directly. It is intended as the first reliable bridge
from GPU1 Isaac runtime to paper-ready 3D/reasoner experiment artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from runtime import load_config
from simulation.isaac.build_marinecity_stage import build_stage
from simulation.isaac.export_rgb_depth_pose import start_isaac_simulation_app, write_replicator_template
from simulation.isaac.marinecity_plan import build_capture_plan, write_capture_plan


def _jsonify(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if value.dtype.fields:
            return [_jsonify(dict(zip(value.dtype.names or (), row.tolist()))) for row in value]
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    return value


def _rgb_uint8(rgb: Any, width: int, height: int) -> np.ndarray:
    arr = np.asarray(rgb)
    if arr.ndim == 1:
        arr = arr.reshape((height, width, -1))
    if arr.shape[-1] == 4:
        arr = arr[:, :, :3]
    if arr.dtype != np.uint8:
        scale = 255.0 if float(np.nanmax(arr)) <= 1.0 else 1.0
        arr = np.clip(arr * scale, 0, 255).astype(np.uint8)
    return arr


def _depth_uint8(depth: Any) -> np.ndarray:
    arr = np.asarray(depth, dtype=np.float32)
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[:, :, 0]
    finite = np.isfinite(arr)
    if not finite.any():
        return np.zeros(arr.shape[:2], dtype=np.uint8)
    limit = float(np.percentile(arr[finite], 95))
    if limit <= 0:
        limit = float(np.max(arr[finite])) or 1.0
    return np.clip(arr / limit, 0, 1) * 255.0


def _annotator_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"available": value is not None}
    data = value.get("data")
    return {
        "available": data is not None,
        "data_shape": list(getattr(data, "shape", [])) if data is not None else [],
        "data_dtype": str(getattr(data, "dtype", "")) if data is not None else "",
        "info": _jsonify(value.get("info", {})),
    }


def _raw_summary(value: Any) -> dict[str, Any]:
    return {
        "available": value is not None,
        "shape": list(getattr(value, "shape", [])) if value is not None else [],
        "dtype": str(getattr(value, "dtype", "")) if value is not None else "",
        "type": type(value).__name__ if value is not None else "",
    }


def _save_png(path: Path, array: np.ndarray) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array.astype(np.uint8)).save(path)


def _optional_relative(path: Path | None, root: Path) -> str:
    if path is None:
        return ""
    return str(path.relative_to(root))


def _frame_has_payload(frame: dict[str, Any]) -> bool:
    return frame.get("rgb") is not None or frame.get("distance_to_camera") is not None


def _wait_for_updates(simulation_app: Any, count: int, label: str) -> None:
    print(f"[camera_sensor] wait updates: {label} ({count})", flush=True)
    for _ in range(max(count, 1)):
        simulation_app.update()


def _capture_camera_frame(camera: Any, simulation_app: Any, frames: int) -> dict[str, Any]:
    print("[camera_sensor] initialize camera", flush=True)
    camera.initialize()
    print("[camera_sensor] attach depth", flush=True)
    camera.add_distance_to_camera_to_frame()
    print("[camera_sensor] attach bbox 2d", flush=True)
    camera.add_bounding_box_2d_tight_to_frame(init_params={"semanticTypes": ["class"]})
    print("[camera_sensor] attach bbox 3d", flush=True)
    camera.add_bounding_box_3d_to_frame(init_params={"semanticTypes": ["class"]})
    print("[camera_sensor] attach semantic", flush=True)
    camera.add_semantic_segmentation_to_frame()
    print("[camera_sensor] attach instance", flush=True)
    camera.add_instance_segmentation_to_frame()

    _wait_for_updates(simulation_app, max(frames, 1) * 24, "camera warmup")
    frame: dict[str, Any] = {}
    for attempt in range(1, 16):
        frame = camera.get_current_frame(clone=True)
        print(
            "[camera_sensor] read current frame "
            f"attempt={attempt} keys={sorted(frame.keys())} payload={_frame_has_payload(frame)}",
            flush=True,
        )
        if _frame_has_payload(frame):
            return frame
        _wait_for_updates(simulation_app, 12, f"payload retry {attempt}")
    return frame


def capture_direct(
    config: dict[str, Any],
    out_dir: Path,
    active_gpu: int | None = None,
    frame_count: int = 1,
) -> dict[str, Any]:
    simulation_app = start_isaac_simulation_app(active_gpu=active_gpu)
    try:
        import omni.usd  # type: ignore
        from isaacsim.sensors.camera import Camera  # type: ignore

        out_dir.mkdir(parents=True, exist_ok=True)
        stage_path = out_dir / "marinecity_proxy_stage.usda"
        stage_summary = build_stage(config, stage_path)
        write_capture_plan(build_capture_plan(config), out_dir / "capture_plan.json")
        write_replicator_template(config, out_dir / "isaac_replicator_capture_template.py")

        _wait_for_updates(simulation_app, 90, "post-app-start")
        omni.usd.get_context().open_stage(str(stage_path))
        _wait_for_updates(simulation_app, 120, "post-stage-open")

        width = int(config.get("camera", {}).get("width", 1280))
        height = int(config.get("camera", {}).get("height", 720))
        frame_summaries = []
        for index, uav in enumerate(stage_summary.get("uavs", []), start=1):
            print(f"[camera_sensor] capturing {uav['uav_id']} from {uav['camera_prim']}", flush=True)
            camera = Camera(
                prim_path=uav["camera_prim"],
                name=f"{uav['uav_id']}_camera_sensor",
                resolution=(width, height),
                frequency=20,
            )
            frame = _capture_camera_frame(camera, simulation_app, frame_count)
            print(f"[camera_sensor] frame keys: {sorted(frame.keys())}", flush=True)
            rgb_raw = frame.get("rgb")
            depth_raw = frame.get("distance_to_camera")

            stem = f"frame_{index:03d}_{uav['uav_id']}"
            rgb_path = out_dir / "camera_sensor" / f"{stem}_rgb.png"
            depth_npy_path = out_dir / "camera_sensor" / f"{stem}_depth.npy"
            depth_png_path = out_dir / "camera_sensor" / f"{stem}_depth_preview.png"
            bbox_path = out_dir / "camera_sensor" / f"{stem}_annotations.json"

            annotations = {
                "uav_id": uav["uav_id"],
                "camera_prim": uav["camera_prim"],
                "view_angle": uav["view_angle"],
                "altitude_m": uav["altitude_m"],
                "frame_keys": sorted(frame.keys()),
                "rgb": _raw_summary(rgb_raw),
                "distance_to_camera": _raw_summary(depth_raw),
                "bbox_2d_tight": _annotator_summary(frame.get("bounding_box_2d_tight", {})),
                "bbox_3d": _annotator_summary(frame.get("bounding_box_3d", {})),
                "semantic_segmentation": _annotator_summary(frame.get("semantic_segmentation", {})),
                "instance_segmentation": _annotator_summary(frame.get("instance_segmentation", {})),
            }
            bbox_path.parent.mkdir(parents=True, exist_ok=True)
            if rgb_raw is not None:
                _save_png(rgb_path, _rgb_uint8(rgb_raw, width, height))
            else:
                rgb_path = None
            if depth_raw is not None:
                depth_arr = np.asarray(depth_raw, dtype=np.float32)
                depth_npy_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(depth_npy_path, depth_arr)
                _save_png(depth_png_path, _depth_uint8(depth_arr))
            else:
                depth_npy_path = None
                depth_png_path = None
            bbox_path.write_text(json.dumps(annotations, indent=2, ensure_ascii=False), encoding="utf-8")
            bbox_2d = frame.get("bounding_box_2d_tight")
            bbox_2d_data = bbox_2d.get("data") if isinstance(bbox_2d, dict) else None
            frame_summaries.append(
                {
                    "uav_id": uav["uav_id"],
                    "camera_prim": uav["camera_prim"],
                    "rgb_path": _optional_relative(rgb_path, out_dir),
                    "depth_npy_path": _optional_relative(depth_npy_path, out_dir),
                    "depth_preview_path": _optional_relative(depth_png_path, out_dir),
                    "annotation_path": str(bbox_path.relative_to(out_dir)),
                    "rgb_shape": list(getattr(rgb_raw, "shape", [])) if rgb_raw is not None else [],
                    "frame_keys": sorted(frame.keys()),
                    "bbox_2d_count": len(bbox_2d_data) if bbox_2d_data is not None else 0,
                }
            )
            print(f"[camera_sensor] wrote {stem}", flush=True)

        files = sorted(str(path.relative_to(out_dir)) for path in out_dir.rglob("*") if path.is_file())
        summary = {
            "status": "camera_sensor_capture_complete",
            "stage_path": str(stage_path),
            "output_dir": str(out_dir),
            "camera_count": len(frame_summaries),
            "frame_count": frame_count,
            "render_resolution": [width, height],
            "frames": frame_summaries,
            "file_count": len(files),
            "files": files[:160],
            "stage_summary": stage_summary,
        }
        (out_dir / "camera_sensor_capture_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return summary
    finally:
        simulation_app.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture MarineCity proxy frames through Isaac Camera sensor API.")
    parser.add_argument("--config", default="configs/sim/marinecity_isaac_stage1.yaml")
    parser.add_argument("--out-dir", default="/tmp/com3d_isaac_camera_sensor")
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument(
        "--active-gpu",
        type=int,
        default=int(os.environ["ISAAC_ACTIVE_GPU"]) if os.environ.get("ISAAC_ACTIVE_GPU") else None,
    )
    args = parser.parse_args()

    summary = capture_direct(load_config(args.config), Path(args.out_dir), active_gpu=args.active_gpu, frame_count=args.frames)
    print(f"Camera sensor capture status: {summary['status']}")
    print(f"Output dir: {summary['output_dir']}")
    print(f"Files: {summary['file_count']}")


if __name__ == "__main__":
    main()
