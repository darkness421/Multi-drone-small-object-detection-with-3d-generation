"""Selective VLM verification ablation table helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VLMOutcome:
    name: str
    ambiguous_subset_accuracy: float
    correction_rate: float
    over_correction_rate: float
    vlm_call_count: float
    average_tokens: float
    latency: float
    explanation_usefulness: float
    json_parse_success_rate: float


VLM_METHODS = [
    "No VLM",
    "Always-on VLM",
    "Random VLM",
    "Uncertainty-triggered VLM",
    "SAGE-triggered VLM",
]


def compare_vlm_outcomes(outcomes: list[VLMOutcome]) -> list[dict[str, float | str]]:
    return [
        {
            "Method": outcome.name,
            "Ambiguous Acc ↑": outcome.ambiguous_subset_accuracy,
            "Correction Rate ↑": outcome.correction_rate,
            "Over-correction ↓": outcome.over_correction_rate,
            "VLM Calls ↓": outcome.vlm_call_count,
            "Avg Tokens ↓": outcome.average_tokens,
            "Latency ↓": outcome.latency,
            "Explanation Usefulness ↑": outcome.explanation_usefulness,
            "JSON Parse Success ↑": outcome.json_parse_success_rate,
        }
        for outcome in outcomes
    ]


def empty_vlm_table() -> list[dict[str, float | str]]:
    rows = []
    for method in VLM_METHODS:
        rows.append(
            {
                "Method": method,
                "Ambiguous Acc ↑": "",
                "Correction Rate ↑": "",
                "Over-correction ↓": "",
                "VLM Calls ↓": 0 if method == "No VLM" else "",
                "Avg Tokens ↓": 0 if method == "No VLM" else "",
                "Latency ↓": "",
                "Explanation Usefulness ↑": "",
                "JSON Parse Success ↑": "",
            }
        )
    return rows

