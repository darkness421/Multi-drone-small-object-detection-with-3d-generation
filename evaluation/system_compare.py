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


SYSTEM_COLUMNS = ["Method", "Final Acc ↑", "3D Error ↓", "Assoc. F1 ↑", "Ambiguity Res. ↑", "Reobs ↓", "VLM Calls ↓"]


def empty_system_table() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for method in SYSTEM_METHODS:
        rows.append(
            {
                "Method": method,
                "Final Acc ↑": "",
                "3D Error ↓": "",
                "Assoc. F1 ↑": "-" if method == "Single-view detector" else "",
                "Ambiguity Res. ↑": "-" if method in {"Single-view detector", "Multi-view average pooling", "Multi-view max pooling", "Naive 3D fusion"} else "",
                "Reobs ↓": 0
                if method
                in {
                    "Single-view detector",
                    "Multi-view average pooling",
                    "Multi-view max pooling",
                    "Naive 3D fusion",
                    "Graph-only",
                    "Graph + cross-view alignment",
                    "Graph + ambiguity diagnosis",
                }
                else "",
                "VLM Calls ↓": 0 if method != "Full CoM3D-ACE" else "",
            }
        )
    return rows

