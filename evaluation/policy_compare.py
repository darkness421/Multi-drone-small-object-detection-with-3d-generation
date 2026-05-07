"""Policy comparison helpers for ablation tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(slots=True)
class PolicyOutcome:
    name: str
    final_accuracy: float
    ambiguity_resolution_rate: float
    reobservation_count: float
    flight_cost: float
    vlm_call_count: float
    latency: float


def compare_policy_outcomes(outcomes: Sequence[PolicyOutcome]) -> list[dict[str, float | str]]:
    """Return paper-table rows for no-reobserve/random/uncertainty/CoM3D policies."""

    return [
        {
            "policy": outcome.name,
            "final_accuracy": outcome.final_accuracy,
            "ambiguity_resolution_rate": outcome.ambiguity_resolution_rate,
            "reobservation_count": outcome.reobservation_count,
            "flight_cost": outcome.flight_cost,
            "VLM_call_count": outcome.vlm_call_count,
            "latency": outcome.latency,
        }
        for outcome in outcomes
    ]

