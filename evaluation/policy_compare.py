"""Policy comparison helpers for re-observation ablation tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(slots=True)
class PolicyOutcome:
    name: str
    final_accuracy: float
    ambiguity_resolution_rate: float
    reobservation_success_rate: float
    delta_entropy: float
    delta_3d_error: float
    reobservation_count: float
    flight_cost: float
    energy_cost: float
    communication_cost: float
    vlm_call_count: float
    latency: float


def compare_policy_outcomes(outcomes: Sequence[PolicyOutcome]) -> list[dict[str, float | str]]:
    """Return paper-table rows for re-observation policy ablations."""

    return [
        {
            "Method": outcome.name,
            "Final Acc ↑": outcome.final_accuracy,
            "Ambiguity Res. ↑": outcome.ambiguity_resolution_rate,
            "Reobs Success ↑": outcome.reobservation_success_rate,
            "ΔEntropy ↓": outcome.delta_entropy,
            "Δ3D Error ↓": outcome.delta_3d_error,
            "Reobs ↓": outcome.reobservation_count,
            "Flight Cost ↓": outcome.flight_cost,
            "Energy Cost ↓": outcome.energy_cost,
            "Communication Cost ↓": outcome.communication_cost,
            "VLM Calls ↓": outcome.vlm_call_count,
            "Latency ↓": outcome.latency,
        }
        for outcome in outcomes
    ]


REOBSERVATION_METHODS = [
    "No re-observation",
    "Random re-observation",
    "Density-guided crop style",
    "Greedy uncertainty",
    "Greedy information gain",
    "CoM3D-ACE policy",
]


def empty_reobservation_table() -> list[dict[str, float | str]]:
    """Create an empty paper-table template with the required method rows."""

    rows = []
    for method in REOBSERVATION_METHODS:
        rows.append(
            {
                "Method": method,
                "Final Acc ↑": "",
                "Ambiguity Res. ↑": "",
                "Reobs Success ↑": "",
                "ΔEntropy ↓": "",
                "Δ3D Error ↓": "",
                "Reobs ↓": 0 if method == "No re-observation" else "",
                "Flight Cost ↓": 0 if method == "No re-observation" else "",
                "Energy Cost ↓": 0 if method == "No re-observation" else "",
                "Communication Cost ↓": 0 if method == "No re-observation" else "",
                "VLM Calls ↓": 0 if method == "No re-observation" else "",
                "Latency ↓": "",
            }
        )
    return rows

