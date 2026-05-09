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


REOBSERVATION_COLUMNS = [
    "Method",
    "Final_Acc",
    "Ambiguity_Res",
    "Reobs_Success",
    "Delta_Entropy",
    "Delta_3D_Error",
    "Reobs",
    "Flight_Cost",
    "Energy_Cost",
    "Communication_Cost",
    "VLM_Calls",
    "Latency",
]


def compare_policy_outcomes(outcomes: Sequence[PolicyOutcome]) -> list[dict[str, float | str]]:
    """Return paper-table rows for re-observation policy ablations."""

    return [
        {
            "Method": outcome.name,
            "Final_Acc": outcome.final_accuracy,
            "Ambiguity_Res": outcome.ambiguity_resolution_rate,
            "Reobs_Success": outcome.reobservation_success_rate,
            "Delta_Entropy": outcome.delta_entropy,
            "Delta_3D_Error": outcome.delta_3d_error,
            "Reobs": outcome.reobservation_count,
            "Flight_Cost": outcome.flight_cost,
            "Energy_Cost": outcome.energy_cost,
            "Communication_Cost": outcome.communication_cost,
            "VLM_Calls": outcome.vlm_call_count,
            "Latency": outcome.latency,
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
        no_reobs = method == "No re-observation"
        rows.append(
            {
                "Method": method,
                "Final_Acc": "",
                "Ambiguity_Res": "",
                "Reobs_Success": "",
                "Delta_Entropy": "",
                "Delta_3D_Error": "",
                "Reobs": 0 if no_reobs else "",
                "Flight_Cost": 0 if no_reobs else "",
                "Energy_Cost": 0 if no_reobs else "",
                "Communication_Cost": 0 if no_reobs else "",
                "VLM_Calls": 0 if no_reobs else "",
                "Latency": "",
            }
        )
    return rows
