"""Open UAV MarineCity overlay and prepare multi-UAV review cameras.

Run this with Isaac/Kit ``--exec``. It opens the non-destructive overlay stage,
waits for Cesium tiles and globe anchors, orients cameras toward the object
cluster, and writes a status JSON. It does not save the stage.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import time
from pathlib import Path

import carb
import omni.kit.app
import omni.usd
from pxr import Gf, Sdf, UsdGeom, UsdLux


DEFAULT_STAGE = "/workspace/uav_marinecity/uavmarine_multiuav_overlay.usda"
DEFAULT_STATUS = "/workspace/uav_marinecity/outputs/uavmarine_multiuav_status.json"
DEFAULT_CAPTURE_DIR = "/workspace/uav_marinecity/outputs/uavmarine_multiuav_review"
ROOT = "/World/CoM3D_ACE_UAVMarine"
OBJECT_ROOT = f"{ROOT}/Objects"
UAV_ROOT = f"{ROOT}/UAVs"
CAMERA_ROOT = f"{ROOT}/RuntimeCameras"
OBJECT_IDS = ["car_01", "van_01", "truck_01", "bus_01", "pedestrian_01", "person_01"]
UAV_IDS = ["uav_01", "uav_02", "uav_03"]
UAV_CAMERA_ALTITUDES_M = {
    "uav_01": 140.0,
    "uav_02": 150.0,
    "uav_03": 160.0,
}
UAV_ALTITUDE_MIN_M = 140.0
UAV_ALTITUDE_MAX_M = 160.0
UAV_REVIEW_HEIGHT_M = 160.0
GEORREF_CANDIDATES = [
    "/World/Cesium/Georeference",
    "/World/CesiumGeoreference",
    "/CesiumGeoreference",
]


def _write_json(path: str, payload: dict[str, object]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _wait_sync(app, frames: int) -> None:
    for _ in range(max(1, int(frames))):
        app.update()


def _find_prim(stage, paths: list[str]):
    for path in paths:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            return prim
    return None


def _read_georef(stage) -> dict[str, object]:
    prim = _find_prim(stage, GEORREF_CANDIDATES)
    payload: dict[str, object] = {"valid": bool(prim and prim.IsValid())}
    if not prim or not prim.IsValid():
        return payload
    payload["path"] = str(prim.GetPath())
    for attr in prim.GetAttributes():
        name = attr.GetName()
        low = name.lower()
        if "latitude" in low or "longitude" in low or low.endswith("height") or "origin:height" in low:
            try:
                payload[name] = attr.Get()
            except Exception:
                payload[name] = None
    return payload


def _scan_cesium_prims(stage) -> list[str]:
    names: list[str] = []
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        low = path.lower()
        if "cesium" in low or "google" in low or "terrain" in low or "building" in low:
            names.append(path)
    return names[:80]


def _make_visible(stage, paths: list[str]) -> None:
    for path in paths:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            try:
                UsdGeom.Imageable(prim).MakeVisible()
            except Exception:
                pass


def _world_position(stage, path: str) -> list[float] | None:
    prim = stage.GetPrimAtPath(path)
    if not prim or not prim.IsValid():
        return None
    try:
        pos = UsdGeom.XformCache().GetLocalToWorldTransform(prim).ExtractTranslation()
        return [float(pos[0]), float(pos[1]), float(pos[2])]
    except Exception:
        return None


def _valid_positions(positions: list[list[float]]) -> bool:
    if not positions:
        return False
    max_norm = 0.0
    for pos in positions:
        if len(pos) != 3:
            return False
        max_norm = max(max_norm, float(Gf.Vec3d(*pos).GetLength()))
    return max_norm > 1.0


def _mean_position(positions: list[list[float]]) -> list[float]:
    n = float(len(positions))
    return [sum(pos[i] for pos in positions) / n for i in range(3)]


def _uav_camera_eye(base_eye: list[float], uav_id: str) -> list[float]:
    eye = [float(base_eye[0]), float(base_eye[1]), float(base_eye[2])]
    requested = UAV_CAMERA_ALTITUDES_M.get(uav_id, UAV_REVIEW_HEIGHT_M)
    eye[2] = min(max(requested, UAV_ALTITUDE_MIN_M), UAV_ALTITUDE_MAX_M)
    return eye


def _ensure_light(stage) -> None:
    UsdGeom.Xform.Define(stage, Sdf.Path(f"{ROOT}/RuntimeLighting"))
    sun = UsdLux.DistantLight.Define(stage, Sdf.Path(f"{ROOT}/RuntimeLighting/SunKey"))
    sun.CreateIntensityAttr(4200.0)
    sun.CreateAngleAttr(0.45)
    sky = UsdLux.DomeLight.Define(stage, Sdf.Path(f"{ROOT}/RuntimeLighting/SkyFill"))
    sky.CreateIntensityAttr(220.0)


def _make_camera(stage, path: str, eye: list[float], target: list[float], focal_length: float = 34.0) -> None:
    camera = UsdGeom.Camera.Define(stage, Sdf.Path(path))
    camera.CreateProjectionAttr(UsdGeom.Tokens.perspective)
    camera.CreateFocalLengthAttr(float(focal_length))
    camera.CreateHorizontalApertureAttr(20.955)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 2_000_000.0))
    camera.CreateFocusDistanceAttr(float((Gf.Vec3d(*eye) - Gf.Vec3d(*target)).GetLength()))
    view = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0.0, 0.0, 1.0))
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(view.GetInverse())


def _set_viewport_camera(camera_path: str) -> bool:
    try:
        import omni.kit.viewport.utility as viewport_utility

        viewport = viewport_utility.get_active_viewport()
        if viewport is None:
            return False
        viewport.camera_path = camera_path
        try:
            viewport.resolution = (1920, 1080)
        except Exception:
            pass
        return True
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not set viewport camera: {exc}")
        return False


async def _capture(camera_path: str, out_dir: str) -> list[str]:
    import omni.kit.viewport.utility as viewport_utility

    viewport = viewport_utility.get_active_viewport()
    capture_fn = getattr(viewport_utility, "capture_viewport_to_file", None)
    if viewport is None or capture_fn is None:
        return []
    app = omni.kit.app.get_app()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for idx, wait_frames in enumerate((180, 240, 300), start=1):
        viewport.camera_path = camera_path
        for _ in range(wait_frames):
            await app.next_update_async()
        path = out / f"uavmarine_multiuav_review_{idx:02d}.png"
        result = capture_fn(viewport, str(path))
        if inspect.isawaitable(result):
            result = await result
        wait = getattr(result, "wait_for_result", None)
        if wait is not None:
            maybe = wait()
            if inspect.isawaitable(maybe):
                await maybe
        for _ in range(10):
            await app.next_update_async()
        if path.exists() and path.stat().st_size > 0:
            saved.append(str(path))
    return saved


async def main() -> None:
    stage_path = os.environ.get("COM3D_UAVMARINE_STAGE", DEFAULT_STAGE)
    status_path = os.environ.get("COM3D_UAVMARINE_STATUS", DEFAULT_STATUS)
    capture_dir = os.environ.get("COM3D_UAVMARINE_CAPTURE_DIR", DEFAULT_CAPTURE_DIR)
    app = omni.kit.app.get_app()
    context = omni.usd.get_context()

    print(f"[CoM3D-ACE] Opening UAVMarine overlay: {stage_path}", flush=True)
    opened = context.open_stage(stage_path)
    for _ in range(720):
        await app.next_update_async()
    stage = context.get_stage()
    if stage is None:
        _write_json(status_path, {"status": "failed_no_stage", "stage_path": stage_path, "opened": bool(opened)})
        return

    cesium_prims = _scan_cesium_prims(stage)
    _make_visible(stage, cesium_prims)
    _ensure_light(stage)
    for _ in range(180):
        await app.next_update_async()

    object_positions = []
    object_valid = {}
    for actor_id in OBJECT_IDS:
        path = f"{OBJECT_ROOT}/{actor_id}"
        pos = _world_position(stage, path)
        object_valid[path] = pos is not None
        if pos is not None:
            object_positions.append(pos)
    uav_positions = {}
    for uav_id in UAV_IDS:
        path = f"{UAV_ROOT}/{uav_id}"
        uav_positions[uav_id] = _world_position(stage, path)

    if _valid_positions(object_positions):
        target = _mean_position(object_positions)
    else:
        target = [-20.0, -10.0, 0.0]

    fallback_eyes = {
        "uav_01": [8.0, -80.0, 140.0],
        "uav_02": [-90.0, 45.0, 150.0],
        "uav_03": [80.0, 95.0, 160.0],
    }
    camera_paths = {}
    camera_eye_positions = {}
    for uav_id in UAV_IDS:
        pos = uav_positions.get(uav_id)
        base_eye = pos if pos is not None and _valid_positions([pos]) else fallback_eyes[uav_id]
        eye = _uav_camera_eye(base_eye, uav_id)
        camera_path = f"{CAMERA_ROOT}/{uav_id}_Camera"
        _make_camera(stage, camera_path, eye, target, focal_length=34.0 if uav_id == "uav_01" else 42.0)
        camera_paths[uav_id] = camera_path
        camera_eye_positions[uav_id] = eye
    overview_eye = [
        target[0] - 120.0,
        target[1] - 170.0,
        target[2] + 160.0,
    ]
    overview_camera = f"{CAMERA_ROOT}/overview_Camera"
    _make_camera(stage, overview_camera, overview_eye, target, focal_length=30.0)
    camera_set = _set_viewport_camera(overview_camera)
    captures = []
    if os.environ.get("COM3D_UAVMARINE_CAPTURE", "1") == "1":
        try:
            captures = await _capture(overview_camera, capture_dir)
        except Exception as exc:
            carb.log_warn(f"[CoM3D-ACE] capture failed: {exc}")

    payload = {
        "status": "uavmarine_overlay_opened",
        "stage_path": stage_path,
        "root_layer": stage.GetRootLayer().identifier,
        "opened": bool(opened),
        "georeference_readback": _read_georef(stage),
        "cesium_prim_count": len(cesium_prims),
        "cesium_prims_sample": cesium_prims[:20],
        "object_marker_count": sum(1 for ok in object_valid.values() if ok),
        "object_paths": object_valid,
        "uav_marker_count": sum(1 for value in uav_positions.values() if value is not None),
        "uav_positions": uav_positions,
        "uav_camera_altitude_policy_m": {
            "min": UAV_ALTITUDE_MIN_M,
            "max": UAV_ALTITUDE_MAX_M,
            "review_height": UAV_REVIEW_HEIGHT_M,
            "per_uav": UAV_CAMERA_ALTITUDES_M,
        },
        "uav_camera_eye_positions": camera_eye_positions,
        "target_position": target,
        "active_camera_path": overview_camera,
        "uav_camera_paths": camera_paths,
        "camera_set": camera_set,
        "review_capture_paths": captures,
        "note": "No fake city geometry was generated; only overlay actors/cameras were added over the real Cesium stage.",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print(f"[CoM3D-ACE] UAVMarine payload: {payload}", flush=True)
    _write_json(status_path, payload)


asyncio.ensure_future(main())
