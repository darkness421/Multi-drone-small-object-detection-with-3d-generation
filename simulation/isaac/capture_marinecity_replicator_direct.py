"""Direct Replicator annotator capture for the MarineCity proxy stage.

This script bypasses BasicWriter and Isaac's Camera sensor wrapper. It creates
render products for the generated UAV camera prims, attaches Replicator
annotators directly, and saves whatever payloads are returned by get_data().
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
from simulation.isaac.capture_marinecity_camera_sensor import (
    _annotator_summary,
    _depth_uint8,
    _jsonify,
    _raw_summary,
    _rgb_uint8,
    _save_png,
)
from simulation.isaac.export_rgb_depth_pose import start_isaac_simulation_app, write_replicator_template
from simulation.isaac.marinecity_plan import build_capture_plan, write_capture_plan


def _wait(simulation_app: Any, count: int, label: str) -> None:
    print(f"[rep_direct] wait updates: {label} ({count})", flush=True)
    for _ in range(max(count, 1)):
        simulation_app.update()


def _payload(value: Any) -> Any:
    if isinstance(value, dict) and "data" in value:
        return value["data"]
    return value


def _as_numpy(value: Any) -> np.ndarray:
    data = _payload(value)
    if hasattr(data, "numpy"):
        data = data.numpy()
    return np.asarray(data)


def _payload_brief(value: Any) -> dict[str, Any]:
    data = _payload(value)
    return {
        "available": data is not None,
        "type": type(data).__name__ if data is not None else "",
        "module": type(data).__module__ if data is not None else "",
        "shape": list(getattr(data, "shape", [])) if data is not None else [],
        "dtype": str(getattr(data, "dtype", "")) if data is not None else "",
    }


def _is_available(value: Any) -> bool:
    data = _payload(value)
    if data is None:
        return False
    size = getattr(data, "size", None)
    return size is None or int(size) > 0


def _save_annotator_json(path: Path, payloads: dict[str, Any], uav: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bbox_2d = payloads.get("bounding_box_2d_tight")
    bbox_3d = payloads.get("bounding_box_3d")
    annotations = {
        "uav_id": uav["uav_id"],
        "camera_prim": uav["camera_prim"],
        "view_angle": uav["view_angle"],
        "altitude_m": uav["altitude_m"],
        "rgb": _raw_summary(_payload(payloads.get("rgb"))),
        "distance_to_camera": _raw_summary(_payload(payloads.get("distance_to_camera"))),
        "bbox_2d_tight": _annotator_summary(bbox_2d),
        "bbox_2d_tight_data": _jsonify(_payload(bbox_2d)),
        "bbox_3d": _annotator_summary(bbox_3d),
        "bbox_3d_data": _jsonify(_payload(bbox_3d)),
        "semantic_segmentation": _annotator_summary(payloads.get("semantic_segmentation")),
        "instance_segmentation": _annotator_summary(payloads.get("instance_segmentation")),
        "camera_params": _jsonify(payloads.get("camera_params", {})),
    }
    path.write_text(json.dumps(annotations, indent=2, ensure_ascii=False), encoding="utf-8")


def _save_bbox_preview(path: Path, rgb_array: np.ndarray, bbox_payload: Any) -> None:
    from PIL import Image, ImageDraw

    if not isinstance(bbox_payload, dict):
        return
    data = bbox_payload.get("data")
    if data is None or len(data) == 0:
        return
    id_to_labels = bbox_payload.get("info", {}).get("idToLabels", {})
    image = Image.fromarray(rgb_array[:, :, :3].astype(np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(image)
    for row in data:
        x_min = int(row["x_min"])
        y_min = int(row["y_min"])
        x_max = int(row["x_max"])
        y_max = int(row["y_max"])
        semantic_id = str(int(row["semanticId"]))
        label = id_to_labels.get(semantic_id, {}).get("class", semantic_id)
        draw.rectangle((x_min, y_min, x_max, y_max), outline=(255, 64, 32), width=2)
        draw.text((x_min + 2, max(0, y_min - 12)), str(label), fill=(255, 64, 32))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _attach_annotators(rep: Any, render_product: Any) -> dict[str, Any]:
    annotators = {
        "rgb": rep.AnnotatorRegistry.get_annotator("rgb"),
        "distance_to_camera": rep.AnnotatorRegistry.get_annotator("distance_to_camera"),
        "bounding_box_2d_tight": rep.AnnotatorRegistry.get_annotator(
            "bounding_box_2d_tight",
            init_params={"semanticTypes": ["class"]},
        ),
        "bounding_box_3d": rep.AnnotatorRegistry.get_annotator(
            "bounding_box_3d",
            init_params={"semanticTypes": ["class"]},
        ),
        "semantic_segmentation": rep.AnnotatorRegistry.get_annotator(
            "semantic_segmentation",
            init_params={"semanticTypes": ["class"]},
        ),
        "instance_segmentation": rep.AnnotatorRegistry.get_annotator("instance_segmentation"),
        "camera_params": rep.AnnotatorRegistry.get_annotator("camera_params"),
    }
    for name, annotator in annotators.items():
        print(f"[rep_direct] attach annotator {name}", flush=True)
        annotator.attach(render_product)
    return annotators


def _read_payloads(rep: Any, simulation_app: Any, annotators: dict[str, Any]) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    for attempt in range(1, 13):
        rep.orchestrator.step(rt_subframes=8)
        _wait(simulation_app, 8, f"post-step {attempt}")
        payloads = {name: annotator.get_data() for name, annotator in annotators.items()}
        available = {name: _is_available(value) for name, value in payloads.items()}
        print(f"[rep_direct] attempt={attempt} available={available}", flush=True)
        print(
            "[rep_direct] payload brief="
            + json.dumps({name: _payload_brief(value) for name, value in payloads.items()}, ensure_ascii=False),
            flush=True,
        )
        if available.get("rgb") or available.get("distance_to_camera"):
            return payloads
    return payloads


def capture_direct(
    config: dict[str, Any],
    out_dir: Path,
    active_gpu: int | None = None,
    frame_count: int = 1,
) -> dict[str, Any]:
    simulation_app = start_isaac_simulation_app(active_gpu=active_gpu)
    try:
        import omni.usd  # type: ignore
        import carb.settings  # type: ignore
        import omni.replicator.core as rep  # type: ignore

        out_dir.mkdir(parents=True, exist_ok=True)
        stage_path = out_dir / "marinecity_proxy_stage.usda"
        stage_summary = build_stage(config, stage_path)
        write_capture_plan(build_capture_plan(config), out_dir / "capture_plan.json")
        write_replicator_template(config, out_dir / "isaac_replicator_capture_template.py")

        _wait(simulation_app, 120, "post-app-start")
        omni.usd.get_context().open_stage(str(stage_path))
        _wait(simulation_app, 180, "post-stage-open")
        carb.settings.get_settings().set("/omni/replicator/captureOnPlay", False)
        carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)
        rep.orchestrator.set_capture_on_play(False)

        width = int(config.get("camera", {}).get("width", 1280))
        height = int(config.get("camera", {}).get("height", 720))
        frame_summaries = []
        for index, uav in enumerate(stage_summary.get("uavs", []), start=1):
            print(f"[rep_direct] capturing {uav['uav_id']} from {uav['camera_prim']}", flush=True)
            render_product = rep.create.render_product(uav["camera_prim"], resolution=(width, height))
            annotators = _attach_annotators(rep, render_product)
            _wait(simulation_app, max(frame_count, 1) * 24, "render-product warmup")
            payloads = _read_payloads(rep, simulation_app, annotators)

            stem = f"frame_{index:03d}_{uav['uav_id']}"
            rgb_payload = _payload(payloads.get("rgb"))
            depth_payload = _payload(payloads.get("distance_to_camera"))
            bbox_payload = payloads.get("bounding_box_2d_tight")
            bbox_data = bbox_payload.get("data") if isinstance(bbox_payload, dict) else None

            rgb_path = None
            bbox_preview_path = None
            if rgb_payload is not None:
                rgb_path = out_dir / "replicator_direct" / f"{stem}_rgb.png"
                rgb_array = _rgb_uint8(_as_numpy(rgb_payload), width, height)
                _save_png(rgb_path, rgb_array)
                bbox_preview_path = out_dir / "replicator_direct" / f"{stem}_bbox_preview.png"
                _save_bbox_preview(bbox_preview_path, rgb_array, bbox_payload)
                if not bbox_preview_path.exists():
                    bbox_preview_path = None
            depth_npy_path = None
            depth_png_path = None
            if depth_payload is not None:
                depth_arr = _as_numpy(depth_payload).astype(np.float32)
                depth_npy_path = out_dir / "replicator_direct" / f"{stem}_depth.npy"
                depth_png_path = out_dir / "replicator_direct" / f"{stem}_depth_preview.png"
                depth_npy_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(depth_npy_path, depth_arr)
                _save_png(depth_png_path, _depth_uint8(depth_arr))

            annotation_path = out_dir / "replicator_direct" / f"{stem}_annotations.json"
            _save_annotator_json(annotation_path, payloads, uav)

            frame_summaries.append(
                {
                    "uav_id": uav["uav_id"],
                    "camera_prim": uav["camera_prim"],
                    "rgb_path": str(rgb_path.relative_to(out_dir)) if rgb_path else "",
                    "bbox_preview_path": str(bbox_preview_path.relative_to(out_dir)) if bbox_preview_path else "",
                    "depth_npy_path": str(depth_npy_path.relative_to(out_dir)) if depth_npy_path else "",
                    "depth_preview_path": str(depth_png_path.relative_to(out_dir)) if depth_png_path else "",
                    "annotation_path": str(annotation_path.relative_to(out_dir)),
                    "rgb_shape": list(getattr(rgb_payload, "shape", [])) if rgb_payload is not None else [],
                    "depth_shape": list(getattr(depth_payload, "shape", [])) if depth_payload is not None else [],
                    "bbox_2d_count": len(bbox_data) if bbox_data is not None else 0,
                }
            )

        files = sorted(str(path.relative_to(out_dir)) for path in out_dir.rglob("*") if path.is_file())
        summary = {
            "status": "replicator_direct_capture_complete",
            "stage_path": str(stage_path),
            "output_dir": str(out_dir),
            "camera_count": len(frame_summaries),
            "frame_count": frame_count,
            "render_resolution": [width, height],
            "frames": frame_summaries,
            "file_count": len(files),
            "files": files[:200],
            "stage_summary": stage_summary,
        }
        (out_dir / "replicator_direct_capture_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return summary
    except Exception as exc:
        out_dir.mkdir(parents=True, exist_ok=True)
        error_summary = {
            "status": "replicator_direct_capture_failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        (out_dir / "replicator_direct_capture_error.json").write_text(
            json.dumps(error_summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[rep_direct] failed: {type(exc).__name__}: {exc}", flush=True)
        raise
    finally:
        simulation_app.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture MarineCity proxy frames with direct Replicator annotators.")
    parser.add_argument("--config", default="configs/sim/marinecity_isaac_stage1.yaml")
    parser.add_argument("--out-dir", default="/tmp/com3d_isaac_replicator_direct")
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument(
        "--active-gpu",
        type=int,
        default=int(os.environ["ISAAC_ACTIVE_GPU"]) if os.environ.get("ISAAC_ACTIVE_GPU") else None,
    )
    args = parser.parse_args()

    summary = capture_direct(load_config(args.config), Path(args.out_dir), active_gpu=args.active_gpu, frame_count=args.frames)
    print(f"Replicator direct capture status: {summary['status']}")
    print(f"Output dir: {summary['output_dir']}")
    print(f"Files: {summary['file_count']}")


if __name__ == "__main__":
    main()
