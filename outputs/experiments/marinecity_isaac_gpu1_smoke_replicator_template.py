"""Isaac Sim Replicator capture template for CoM3D-MarineCity.

Open Isaac Sim, load or construct the Marine City USD scene, then run this file
from the Script Editor or adapt it into an Isaac standalone Python workflow.
The repo-side exporter writes the capture plan and validates output schema; this
template is the Isaac-facing capture hook.
"""

from pathlib import Path

import omni.replicator.core as rep


OUTPUT_DIR = Path(r"/home/oem/projects/multi-uav-marine-city/outputs/isaac_exports/marinecity_windows")
RESOLUTION = (1920, 1080)


def main():
    # TODO: Replace these camera prim paths with the UAV camera prims created in
    # the Marine City scene, for example /World/UAVs/uav_01/Camera.
    camera_prims = []
    render_products = [rep.create.render_product(camera, RESOLUTION) for camera in camera_prims]

    writer = rep.WriterRegistry.get("BasicWriter")
    writer.initialize(
        output_dir=str(OUTPUT_DIR),
        rgb=True,
        distance_to_camera=True,
        bounding_box_2d_tight=True,
        bounding_box_3d=True,
        camera_params=True,
        semantic_segmentation=True,
        instance_segmentation=True,
    )
    if render_products:
        writer.attach(render_products)
        rep.orchestrator.step()
    else:
        print("No camera prims configured yet. Fill camera_prims after loading the scene.")


main()
