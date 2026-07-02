"""Open the saved Cesium MarineCity ROI stage and capture review screenshots.

This intentionally follows the older working UAV script path: open
``haeundae_marinecity_roi_prep.usd`` directly, draw the ROI/sector overlays, and
leave Isaac Sim running for manual inspection.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": False})

import carb
import omni.usd
from pxr import Gf, Sdf, UsdGeom


UAV_SCRIPT_DIR = Path("/workspace/uav_marinecity/scripts")
if str(UAV_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(UAV_SCRIPT_DIR))

from sector_grid import create_rect_roi, generate_grids, generate_sectors, summarize, update_sector_statuses
from roi_overlay import draw_rect_outline, draw_sector_outlines


USD_PATH = Path("/isaac-sim/.local/share/ov/data/haeundae_marinecity_roi_prep.usd")
CAPTURE_DIR = Path("/isaac-sim/.local/share/ov/data/marinecity_review_captures")
ROI_CFG = {
    "cx": 0.0,
    "cy": 0.0,
    "width": 300.0,
    "height": 200.0,
    "z": 50.0,
}


def wait_frames(count: int) -> None:
    for _ in range(count):
        simulation_app.update()


def ensure_core_tiles(stage) -> None:
    visibility = {
        "/Cesium_Tileset": "invisible",
        "/Cesium_Tileset_01": "invisible",
        "/Cesium_World_Terrain": "inherited",
        "/Cesium_World_Terrain_01": "invisible",
        "/Cesium_OSM_Buildings": "invisible",
        "/Google_Photorealistic_3D_Tiles": "invisible",
    }
    for path, state in visibility.items():
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            imageable = UsdGeom.Imageable(prim)
            if state == "inherited":
                imageable.MakeVisible()
            else:
                imageable.MakeInvisible()


def ensure_overview_camera(stage) -> str:
    camera_path = "/MarineCity_OverviewCamera"
    camera = UsdGeom.Camera.Define(stage, Sdf.Path(camera_path))
    camera.CreateFocalLengthAttr(28.0)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 10_000_000.0))
    xformable = UsdGeom.Xformable(camera.GetPrim())
    xformable.ClearXformOpOrder()
    xformable.AddTranslateOp().Set(Gf.Vec3d(0.0, -650.0, 420.0))
    xformable.AddRotateXYZOp().Set(Gf.Vec3f(58.0, 0.0, 0.0))
    return camera_path


def draw_roi() -> None:
    roi = create_rect_roi(
        cx=ROI_CFG["cx"],
        cy=ROI_CFG["cy"],
        width=ROI_CFG["width"],
        height=ROI_CFG["height"],
    )
    sectors = generate_sectors(roi, 100.0)
    grids = generate_grids(roi, sectors, 10.0)
    update_sector_statuses(sectors, grids)
    summarize(roi, sectors, grids)
    draw_rect_outline(
        cx=roi["cx"],
        cy=roi["cy"],
        width=roi["width"],
        height=roi["height"],
        z=ROI_CFG["z"],
        color=(1.0, 0.5, 0.0, 1.0),
        line_width=5.0,
    )
    draw_sector_outlines(
        sectors=sectors,
        z=ROI_CFG["z"] + 2.0,
        color=(0.1, 0.9, 0.2, 1.0),
        line_width=2.0,
    )
    print("[INFO] ROI and sector outlines drawn.", flush=True)


def capture_review_images() -> list[str]:
    import omni.kit.viewport.utility as viewport_utility

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    viewport = viewport_utility.get_active_viewport()
    if viewport is None:
        print("[WARN] No active viewport for capture.", flush=True)
        return []
    try:
        viewport.camera_path = "/MarineCity_OverviewCamera"
    except Exception as exc:
        print(f"[WARN] Could not set overview viewport camera: {exc}", flush=True)
    try:
        viewport.resolution = (1920, 1080)
    except Exception as exc:
        print(f"[WARN] Could not set viewport resolution: {exc}", flush=True)

    saved: list[str] = []
    capture_fn = getattr(viewport_utility, "capture_viewport_to_file", None)
    if capture_fn is None:
        print("[WARN] capture_viewport_to_file is unavailable.", flush=True)
        return saved

    for index, warmup in enumerate((240, 300, 360), start=1):
        wait_frames(warmup)
        path = CAPTURE_DIR / f"marinecity_roi_direct_review_{index:02d}.png"
        result = capture_fn(viewport, str(path))
        if inspect.isawaitable(result):
            print("[WARN] Unexpected async capture result in direct capture script.", flush=True)
        wait_fn = getattr(result, "wait_for_result", None)
        if wait_fn is not None:
            wait_fn()
        wait_frames(30)
        if path.exists() and path.stat().st_size > 0:
            saved.append(str(path))
            print(f"[INFO] Saved review capture: {path}", flush=True)
    return saved


def main() -> None:
    if not USD_PATH.exists():
        raise FileNotFoundError(f"USD not found: {USD_PATH}")

    print(f"[INFO] Opening stage: {USD_PATH}", flush=True)
    context = omni.usd.get_context()
    context.open_stage(str(USD_PATH))
    wait_frames(240)

    stage = context.get_stage()
    if stage is None:
        raise RuntimeError("No stage after opening MarineCity USD")
    ensure_core_tiles(stage)
    camera_path = ensure_overview_camera(stage)
    wait_frames(60)
    print(f"[INFO] Stage opened and stabilized. Camera={camera_path}", flush=True)

    draw_roi()
    capture_paths = capture_review_images()
    print(f"[INFO] Review captures: {capture_paths}", flush=True)
    print("[INFO] Running main loop. Close the Isaac window to exit.", flush=True)

    while simulation_app.is_running():
        simulation_app.update()

    simulation_app.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        carb.log_error(f"[CoM3D-ACE] MarineCity direct capture failed: {exc}")
        raise
