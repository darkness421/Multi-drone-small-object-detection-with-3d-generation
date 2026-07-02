"""Open the MarineCity proxy USD stage in a visible Isaac Sim GUI.

This script is intended to be passed to Kit/Isaac Sim with ``--exec``. It runs
inside the already-started GUI process, opens the prepared MarineCity USD stage,
selects a UAV camera for an immediate visible view, and writes a small marker
file so the launcher/dashboard can verify that the screen is showing our scene.
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


DEFAULT_STAGE = "outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/marinecity_proxy_stage.usda"
DEFAULT_MARKER = "outputs/logs/gpu1_isaac_visible/marinecity_stage_opened.json"
DEFAULT_CAMERA = "/World/UAVs/uav_01/Camera"


def _path_from_env(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser().resolve()


def _write_marker(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - Isaac/container permission fallback
        carb.log_warn(f"[CoM3D-ACE] Could not write MarineCity GUI marker {path}: {exc}")
        print(f"[CoM3D-ACE] Could not write MarineCity GUI marker {path}: {exc}", flush=True)


async def _wait_for_stage(stage_path: Path, max_updates: int = 240) -> bool:
    context = omni.usd.get_context()
    app = omni.kit.app.get_app()
    opened = context.open_stage(str(stage_path))
    for _ in range(max_updates):
        await app.next_update_async()
        stage = context.get_stage()
        if stage is not None and stage.GetRootLayer().realPath == str(stage_path):
            return bool(opened)
    return bool(opened)


def _set_visible_camera(camera_path: str) -> bool:
    try:
        import omni.kit.viewport.utility as viewport_utility

        viewport = viewport_utility.get_active_viewport()
        if viewport is None:
            return False
        viewport.camera_path = camera_path
        return True
    except Exception as exc:  # pragma: no cover - Isaac-only best effort
        carb.log_warn(f"[CoM3D-ACE] Could not set active viewport camera: {exc}")
        return False


async def main() -> None:
    stage_path = _path_from_env("COM3D_MARINECITY_STAGE", DEFAULT_STAGE)
    marker_path = _path_from_env("COM3D_MARINECITY_OPEN_MARKER", DEFAULT_MARKER)
    camera_path = os.environ.get("COM3D_MARINECITY_CAMERA", DEFAULT_CAMERA)

    carb.log_info(f"[CoM3D-ACE] Opening MarineCity stage in visible Isaac GUI: {stage_path}")
    if not stage_path.exists():
        message = f"MarineCity stage not found: {stage_path}"
        carb.log_error(f"[CoM3D-ACE] {message}")
        _write_marker(
            marker_path,
            {
                "status": "stage_missing",
                "stage_path": str(stage_path),
                "camera_path": camera_path,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "message": message,
            },
        )
        return

    opened = await _wait_for_stage(stage_path)
    app = omni.kit.app.get_app()
    for _ in range(24):
        await app.next_update_async()
    camera_set = _set_visible_camera(camera_path)
    for _ in range(8):
        await app.next_update_async()

    stage = omni.usd.get_context().get_stage()
    root_layer = stage.GetRootLayer().realPath if stage is not None else ""
    payload = {
        "status": "stage_opened" if opened else "stage_open_requested",
        "stage_path": str(stage_path),
        "root_layer": root_layer,
        "camera_path": camera_path,
        "camera_set": camera_set,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "screen": "visible Isaac Sim GUI",
    }
    print(
        "[CoM3D-ACE] MarineCity stage visible request complete: "
        f"status={payload['status']} root_layer={root_layer} camera={camera_path}",
        flush=True,
    )
    _write_marker(marker_path, payload)
    carb.log_info(f"[CoM3D-ACE] MarineCity visible GUI marker written: {marker_path}")


asyncio.ensure_future(main())
