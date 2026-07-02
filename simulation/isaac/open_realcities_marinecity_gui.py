"""Open the real Cesium MarineCity USD in Isaac and force a useful viewport.

This is executed inside Isaac Sim with ``--exec``. It avoids the common failure
mode where Isaac launches into a blank "New Stage" even though the Cesium USD
exists on disk.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import carb
import omni.kit.app
import omni.usd
from pxr import Gf, Sdf, UsdGeom, UsdLux


DEFAULT_STAGE = "/isaac-sim/.local/share/ov/data/haeundae_marinecity_base_map.usd"
DEFAULT_CAMERA = "/World/MarineCityOverviewCamera"
DEFAULT_MARKER = "/isaac-sim/.local/share/ov/data/marinecity_open_marker.json"
DEFAULT_CAPTURE_DIR = "/isaac-sim/.local/share/ov/data/marinecity_review_captures"


def _write_marker(payload: dict[str, object]) -> None:
    marker = Path(os.environ.get("COM3D_MARINECITY_OPEN_MARKER", DEFAULT_MARKER))
    try:
        marker.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not write marker {marker}: {exc}")


def _ensure_tiles_visible(stage) -> None:
    visibility = {
        "/Cesium_Tileset": "invisible",
        "/Cesium_Tileset_01": "invisible",
        "/Cesium_World_Terrain": "inherited",
        "/Cesium_World_Terrain_01": "invisible",
        "/Cesium_OSM_Buildings": "invisible",
        "/Google_Photorealistic_3D_Tiles": "inherited",
    }
    for path, state in visibility.items():
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            imageable = UsdGeom.Imageable(prim)
            if state == "inherited":
                imageable.MakeVisible()
            else:
                imageable.MakeInvisible()


def _ensure_overview_camera(stage, camera_path: str) -> str:
    camera = UsdGeom.Camera.Define(stage, Sdf.Path(camera_path))
    camera.CreateFocalLengthAttr(50.0)
    camera.CreateHorizontalApertureAttr(20.955)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 2_000_000.0))
    camera.CreateFocusDistanceAttr(100.0)
    camera.CreateFStopAttr(128.0)

    # The saved MarineCity stage is already georeferenced; previous successful
    # overlays used positive local-z values (for example z=50 for ROI lines).
    # Keep the camera above that local frame instead of subtracting georef
    # altitude from the z coordinate.
    eye = Gf.Vec3d(0.0, -650.0, 520.0)
    target = Gf.Vec3d(0.0, 0.0, 20.0)
    view = Gf.Matrix4d().SetLookAt(eye, target, Gf.Vec3d(0.0, 0.0, 1.0))
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(view.GetInverse())
    return camera_path


def _ensure_bright_lighting(stage) -> None:
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/MarineCityLighting"))

    sun = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/MarineCityLighting/SunKey"))
    sun.CreateColorAttr(Gf.Vec3f(1.0, 0.96, 0.86))
    sun.CreateIntensityAttr(4500.0)
    sun.CreateAngleAttr(0.75)
    sun_xform = UsdGeom.Xformable(sun.GetPrim())
    sun_xform.ClearXformOpOrder()
    sun_xform.AddTransformOp().Set(
        Gf.Matrix4d(
            0.8660254038,
            0.3535533906,
            -0.3535533906,
            0.0,
            0.0,
            0.7071067812,
            0.7071067812,
            0.0,
            0.5,
            -0.6123724357,
            0.6123724357,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        )
    )

    sky = UsdLux.DomeLight.Define(stage, Sdf.Path("/World/MarineCityLighting/SkyFill"))
    sky.CreateColorAttr(Gf.Vec3f(0.82, 0.90, 1.0))
    sky.CreateIntensityAttr(250.0)


def _set_viewport_camera(camera_path: str) -> bool:
    if not camera_path:
        return False
    try:
        import omni.kit.viewport.utility as viewport_utility

        viewport = viewport_utility.get_active_viewport()
        if viewport is None:
            return False
        viewport.camera_path = camera_path
        return True
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not set viewport camera: {exc}")
        return False


def _apply_paper_render_settings() -> None:
    try:
        import carb.settings

        settings = carb.settings.get_settings()
        settings.set("/rtx/post/motionblur/enabled", False)
        settings.set("/rtx/post/dof/enabled", False)
        settings.set("/rtx/post/lensFlares/enabled", False)
        settings.set("/rtx/post/dlss/execMode", 2)
        settings.set("/persistent/app/viewport/displayOptions", 0)
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not apply paper render settings: {exc}")


def _rgb_payload_to_uint8(payload, width: int, height: int):
    import numpy as np

    data = payload.get("data") if isinstance(payload, dict) and "data" in payload else payload
    if hasattr(data, "numpy"):
        data = data.numpy()
    arr = np.asarray(data)
    if arr.ndim == 1:
        channels = max(1, arr.size // max(width * height, 1))
        arr = arr.reshape((height, width, channels))
    if arr.ndim == 3 and arr.shape[0] != height and arr.shape[1] == height:
        arr = np.transpose(arr, (1, 0, 2))
    if arr.dtype != np.uint8:
        if arr.max(initial=0) <= 1.0:
            arr = arr * 255.0
        arr = arr.clip(0, 255).astype(np.uint8)
    return arr[:, :, :3]


def _save_capture_image(path: Path, rgb) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(path)


async def _capture_review_images(camera_path: str, width: int = 1920, height: int = 1080) -> list[str]:
    import inspect
    import omni.kit.viewport.utility as viewport_utility

    app = omni.kit.app.get_app()
    out_dir = Path(os.environ.get("COM3D_MARINECITY_CAPTURE_DIR", DEFAULT_CAPTURE_DIR))
    out_dir.mkdir(parents=True, exist_ok=True)
    viewport = viewport_utility.get_active_viewport()
    if viewport is None:
        return []
    if camera_path:
        viewport.camera_path = camera_path
    try:
        viewport.resolution = (width, height)
    except Exception:
        pass

    saved: list[str] = []
    for index, warmup_updates in enumerate((180, 240, 300), start=1):
        for _ in range(warmup_updates):
            await app.next_update_async()
        path = out_dir / f"marinecity_saved_view_review_{index:02d}.png"
        capture_fn = getattr(viewport_utility, "capture_viewport_to_file", None)
        if capture_fn is None:
            carb.log_warn(
                "[CoM3D-ACE] omni.kit.viewport.utility.capture_viewport_to_file is unavailable; "
                f"available={sorted(name for name in dir(viewport_utility) if 'capture' in name.lower())}"
            )
            break
        result = capture_fn(viewport, str(path))
        if inspect.isawaitable(result):
            result = await result
        wait_fn = getattr(result, "wait_for_result", None)
        if wait_fn is not None:
            wait_result = wait_fn()
            if inspect.isawaitable(wait_result):
                await wait_result
        for _ in range(24):
            await app.next_update_async()
        if path.exists() and path.stat().st_size > 0:
            saved.append(str(path))

    return saved


async def main() -> None:
    cli_stage = ""
    if len(sys.argv) > 1 and sys.argv[-1].lower().endswith((".usd", ".usda", ".usdc")):
        cli_stage = sys.argv[-1]
    stage_path = Path(os.environ.get("COM3D_MARINECITY_STAGE", cli_stage or DEFAULT_STAGE))
    camera_path = os.environ.get("COM3D_MARINECITY_CAMERA", DEFAULT_CAMERA)
    app = omni.kit.app.get_app()
    context = omni.usd.get_context()

    print(f"[CoM3D-ACE] Force-opening MarineCity stage: {stage_path}", flush=True)
    if not stage_path.exists():
        payload = {
            "status": "stage_missing",
            "stage_path": str(stage_path),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        print(f"[CoM3D-ACE] MarineCity stage missing: {stage_path}", flush=True)
        _write_marker(payload)
        return

    opened = context.open_stage(str(stage_path))
    for _ in range(240):
        await app.next_update_async()
        stage = context.get_stage()
        if stage is not None:
            root_path = stage.GetRootLayer().realPath
            if root_path == str(stage_path):
                break

    stage = context.get_stage()
    root_path = stage.GetRootLayer().realPath if stage is not None else ""
    capture_paths: list[str] = []
    if stage is not None:
        _ensure_tiles_visible(stage)
        _ensure_bright_lighting(stage)
        if camera_path:
            camera_path = _ensure_overview_camera(stage, camera_path)
        _apply_paper_render_settings()

    for _ in range(30):
        await app.next_update_async()

    camera_set = _set_viewport_camera(camera_path)
    for _ in range(30):
        await app.next_update_async()
    if os.environ.get("COM3D_MARINECITY_CAPTURE_REVIEW", "0") == "1":
        try:
            capture_paths = await _capture_review_images(camera_path)
        except Exception as exc:
            carb.log_warn(f"[CoM3D-ACE] MarineCity review capture failed: {exc}")

    payload = {
        "status": "stage_opened" if opened else "stage_open_requested",
        "stage_path": str(stage_path),
        "root_layer": root_path,
        "camera_path": camera_path,
        "camera_set": camera_set,
        "review_capture_paths": capture_paths,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print(f"[CoM3D-ACE] MarineCity stage open payload: {payload}", flush=True)
    _write_marker(payload)


asyncio.ensure_future(main())
