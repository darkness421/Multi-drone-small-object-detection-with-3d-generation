"""Build a compact status page for detector experiments and next actions."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: Any, digits: int = 4) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.{digits}f}"


def fmt_params(value: Any) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "-"
    return f"{parsed / 1_000_000:.2f}M"


def table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows yet._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def top_models(summary_rows: list[dict[str, str]], limit: int) -> list[list[str]]:
    completed = [row for row in summary_rows if as_float(row.get("best_AP_mean")) is not None]
    completed.sort(key=lambda row: as_float(row.get("best_AP_mean")) or -1, reverse=True)
    rows: list[list[str]] = []
    for index, row in enumerate(completed[:limit], start=1):
        rows.append(
            [
                str(index),
                row.get("method") or row.get("model") or "-",
                row.get("dataset") or "-",
                row.get("detector_family") or "-",
                row.get("param_size_group") or row.get("model_scale") or "-",
                row.get("seed_count") or "-",
                row.get("analysis_level") or "-",
                fmt(row.get("best_AP_mean")),
                fmt(row.get("best_AP50_mean")),
                fmt(row.get("best_recall_mean")),
                fmt(row.get("best_F1_mean")),
                fmt_params(row.get("Params_mean")),
                fmt(row.get("GFLOPs_mean"), 1),
            ]
        )
    return rows


def availability_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    wanted = {
        "local_weight_found",
        "ultralytics_or_queue_candidate",
        "blocked_external_assets",
    }
    ordered = [row for row in rows if row.get("runnable_status") in wanted]
    priority = {
        "local_weight_found": 0,
        "ultralytics_or_queue_candidate": 1,
        "blocked_external_assets": 2,
    }
    ordered.sort(key=lambda row: (priority.get(row.get("runnable_status", ""), 9), row.get("name", "")))
    return [
        [
            row.get("name", "-"),
            row.get("family", "-"),
            row.get("architecture_group", "-"),
            row.get("size", "-"),
            row.get("runnable_status", "-"),
            row.get("recommended_action", "-"),
        ]
        for row in ordered[:14]
    ]


def dataset_rows(uavdt_summary: dict[str, Any]) -> list[list[str]]:
    rows = [
        ["VisDrone2019-DET", "ready", "configs/detector/visdrone_yolo_data.yaml", "primary detector baseline/proposed dataset"],
    ]
    if uavdt_summary.get("ready"):
        rows.append(
            [
                "UAVDT",
                "ready",
                f"{uavdt_summary.get('image_count', '-')} images / {uavdt_summary.get('annotation_count', '-')} boxes",
                "cross-dataset validation after active queues",
            ]
        )
    else:
        rows.append(["UAVDT", "not ready", "-", "prepare before cross-dataset training"])
    return rows


def write_status(args: argparse.Namespace) -> Path:
    summary_csv = resolve_path(args.summary_csv)
    stage_gate_json = resolve_path(args.stage_gate_json)
    availability_csv = resolve_path(args.availability_csv)
    uavdt_summary_json = resolve_path(args.uavdt_summary_json)
    out = resolve_path(args.out)

    summary_rows = read_csv(summary_csv)
    stage_gate = read_json(stage_gate_json)
    availability = read_csv(availability_csv)
    uavdt_summary = read_json(uavdt_summary_json)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")

    lines = [
        "# Detector Experiment Status",
        "",
        f"Generated: `{generated}`",
        "",
        "This page is the quick navigation point for detector experiments while long server training is running.",
        "",
        "## Current Queue",
        "",
        table(
            ["Order", "Session", "Role", "Action"],
            [
                ["1", "`server-large-comparison`", "VisDrone L-size anchors", "running"],
                ["2", "`server-top3-proposed-pending`", "top-3 proposed ablation", "waits for large comparison"],
                ["3", "`server-uavdt-comparisons-pending`", "UAVDT cross-dataset comparison", "waits for large and proposed queues"],
            ],
        ),
        "",
        "## Stage Gate",
        "",
        f"- Recommended next stage: `{stage_gate.get('recommended_next_stage', 'not generated')}`",
        f"- Rationale: {stage_gate.get('rationale', 'not generated')}",
        f"- Gate dataset: `{stage_gate.get('dataset', 'all')}`",
        "",
        "## Dataset Readiness",
        "",
        table(["Dataset", "Status", "Evidence", "Use"], dataset_rows(uavdt_summary)),
        "",
        "## Current Top Detector Rows",
        "",
        table(
            ["Rank", "Method", "Dataset", "Family", "Size", "Seeds", "Level", "AP", "AP50", "Recall", "F1", "Params", "GFLOPs"],
            top_models(summary_rows, args.top_k),
        ),
        "",
        "## Paper Comparison Availability",
        "",
        table(["Model", "Family", "Group", "Size", "Runnable Status", "Action"], availability_rows(availability)),
        "",
        "## Next Actions",
        "",
        "1. Let the active VisDrone large comparison finish.",
        "2. Let the top-3 proposed ablation run on the selected backbones.",
        "3. Run UAVDT cross-dataset comparison from the pending queue.",
        "4. Recollect with `bash scripts/ubuntu/collect_proposed_results.sh` and `bash scripts/ubuntu/collect_cross_dataset_results.sh`.",
        "5. If the proposed gate beats best overall and best lightweight baselines, freeze the detector checkpoint for Isaac Sim and 3D benchmark work.",
        "",
        "## Report Links",
        "",
        "- `outputs/reports/server_with_proposed/README.md`",
        "- `outputs/reports/server_with_proposed/paper_model_availability.md`",
        "- `outputs/experiments/server_with_proposed_stage_gate.md`",
        "- `docs/notion_research_comparison_notes.md`",
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build detector experiment status markdown.")
    parser.add_argument("--summary-csv", default="outputs/experiments/server_with_proposed_summary.csv")
    parser.add_argument("--stage-gate-json", default="outputs/experiments/server_with_proposed_stage_gate.json")
    parser.add_argument("--availability-csv", default="outputs/experiments/paper_model_availability.csv")
    parser.add_argument("--uavdt-summary-json", default="outputs/experiments/uavdt_prepare_summary.json")
    parser.add_argument("--out", default="outputs/reports/detector_experiment_status.md")
    parser.add_argument("--top-k", type=int, default=12)
    args = parser.parse_args()
    print(write_status(args))


if __name__ == "__main__":
    main()
