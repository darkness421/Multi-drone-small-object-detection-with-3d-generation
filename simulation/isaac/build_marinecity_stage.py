"""Build a lightweight Marine City proxy USD stage for Isaac Sim validation.

The proxy stage is not the final Cesium digital twin. It gives us a reproducible
local coordinate frame, UAV camera altitudes, and fine-grained object placement
so the 3D/reasoner pipeline can start before the full geospatial scene is ready.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

from runtime import load_config
from runtime.config import resolve_path
from simulation.isaac.export_rgb_depth_pose import start_isaac_simulation_app, write_replicator_template
from simulation.isaac.marinecity_plan import build_capture_plan, summarize_plan, write_capture_plan


OBJECT_LAYOUT = [
    ("obj_0001", "sedan", -30.0, -12.0, 0.8, 0.0),
    ("obj_0002", "sedan", -24.5, -12.0, 0.8, 0.0),
    ("obj_0003", "van", -19.0, -12.0, 1.0, 0.0),
    ("obj_0004", "pickup", -13.5, -12.0, 0.95, 0.0),
    ("obj_0005", "police_car", -8.0, -12.0, 0.8, 0.0),
    ("obj_0006", "truck", 18.0, 8.5, 1.25, 90.0),
    ("obj_0007", "ambulance", 25.0, 8.5, 1.1, 90.0),
    ("obj_0008", "pedestrian", -6.0, 14.0, 0.85, 0.0),
    ("obj_0009", "worker", -3.2, 14.6, 0.85, 0.0),
    ("obj_0010", "pedestrian", 4.0, 15.0, 0.85, 0.0),
    ("obj_0011", "small_boat", 72.0, -52.0, 0.45, -12.0),
    ("obj_0012", "debris", 79.0, -48.0, 0.25, 20.0),
]


CLASS_DIMS = {
    "sedan": (4.5, 1.9, 1.5),
    "pickup": (5.2, 2.0, 1.8),
    "van": (5.3, 2.1, 2.2),
    "ambulance": (5.8, 2.2, 2.3),
    "police_car": (4.7, 1.9, 1.5),
    "truck": (7.2, 2.5, 2.8),
    "pedestrian": (0.55, 0.55, 1.7),
    "worker": (0.55, 0.55, 1.7),
    "small_boat": (5.5, 1.8, 0.9),
    "debris": (1.2, 0.8, 0.4),
}


CLASS_COLORS = {
    "sedan": (0.14, 0.42, 0.85),
    "pickup": (0.95, 0.48, 0.14),
    "van": (0.16, 0.60, 0.32),
    "ambulance": (0.95, 0.95, 0.92),
    "police_car": (0.08, 0.12, 0.20),
    "truck": (0.90, 0.70, 0.15),
    "pedestrian": (0.90, 0.22, 0.18),
    "worker": (0.95, 0.72, 0.18),
    "small_boat": (0.18, 0.58, 0.75),
    "debris": (0.45, 0.42, 0.36),
}


CUTOUT_CLASS_ALIASES = {
    "sedan": "car",
    "pickup": "car",
    "police_car": "car",
    "ambulance": "van",
    "worker": "pedestrian",
}


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_"} else "_" for ch in value).strip("_") or "item"


def _set_xform(prim: Any, translate: tuple[float, float, float], scale: tuple[float, float, float], rotate_z: float = 0.0) -> None:
    from pxr import Gf, UsdGeom

    xformable = UsdGeom.Xformable(prim)
    xformable.ClearXformOpOrder()
    xformable.AddTranslateOp().Set(Gf.Vec3d(*translate))
    if rotate_z:
        xformable.AddRotateXYZOp().Set(Gf.Vec3f(0.0, 0.0, rotate_z))
    xformable.AddScaleOp().Set(Gf.Vec3f(*scale))


def _set_camera_look_at(prim: Any, eye: tuple[float, float, float], target: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> None:
    from pxr import Gf, UsdGeom

    xformable = UsdGeom.Xformable(prim)
    xformable.ClearXformOpOrder()
    view = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0.0, 0.0, 1.0))
    xformable.AddTransformOp().Set(view.GetInverse())


def _set_color(gprim: Any, color: tuple[float, float, float]) -> None:
    from pxr import Gf

    gprim.CreateDisplayColorAttr([Gf.Vec3f(*color)])


def _workspace_asset_path(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return str(candidate)
    return f"/workspace/{candidate.as_posix()}"


def _metadata(prim: Any, **items: str | float | int) -> None:
    from pxr import Sdf

    type_map = {
        str: Sdf.ValueTypeNames.String,
        int: Sdf.ValueTypeNames.Int,
        float: Sdf.ValueTypeNames.Float,
    }
    for key, value in items.items():
        attr_type = type_map.get(type(value), Sdf.ValueTypeNames.String)
        prim.CreateAttribute(f"com3d:{key}", attr_type).Set(value)


def _semantic_label(prim: Any, class_name: str) -> None:
    try:
        from pxr import UsdSemantics

        labels_api = UsdSemantics.LabelsAPI.Apply(prim, "class")
        labels_api.CreateLabelsAttr().Set([class_name])
        return
    except ImportError:
        pass

    try:
        from isaacsim.core.utils.semantics import add_labels  # type: ignore

        add_labels(prim, labels=[class_name], instance_name="class")
        return
    except ImportError:
        pass

    try:
        from pxr import Semantics
    except ImportError:
        return

    sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
    sem.CreateSemanticTypeAttr().Set("class")
    sem.CreateSemanticDataAttr().Set(class_name)


def _load_cutout_manifest(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    manifest_path = Path(path)
    if not manifest_path.exists():
        return []
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


def _group_cutouts_by_class(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        class_name = str(item.get("class_name", "")).strip()
        cutout_path = str(item.get("cutout_path", "")).strip()
        if not class_name or not cutout_path:
            continue
        grouped.setdefault(class_name, []).append(item)
    return grouped


def _texture_material(stage: Any, material_path: str, texture_path: str) -> Any:
    from pxr import Sdf, UsdShade

    material = UsdShade.Material.Define(stage, Sdf.Path(material_path))
    shader = UsdShade.Shader.Define(stage, Sdf.Path(f"{material_path}/PreviewSurface"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.82)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

    texture = UsdShade.Shader.Define(stage, Sdf.Path(f"{material_path}/DiffuseTexture"))
    texture.CreateIdAttr("UsdUVTexture")
    texture.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(_workspace_asset_path(texture_path))
    texture.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("clamp")
    texture.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("clamp")
    texture.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(texture.ConnectableAPI(), "rgb")
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _textured_top_plane(
    stage: Any,
    path: str,
    material: Any,
    center: tuple[float, float, float],
    size_xy: tuple[float, float],
    yaw_deg: float,
) -> Any:
    from pxr import Gf, Sdf, UsdGeom, UsdShade, Vt

    mesh = UsdGeom.Mesh.Define(stage, Sdf.Path(path))
    half_x = size_xy[0] / 2.0
    half_y = size_xy[1] / 2.0
    points = [
        Gf.Vec3f(-half_x, -half_y, 0.0),
        Gf.Vec3f(half_x, -half_y, 0.0),
        Gf.Vec3f(half_x, half_y, 0.0),
        Gf.Vec3f(-half_x, half_y, 0.0),
    ]
    mesh.CreatePointsAttr(points)
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    mesh.CreateDoubleSidedAttr(True)
    st = UsdGeom.PrimvarsAPI(mesh).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    st.Set(Vt.Vec2fArray([Gf.Vec2f(0.0, 0.0), Gf.Vec2f(1.0, 0.0), Gf.Vec2f(1.0, 1.0), Gf.Vec2f(0.0, 1.0)]))
    _set_xform(mesh.GetPrim(), center, (1.0, 1.0, 1.0), yaw_deg)
    UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material)
    return mesh.GetPrim()


def _cube(stage: Any, path: str, translate: tuple[float, float, float], scale: tuple[float, float, float], color: tuple[float, float, float]) -> Any:
    from pxr import Sdf, UsdGeom

    cube = UsdGeom.Cube.Define(stage, Sdf.Path(path))
    cube.CreateSizeAttr(1.0)
    _set_xform(cube.GetPrim(), translate, scale)
    _set_color(cube, color)
    return cube.GetPrim()


def _build_proxy_map(stage: Any, config: dict[str, Any]) -> None:
    from pxr import Sdf, UsdGeom, UsdLux

    UsdGeom.Xform.Define(stage, Sdf.Path("/World/Map"))
    extent = config.get("map", {}).get("proxy_extent_m", [240, 180])
    width = float(extent[0])
    height = float(extent[1])
    road_width = float(config.get("map", {}).get("road_width_m", 18))

    _cube(stage, "/World/Map/Ground", (0.0, 0.0, -0.05), (width, height, 0.1), (0.25, 0.35, 0.28))
    _cube(stage, "/World/Map/CoastalWater", (0.0, -height * 0.42, -0.02), (width, height * 0.18, 0.04), (0.05, 0.28, 0.42))
    _cube(stage, "/World/Map/MainRoad_EW", (0.0, -12.0, 0.02), (width * 0.86, road_width, 0.05), (0.10, 0.10, 0.11))
    _cube(stage, "/World/Map/MainRoad_NS", (12.0, 0.0, 0.03), (road_width, height * 0.72, 0.05), (0.11, 0.11, 0.12))
    _cube(stage, "/World/Map/Crosswalk", (-2.0, 13.6, 0.06), (24.0, 4.0, 0.04), (0.88, 0.88, 0.82))

    building_count = int(config.get("map", {}).get("building_count", 14))
    for idx in range(building_count):
        row = idx // 7
        col = idx % 7
        x = -84.0 + col * 28.0
        y = 36.0 + row * 24.0
        z = 10.0 + (idx % 5) * 3.0
        _cube(
            stage,
            f"/World/Map/Buildings/building_{idx + 1:02d}",
            (x, y, z / 2.0),
            (13.0 + (idx % 3) * 2.0, 11.0 + (idx % 2) * 2.0, z),
            (0.48, 0.51, 0.55),
        )

    lights = UsdGeom.Xform.Define(stage, Sdf.Path("/World/Lights"))
    dome = UsdLux.DomeLight.Define(stage, Sdf.Path("/World/Lights/Dome"))
    dome.CreateIntensityAttr(350.0)
    sun = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/Lights/Sun"))
    sun.CreateIntensityAttr(1800.0)
    sun.CreateAngleAttr(0.25)
    _metadata(lights.GetPrim(), role="proxy_lighting")


def _build_objects(stage: Any) -> list[dict[str, Any]]:
    from pxr import Sdf, UsdGeom

    UsdGeom.Xform.Define(stage, Sdf.Path("/World/Objects"))
    objects = []
    for object_id, class_name, x, y, z, yaw in OBJECT_LAYOUT:
        dims = CLASS_DIMS.get(class_name, (1.0, 1.0, 1.0))
        color = CLASS_COLORS.get(class_name, (0.5, 0.5, 0.5))
        path = f"/World/Objects/{object_id}_{_safe_name(class_name)}"
        prim = _cube(stage, path, (x, y, z), dims, color)
        if yaw:
            _set_xform(prim, (x, y, z), dims, yaw)
        ambiguity_group = "adjacent_vehicle_cluster" if object_id in {"obj_0001", "obj_0002", "obj_0003", "obj_0004", "obj_0005"} else "context"
        _metadata(prim, object_id=object_id, class_name=class_name, ambiguity_group=ambiguity_group)
        _semantic_label(prim, class_name)
        objects.append(
            {
                "object_id": object_id,
                "class_name": class_name,
                "position_xyz_m": [x, y, z],
                "dims_lwh_m": list(dims),
                "yaw_deg": yaw,
                "ambiguity_group": ambiguity_group,
            }
        )
    return objects


def _build_cutout_overlays(stage: Any, config: dict[str, Any], objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from pxr import Sdf, UsdGeom

    cutout_cfg = config.get("cutout_overlays", {})
    if not bool(cutout_cfg.get("enabled", False)):
        return []
    items = _load_cutout_manifest(cutout_cfg.get("manifest"))
    grouped = _group_cutouts_by_class(items)
    if not grouped:
        return []

    UsdGeom.Xform.Define(stage, Sdf.Path("/World/CutoutOverlays"))
    overlays = []
    class_counters: dict[str, int] = {}
    z_offset = float(cutout_cfg.get("z_offset_m", 0.06))
    length_scale = float(cutout_cfg.get("length_scale", 1.04))
    width_scale = float(cutout_cfg.get("width_scale", 1.08))

    for obj in objects:
        object_id = str(obj["object_id"])
        scene_class = str(obj["class_name"])
        cutout_class = CUTOUT_CLASS_ALIASES.get(scene_class, scene_class)
        candidates = grouped.get(cutout_class)
        if not candidates:
            continue

        next_idx = class_counters.get(cutout_class, 0)
        item = candidates[next_idx % len(candidates)]
        class_counters[cutout_class] = next_idx + 1

        x, y, z = [float(value) for value in obj["position_xyz_m"]]
        length, width, height = [float(value) for value in obj["dims_lwh_m"]]
        yaw = float(obj["yaw_deg"])
        top_z = z + (height * 0.52) + z_offset
        overlay_root = f"/World/CutoutOverlays/{_safe_name(object_id)}_{_safe_name(cutout_class)}"
        material = _texture_material(stage, f"{overlay_root}/Material", str(item["cutout_path"]))
        prim = _textured_top_plane(
            stage,
            f"{overlay_root}/Plane",
            material,
            (x, y, top_z),
            (max(length * length_scale, 0.8), max(width * width_scale, 0.5)),
            yaw,
        )
        _metadata(
            prim,
            object_id=object_id,
            class_name=cutout_class,
            role="visdrone_texture_cutout_overlay",
            source_cutout=str(item["cutout_path"]),
        )
        _semantic_label(prim, cutout_class)
        overlays.append(
            {
                "object_id": object_id,
                "scene_class_name": scene_class,
                "cutout_class_name": cutout_class,
                "cutout_path": str(item["cutout_path"]),
                "position_xyz_m": [x, y, top_z],
                "size_xy_m": [max(length * length_scale, 0.8), max(width * width_scale, 0.5)],
                "yaw_deg": yaw,
            }
        )
    return overlays


def _build_uavs(stage: Any, config: dict[str, Any]) -> list[dict[str, Any]]:
    from pxr import Sdf, UsdGeom

    views = build_capture_plan(config)
    by_uav: dict[str, Any] = {}
    for view in views:
        by_uav.setdefault(view.uav_id, view)

    UsdGeom.Xform.Define(stage, Sdf.Path("/World/UAVs"))
    uavs = []
    for uav_id, view in sorted(by_uav.items()):
        pose = view.uav_pose
        uav_root = f"/World/UAVs/{_safe_name(uav_id)}"
        UsdGeom.Xform.Define(stage, Sdf.Path(uav_root))
        body = _cube(stage, f"{uav_root}/Body", (pose.x, pose.y, pose.z), (2.2, 2.2, 0.5), (0.08, 0.10, 0.12))
        _metadata(body, uav_id=uav_id, role="uav_body", view_angle=view.view_angle, altitude_m=float(view.altitude_m))

        camera = UsdGeom.Camera.Define(stage, Sdf.Path(f"{uav_root}/Camera"))
        camera.CreateFocalLengthAttr(float(config.get("camera", {}).get("focal_px", 780)) / 40.0)
        camera.CreateHorizontalApertureAttr(20.955)
        _set_camera_look_at(camera.GetPrim(), (pose.x, pose.y, pose.z - 0.35))
        _metadata(camera.GetPrim(), uav_id=uav_id, role="rgb_depth_camera", view_angle=view.view_angle, altitude_m=float(view.altitude_m))

        uavs.append(
            {
                "uav_id": uav_id,
                "view_angle": view.view_angle,
                "altitude_m": view.altitude_m,
                "pose_xyz_rpy": [pose.x, pose.y, pose.z, pose.roll, pose.pitch, pose.yaw],
                "camera_prim": f"{uav_root}/Camera",
            }
        )
    return uavs


def build_stage(config: dict[str, Any], out_usd: Path) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom

    out_usd.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(out_usd))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
    stage.SetDefaultPrim(world.GetPrim())

    origin = config.get("scene", {}).get("origin", {})
    _metadata(
        world.GetPrim(),
        dataset=str(config.get("dataset_name", "CoM3D-MarineCity")),
        origin_latitude_deg=float(origin.get("latitude_deg", 35.1569)),
        origin_longitude_deg=float(origin.get("longitude_deg", 129.1456)),
        origin_height_m=float(origin.get("height_m", 80.0)),
    )

    _build_proxy_map(stage, config)
    objects = _build_objects(stage)
    cutout_overlays = _build_cutout_overlays(stage, config, objects)
    uavs = _build_uavs(stage, config)
    stage.GetRootLayer().Save()

    plan = build_capture_plan(config)
    return {
        "dataset": config.get("dataset_name", "CoM3D-MarineCity"),
        "stage_path": str(out_usd),
        "status": "proxy_usd_stage_ready",
        "note": "Proxy stage validates Isaac GPU1 runtime, UAV poses, and object layout before Cesium tiles are attached.",
        "origin": origin,
        "capture_summary": summarize_plan(plan),
        "uav_count": len(uavs),
        "object_count": len(objects),
        "cutout_overlay_count": len(cutout_overlays),
        "uavs": uavs,
        "objects": objects,
        "cutout_overlays": cutout_overlays,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MarineCity proxy USD stage for Isaac validation.")
    parser.add_argument("--config", default="configs/sim/marinecity_isaac_stage1.yaml")
    parser.add_argument("--out-usd", default=None)
    parser.add_argument("--summary-out", default=None)
    parser.add_argument("--plan-out", default=None)
    parser.add_argument("--template-out", default=None)
    parser.add_argument(
        "--active-gpu",
        type=int,
        default=int(os.environ["ISAAC_ACTIVE_GPU"]) if os.environ.get("ISAAC_ACTIVE_GPU") else None,
    )
    parser.add_argument("--skip-simulation-app", action="store_true", help="Build USD with pxr only; useful for local schema debugging.")
    args = parser.parse_args()

    config = load_config(args.config)
    output_root = Path(config.get("output_root", "/tmp/com3d_isaac_stage_exports"))
    out_usd = Path(args.out_usd) if args.out_usd else output_root / "marinecity_proxy_stage.usda"
    summary_out = Path(args.summary_out) if args.summary_out else output_root / "marinecity_proxy_stage_summary.json"
    plan_out = Path(args.plan_out) if args.plan_out else output_root / "capture_plan.json"
    template_out = Path(args.template_out) if args.template_out else output_root / "isaac_replicator_capture_template.py"

    simulation_app = None
    if not args.skip_simulation_app:
        simulation_app = start_isaac_simulation_app(active_gpu=args.active_gpu)

    try:
        summary = build_stage(config, out_usd)
        summary_out.parent.mkdir(parents=True, exist_ok=True)
        summary_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        write_capture_plan(build_capture_plan(config), plan_out)
        write_replicator_template(config, template_out)
        print(f"MarineCity proxy USD ready: {out_usd}")
        print(f"Summary: {summary_out}")
        print(f"Capture plan: {plan_out}")
        print(f"Replicator template: {template_out}")
    finally:
        if simulation_app is not None:
            simulation_app.close()


if __name__ == "__main__":
    main()
