"""Open the real Cesium Marine City multi-UAV overlay in visible Isaac GUI.

Run with Isaac/Kit ``--exec``. The script does not save or modify the source
USD on disk. It only opens the real overlay stage, creates transient review
cameras, sets the active viewport to a useful Marine City UAV-style view, and
writes a small diagnostic marker.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import carb
import omni.kit.app
import omni.usd
from pxr import Gf, Sdf, UsdGeom, UsdLux


DEFAULT_STAGE = "/isaac-sim/.local/share/ov/data/haeundae_marinecity_real_multiuav_scene.usda"
DEFAULT_MARKER = "/isaac-sim/.local/share/ov/data/marinecity_multiuav_open_marker.json"
DEFAULT_CAPTURE_DIR = "/isaac-sim/.local/share/ov/data/marinecity_multiuav_review_captures"
REVIEW_CAMERA = "/World/CoM3D_ACE_RealMarineCity/ReviewCameras/MarineCityUAVReviewCamera"
UAV_CAMERA_ROOT = "/World/CoM3D_ACE_RealMarineCity/ReviewCameras"
CHECK_PATHS = [
    "/CesiumGeoreference",
    "/Cesium_World_Terrain",
    "/Cesium_OSM_Buildings",
    "/Google_Photorealistic_3D_Tiles",
    "/World/CoM3D_ACE_RealMarineCity/VisDroneObjects/car_01",
    "/World/CoM3D_ACE_RealMarineCity/VisDroneObjects/van_01",
    "/World/CoM3D_ACE_RealMarineCity/VisDroneObjects/truck_01",
    "/World/CoM3D_ACE_RealMarineCity/VisDroneObjects/bus_01",
    "/World/CoM3D_ACE_RealMarineCity/VisDroneObjects/pedestrian_01",
    "/World/CoM3D_ACE_RealMarineCity/VisDroneObjects/person_01",
    "/World/CoM3D_ACE_RealMarineCity/UAVs/uav_01",
    "/World/CoM3D_ACE_RealMarineCity/UAVs/uav_02",
    "/World/CoM3D_ACE_RealMarineCity/UAVs/uav_03",
]
CAMERA_PROFILES = {
    "MarineCityUAVReviewCamera": {
        "eye": [-60.0, -210.0, 160.0],
        "target": [-15.0, -15.0, 15.0],
        "focal_length": 34.0,
    },
    "uav_01_Camera": {
        "eye": [8.0, 3.0, 140.0],
        "target": [-20.0, -10.0, 15.0],
        "focal_length": 34.0,
    },
    "uav_02_Camera": {
        "eye": [-75.0, 55.0, 150.0],
        "target": [-20.0, -10.0, 15.0],
        "focal_length": 40.0,
    },
    "uav_03_Camera": {
        "eye": [55.0, -120.0, 160.0],
        "target": [-20.0, -10.0, 15.0],
        "focal_length": 42.0,
    },
}


def _write_marker(payload: dict[str, object]) -> None:
    marker = Path(os.environ.get("COM3D_MARINECITY_OPEN_MARKER", DEFAULT_MARKER))
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not write marker {marker}: {exc}")


def _read_georef(stage) -> dict[str, object]:
    prim = stage.GetPrimAtPath("/CesiumGeoreference")
    payload: dict[str, object] = {"valid": bool(prim and prim.IsValid())}
    if not payload["valid"]:
        return payload
    for key in ("latitude", "longitude", "height"):
        attr = prim.GetAttribute(f"cesium:georeferenceOrigin:{key}")
        payload[key] = attr.Get() if attr and attr.IsValid() else None
    return payload


def _set_tiles_visible(stage) -> None:
    for path in ("/Cesium_World_Terrain", "/Cesium_OSM_Buildings", "/Google_Photorealistic_3D_Tiles"):
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            UsdGeom.Imageable(prim).MakeVisible()


def _ensure_light(stage) -> None:
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/CoM3D_ACE_RealMarineCity/ReviewLighting"))
    sun = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/CoM3D_ACE_RealMarineCity/ReviewLighting/SunKey"))
    sun.CreateIntensityAttr(3500.0)
    sun.CreateAngleAttr(0.5)
    sky = UsdLux.DomeLight.Define(stage, Sdf.Path("/World/CoM3D_ACE_RealMarineCity/ReviewLighting/SkyFill"))
    sky.CreateIntensityAttr(150.0)


def _ensure_camera(stage, name: str, profile: dict[str, object]) -> str:
    camera_path = f"{UAV_CAMERA_ROOT}/{name}"
    eye = profile["eye"]
    target = profile["target"]
    camera = UsdGeom.Camera.Define(stage, Sdf.Path(camera_path))
    camera.CreateProjectionAttr(UsdGeom.Tokens.perspective)
    camera.CreateFocalLengthAttr(float(profile["focal_length"]))
    camera.CreateHorizontalApertureAttr(20.955)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 2_000_000.0))
    camera.CreateFocusDistanceAttr(float((Gf.Vec3d(*eye) - Gf.Vec3d(*target)).GetLength()))
    view = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0.0, 0.0, 1.0))
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(view.GetInverse())
    return camera_path


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


async def _capture_review(camera_path: str) -> list[str]:
    import inspect
    import omni.kit.viewport.utility as viewport_utility

    out_dir = Path(os.environ.get("COM3D_MARINECITY_CAPTURE_DIR", DEFAULT_CAPTURE_DIR))
    out_dir.mkdir(parents=True, exist_ok=True)
    viewport = viewport_utility.get_active_viewport()
    if viewport is None:
        return []
    viewport.camera_path = camera_path
    capture_fn = getattr(viewport_utility, "capture_viewport_to_file", None)
    if capture_fn is None:
        return []

    app = omni.kit.app.get_app()
    saved: list[str] = []
    for idx, frames in enumerate((180, 240, 300), start=1):
        for _ in range(frames):
            await app.next_update_async()
        path = out_dir / f"marinecity_multiuav_review_{idx:02d}.png"
        result = capture_fn(viewport, str(path))
        if inspect.isawaitable(result):
            result = await result
        wait = getattr(result, "wait_for_result", None)
        if wait is not None:
            maybe = wait()
            if inspect.isawaitable(maybe):
                await maybe
        for _ in range(12):
            await app.next_update_async()
        if path.exists() and path.stat().st_size > 0:
            saved.append(str(path))
    return saved


async def main() -> None:
    stage_path = Path(os.environ.get("COM3D_MARINECITY_STAGE", DEFAULT_STAGE))
    context = omni.usd.get_context()
    app = omni.kit.app.get_app()
    print(f"[CoM3D-ACE] Opening real MarineCity multi-UAV overlay: {stage_path}", flush=True)
    if not stage_path.exists():
        _write_marker({"status": "stage_missing", "stage_path": str(stage_path)})
        return

    opened = context.open_stage(str(stage_path))
    for _ in range(360):
        await app.next_update_async()
    stage = context.get_stage()
    if stage is None:
        _write_marker({"status": "stage_missing_after_open", "stage_path": str(stage_path), "opened": bool(opened)})
        return

    _set_tiles_visible(stage)
    _ensure_light(stage)
    camera_paths = {name: _ensure_camera(stage, name, profile) for name, profile in CAMERA_PROFILES.items()}
    for _ in range(90):
        await app.next_update_async()
    camera_set = _set_viewport_camera(REVIEW_CAMERA)
    review_captures: list[str] = []
    if os.environ.get("COM3D_MARINECITY_CAPTURE_REVIEW", "1") == "1":
        try:
            review_captures = await _capture_review(REVIEW_CAMERA)
        except Exception as exc:
            carb.log_warn(f"[CoM3D-ACE] Review capture failed: {exc}")

    prim_status = {}
    for path in CHECK_PATHS:
        prim = stage.GetPrimAtPath(path)
        prim_status[path] = bool(prim and prim.IsValid())
    payload = {
        "status": "real_multiuav_stage_opened",
        "stage_path": str(stage_path),
        "root_layer": stage.GetRootLayer().identifier,
        "opened": bool(opened),
        "georeference_readback": _read_georef(stage),
        "camera_set": camera_set,
        "active_camera_path": REVIEW_CAMERA,
        "camera_paths": camera_paths,
        "camera_profile_note": "UAV camera altitudes are 140/150/160m with 160m review height; CesiumGeoreference height is not the drone altitude.",
        "prim_status": prim_status,
        "review_capture_paths": review_captures,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print(f"[CoM3D-ACE] MarineCity multi-UAV GUI payload: {payload}", flush=True)
    _write_marker(payload)


asyncio.ensure_future(main())
