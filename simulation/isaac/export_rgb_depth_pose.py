"""Export RGB/depth/pose annotation manifests from Isaac Sim.

This module is intentionally importable outside Isaac Sim. Use --dry-run on a
normal Python environment to validate paths, config loading, and output schema.
Inside Isaac Sim, replace the dry-run frame generator with Replicator/ROS2
capture calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime import load_config, prepare_run_dir, setup_logging
from runtime.config import resolve_path
from simulation.isaac.marinecity_plan import build_capture_plan, build_dry_run_manifest, write_capture_plan


def write_manifest(manifest: dict[str, Any], out_path: str | Path) -> Path:
    out_path = resolve_path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def create_placeholder_files(manifest: dict[str, Any], output_root: str | Path) -> None:
    root = resolve_path(output_root)
    for frame in manifest.get("frames", []):
        for key, content in {
            "rgb_path": "placeholder rgb file for Isaac export dry-run\n",
            "pose_path": json.dumps({"placeholder": True, "image_id": frame.get("image_id")}, indent=2),
        }.items():
            rel = frame.get(key)
            if not rel:
                continue
            path = root / str(rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(content, encoding="utf-8")
        depth = frame.get("depth_path")
        if depth:
            path = root / str(depth)
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("placeholder depth file for Isaac export dry-run\n", encoding="utf-8")


def write_replicator_template(config: dict[str, Any], out_path: str | Path) -> Path:
    """Write a small Isaac Script Editor template for the generated capture plan."""
    out = resolve_path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    width = int(config.get("camera", {}).get("width", 1920))
    height = int(config.get("camera", {}).get("height", 1080))
    text = f'''"""Isaac Sim Replicator capture template for CoM3D-MarineCity.

Open Isaac Sim, load or construct the Marine City USD scene, then run this file
from the Script Editor or adapt it into an Isaac standalone Python workflow.
The repo-side exporter writes the capture plan and validates output schema; this
template is the Isaac-facing capture hook.
"""

from pathlib import Path

import omni.replicator.core as rep


OUTPUT_DIR = Path(r"{resolve_path(config.get('output_root', 'outputs/isaac_exports'))}")
RESOLUTION = ({width}, {height})


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
'''
    out.write_text(text, encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CoM3D-UAV-Sim RGB/depth/pose manifest.")
    parser.add_argument("--config", default="configs/sim/isaac_export.yaml")
    parser.add_argument("--out", default=None)
    parser.add_argument("--plan-out", default=None, help="Optional capture-plan JSON path.")
    parser.add_argument("--template-out", default=None, help="Optional Isaac Replicator template path.")
    parser.add_argument("--create-placeholders", action="store_true", help="Create tiny placeholder files for dry-run frame paths.")
    parser.add_argument("--isaac-smoke", action="store_true", help="Inside Isaac Python, only verify Replicator import and write plan/template.")
    parser.add_argument("--dry-run", action="store_true", help="Generate a schema-valid manifest without Isaac imports.")
    args = parser.parse_args()

    config = load_config(args.config)
    run_dir = prepare_run_dir("isaac_export", output_root=config.get("output_root", "outputs/isaac_exports"))
    logger = setup_logging(run_dir / "logs" / "export.log")
    out_path = Path(args.out) if args.out else run_dir / "manifest.json"

    plan = build_capture_plan(config)
    plan_path = Path(args.plan_out) if args.plan_out else run_dir / "capture_plan.json"
    write_capture_plan(plan, plan_path)
    template_path = Path(args.template_out) if args.template_out else run_dir / "isaac_replicator_capture_template.py"
    write_replicator_template(config, template_path)

    if args.dry_run:
        manifest = build_dry_run_manifest(config)
        write_manifest(manifest, out_path)
        if args.create_placeholders:
            create_placeholder_files(manifest, Path(out_path).parent)
        logger.info("Wrote dry-run Isaac manifest to %s", out_path)
        logger.info("Wrote capture plan to %s", plan_path)
        logger.info("Wrote Isaac Replicator template to %s", template_path)
        print(out_path)
        return

    try:
        import omni.replicator.core as rep  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Run this script with Isaac Sim python.bat, or use --dry-run outside Isaac Sim.") from exc

    if args.isaac_smoke:
        logger.info("Isaac Replicator import OK. Capture plan/template are ready.")
        print(f"Isaac Replicator import OK. Plan: {plan_path}")
        print(f"Template: {template_path}")
        return

    raise NotImplementedError("Isaac runtime capture is scaffolded; implement Replicator capture calls here.")


if __name__ == "__main__":
    main()
