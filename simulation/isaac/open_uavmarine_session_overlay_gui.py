"""Open the saved UAVMarine Cesium stage and add actors as a session layer.

This is the safer interactive path for the user-verified MarineCity view:

1. Open the real saved Cesium stage (`uavmarine.usd`).
2. Add only the actor/ROI/UAV overlay as a session sublayer.
3. Do not save or overwrite the base USD.
4. Do not create any synthetic city geometry.

Run with Isaac/Kit `--exec`.
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
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux


DEFAULT_BASE_STAGE = "/workspace/uav_marinecity/uavmarine.usd"
DEFAULT_ACTOR_LAYER = "/workspace/uav_marinecity/uavmarine_multiuav_actor_overlay_s0_locked_roi.usda"
DEFAULT_STATUS = "/workspace/uav_marinecity/outputs/uavmarine_session_overlay_status_s0.json"

CESIUM_PRIMS = [
    "/CesiumGeoreference",
    "/Google_Photorealistic_3D_Tiles",
    "/Cesium_World_Terrain",
    "/Cesium_OSM_Buildings",
]
ROOT = "/World/CoM3D_ACE_UAVMarine"
RUNTIME_ROOT = f"{ROOT}/RuntimeView"
VIEWER160_CAMERA = f"{RUNTIME_ROOT}/viewer160_OverviewCamera"
VIEWER160_TARGET = [-22.0, -13.0, 15.0]
VIEWER160_EYE = [8.0, -2.0, 160.0]
UAV_ALTITUDE_MIN_M = 140.0
UAV_ALTITUDE_MAX_M = 160.0
UAV_REVIEW_HEIGHT_M = 160.0

VIEW_PROFILES = {
    "viewer160": {
        "camera_path": VIEWER160_CAMERA,
        "eye": VIEWER160_EYE,
        "target": VIEWER160_TARGET,
        "focal_length": 30.0,
        "note": "matches the user-inspected 160 m MarineCity viewport",
    },
    "bright160": {
        "camera_path": f"{RUNTIME_ROOT}/bright160_ReviewCamera",
        "eye": [-10.0, -58.0, 158.0],
        "target": [-26.0, -11.0, 14.0],
        "focal_length": 26.0,
        "note": "bright 140-160 m UAV-style review camera over the real Cesium ROI",
    },
}


def _write_json(path: str, payload: dict[str, object]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


async def _wait(frames: int) -> None:
    app = omni.kit.app.get_app()
    for _ in range(max(1, frames)):
        await app.next_update_async()


def _read_georef(stage) -> dict[str, object]:
    prim = stage.GetPrimAtPath("/CesiumGeoreference")
    result: dict[str, object] = {"valid": bool(prim and prim.IsValid())}
    if not prim or not prim.IsValid():
        return result
    result["path"] = str(prim.GetPath())
    for attr in prim.GetAttributes():
        name = attr.GetName()
        low = name.lower()
        if "latitude" in low or "longitude" in low or "height" in low:
            try:
                result[name] = attr.Get()
            except Exception:
                result[name] = None
    return result


def _apply_georef_height_override(stage, height_value: str | None) -> float | None:
    if not height_value:
        return None
    try:
        height = float(height_value)
    except ValueError:
        carb.log_warn(f"[CoM3D-ACE] Invalid COM3D_GEOREF_HEIGHT={height_value!r}; keeping saved USD height")
        return None
    prim = stage.GetPrimAtPath("/CesiumGeoreference")
    if not prim or not prim.IsValid():
        return None
    attr = prim.GetAttribute("cesium:georeferenceOrigin:height")
    if not attr:
        return None
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        attr.Set(height)
    return height


def _prim_status(stage) -> dict[str, object]:
    status: dict[str, object] = {}
    for path in CESIUM_PRIMS:
        prim = stage.GetPrimAtPath(path)
        status[path] = {
            "valid": bool(prim and prim.IsValid()),
            "type": prim.GetTypeName() if prim and prim.IsValid() else "",
        }
    root = stage.GetPrimAtPath(ROOT)
    status[ROOT] = {
        "valid": bool(root and root.IsValid()),
        "type": root.GetTypeName() if root and root.IsValid() else "",
    }
    return status


def _session_sublayers(stage) -> list[str]:
    layer = stage.GetSessionLayer()
    return list(layer.subLayerPaths)


def _ensure_review_lighting(stage) -> None:
    """Add session-only review lighting so the live viewport is not trapped in shadows."""
    UsdGeom.Xform.Define(stage, Sdf.Path(f"{RUNTIME_ROOT}/Lighting"))
    sun = UsdLux.DistantLight.Define(stage, Sdf.Path(f"{RUNTIME_ROOT}/Lighting/SunKey"))
    sun.CreateIntensityAttr(9000.0)
    sun.CreateAngleAttr(0.55)
    fill = UsdLux.DomeLight.Define(stage, Sdf.Path(f"{RUNTIME_ROOT}/Lighting/SkyFill"))
    fill.CreateIntensityAttr(1600.0)

    try:
        settings = carb.settings.get_settings()
        settings.set("/rtx/post/tonemap/exposure", 0.35)
        settings.set("/rtx/sceneDb/ambientLightIntensity", 0.8)
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not apply viewport exposure settings: {exc}")


def _make_camera(stage, path: str, eye: list[float], target: list[float], focal_length: float) -> str:
    UsdGeom.Xform.Define(stage, Sdf.Path(RUNTIME_ROOT))
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
    return path


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
        carb.log_warn(f"[CoM3D-ACE] Could not set viewer160 viewport camera: {exc}")
        return False


async def main() -> None:
    base_stage = os.environ.get("COM3D_UAVMARINE_BASE_STAGE", DEFAULT_BASE_STAGE)
    actor_layer = os.environ.get("COM3D_UAVMARINE_ACTOR_LAYER", DEFAULT_ACTOR_LAYER)
    status_path = os.environ.get("COM3D_UAVMARINE_SESSION_STATUS", DEFAULT_STATUS)
    keep_user_camera = os.environ.get("COM3D_KEEP_USER_CAMERA", "1") == "1"
    view_profile_name = os.environ.get("COM3D_VIEWER_PROFILE", "viewer160")
    view_profile = VIEW_PROFILES.get(view_profile_name, VIEW_PROFILES["viewer160"])
    georef_height_override = os.environ.get("COM3D_GEOREF_HEIGHT")

    payload: dict[str, object] = {
        "status": "starting",
        "base_stage": base_stage,
        "actor_layer": actor_layer,
        "keep_user_camera": keep_user_camera,
        "requested_view_profile": view_profile_name,
        "requested_georef_height": georef_height_override,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    if not Path(base_stage).exists():
        payload.update({"status": "failed_missing_base_stage"})
        _write_json(status_path, payload)
        return
    if not Path(actor_layer).exists():
        payload.update({"status": "failed_missing_actor_layer"})
        _write_json(status_path, payload)
        return

    context = omni.usd.get_context()
    print(f"[CoM3D-ACE] opening base UAVMarine stage: {base_stage}", flush=True)
    opened = context.open_stage(base_stage)
    await _wait(720)

    stage = context.get_stage()
    if stage is None:
        payload.update({"status": "failed_no_stage", "open_stage_returned": bool(opened)})
        _write_json(status_path, payload)
        return

    session_layer = stage.GetSessionLayer()
    actor_layer_path = str(Path(actor_layer))
    if actor_layer_path not in session_layer.subLayerPaths:
        session_layer.subLayerPaths.append(actor_layer_path)
    await _wait(360)

    applied_georef_height = _apply_georef_height_override(stage, georef_height_override)
    if applied_georef_height is not None:
        await _wait(120)

    # Default: keep the user's saved or manually adjusted view. If the live GUI
    # drifts into a dark/shadowed tile, COM3D_KEEP_USER_CAMERA=0 forces a
    # viewer160 review camera over the real Cesium map without saving the USD.
    active_camera = ""
    camera_set = False
    camera_profile = "manual_user_camera"
    if not keep_user_camera:
        _ensure_review_lighting(stage)
        active_camera = _make_camera(
            stage,
            str(view_profile["camera_path"]),
            list(view_profile["eye"]),
            list(view_profile["target"]),
            float(view_profile["focal_length"]),
        )
        camera_set = _set_viewport_camera(active_camera)
        camera_profile = f"{view_profile_name}_marinecity_roi"
        await _wait(240)
    try:
        import omni.kit.viewport.utility as viewport_utility

        viewport = viewport_utility.get_active_viewport()
        if viewport is not None:
            active_camera = str(viewport.camera_path)
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not read active viewport camera: {exc}")

    payload.update(
        {
            "status": "session_overlay_added",
            "open_stage_returned": bool(opened),
            "root_layer": stage.GetRootLayer().identifier,
            "session_sublayers": _session_sublayers(stage),
            "applied_georef_height": applied_georef_height,
            "georeference_readback": _read_georef(stage),
            "prim_status": _prim_status(stage),
            "active_camera_path": active_camera,
            "camera_set": camera_set,
            "camera_profile": camera_profile,
            "uav_altitude_policy_m": {
                "min": UAV_ALTITUDE_MIN_M,
                "max": UAV_ALTITUDE_MAX_M,
                "review_height": UAV_REVIEW_HEIGHT_M,
            },
            "viewer_eye": list(view_profile["eye"]) if not keep_user_camera else None,
            "viewer_target": list(view_profile["target"]) if not keep_user_camera else None,
            "viewer_note": str(view_profile["note"]) if not keep_user_camera else None,
            "viewer160_eye": VIEWER160_EYE if not keep_user_camera else None,
            "viewer160_target": VIEWER160_TARGET if not keep_user_camera else None,
            "substitute_city_geometry_created": False,
            "note": "Base USD is open; actor-only overlay is added to the session layer only. Base stage was not saved.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
    )
    print(f"[CoM3D-ACE] UAVMarine session overlay status: {payload}", flush=True)
    _write_json(status_path, payload)


asyncio.ensure_future(main())
