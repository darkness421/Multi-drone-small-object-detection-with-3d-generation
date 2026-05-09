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


VLM_COLUMNS = [
    "Method",
    "Ambiguous_Acc",
    "Correction_Rate",
    "Over_Correction",
    "VLM_Calls",
    "Avg_Tokens",
    "Latency",
    "Explanation_Usefulness",
    "JSON_Parse_Success",
]


def compare_vlm_outcomes(outcomes: list[VLMOutcome]) -> list[dict[str, float | str]]:
    """Return paper-table rows for selective VLM ablations."""

    return [
        {
            "Method": outcome.name,
            "Ambiguous_Acc": outcome.ambiguous_subset_accuracy,
            "Correction_Rate": outcome.correction_rate,
            "Over_Correction": outcome.over_correction_rate,
            "VLM_Calls": outcome.vlm_call_count,
            "Avg_Tokens": outcome.average_tokens,
            "Latency": outcome.latency,
            "Explanation_Usefulness": outcome.explanation_usefulness,
            "JSON_Parse_Success": outcome.json_parse_success_rate,
        }
        for outcome in outcomes
    ]


def empty_vlm_table() -> list[dict[str, float | str]]:
    """Create an empty selective VLM comparison table."""

    rows = []
    for method in VLM_METHODS:
        no_vlm = method == "No VLM"
        rows.append(
            {
                "Method": method,
                "Ambiguous_Acc": "",
                "Correction_Rate": "",
                "Over_Correction": "",
                "VLM_Calls": 0 if no_vlm else "",
                "Avg_Tokens": 0 if no_vlm else "",
                "Latency": "",
                "Explanation_Usefulness": "",
                "JSON_Parse_Success": "",
            }
        )
    return rows
