"""System-level comparison table helpers for CoM3D-ACE."""

from __future__ import annotations


SYSTEM_METHODS = [
    "Single-view detector",
    "Multi-view average pooling",
    "Multi-view max pooling",
    "Naive 3D fusion",
    "Graph-only",
    "Graph + cross-view alignment",
    "Graph + ambiguity diagnosis",
    "Graph + random re-observation",
    "Graph + uncertainty re-observation",
    "Full CoM3D-ACE",
]


SYSTEM_COLUMNS = [
    "Method",
    "Final_Acc",
    "Center_3D_Error",
    "Assoc_F1",
    "Ambiguity_Res",
    "Reobs",
    "VLM_Calls",
]


def empty_system_table() -> list[dict[str, str | int]]:
    """Return an empty system-level comparison table template."""

    rows: list[dict[str, str | int]] = []
    zero_reobs_methods = {
        "Single-view detector",
        "Multi-view average pooling",
        "Multi-view max pooling",
        "Naive 3D fusion",
        "Graph-only",
        "Graph + cross-view alignment",
        "Graph + ambiguity diagnosis",
    }
    no_ambiguity_methods = {
        "Single-view detector",
        "Multi-view average pooling",
        "Multi-view max pooling",
        "Naive 3D fusion",
    }
    for method in SYSTEM_METHODS:
        rows.append(
            {
                "Method": method,
                "Final_Acc": "",
                "Center_3D_Error": "",
                "Assoc_F1": "-" if method == "Single-view detector" else "",
                "Ambiguity_Res": "-" if method in no_ambiguity_methods else "",
                "Reobs": 0 if method in zero_reobs_methods else "",
                "VLM_Calls": 0 if method != "Full CoM3D-ACE" else "",
            }
        )
    return rows
