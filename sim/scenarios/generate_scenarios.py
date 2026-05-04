"""Generate sample CoM3D-MarineCity simulation scenarios.

TODO:
- Replace deterministic examples with failure-conditioned generation.
- Add asset placement constraints from the Isaac Sim scene.
- Validate output with scenario_schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path


OUTPUT = Path(__file__).with_name("sample_scenarios.json")


def make_scenario(index: int) -> dict:
    """Create one deterministic sample scenario."""
    ambiguity_pairs = ["van_vs_ambulance", "sedan_vs_pickup", "truck_vs_rescue_vehicle"]
    view_types = ["nadir", "right_oblique", "left_oblique"]
    pair = ambiguity_pairs[index % len(ambiguity_pairs)]
    return {
        "scene_id": f"marinecity_{index:06d}",
        "area": "Busan Haeundae Marine City",
        "uavs": [
            {
                "uav_id": f"UAV_{uav_id}",
                "altitude_m": [100, 150, 200][(index + uav_id) % 3],
                "view_type": view_types[(index + uav_id) % len(view_types)],
                "camera_pose": {
                    "x": 20.0 * uav_id,
                    "y": -15.0 * index,
                    "z": [100.0, 150.0, 200.0][(index + uav_id) % 3],
                    "yaw_deg": 45.0 * uav_id,
                    "pitch_deg": -40.0,
                    "roll_deg": 0.0
                }
            }
            for uav_id in range(1, 4)
        ],
        "objects": [
            {
                "object_id": f"vehicle_{index:03d}",
                "coarse_class": "vehicle",
                "fine_class": ["van", "sedan", "truck"][index % 3],
                "ambiguity_pair": pair,
                "occlusion_level": ["none", "partial", "heavy"][index % 3]
            }
        ],
        "conditions": {
            "weather": ["clear", "cloudy", "hazy"][index % 3],
            "time_of_day": ["morning", "noon", "evening"][index % 3]
        },
        "recommended_next_view": {
            "view_type": ["right_oblique", "rear_oblique", "side_oblique"][index % 3],
            "altitude_m": [80, 100, 120][index % 3],
            "reason": f"Need missing evidence for {pair}."
        }
    }


def generate_scenarios(count: int = 10) -> list[dict]:
    """Generate a list of sample scenarios."""
    return [make_scenario(index) for index in range(count)]


def main() -> None:
    """Write sample scenarios to disk."""
    scenarios = generate_scenarios()
    OUTPUT.write_text(json.dumps(scenarios, indent=2), encoding="utf-8")
    print(f"wrote {len(scenarios)} scenarios to {OUTPUT}")


if __name__ == "__main__":
    main()

