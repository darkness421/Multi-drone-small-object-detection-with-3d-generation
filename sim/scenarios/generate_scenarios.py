"""Generate controlled CoM3D-MarineCity simulation scenarios.

The generator creates ambiguity-centric hard cases for Marine City digital twin
experiments. It uses only the Python standard library so it can run before the
Isaac Sim environment is installed.

TODO:
- Replace placeholder object positions with real Marine City asset constraints.
- Add geometry-aware collision checks.
- Add Isaac Replicator scenario export after the simulator setup is ready.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path(__file__).with_name("sample_scenarios.json")
AREA_NAME = "Busan Haeundae Marine City"
ALTITUDES_M = (50, 80, 100, 150, 200)
WEATHER_CONDITIONS = ("clear", "cloudy", "hazy", "shadow-heavy")
TIME_OF_DAY = ("morning", "noon", "evening")
UAV_COUNTS = (1, 2, 3, 5)


@dataclass(frozen=True)
class AmbiguityCase:
    """Definition of one fine-grained ambiguity case."""

    case_id: str
    coarse_class: str
    fine_classes: tuple[str, str]
    missing_evidence: tuple[str, ...]
    recommended_view: str
    recommended_altitude_m: int
    context: str


AMBIGUITY_CASES = (
    AmbiguityCase(
        case_id="van_vs_ambulance",
        coarse_class="vehicle",
        fine_classes=("van", "ambulance"),
        missing_evidence=("side marking", "roof light bar", "vehicle side profile"),
        recommended_view="right_oblique",
        recommended_altitude_m=80,
        context="urban road near high-rise buildings",
    ),
    AmbiguityCase(
        case_id="sedan_vs_pickup",
        coarse_class="vehicle",
        fine_classes=("sedan", "pickup"),
        missing_evidence=("rear cargo bed", "side silhouette"),
        recommended_view="rear_oblique",
        recommended_altitude_m=80,
        context="roadside parking and shadowed lanes",
    ),
    AmbiguityCase(
        case_id="truck_vs_rescue_vehicle",
        coarse_class="vehicle",
        fine_classes=("truck", "rescue_vehicle"),
        missing_evidence=("emergency marking", "equipment outline", "side profile"),
        recommended_view="side_oblique",
        recommended_altitude_m=100,
        context="wide road next to waterfront buildings",
    ),
    AmbiguityCase(
        case_id="pedestrian_vs_worker",
        coarse_class="person",
        fine_classes=("pedestrian", "worker"),
        missing_evidence=("safety vest", "helmet", "work zone context"),
        recommended_view="front_oblique",
        recommended_altitude_m=50,
        context="construction or maintenance zone",
    ),
    AmbiguityCase(
        case_id="small_boat_vs_debris",
        coarse_class="marine_object",
        fine_classes=("small_boat", "debris"),
        missing_evidence=("object shape", "wake pattern", "nearby sea context"),
        recommended_view="left_oblique",
        recommended_altitude_m=100,
        context="waterfront and marina edge",
    ),
)


def camera_pose(index: int, uav_number: int, altitude_m: int, view_type: str) -> dict[str, float]:
    """Create a deterministic camera pose placeholder in a local ENU frame."""
    yaw_by_view = {
        "nadir": 0.0,
        "front_oblique": 0.0,
        "rear_oblique": 180.0,
        "left_oblique": -90.0,
        "right_oblique": 90.0,
        "side_oblique": 90.0,
    }
    pitch = -90.0 if view_type == "nadir" else -42.0
    return {
        "x": round((uav_number - 1) * 45.0 - 60.0, 3),
        "y": round((index % 7) * 18.0 - 54.0, 3),
        "z": float(altitude_m),
        "yaw_deg": yaw_by_view.get(view_type, 0.0),
        "pitch_deg": pitch,
        "roll_deg": 0.0,
    }


def view_sequence(case: AmbiguityCase, uav_count: int) -> list[str]:
    """Choose UAV views so the missing evidence is recoverable by the recommended view."""
    base_views = ["nadir", "front_oblique", "left_oblique", "right_oblique", "rear_oblique"]
    views = base_views[: max(1, min(uav_count, len(base_views)))]
    if case.recommended_view not in views and views:
        views[-1] = case.recommended_view
    return views


def make_uavs(index: int, case: AmbiguityCase, uav_count: int) -> list[dict[str, Any]]:
    """Create UAV settings for one scenario."""
    views = view_sequence(case, uav_count)
    uavs = []
    for offset, view_type in enumerate(views, start=1):
        altitude = ALTITUDES_M[(index + offset) % len(ALTITUDES_M)]
        if view_type == case.recommended_view:
            altitude = case.recommended_altitude_m
        uavs.append(
            {
                "uav_id": f"UAV_{offset}",
                "altitude_m": altitude,
                "view_type": view_type,
                "camera_pose": camera_pose(index, offset, altitude, view_type),
            }
        )
    return uavs


def make_object(index: int, case: AmbiguityCase, occlusion_level: str) -> dict[str, Any]:
    """Create one controlled ambiguous object."""
    fine_class = case.fine_classes[index % len(case.fine_classes)]
    return {
        "object_id": f"{case.coarse_class}_{index:04d}",
        "coarse_class": case.coarse_class,
        "fine_class": fine_class,
        "candidate_fine_classes": list(case.fine_classes),
        "ambiguity_pair": case.case_id,
        "ambiguity_type": case.case_id,
        "missing_evidence": list(case.missing_evidence),
        "occlusion_level": occlusion_level,
        "context": case.context,
        "local_position": {
            "east_m": round((index % 5) * 12.0 - 24.0, 3),
            "north_m": round((index % 6) * 10.0 - 30.0, 3),
            "up_m": 0.0,
        },
    }


def make_scenario(index: int) -> dict[str, Any]:
    """Create one controlled sample scenario."""
    case = AMBIGUITY_CASES[index % len(AMBIGUITY_CASES)]
    uav_count = UAV_COUNTS[index % len(UAV_COUNTS)]
    occlusion_level = ("none", "partial", "heavy")[index % 3]
    weather = WEATHER_CONDITIONS[index % len(WEATHER_CONDITIONS)]
    time_of_day = TIME_OF_DAY[index % len(TIME_OF_DAY)]
    return {
        "scene_id": f"marinecity_{index:06d}",
        "area": AREA_NAME,
        "scenario_type": "ambiguity_controlled",
        "uav_count": uav_count,
        "uavs": make_uavs(index, case, uav_count),
        "objects": [make_object(index, case, occlusion_level)],
        "conditions": {
            "weather": weather,
            "time_of_day": time_of_day,
            "expected_failure_mode": case.case_id,
        },
        "recommended_next_view": {
            "view_type": case.recommended_view,
            "altitude_m": case.recommended_altitude_m,
            "reason": (
                f"Need {', '.join(case.missing_evidence)} to resolve "
                f"{case.fine_classes[0]} vs {case.fine_classes[1]}."
            ),
        },
        "paper_tags": [
            "CoM3D-MarineCity",
            "ambiguity-centric",
            "multi-uav",
            case.case_id,
        ],
    }


def generate_scenarios(count: int = 20) -> list[dict[str, Any]]:
    """Generate a list of controlled scenarios."""
    return [make_scenario(index) for index in range(count)]


def validate_scenario(scenario: dict[str, Any]) -> None:
    """Validate core fields without external jsonschema dependency."""
    required = ("scene_id", "area", "uavs", "objects", "conditions", "recommended_next_view")
    for key in required:
        if key not in scenario:
            raise ValueError(f"missing required scenario key: {key}")
    if not scenario["uavs"]:
        raise ValueError("scenario must include at least one UAV")
    if not scenario["objects"]:
        raise ValueError("scenario must include at least one object")
    for uav in scenario["uavs"]:
        for key in ("uav_id", "altitude_m", "view_type", "camera_pose"):
            if key not in uav:
                raise ValueError(f"missing UAV key: {key}")
    for obj in scenario["objects"]:
        for key in ("object_id", "coarse_class", "fine_class", "ambiguity_pair", "occlusion_level"):
            if key not in obj:
                raise ValueError(f"missing object key: {key}")


def write_scenarios(scenarios: list[dict[str, Any]], output: Path) -> None:
    """Validate and write scenarios."""
    for scenario in scenarios:
        validate_scenario(scenario)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scenarios, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Generate CoM3D-MarineCity scenarios.")
    parser.add_argument("--count", type=int, default=20, help="Number of scenarios to generate.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSON path.")
    return parser.parse_args()


def main() -> None:
    """Write sample scenarios to disk."""
    args = parse_args()
    scenarios = generate_scenarios(args.count)
    write_scenarios(scenarios, args.output)
    print(f"wrote {len(scenarios)} scenarios to {args.output}")


if __name__ == "__main__":
    main()
