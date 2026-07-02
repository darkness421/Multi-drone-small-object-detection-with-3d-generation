"""Capture UAV RGB/depth views from the real Cesium Marine City overlay.

This script deliberately does not create proxy/fallback city geometry. It opens
the real Cesium Marine City USD, optionally adds an actor-only scenario layer to
the session layer, waits for tiles and globe anchors, then adds transient camera
prims for the UAV markers already present in the overlay.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_STAGE = "/isaac-sim/.local/share/ov/data/haeundae_marinecity_real_multiuav_scene.usda"
DEFAULT_ROOT_CANDIDATES = [
    "/World/CoM3D_ACE_UAVMarine",
    "/World/CoM3D_ACE_RealMarineCity",
]
OBJECT_IDS = ["car_01", "van_01", "truck_01", "bus_01", "pedestrian_01", "person_01"]
UAV_IDS = ["uav_01", "uav_02", "uav_03"]
FALLBACK_CAMERA_PROFILE = {
    "name": "local_marinecity_uav_altitudes",
    "reason": (
        "CesiumGlobeAnchor world transforms can remain identity in standalone/headless "
        "capture; use fixed UAV camera poses over the real Cesium stage, without creating "
        "any proxy/fallback city geometry."
    ),
    "target": [-20.0, -10.0, 15.0],
    # These are UAV-style camera altitudes in the local Marine City stage, not
    # CesiumGeoreference height. They are intentionally lower than the old
    # overview camera to resemble UAV small-object training imagery.
    "eyes": {
        "uav_01": [8.0, 3.0, 140.0],
        "uav_02": [-75.0, 55.0, 150.0],
        "uav_03": [55.0, -120.0, 160.0],
    },
}
VISIBLE_ROI_CAMERA_PROFILE = {
    "name": "visible_marinecity_roi",
    "reason": (
        "Use calibrated saved-stage local camera poses that keep the real Cesium "
        "Marine City ROI inside the view. Object/UAV world positions remain "
        "recorded separately for evidence and planning metadata."
    ),
    "target": [-47.0, 3.0, 15.0],
    "eyes": {
        "uav_01": [-17.0, 14.0, 140.0],
        "uav_02": [-27.0, 19.0, 150.0],
        "uav_03": [-7.0, 5.0, 160.0],
    },
}
VIEWER160_CAMERA_PROFILE = {
    "name": "viewer160_marinecity_roi",
    "reason": (
        "Match the manually verified Isaac viewport more closely: a centered "
        "MarineCity ROI view with UAV-style camera altitudes in the 140-160 m "
        "band. Use this for paper-facing qualitative recaptures after the user "
        "has aligned the Cesium view in GUI."
    ),
    "target": [-22.0, -13.0, 15.0],
    "eyes": {
        "uav_01": [8.0, -2.0, 140.0],
        "uav_02": [-2.0, 3.0, 150.0],
        "uav_03": [18.0, -15.0, 160.0],
    },
}
VIEWER160_CLEAN_CAMERA_PROFILE = {
    **VIEWER160_CAMERA_PROFILE,
    "name": "viewer160_clean_fullframe",
    "reason": (
        "Tighter full-frame MarineCity recapture profile derived from the "
        "successful 2026-06-26 S0 focal/film-shift test. It preserves the "
        "140-160 m UAV-style camera band while reducing black tile-boundary "
        "voids without post-cropping or synthetic city geometry."
    ),
    "focal_length": 52.0,
    "horizontal_aperture_offset": -3.7,
    "vertical_aperture_offset": 1.0,
}
CESIUM_PATHS = [
    "/World/Cesium/Georeference",
    "/World/Cesium/Google_Photorealistic_3D_Tiles",
    "/World/Cesium/Cesium_World_Terrain",
    "/World/Cesium/Cesium_OSM_Buildings",
    "/CesiumGeoreference",
    "/Cesium_World_Terrain",
    "/Cesium_OSM_Buildings",
    "/Google_Photorealistic_3D_Tiles",
]


def _start_simulation_app(active_gpu: int | None, headless: bool, width: int, height: int) -> Any:
    try:
        from isaacsim import SimulationApp  # type: ignore
    except ImportError:
        from omni.isaac.kit import SimulationApp  # type: ignore

    launch_config: dict[str, Any] = {
        "headless": headless,
        "hide_ui": headless,
        "renderer": "RaytracedLighting",
        "width": width,
        "height": height,
        "multi_gpu": False,
        "max_gpu_count": 1,
        "create_new_stage": False,
        "sync_loads": False,
        "samples_per_pixel_per_frame": 1,
        "anti_aliasing": 0,
        "extra_args": [
            "--ext-folder",
            "/isaac-sim/.local/share/ov/data/exts/v2",
            "--enable",
            "cesium.usd.plugins",
            "--enable",
            "cesium.omniverse",
        ],
    }
    if active_gpu is not None:
        launch_config["active_gpu"] = active_gpu
        launch_config["physics_gpu"] = active_gpu
    return SimulationApp(launch_config)


def _wait(simulation_app: Any, frames: int, label: str) -> None:
    print(f"[real_capture] wait {frames} frames: {label}", flush=True)
    for _ in range(max(1, int(frames))):
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


def _rgb_uint8(value: Any, width: int, height: int) -> np.ndarray:
    arr = _as_numpy(value)
    if arr.ndim == 1:
        channels = max(1, arr.size // max(width * height, 1))
        arr = arr.reshape((height, width, channels))
    if arr.ndim == 3 and arr.shape[-1] == 4:
        arr = arr[:, :, :3]
    if arr.dtype != np.uint8:
        scale = 255.0 if float(np.nanmax(arr)) <= 1.0 else 1.0
        arr = np.clip(arr * scale, 0, 255).astype(np.uint8)
    return arr[:, :, :3]


def _depth_uint8(value: Any) -> np.ndarray:
    arr = _as_numpy(value).astype(np.float32)
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[:, :, 0]
    finite = np.isfinite(arr)
    if not finite.any():
        return np.zeros(arr.shape[:2], dtype=np.uint8)
    limit = float(np.percentile(arr[finite], 95))
    if limit <= 0:
        limit = float(np.max(arr[finite])) or 1.0
    return (np.clip(arr / limit, 0, 1) * 255.0).astype(np.uint8)


def _save_png(path: Path, array: np.ndarray) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array.astype(np.uint8)).save(path)


def _matrix_to_list(matrix: Any) -> list[list[float]]:
    return [[float(matrix[i][j]) for j in range(4)] for i in range(4)]


def _prim_position(stage: Any, path: str) -> tuple[bool, list[float]]:
    from pxr import UsdGeom

    prim = stage.GetPrimAtPath(path)
    if not prim or not prim.IsValid():
        return False, []
    matrix = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    pos = matrix.ExtractTranslation()
    return True, [float(pos[0]), float(pos[1]), float(pos[2])]


def _mean_position(points: list[list[float]]) -> list[float]:
    arr = np.asarray(points, dtype=float)
    if arr.size == 0:
        return [0.0, 0.0, 0.0]
    return arr.mean(axis=0).tolist()


def _positions_resolved(points: list[list[float]]) -> bool:
    if not points:
        return False
    arr = np.asarray(points, dtype=float)
    if not np.isfinite(arr).all():
        return False
    return bool(np.nanmax(np.linalg.norm(arr, axis=1)) > 1.0)


def _detect_root(stage: Any, requested_root: str | None = None) -> str:
    roots = [requested_root] if requested_root else []
    roots.extend(DEFAULT_ROOT_CANDIDATES)
    for root in roots:
        if not root:
            continue
        prim = stage.GetPrimAtPath(root)
        if prim and prim.IsValid():
            return root
    raise RuntimeError(f"No supported CoM3D-ACE MarineCity root found. Tried: {roots}")


def _object_paths(root: str) -> list[str]:
    object_root = f"{root}/Objects" if root.endswith("UAVMarine") else f"{root}/VisDroneObjects"
    return [f"{object_root}/{object_id}" for object_id in OBJECT_IDS]


def _uav_paths(root: str) -> list[str]:
    return [f"{root}/UAVs/{uav_id}" for uav_id in UAV_IDS]


def _camera_root(root: str) -> str:
    return f"{root}/CaptureCameras"


def _hide_debug_markers(stage: Any, root: str) -> list[str]:
    """Hide visual-only UAV/ROI markers so capture cameras do not see them."""

    from pxr import UsdGeom

    hidden: list[str] = []
    candidates = [f"{root}/UAVs/{uav_id}/Body" for uav_id in UAV_IDS]
    candidates.extend(
        [
            f"{root}/ROI/roi_sw/Marker",
            f"{root}/ROI/roi_se/Marker",
            f"{root}/ROI/roi_ne/Marker",
            f"{root}/ROI/roi_nw/Marker",
        ]
    )
    for path in candidates:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            UsdGeom.Imageable(prim).MakeInvisible()
            hidden.append(path)
    return hidden


def _make_camera(
    stage: Any,
    camera_path: str,
    eye: list[float],
    target: list[float],
    focal_length: float,
    horizontal_aperture_offset: float = 0.0,
    vertical_aperture_offset: float = 0.0,
) -> list[list[float]]:
    from pxr import Gf, Sdf, UsdGeom

    camera = UsdGeom.Camera.Define(stage, Sdf.Path(camera_path))
    camera.CreateProjectionAttr(UsdGeom.Tokens.perspective)
    camera.CreateFocalLengthAttr(float(focal_length))
    camera.CreateHorizontalApertureAttr(20.955)
    if horizontal_aperture_offset:
        camera.CreateHorizontalApertureOffsetAttr(float(horizontal_aperture_offset))
    if vertical_aperture_offset:
        camera.CreateVerticalApertureOffsetAttr(float(vertical_aperture_offset))
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 2_000_000.0))
    camera.CreateFocusDistanceAttr(float(np.linalg.norm(np.asarray(eye) - np.asarray(target))))
    view = Gf.Matrix4d().SetLookAt(
        Gf.Vec3d(float(eye[0]), float(eye[1]), float(eye[2])),
        Gf.Vec3d(float(target[0]), float(target[1]), float(target[2])),
        Gf.Vec3d(0.0, 0.0, 1.0),
    )
    world = view.GetInverse()
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(world)
    return _matrix_to_list(world)


def _read_georef(stage: Any) -> dict[str, Any]:
    prim = None
    for path in ("/World/Cesium/Georeference", "/World/CesiumGeoreference", "/CesiumGeoreference"):
        candidate = stage.GetPrimAtPath(path)
        if candidate and candidate.IsValid():
            prim = candidate
            break
    result: dict[str, Any] = {"valid": bool(prim and prim.IsValid())}
    if not result["valid"]:
        return result
    result["path"] = str(prim.GetPath())
    for key in ("latitude", "longitude", "height"):
        values = []
        for attr in prim.GetAttributes():
            low = attr.GetName().lower()
            if key in low and ("origin" in low or "georeference" in low):
                values.append((attr.GetName(), attr.Get() if attr and attr.IsValid() else None))
        result[key] = values[0][1] if values else None
        if values:
            result[f"{key}_attr"] = values[0][0]
    return result


def _capture_one(
    rep: Any,
    simulation_app: Any,
    camera_path: str,
    out_dir: Path,
    stem: str,
    width: int,
    height: int,
    warmup_frames: int,
) -> dict[str, Any]:
    render_product = rep.create.render_product(camera_path, resolution=(width, height))
    annotators = {
        "rgb": rep.AnnotatorRegistry.get_annotator("rgb"),
        "distance_to_camera": rep.AnnotatorRegistry.get_annotator("distance_to_camera"),
        "camera_params": rep.AnnotatorRegistry.get_annotator("camera_params"),
    }
    for annotator in annotators.values():
        annotator.attach(render_product)

    _wait(simulation_app, warmup_frames, f"render warmup {stem}")
    payloads: dict[str, Any] = {}
    for attempt in range(1, 13):
        rep.orchestrator.step(rt_subframes=8)
        _wait(simulation_app, 8, f"read retry {stem} #{attempt}")
        payloads = {name: annotator.get_data() for name, annotator in annotators.items()}
        rgb_payload = _payload(payloads.get("rgb"))
        if rgb_payload is not None and getattr(rgb_payload, "size", 1):
            break

    rgb_path = ""
    depth_path = ""
    depth_preview_path = ""
    rgb_payload = _payload(payloads.get("rgb"))
    depth_payload = _payload(payloads.get("distance_to_camera"))

    if rgb_payload is not None:
        rgb_out = out_dir / "real_cesium_capture" / f"{stem}_rgb.png"
        _save_png(rgb_out, _rgb_uint8(rgb_payload, width, height))
        rgb_path = str(rgb_out.relative_to(out_dir))
    if depth_payload is not None:
        depth_arr = _as_numpy(depth_payload).astype(np.float32)
        depth_out = out_dir / "real_cesium_capture" / f"{stem}_depth.npy"
        depth_png = out_dir / "real_cesium_capture" / f"{stem}_depth_preview.png"
        depth_out.parent.mkdir(parents=True, exist_ok=True)
        np.save(depth_out, depth_arr)
        _save_png(depth_png, _depth_uint8(depth_arr))
        depth_path = str(depth_out.relative_to(out_dir))
        depth_preview_path = str(depth_png.relative_to(out_dir))

    return {
        "rgb_path": rgb_path,
        "depth_npy_path": depth_path,
        "depth_preview_path": depth_preview_path,
        "camera_params_available": payloads.get("camera_params") is not None,
        "rgb_available": bool(rgb_path),
        "depth_available": bool(depth_path),
    }


def main() -> None:
    print("[real_capture] script entry", flush=True)
    parser = argparse.ArgumentParser(description="Capture real Cesium Marine City multi-UAV views.")
    parser.add_argument("--stage", default=DEFAULT_STAGE)
    parser.add_argument("--base-stage", default=None, help="Real Cesium base USD to open before adding an actor-only session layer.")
    parser.add_argument("--actor-layer", default=None, help="Actor-only scenario layer to append to the USD session layer.")
    parser.add_argument("--root", default=None, help="Optional CoM3D-ACE root prim. Auto-detected when omitted.")
    parser.add_argument("--out-dir", default="outputs/isaac_exports/marinecity_real_cesium_multiuav_v1")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--active-gpu", type=int, default=int(os.environ["ISAAC_ACTIVE_GPU"]) if os.environ.get("ISAAC_ACTIVE_GPU") else None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--open-warmup", type=int, default=600)
    parser.add_argument("--render-warmup", type=int, default=120)
    parser.add_argument(
        "--focal-length",
        type=float,
        default=None,
        help="Optional focal length override for clean full-frame recapture framing.",
    )
    parser.add_argument(
        "--horizontal-aperture-offset",
        type=float,
        default=None,
        help="Optional camera film shift in USD aperture units. Use for full-frame framing, not post-crop.",
    )
    parser.add_argument(
        "--vertical-aperture-offset",
        type=float,
        default=None,
        help="Optional camera film shift in USD aperture units. Use for full-frame framing, not post-crop.",
    )
    parser.add_argument(
        "--show-debug-markers",
        action="store_true",
        help="Render visual-only UAV/ROI markers. By default these are hidden from capture cameras.",
    )
    parser.add_argument(
        "--camera-profile",
        choices=["auto", "visible-roi", "viewer160", "viewer160-clean", "fallback-original"],
        default="auto",
        help=(
            "Camera policy. visible-roi uses the earlier low-altitude smoke-test "
            "poses; viewer160 matches the manually inspected 160 m Isaac viewport "
            "for paper-facing recapture."
        ),
    )
    args = parser.parse_args()
    print(f"[real_capture] parsed args: {vars(args)}", flush=True)

    simulation_app = _start_simulation_app(args.active_gpu, args.headless, args.width, args.height)
    print("[real_capture] SimulationApp created", flush=True)
    try:
        print("[real_capture] importing omni/carb/pxr modules", flush=True)
        import carb.settings  # type: ignore
        import omni.replicator.core as rep  # type: ignore
        import omni.usd  # type: ignore
        from pxr import Sdf, UsdGeom  # type: ignore

        print("[real_capture] imports complete", flush=True)
        print(f"[real_capture] creating output dir: {args.out_dir}", flush=True)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        print("[real_capture] output dir ready", flush=True)
        print("[real_capture] getting USD context", flush=True)
        context = omni.usd.get_context()
        print(f"[real_capture] USD context: {context}", flush=True)
        stage_to_open = args.base_stage or args.stage
        print(f"[real_capture] opening stage: {stage_to_open}", flush=True)
        opened = context.open_stage(str(stage_to_open))
        print(f"[real_capture] open_stage returned: {opened}", flush=True)
        _wait(simulation_app, args.open_warmup, "post real-Cesium stage open")
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("No USD stage after open_stage")
        print(f"[real_capture] root layer after open: {stage.GetRootLayer().identifier}", flush=True)
        session_sublayers: list[str] = []
        if args.actor_layer:
            actor_layer = str(args.actor_layer)
            session_layer = stage.GetSessionLayer()
            if actor_layer not in session_layer.subLayerPaths:
                session_layer.subLayerPaths.append(actor_layer)
            session_sublayers = list(session_layer.subLayerPaths)
            print(f"[real_capture] actor session layer added: {actor_layer}", flush=True)
            print(f"[real_capture] session sublayers: {session_sublayers}", flush=True)
            _wait(simulation_app, max(120, args.open_warmup // 3), "post actor session layer add")
        root = _detect_root(stage, args.root)
        object_paths = _object_paths(root)
        uav_paths = _uav_paths(root)
        camera_root = _camera_root(root)
        hidden_debug_markers: list[str] = []
        if not args.show_debug_markers:
            hidden_debug_markers = _hide_debug_markers(stage, root)
            print(f"[real_capture] hidden debug markers: {hidden_debug_markers}", flush=True)

        settings = carb.settings.get_settings()
        settings.set("rtx/post/dlss/execMode", 2)
        settings.set("/rtx/post/motionblur/enabled", False)
        settings.set("/rtx/post/dof/enabled", False)
        rep.orchestrator.set_capture_on_play(False)

        UsdGeom.Xform.Define(stage, Sdf.Path(camera_root))
        object_positions = []
        prim_status: dict[str, Any] = {}
        for path in CESIUM_PATHS + object_paths + uav_paths:
            valid, position = _prim_position(stage, path)
            prim_status[path] = {"valid": valid, "position": position}
            if path in object_paths and valid and position:
                object_positions.append(position)

        if len(object_positions) < 3:
            raise RuntimeError("Real Cesium object anchors did not resolve enough positions; failing instead of using proxy geometry.")

        anchor_positions_resolved = _positions_resolved(object_positions)
        forced_profile = None
        if args.camera_profile == "visible-roi":
            forced_profile = VISIBLE_ROI_CAMERA_PROFILE
        elif args.camera_profile == "viewer160":
            forced_profile = VIEWER160_CAMERA_PROFILE
        elif args.camera_profile == "viewer160-clean":
            forced_profile = VIEWER160_CLEAN_CAMERA_PROFILE
        elif args.camera_profile == "fallback-original":
            forced_profile = FALLBACK_CAMERA_PROFILE

        if forced_profile is not None:
            target = list(forced_profile["target"])
            camera_profile = forced_profile
            print(f"[real_capture] forcing camera profile: {camera_profile['name']}", flush=True)
        elif anchor_positions_resolved:
            target = _mean_position(object_positions)
            camera_profile = {"name": "cesium_anchor_readback", "reason": "CesiumGlobeAnchor transforms resolved.", "target": target}
        else:
            target = list(FALLBACK_CAMERA_PROFILE["target"])
            camera_profile = FALLBACK_CAMERA_PROFILE
            print(
                "[real_capture] CesiumGlobeAnchor readback stayed near identity; "
                "using fixed UAV camera poses over the real Cesium stage.",
                flush=True,
            )
        frames = []
        views = []
        for index, uav_path in enumerate(uav_paths, start=1):
            uav_id = uav_path.rsplit("/", 1)[-1]
            valid, eye = _prim_position(stage, uav_path)
            if not valid or not eye:
                raise RuntimeError(f"UAV anchor did not resolve: {uav_path}")
            if forced_profile is not None:
                eye = list(forced_profile["eyes"][uav_id])
            elif not anchor_positions_resolved:
                eye = list(FALLBACK_CAMERA_PROFILE["eyes"][uav_id])
            camera_path = f"{camera_root}/{uav_id}_Camera"
            focal_length = float(args.focal_length if args.focal_length is not None else camera_profile.get("focal_length", 34.0))
            horizontal_aperture_offset = float(
                args.horizontal_aperture_offset
                if args.horizontal_aperture_offset is not None
                else camera_profile.get("horizontal_aperture_offset", 0.0)
            )
            vertical_aperture_offset = float(
                args.vertical_aperture_offset
                if args.vertical_aperture_offset is not None
                else camera_profile.get("vertical_aperture_offset", 0.0)
            )
            camera_extrinsic = _make_camera(
                stage,
                camera_path,
                eye,
                target,
                focal_length=focal_length,
                horizontal_aperture_offset=horizontal_aperture_offset,
                vertical_aperture_offset=vertical_aperture_offset,
            )
            _wait(simulation_app, 48, f"camera transform settle {uav_id}")
            stem = f"frame_{index:03d}_{uav_id}"
            capture = _capture_one(rep, simulation_app, camera_path, out_dir, stem, args.width, args.height, args.render_warmup)
            frame = {
                "uav_id": uav_id,
                "camera_prim": camera_path,
                "rgb_path": capture["rgb_path"],
                "depth_npy_path": capture["depth_npy_path"],
                "depth_preview_path": capture["depth_preview_path"],
                "rgb_available": capture["rgb_available"],
                "depth_available": capture["depth_available"],
                "camera_position": eye,
                "look_at_target": target,
            }
            frames.append(frame)
            views.append(
                {
                    "scene_id": "marinecity_real_cesium_multiuav",
                    "frame_id": f"marinecity_real_cesium_{uav_id}",
                    "image_id": stem,
                    "uav_id": uav_id,
                    "timestamp": 0.0,
                    "altitude_m": float(eye[2]),
                    "view_angle": "multi_uav_real_cesium",
                    "weather": "clear",
                    "lighting": "day",
                    "object_density": "visdrone_overlay_6",
                    "uav_pose": {"x": eye[0], "y": eye[1], "z": eye[2], "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
                    "camera_intrinsic": [[780.0, 0.0, args.width / 2.0], [0.0, 780.0, args.height / 2.0], [0.0, 0.0, 1.0]],
                    "camera_extrinsic": camera_extrinsic,
                    "metadata": {"stage": str(args.stage), "real_cesium": True},
                }
            )

        camera_profile = dict(camera_profile)
        camera_profile["effective_focal_length"] = float(args.focal_length if args.focal_length is not None else camera_profile.get("focal_length", 34.0))
        camera_profile["horizontal_aperture_offset"] = float(
            args.horizontal_aperture_offset
            if args.horizontal_aperture_offset is not None
            else camera_profile.get("horizontal_aperture_offset", 0.0)
        )
        camera_profile["vertical_aperture_offset"] = float(
            args.vertical_aperture_offset
            if args.vertical_aperture_offset is not None
            else camera_profile.get("vertical_aperture_offset", 0.0)
        )

        summary = {
            "status": "real_cesium_capture_complete" if all(f["rgb_available"] for f in frames) else "real_cesium_capture_partial",
            "opened": bool(opened),
            "stage_path": str(stage_to_open),
            "base_stage": str(args.base_stage or ""),
            "actor_layer": str(args.actor_layer or ""),
            "session_sublayers": session_sublayers,
            "root_prim": root,
            "root_layer": stage.GetRootLayer().identifier,
            "out_dir": str(out_dir),
            "render_resolution": [args.width, args.height],
            "debug_markers_hidden": not args.show_debug_markers,
            "hidden_debug_markers": hidden_debug_markers,
            "georeference_readback": _read_georef(stage),
            "camera_profile": camera_profile,
            "anchor_positions_resolved": anchor_positions_resolved,
            "prim_status": prim_status,
            "object_marker_count": len(object_paths),
            "uav_marker_count": len(uav_paths),
            "frames": frames,
        }
        (out_dir / "real_cesium_capture_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        capture_plan = {
            "summary": {
                "planned_frame_count": len(views),
                "scene_count": 1,
                "by_scene": {"marinecity_real_cesium_multiuav": len(views)},
                "by_view_angle": {"multi_uav_real_cesium": len(views)},
            },
            "views": views,
        }
        (out_dir / "capture_plan.json").write_text(json.dumps(capture_plan, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    except BaseException as exc:
        print(f"[real_capture] EXCEPTION {type(exc).__name__}: {exc}", flush=True)
        raise
    finally:
        print("[real_capture] closing SimulationApp", flush=True)
        simulation_app.close()


if __name__ == "__main__":
    main()
