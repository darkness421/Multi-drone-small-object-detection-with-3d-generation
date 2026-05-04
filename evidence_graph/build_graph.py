"""Build a JSON-based 3D object evidence graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from graph_schema import EvidenceNode, graph_document


def build_dummy_graph() -> dict:
    """Build one dummy evidence graph."""
    node = EvidenceNode(
        object_id="vehicle_021",
        coarse_class="vehicle",
        fine_class_candidates=["van", "ambulance"],
        center_3d=[0.0, 0.0, 0.0],
        multi_view_crops=[
            "crops/scene_000132/uav1_vehicle_021.png",
            "crops/scene_000132/uav2_vehicle_021.png"
        ],
        per_view_logits={
            "UAV_1": {"van": 0.48, "ambulance": 0.44},
            "UAV_2": {"van": 0.30, "ambulance": 0.62}
        },
        view_angles={"UAV_1": "nadir", "UAV_2": "right_oblique"},
        occlusion_level="partial",
        uncertainty=0.42,
        ambiguity_type="van_vs_ambulance",
        missing_evidence=["side marking", "roof light bar"],
        recommended_next_view={
            "view_type": "right_oblique",
            "altitude": 80,
            "reason": "Need side marking and roof light bar evidence."
        }
    )
    return graph_document([node])


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Build dummy evidence graph.")
    parser.add_argument("--output", type=Path, default=Path("outputs/results/dummy_evidence_graph.json"))
    return parser.parse_args()


def main() -> None:
    """Write dummy graph JSON."""
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_dummy_graph(), indent=2), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

