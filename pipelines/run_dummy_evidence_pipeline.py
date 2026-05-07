"""Run a dummy end-to-end evidence pipeline.

Input:
- One CoM3D-MarineCity annotation JSON.

Output:
- COCO-style 2D annotation JSON.
- Evidence JSON preserving multi-view metadata.
- Per-view synthetic 3D lifting JSON.
- Object-centered 3D evidence graph JSON.
- Pipeline summary JSON.

This script intentionally uses synthetic depth maps and identity camera
extrinsics so it can run before Isaac Sim capture is available.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datasets.converters.marinecity_to_coco import convert, load_json, validate_annotation
from evidence_graph.graph_schema import EvidenceNode, graph_document
from lifting3d.depth_lifting import estimate_object_center_3d


DEFAULT_INPUT = Path("datasets/converters/dummy_marinecity_input.json")
DEFAULT_OUTPUT_DIR = Path("outputs/pipeline_dummy")


def synthetic_depth_map(width: int, height: int, altitude: float) -> np.ndarray:
    """Create a deterministic synthetic depth map for placeholder lifting."""
    base_depth = max(5.0, altitude * 0.12)
    return np.full((height, width), base_depth, dtype=float)


def synthetic_intrinsics(width: int, height: int) -> np.ndarray:
    """Create simple pinhole camera intrinsics."""
    focal = float(max(width, height))
    return np.array(
        [
            [focal, 0.0, width / 2.0],
            [0.0, focal, height / 2.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def synthetic_extrinsics(view_index: int, altitude: float) -> np.ndarray:
    """Create a simple world transform for placeholder lifting."""
    transform = np.eye(4, dtype=float)
    transform[0, 3] = view_index * 5.0
    transform[1, 3] = view_index * -3.0
    transform[2, 3] = altitude
    return transform


def lift_views(annotation: dict[str, Any]) -> list[dict[str, Any]]:
    """Lift each view bbox into a synthetic 3D hypothesis."""
    lifted = []
    for view_index, view in enumerate(annotation["views"], start=1):
        width = int(view["width"])
        height = int(view["height"])
        altitude = float(view["altitude"])
        depth = synthetic_depth_map(width, height, altitude)
        intrinsics = synthetic_intrinsics(width, height)
        extrinsics = synthetic_extrinsics(view_index, altitude)
        lifting = estimate_object_center_3d(
            tuple(int(value) for value in view["bbox_2d"]),
            depth,
            intrinsics,
            extrinsics,
        )
        lifted.append(
            {
                "uav_id": view["uav_id"],
                "view_type": view["view_type"],
                "bbox_2d": view["bbox_2d"],
                "synthetic_depth_m": float(depth[0, 0]),
                "lifting": lifting,
            }
        )
    return lifted


def average_center(lifted_views: list[dict[str, Any]]) -> list[float]:
    """Average lifted centers across views."""
    centers = np.array([view["lifting"]["center_3d"] for view in lifted_views], dtype=float)
    return centers.mean(axis=0).tolist()


def mean_uncertainty(lifted_views: list[dict[str, Any]]) -> float:
    """Average uncertainty across lifted views."""
    values = [float(view["lifting"]["uncertainty"]) for view in lifted_views]
    return float(sum(values) / len(values)) if values else 1.0


def build_graph_from_evidence(evidence: dict[str, Any], lifted_views: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an object-centered evidence graph from evidence and lifted views."""
    fine_class = evidence["fine_class"]
    ambiguity_type = evidence["ambiguity_type"]
    candidate_classes = sorted(
        set(
            part
            for part in ambiguity_type.split("_vs_")
            if part
        )
        | {fine_class}
    )
    per_view_logits = {
        view["uav_id"]: {
            candidate: (0.65 if candidate == fine_class else 0.35 / max(1, len(candidate_classes) - 1))
            for candidate in candidate_classes
        }
        for view in lifted_views
    }
    view_angles = {view["uav_id"]: view["view_type"] for view in lifted_views}
    crop_paths = [
        f"crops/{evidence['scene_id']}/{view['uav_id']}_{evidence['object_id']}.png"
        for view in lifted_views
    ]
    node = EvidenceNode(
        object_id=evidence["object_id"],
        coarse_class=evidence["coarse_class"],
        fine_class_candidates=candidate_classes,
        center_3d=average_center(lifted_views),
        multi_view_crops=crop_paths,
        per_view_logits=per_view_logits,
        view_angles=view_angles,
        occlusion_level=evidence["occlusion_level"],
        uncertainty=mean_uncertainty(lifted_views),
        ambiguity_type=ambiguity_type,
        missing_evidence=evidence["missing_evidence"],
        recommended_next_view=evidence["recommended_next_view"],
    )
    return graph_document([node])


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    """Write JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run_pipeline(input_path: Path, output_dir: Path) -> dict[str, str]:
    """Run the dummy evidence pipeline and return generated file paths."""
    annotation = load_json(input_path)
    validate_annotation(annotation)
    coco, evidence = convert(annotation)
    lifted_views = lift_views(annotation)
    graph = build_graph_from_evidence(evidence, lifted_views)

    outputs = {
        "coco": output_dir / "coco.json",
        "evidence": output_dir / "evidence.json",
        "lifted_views": output_dir / "lifted_views.json",
        "evidence_graph": output_dir / "evidence_graph.json",
        "summary": output_dir / "summary.json",
    }
    summary = {
        "input": str(input_path),
        "scene_id": evidence["scene_id"],
        "object_id": evidence["object_id"],
        "fine_class": evidence["fine_class"],
        "ambiguity_type": evidence["ambiguity_type"],
        "num_views": len(lifted_views),
        "recommended_next_view": evidence["recommended_next_view"],
        "outputs": {key: str(path) for key, path in outputs.items() if key != "summary"},
    }

    write_json(outputs["coco"], coco)
    write_json(outputs["evidence"], evidence)
    write_json(outputs["lifted_views"], lifted_views)
    write_json(outputs["evidence_graph"], graph)
    write_json(outputs["summary"], summary)
    return {key: str(path) for key, path in outputs.items()}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run dummy CoM3D evidence pipeline.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    """Run from CLI."""
    args = parse_args()
    outputs = run_pipeline(args.input, args.output_dir)
    print(json.dumps(outputs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
