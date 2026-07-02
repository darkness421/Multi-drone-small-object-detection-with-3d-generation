"""Build a non-destructive multi-UAV overlay for the saved UAV MarineCity USD.

The generated USD does not create a fake city. It sublayers the user-saved
Cesium stage and adds only ROI markers, VisDrone object cards, UAV markers, and
camera placeholders for the simulation smoke test.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Actor:
    actor_id: str
    class_name: str
    texture: str
    latitude: float
    longitude: float
    height: float
    width: float
    length: float
    yaw: float


@dataclass(frozen=True)
class Uav:
    uav_id: str
    latitude: float
    longitude: float
    height: float
    color: tuple[float, float, float]
    role: str


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    description: str
    object_offsets: dict[str, tuple[float, float, float]]
    uav_offsets: dict[str, tuple[float, float, float]]


# The user-saved Isaac/Cesium stage stores the georeference at the root. Keep
# this as the default so GlobeAnchor actors resolve on the real Marine City USD.
GEORREF_PATH = "/CesiumGeoreference"
BASE_LATITUDE = 35.156900
BASE_LONGITUDE = 129.143900
METERS_PER_DEGREE_LAT = 111_320.0
METERS_PER_DEGREE_LON = METERS_PER_DEGREE_LAT * math.cos(math.radians(BASE_LATITUDE))
# Empirical calibration for the user-saved uavmarine.usd viewport. The saved
# Cesium stage streams the correct MarineCity location, while the visual tile
# center is offset from the simple ENU origin used for automated actor overlays.
LOCAL_STAGE_OFFSET_X = -45.0
LOCAL_STAGE_OFFSET_Y = 0.0
LOCAL_STAGE_OFFSET_Z = 0.0
UAV_ALTITUDE_MIN_M = 140.0
UAV_ALTITUDE_MAX_M = 160.0
UAV_REVIEW_HEIGHT_M = 160.0


def wgs84_from_local_xy(east: float, north: float) -> tuple[float, float]:
    """Convert manually inspected local MarineCity overlay anchors to WGS84.

    These anchors are used only for the actor overlay. They keep the base
    Cesium USD untouched while moving the training-set object cards away from
    high-rise roofs and onto the visible road / pedestrian areas in the saved
    viewer160 MarineCity scene.
    """

    longitude = (east - LOCAL_STAGE_OFFSET_X) / METERS_PER_DEGREE_LON + BASE_LONGITUDE
    latitude = (north - LOCAL_STAGE_OFFSET_Y) / METERS_PER_DEGREE_LAT + BASE_LATITUDE
    return latitude, longitude


def actor_from_local(
    actor_id: str,
    class_name: str,
    texture: str,
    east: float,
    north: float,
    height: float,
    width: float,
    length: float,
    yaw: float,
) -> Actor:
    latitude, longitude = wgs84_from_local_xy(east, north)
    return Actor(actor_id, class_name, texture, latitude, longitude, height, width, length, yaw)


OBJECTS = [
    actor_from_local("car_01", "car", "car_01.png", -23.0, -18.0, 18.0, 2.4, 4.8, 4.0),
    actor_from_local("van_01", "van", "van_01.png", -12.0, -25.0, 18.0, 2.6, 5.5, 5.0),
    actor_from_local("truck_01", "truck", "truck_01.png", -21.0, -30.0, 18.0, 3.0, 8.0, 4.0),
    actor_from_local("bus_01", "bus", "bus_01.png", -7.0, -33.0, 18.0, 3.4, 11.5, 88.0),
    actor_from_local("pedestrian_01", "pedestrian", "pedestrian_01.png", -9.0, -27.0, 20.0, 2.6, 2.6, -8.0),
    actor_from_local("person_01", "person", "person_01.png", -4.5, -30.0, 20.0, 2.6, 2.6, 14.0),
]

UAVS = [
    Uav("uav_01", 35.156515, 129.143955, 140.0, (0.05, 0.45, 1.0), "low-altitude detector view"),
    Uav("uav_02", 35.156965, 129.143420, 150.0, (0.05, 0.82, 0.35), "cross-view confirmation"),
    Uav("uav_03", 35.157150, 129.144580, 160.0, (0.95, 0.48, 0.05), "wide-area context"),
]

SCENARIOS = {
    "s0_locked_roi": Scenario(
        key="s0_locked_roi",
        title="Locked MarineCity ROI",
        description=(
            "Preserves the current saved Marine City georeference and places a "
            "balanced car/person cluster for the first visible smoke test."
        ),
        object_offsets={},
        uav_offsets={},
    ),
    "s1_adjacent_overlap": Scenario(
        key="s1_adjacent_overlap",
        title="Adjacent/Overlapping Small Objects",
        description=(
            "Moves vehicles and pedestrians closer together to stress adjacent "
            "small-object detection and overlap-aware NMS."
        ),
        object_offsets={
            "car_01": (0.000000, 0.000000, 0.0),
            "van_01": (0.000012, -0.000018, 0.0),
            "truck_01": (0.000024, -0.000034, 0.0),
            "bus_01": (-0.000020, 0.000035, 0.0),
            "pedestrian_01": (-0.000010, -0.000020, 0.0),
            "person_01": (-0.000004, -0.000032, 0.0),
        },
        uav_offsets={
            "uav_01": (0.000030, 0.000030, 5.0),
            "uav_02": (-0.000020, 0.000040, 0.0),
            "uav_03": (0.000020, -0.000020, -5.0),
        },
    ),
    "s2_coastline_multiview": Scenario(
        key="s2_coastline_multiview",
        title="Coastline Multi-View Ambiguity",
        description=(
            "Spreads objects toward the road/coast boundary and increases UAV "
            "view diversity for 3D evidence and reasoner testing."
        ),
        object_offsets={
            "car_01": (-0.000030, -0.000045, 0.0),
            "van_01": (-0.000055, 0.000020, 0.0),
            "truck_01": (-0.000075, 0.000070, 0.0),
            "bus_01": (0.000060, -0.000055, 0.0),
            "pedestrian_01": (0.000035, 0.000030, 0.0),
            "person_01": (0.000062, 0.000058, 0.0),
        },
        uav_offsets={
            "uav_01": (-0.000060, -0.000030, 20.0),
            "uav_02": (0.000055, -0.000055, 0.0),
            "uav_03": (-0.000040, 0.000065, -20.0),
        },
    ),
}

ROI_CORNERS = [
    ("roi_sw", 35.156480, 129.143780),
    ("roi_se", 35.156480, 129.144660),
    ("roi_ne", 35.157220, 129.144660),
    ("roi_nw", 35.157220, 129.143780),
]


def shifted_actor(actor: Actor, scenario: Scenario) -> Actor:
    dlat, dlon, dh = scenario.object_offsets.get(actor.actor_id, (0.0, 0.0, 0.0))
    return Actor(
        actor.actor_id,
        actor.class_name,
        actor.texture,
        actor.latitude + dlat,
        actor.longitude + dlon,
        actor.height + dh,
        actor.width,
        actor.length,
        actor.yaw,
    )


def shifted_uav(uav: Uav, scenario: Scenario) -> Uav:
    dlat, dlon, dh = scenario.uav_offsets.get(uav.uav_id, (0.0, 0.0, 0.0))
    height = min(max(uav.height + dh, UAV_ALTITUDE_MIN_M), UAV_ALTITUDE_MAX_M)
    return Uav(
        uav.uav_id,
        uav.latitude + dlat,
        uav.longitude + dlon,
        height,
        uav.color,
        uav.role,
    )


def local_enu_xyz(latitude: float, longitude: float, height: float) -> tuple[float, float, float]:
    """Approximate WGS84 offsets around the locked MarineCity georeference.

    Isaac/Cesium keeps the real streamed city as the base layer. These local
    positions are only for our added actors/cameras so automated captures remain
    stable even when CesiumGlobeAnchor transforms are not evaluated headlessly.
    """

    east = (longitude - BASE_LONGITUDE) * METERS_PER_DEGREE_LON + LOCAL_STAGE_OFFSET_X
    north = (latitude - BASE_LATITUDE) * METERS_PER_DEGREE_LAT + LOCAL_STAGE_OFFSET_Y
    return east, north, height + LOCAL_STAGE_OFFSET_Z


def usd_string(value: str) -> str:
    return json.dumps(value)


def material_block(actor: Actor) -> str:
    mat_path = f"/World/CoM3D_ACE_UAVMarine/Materials/{actor.actor_id}"
    return f"""
            def Material {usd_string(actor.actor_id)}
            {{
                token outputs:surface.connect = <{mat_path}/PreviewSurface.outputs:surface>

                def Shader "PreviewSurface"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor.connect = <{mat_path}/DiffuseTexture.outputs:rgb>
                    color3f inputs:emissiveColor.connect = <{mat_path}/DiffuseTexture.outputs:rgb>
                    float inputs:opacity.connect = <{mat_path}/DiffuseTexture.outputs:a>
                    float inputs:metallic = 0
                    float inputs:roughness = 0.82
                    token outputs:surface
                }}

                def Shader "DiffuseTexture"
                {{
                    uniform token info:id = "UsdUVTexture"
                    asset inputs:file = @./visdrone_objects/{actor.texture}@
                    float2 inputs:st.connect = <{mat_path}/PrimvarReader_st.outputs:result>
                    token inputs:sourceColorSpace = "sRGB"
                    token inputs:wrapS = "clamp"
                    token inputs:wrapT = "clamp"
                    float3 outputs:rgb
                    float outputs:a
                }}

                def Shader "PrimvarReader_st"
                {{
                    uniform token info:id = "UsdPrimvarReader_float2"
                    token inputs:varname = "st"
                    float2 outputs:result
                }}
            }}
"""


def globe_anchor_attrs(latitude: float, longitude: float, height: float, georef_path: str) -> str:
    return f"""                double cesium:anchor:latitude = {latitude:.9f}
                double cesium:anchor:longitude = {longitude:.9f}
                double cesium:anchor:height = {height:.3f}
                bool cesium:anchor:adjustOrientationForGlobeWhenMoving = true
                rel cesium:anchor:georeferenceBinding = <{georef_path}>
"""


def placement_header(placement_mode: str) -> str:
    if placement_mode == "globe_anchor":
        return ' (\n                prepend apiSchemas = ["CesiumGlobeAnchorAPI"]\n            )'
    return ""


def placement_attrs(
    latitude: float,
    longitude: float,
    height: float,
    georef_path: str,
    placement_mode: str,
    include_rotate: bool = False,
    yaw: float = 0.0,
) -> str:
    if placement_mode == "globe_anchor":
        rotate = ""
        order = ""
        if include_rotate:
            rotate = f"                double3 xformOp:rotateXYZ = (0, 0, {yaw:.3f})\n"
            order = '                uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]\n'
        return f"{globe_anchor_attrs(latitude, longitude, height, georef_path)}{rotate}{order}"

    x, y, z = local_enu_xyz(latitude, longitude, height)
    rotate = ""
    order = '                uniform token[] xformOpOrder = ["xformOp:translate"]\n'
    if include_rotate:
        rotate = f"                double3 xformOp:rotateXYZ = (0, 0, {yaw:.3f})\n"
        order = '                uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]\n'
    return f"""                custom string com3d:placement_mode = "local_enu_from_saved_cesium_georeference"
                custom double com3d:wgs84_latitude = {latitude:.9f}
                custom double com3d:wgs84_longitude = {longitude:.9f}
                custom double com3d:wgs84_height = {height:.3f}
                custom double com3d:local_origin_latitude = {BASE_LATITUDE:.9f}
                custom double com3d:local_origin_longitude = {BASE_LONGITUDE:.9f}
                custom double3 com3d:local_stage_offset_xyz = ({LOCAL_STAGE_OFFSET_X:.3f}, {LOCAL_STAGE_OFFSET_Y:.3f}, {LOCAL_STAGE_OFFSET_Z:.3f})
                double3 xformOp:translate = ({x:.3f}, {y:.3f}, {z:.3f})
{rotate}{order}"""


def object_block(actor: Actor, georef_path: str, placement_mode: str) -> str:
    half_w = actor.width / 2.0
    half_l = actor.length / 2.0
    mat_path = f"/World/CoM3D_ACE_UAVMarine/Materials/{actor.actor_id}"
    return f"""
            def Xform {usd_string(actor.actor_id)}{placement_header(placement_mode)}
            {{
{placement_attrs(actor.latitude, actor.longitude, actor.height, georef_path, placement_mode, include_rotate=True, yaw=actor.yaw)}
                custom string com3d:class_name = {usd_string(actor.class_name)}
                custom string com3d:source_dataset = "VisDrone2019-DET"
                custom string com3d:actor_type = "texture_card_from_training_dataset"
                custom double com3d:yaw_degrees = {actor.yaw:.3f}

                def Mesh "TextureCard" (
                    prepend apiSchemas = ["MaterialBindingAPI"]
                )
                {{
                    point3f[] points = [(-{half_w:.3f}, -{half_l:.3f}, 0), ({half_w:.3f}, -{half_l:.3f}, 0), ({half_w:.3f}, {half_l:.3f}, 0), (-{half_w:.3f}, {half_l:.3f}, 0)]
                    int[] faceVertexCounts = [4]
                    int[] faceVertexIndices = [0, 1, 2, 3]
                    bool doubleSided = 1
                    texCoord2f[] primvars:st = [(0, 0), (1, 0), (1, 1), (0, 1)] (
                        interpolation = "vertex"
                    )
                    rel material:binding = <{mat_path}>
                }}
            }}
"""


def roi_marker_block(name: str, latitude: float, longitude: float, georef_path: str, placement_mode: str) -> str:
    return f"""
            def Xform {usd_string(name)}{placement_header(placement_mode)}
            {{
{placement_attrs(latitude, longitude, 22.0, georef_path, placement_mode)}
                custom string com3d:marker_type = "roi_corner"

                def Sphere "Marker"
                {{
                    double radius = 4.0
                    color3f[] primvars:displayColor = [(0.1, 0.45, 1.0)] (
                        interpolation = "constant"
                    )
                }}
            }}
"""


def uav_block(uav: Uav, georef_path: str, placement_mode: str) -> str:
    color = f"({uav.color[0]:.3f}, {uav.color[1]:.3f}, {uav.color[2]:.3f})"
    return f"""
            def Xform {usd_string(uav.uav_id)}{placement_header(placement_mode)}
            {{
{placement_attrs(uav.latitude, uav.longitude, uav.height, georef_path, placement_mode)}
                custom string com3d:role = {usd_string(uav.role)}
                custom string com3d:actor_type = "uav_observer_marker"

                def Sphere "Body"
                {{
                    double radius = 10.0
                    color3f[] primvars:displayColor = [{color}] (
                        interpolation = "constant"
                    )
                }}

                def Sphere "TopBeacon"
                {{
                    double radius = 4.0
                    double3 xformOp:translate = (0, 0, 12)
                    uniform token[] xformOpOrder = ["xformOp:translate"]
                    color3f[] primvars:displayColor = [(1.0, 1.0, 1.0)] (
                        interpolation = "constant"
                    )
                }}

                def Camera "Camera"
                {{
                    float focalLength = 34
                    float horizontalAperture = 20.955
                    float2 clippingRange = (0.1, 2000000)
                    custom string com3d:target = "center_of_VisDrone_object_cluster"
                }}
            }}
"""


def build_overlay(
    base_usd_name: str,
    georef_path: str,
    scenario: Scenario,
    placement_mode: str,
    include_base_sublayer: bool = True,
) -> str:
    actors = [shifted_actor(actor, scenario) for actor in OBJECTS]
    uavs = [shifted_uav(uav, scenario) for uav in UAVS]
    materials = "".join(material_block(actor) for actor in actors)
    objects = "".join(object_block(actor, georef_path, placement_mode) for actor in actors)
    roi = "".join(roi_marker_block(name, lat, lon, georef_path, placement_mode) for name, lat, lon in ROI_CORNERS)
    uav_blocks = "".join(uav_block(uav, georef_path, placement_mode) for uav in uavs)
    sublayers = (
        f"""    subLayers = [
        @{base_usd_name}@
    ]
"""
        if include_base_sublayer
        else ""
    )
    base_note = (
        "Base map: real Cesium Marine City stage saved by the user."
        if include_base_sublayer
        else "Actor-only layer: add this as a session sublayer over the user-saved real Cesium Marine City stage."
    )
    return f"""#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
{sublayers.rstrip()}
)

# CoM3D-ACE non-destructive overlay.
# {base_note}
# This file adds only ROI markers, VisDrone object cards, UAV markers, and
# camera placeholders. It intentionally does not create any fake/proxy city.

over "World"
{{
    def Xform "CoM3D_ACE_UAVMarine"
    {{
        custom string com3d:scene = "Real Cesium Marine City ROI with VisDrone actors and multi-UAV observers"
        custom string com3d:base_usd = {usd_string(base_usd_name)}
        custom string com3d:georeference_binding = {usd_string(georef_path)}
        custom string com3d:placement_mode = {usd_string(placement_mode)}
        custom string com3d:scenario_key = {usd_string(scenario.key)}
        custom string com3d:scenario_title = {usd_string(scenario.title)}
        custom string com3d:scenario_description = {usd_string(scenario.description)}
        custom string com3d:uav_altitude_policy = "UAV marker/camera heights are clamped to 140--160 m; user review height is approximately 160 m."
        custom double com3d:uav_altitude_min_m = {UAV_ALTITUDE_MIN_M:.1f}
        custom double com3d:uav_altitude_max_m = {UAV_ALTITUDE_MAX_M:.1f}
        custom double com3d:review_height_m = {UAV_REVIEW_HEIGHT_M:.1f}
        custom int com3d:object_count = {len(actors)}
        custom int com3d:uav_count = {len(uavs)}
        custom string com3d:note = "This layer adds only object/UAV/ROI/camera primitives. It does not replace or synthesize the city."

        def Scope "Materials"
        {{
{materials}
        }}

        def Scope "ROI"
        {{
            custom string com3d:roi_name = "Haeundae Marine City road/coast object-placement ROI"
{roi}
        }}

        def Xform "Objects"
        {{
            custom string com3d:source_dataset = "VisDrone2019-DET"
            custom string com3d:placement_policy = "WGS84 CesiumGlobeAnchor markers near the manually verified Marine City view"
{objects}
        }}

        def Xform "UAVs"
        {{
            custom string com3d:camera_policy = "Three UAV observer cameras; runtime script orients cameras toward the object cluster"
{uav_blocks}
        }}
    }}
}}
"""


def copy_textures(texture_src: Path, deploy_root: Path) -> None:
    out_dir = deploy_root / "visdrone_objects"
    out_dir.mkdir(parents=True, exist_ok=True)
    for actor in OBJECTS:
        src = texture_src / actor.texture
        if not src.exists():
            raise FileNotFoundError(f"Missing texture: {src}")
        shutil.copy2(src, out_dir / actor.texture)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the UAV MarineCity multi-UAV overlay USD.")
    parser.add_argument("--deploy-root", default="/home/oem/UAV/uav_marinecity")
    parser.add_argument("--base", default="uavmarine.usd")
    parser.add_argument("--out", default="uavmarine_multiuav_overlay.usda")
    parser.add_argument("--georef-path", default=GEORREF_PATH)
    parser.add_argument("--placement-mode", choices=["local_enu", "globe_anchor"], default="local_enu")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="s0_locked_roi")
    parser.add_argument("--all-scenarios", action="store_true")
    parser.add_argument(
        "--actor-only",
        action="store_true",
        help="Do not sublayer the base USD; intended for session-layer injection into an already opened base stage.",
    )
    parser.add_argument("--copy-textures", action="store_true")
    parser.add_argument("--texture-src", default="sim/isaac/assets/visdrone_objects")
    args = parser.parse_args()

    deploy_root = Path(args.deploy_root)
    deploy_root.mkdir(parents=True, exist_ok=True)
    if args.copy_textures:
        copy_textures(Path(args.texture_src), deploy_root)

    outputs: list[dict[str, object]] = []
    selected = list(SCENARIOS.values()) if args.all_scenarios else [SCENARIOS[args.scenario]]
    for scenario in selected:
        out_name = args.out
        if args.all_scenarios:
            stem = Path(args.out).stem
            suffix = Path(args.out).suffix or ".usda"
            out_name = f"{stem}_{scenario.key}{suffix}"
        out_path = deploy_root / out_name
        out_path.write_text(
            build_overlay(
                args.base,
                args.georef_path,
                scenario,
                args.placement_mode,
                include_base_sublayer=not args.actor_only,
            ),
            encoding="utf-8",
        )
        outputs.append(
            {
                "out_path": str(out_path),
                "scenario": scenario.key,
                "title": scenario.title,
                "description": scenario.description,
            }
        )

    manifest = {
        "status": "uavmarine_overlay_written",
        "outputs": outputs,
        "base_usd": str(deploy_root / args.base),
        "georef_path": args.georef_path,
        "placement_mode": args.placement_mode,
        "actor_only": bool(args.actor_only),
        "object_count": len(OBJECTS),
        "uav_count": len(UAVS),
        "roi_corner_count": len(ROI_CORNERS),
        "uav_altitude_policy": {
            "min_m": UAV_ALTITUDE_MIN_M,
            "max_m": UAV_ALTITUDE_MAX_M,
            "review_height_m": UAV_REVIEW_HEIGHT_M,
        },
        "scenario_count": len(outputs),
        "textures_copied": bool(args.copy_textures),
    }
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
