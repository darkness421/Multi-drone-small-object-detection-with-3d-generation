from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import os
import time
import math
from pathlib import Path

import carb
import omni.kit.app
import omni.usd
from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdShade


USD_PATH = os.environ.get(
    "COM3D_MARINECITY_USD",
    "/isaac-sim/.local/share/ov/data/haeundae_marinecity_roi_prep.usd",
)
TEXTURE_ROOT = os.environ.get(
    "COM3D_VISDRONE_TEXTURE_ROOT",
    "/isaac-sim/.local/share/ov/data/visdrone_objects",
)
MARINECITY_ORIGIN = {
    "name": "Busan Haeundae Marine City origin",
    "latitude_deg": float(os.environ.get("COM3D_MARINECITY_LAT", "35.1569")),
    "longitude_deg": float(os.environ.get("COM3D_MARINECITY_LON", "129.1439")),
    "height_m": float(os.environ.get("COM3D_MARINECITY_HEIGHT", "160.0")),
}
# Keep the Cesium georeference near the user-verified MarineCity view. UAV
# camera/marker heights are then expressed as offsets from the object plane.
OBJECT_Z_M = float(os.environ.get("COM3D_OBJECT_Z_M", str(-MARINECITY_ORIGIN["height_m"] + 8.0)))
OBJECT_VISIBILITY_SCALE = float(os.environ.get("COM3D_OBJECT_VISIBILITY_SCALE", "2.0"))


def wgs84_to_local_enu(latitude_deg, longitude_deg, height_m=0.0):
    """Small-area WGS84 to local ENU conversion around the MarineCity origin."""
    meters_per_degree_lat = 111_320.0
    lat0 = MARINECITY_ORIGIN["latitude_deg"]
    lon0 = MARINECITY_ORIGIN["longitude_deg"]
    east = (
        (longitude_deg - lon0)
        * meters_per_degree_lat
        * math.cos(math.radians(lat0))
    )
    north = (latitude_deg - lat0) * meters_per_degree_lat
    up = height_m - MARINECITY_ORIGIN["height_m"]
    return (east, north, up)


def local_enu_to_wgs84(east_m, north_m, up_m=0.0):
    meters_per_degree_lat = 111_320.0
    lat0 = MARINECITY_ORIGIN["latitude_deg"]
    lon0 = MARINECITY_ORIGIN["longitude_deg"]
    latitude = lat0 + north_m / meters_per_degree_lat
    longitude = lon0 + east_m / (meters_per_degree_lat * math.cos(math.radians(lat0)))
    height = MARINECITY_ORIGIN["height_m"] + up_m
    return (latitude, longitude, height)


def scaled_size(width_m, length_m):
    return (width_m * OBJECT_VISIBILITY_SCALE, length_m * OBJECT_VISIBILITY_SCALE)

OBJECTS = [
    {
        "id": "car_01",
        "class_name": "car",
        "texture": "car_01.png",
        "xyz": (-42.0, -18.0, OBJECT_Z_M),
        "size_xy": scaled_size(1.9, 4.6),
        "metric_size_xy": (1.9, 4.6),
        "yaw": 0.0,
    },
    {
        "id": "van_01",
        "class_name": "van",
        "texture": "van_01.png",
        "xyz": (-30.0, -18.0, OBJECT_Z_M),
        "size_xy": scaled_size(2.1, 5.5),
        "metric_size_xy": (2.1, 5.5),
        "yaw": 0.0,
    },
    {
        "id": "truck_01",
        "class_name": "truck",
        "texture": "truck_01.png",
        "xyz": (-17.0, -18.0, OBJECT_Z_M),
        "size_xy": scaled_size(2.5, 8.2),
        "metric_size_xy": (2.5, 8.2),
        "yaw": 0.0,
    },
    {
        "id": "bus_01",
        "class_name": "bus",
        "texture": "bus_01.png",
        "xyz": (3.0, 2.0, OBJECT_Z_M),
        "size_xy": scaled_size(2.6, 12.0),
        "metric_size_xy": (2.6, 12.0),
        "yaw": 90.0,
    },
    {
        "id": "pedestrian_01",
        "class_name": "pedestrian",
        "texture": "pedestrian_01.png",
        "xyz": (-9.0, 14.0, OBJECT_Z_M),
        "size_xy": scaled_size(0.75, 0.75),
        "metric_size_xy": (0.75, 0.75),
        "yaw": -10.0,
    },
    {
        "id": "person_01",
        "class_name": "people",
        "texture": "person_01.png",
        "xyz": (-6.5, 15.2, OBJECT_Z_M),
        "size_xy": scaled_size(0.75, 0.75),
        "metric_size_xy": (0.75, 0.75),
        "yaw": 15.0,
    },
]

UAVS = [
    ("uav_01", (15.0, -40.0, OBJECT_Z_M + 140.0), (0.0, 0.55, 0.15), "low-altitude detector view"),
    ("uav_02", (-70.0, 48.0, OBJECT_Z_M + 150.0), (0.0, 0.25, 0.95), "cross-view confirmation"),
    ("uav_03", (36.0, 55.0, OBJECT_Z_M + 160.0), (0.95, 0.45, 0.05), "wide-area context"),
]

ROI_MARKERS = [
    ("marinecity_origin", (0.0, 0.0, OBJECT_Z_M + 0.5), (0.2, 0.9, 0.2), "MarineCity georef origin"),
    ("roi_north", (0.0, 100.0, OBJECT_Z_M + 0.5), (0.1, 0.4, 1.0), "ROI north edge"),
    ("roi_south", (0.0, -100.0, OBJECT_Z_M + 0.5), (0.1, 0.4, 1.0), "ROI south edge"),
    ("roi_east", (150.0, 0.0, OBJECT_Z_M + 0.5), (0.1, 0.4, 1.0), "ROI east edge"),
    ("roi_west", (-150.0, 0.0, OBJECT_Z_M + 0.5), (0.1, 0.4, 1.0), "ROI west edge"),
]


def wait_frames(n=120):
    app = omni.kit.app.get_app()
    for _ in range(n):
        app.update()


def safe_name(value):
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)


def set_xform(prim, translate, rotate_z=0.0, scale=(1.0, 1.0, 1.0)):
    xform = UsdGeom.Xformable(prim)
    xform.ClearXformOpOrder()
    xform.AddTranslateOp().Set(Gf.Vec3d(*translate))
    if rotate_z:
        xform.AddRotateXYZOp().Set(Gf.Vec3f(0.0, 0.0, rotate_z))
    if scale != (1.0, 1.0, 1.0):
        xform.AddScaleOp().Set(Gf.Vec3f(*scale))


def make_texture_material(stage, material_path, texture_path):
    material = UsdShade.Material.Define(stage, Sdf.Path(material_path))
    shader = UsdShade.Shader.Define(stage, Sdf.Path(f"{material_path}/PreviewSurface"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.82)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

    texture = UsdShade.Shader.Define(stage, Sdf.Path(f"{material_path}/DiffuseTexture"))
    texture.CreateIdAttr("UsdUVTexture")
    texture.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(str(texture_path))
    texture.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
    texture.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("clamp")
    texture.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("clamp")
    texture.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
    texture.CreateOutput("a", Sdf.ValueTypeNames.Float)

    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(texture.ConnectableAPI(), "rgb")
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).ConnectToSource(texture.ConnectableAPI(), "a")
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def add_textured_card(stage, spec):
    root = f"/World/VisDroneObjects/{safe_name(spec['id'])}"
    xform = UsdGeom.Xform.Define(stage, Sdf.Path(root))
    set_xform(xform.GetPrim(), spec["xyz"], spec["yaw"])
    xform.GetPrim().CreateAttribute("com3d:class_name", Sdf.ValueTypeNames.String).Set(spec["class_name"])
    xform.GetPrim().CreateAttribute("com3d:source_dataset", Sdf.ValueTypeNames.String).Set("VisDrone2019-DET")
    xform.GetPrim().CreateAttribute("com3d:actor_type", Sdf.ValueTypeNames.String).Set("texture_card_from_real_detection_crop")
    xform.GetPrim().CreateAttribute("com3d:metric_width_length_m", Sdf.ValueTypeNames.Float2).Set(
        Gf.Vec2f(*spec["metric_size_xy"])
    )
    xform.GetPrim().CreateAttribute("com3d:visibility_scale", Sdf.ValueTypeNames.Float).Set(OBJECT_VISIBILITY_SCALE)

    material = make_texture_material(
        stage,
        f"{root}/Material",
        Path(TEXTURE_ROOT) / spec["texture"],
    )

    mesh = UsdGeom.Mesh.Define(stage, Sdf.Path(f"{root}/TexturePlane"))
    sx, sy = spec["size_xy"]
    mesh.CreatePointsAttr(
        [
            Gf.Vec3f(-sx / 2.0, -sy / 2.0, 0.0),
            Gf.Vec3f(sx / 2.0, -sy / 2.0, 0.0),
            Gf.Vec3f(sx / 2.0, sy / 2.0, 0.0),
            Gf.Vec3f(-sx / 2.0, sy / 2.0, 0.0),
        ]
    )
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    mesh.CreateDoubleSidedAttr(True)
    st = UsdGeom.PrimvarsAPI(mesh).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex)
    st.Set([Gf.Vec2f(0.0, 0.0), Gf.Vec2f(1.0, 0.0), Gf.Vec2f(1.0, 1.0), Gf.Vec2f(0.0, 1.0)])
    UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material)
    return xform.GetPrim()


def add_marker_cube(stage, path, xyz, color, scale, label):
    cube = UsdGeom.Cube.Define(stage, Sdf.Path(path))
    cube.CreateSizeAttr(1.0)
    set_xform(cube.GetPrim(), xyz, scale=scale)
    cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    cube.GetPrim().CreateAttribute("com3d:label", Sdf.ValueTypeNames.String).Set(label)
    lat, lon, h = local_enu_to_wgs84(xyz[0], xyz[1], xyz[2] - MARINECITY_ORIGIN["height_m"])
    cube.GetPrim().CreateAttribute("com3d:wgs84_lat_lon_height", Sdf.ValueTypeNames.Float3).Set(
        Gf.Vec3f(lat, lon, h)
    )
    return cube.GetPrim()


def add_uav_marker(stage, uav_id, xyz, color, role):
    root = UsdGeom.Xform.Define(stage, Sdf.Path(f"/World/VisDroneUAVs/{uav_id}"))
    add_marker_cube(
        stage,
        f"/World/VisDroneUAVs/{uav_id}/Body",
        xyz,
        color,
        scale=(3.4, 3.4, 0.55),
        label=f"{uav_id}: {role}",
    )
    root.GetPrim().CreateAttribute("com3d:role", Sdf.ValueTypeNames.String).Set("multi_uav_observer")
    root.GetPrim().CreateAttribute("com3d:mission_role", Sdf.ValueTypeNames.String).Set(role)


def add_roi_markers(stage):
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/MarineCityCoordinateAnchors"))
    for marker_id, xyz, color, label in ROI_MARKERS:
        add_marker_cube(
            stage,
            f"/World/MarineCityCoordinateAnchors/{marker_id}",
            xyz,
            color,
            scale=(4.0, 4.0, 1.0),
            label=label,
        )


def add_overview_camera(stage):
    camera_path = Sdf.Path("/World/CoM3DACE_VisDroneOverviewCamera")
    camera = UsdGeom.Camera.Define(stage, camera_path)
    camera.CreateFocalLengthAttr(34.0)
    eye = Gf.Vec3d(-15.0, -92.0, OBJECT_Z_M + 190.0)
    target = Gf.Vec3d(-22.0, -8.0, OBJECT_Z_M)
    view = Gf.Matrix4d().SetLookAt(eye, target, Gf.Vec3d(0.0, 0.0, 1.0))
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(view.GetInverse())
    return str(camera_path)


def add_wide_roi_camera(stage):
    """Frame MarineCity buildings, coastline, ROI, UAVs, and ground actors."""
    camera_path = Sdf.Path("/World/CoM3DACE_MarineCityWideROICamera")
    camera = UsdGeom.Camera.Define(stage, camera_path)
    camera.CreateFocalLengthAttr(24.0)
    camera.CreateHorizontalApertureAttr(24.0)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 2_000_000.0))
    camera.CreateFocusDistanceAttr(260.0)
    eye = Gf.Vec3d(-40.0, -235.0, OBJECT_Z_M + 420.0)
    target = Gf.Vec3d(-5.0, -15.0, OBJECT_Z_M)
    view = Gf.Matrix4d().SetLookAt(eye, target, Gf.Vec3d(0.0, 0.0, 1.0))
    xform = UsdGeom.Xformable(camera.GetPrim())
    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(view.GetInverse())
    return str(camera_path)


def ensure_cesium_tiles_visible(stage):
    visibility = {
        "/Cesium_Tileset": "invisible",
        "/Cesium_Tileset_01": "invisible",
        "/Cesium_World_Terrain": "inherited",
        "/Cesium_World_Terrain_01": "invisible",
        "/Cesium_OSM_Buildings": "inherited",
        "/Google_Photorealistic_3D_Tiles": "inherited",
    }
    for path, state in visibility.items():
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            continue
        imageable = UsdGeom.Imageable(prim)
        if state == "inherited":
            imageable.MakeVisible()
        else:
            imageable.MakeInvisible()


def add_daylight(stage):
    root = UsdGeom.Xform.Define(stage, Sdf.Path("/World/CoM3DACE_Daylight"))
    root.GetPrim().CreateAttribute("com3d:purpose", Sdf.ValueTypeNames.String).Set(
        "Stable daytime lighting for MarineCity visual inspection"
    )

    sun = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/CoM3DACE_Daylight/SunKey"))
    sun.CreateColorAttr(Gf.Vec3f(1.0, 0.96, 0.88))
    sun.CreateIntensityAttr(6500.0)
    sun.CreateAngleAttr(0.55)
    sun_xform = UsdGeom.Xformable(sun.GetPrim())
    sun_xform.ClearXformOpOrder()
    sun_xform.AddRotateXYZOp().Set(Gf.Vec3f(-55.0, 0.0, 35.0))

    sky = UsdLux.DomeLight.Define(stage, Sdf.Path("/World/CoM3DACE_Daylight/SkyFill"))
    sky.CreateColorAttr(Gf.Vec3f(0.78, 0.88, 1.0))
    sky.CreateIntensityAttr(550.0)


def set_viewport_camera(camera_path):
    try:
        import omni.kit.viewport.utility as viewport_utility

        viewport = viewport_utility.get_active_viewport()
        if viewport is not None:
            viewport.camera_path = camera_path
            try:
                viewport.resolution = (1600, 900)
            except Exception:
                pass
            return True
    except Exception as exc:
        carb.log_warn(f"[CoM3D-ACE] Could not set viewport camera: {exc}")
    return False


def main():
    if not os.path.exists(USD_PATH):
        raise FileNotFoundError(f"USD not found: {USD_PATH}")

    print(f"[CoM3D-ACE] Opening real Cesium MarineCity USD: {USD_PATH}", flush=True)
    omni.usd.get_context().open_stage(USD_PATH)
    wait_frames(180)
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("No stage after opening MarineCity USD")

    ensure_cesium_tiles_visible(stage)
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/VisDroneObjects"))
    UsdGeom.Xform.Define(stage, Sdf.Path("/World/VisDroneUAVs"))
    add_daylight(stage)
    add_roi_markers(stage)
    for spec in OBJECTS:
        add_textured_card(stage, spec)
    for uav_id, xyz, color, role in UAVS:
        add_uav_marker(stage, uav_id, xyz, color, role)

    add_overview_camera(stage)
    camera_path = add_wide_roi_camera(stage)
    wait_frames(20)
    camera_set = set_viewport_camera(camera_path)
    print(
        f"[CoM3D-ACE] Added {len(OBJECTS)} VisDrone texture objects and {len(UAVS)} UAV markers. "
        f"Viewport camera set={camera_set}.",
        flush=True,
    )
    print(
        "[CoM3D-ACE] MarineCity origin WGS84="
        f"({MARINECITY_ORIGIN['latitude_deg']:.6f}, {MARINECITY_ORIGIN['longitude_deg']:.6f}, "
        f"{MARINECITY_ORIGIN['height_m']:.1f}m). Local stage axes are ENU meters around this origin.",
        flush=True,
    )
    print(f"[CoM3D-ACE] Ground/object local z={OBJECT_Z_M:.1f}m; UAV z={[round(item[1][2], 1) for item in UAVS]}.", flush=True)

    while simulation_app.is_running():
        simulation_app.update()

    simulation_app.close()


if __name__ == "__main__":
    main()
