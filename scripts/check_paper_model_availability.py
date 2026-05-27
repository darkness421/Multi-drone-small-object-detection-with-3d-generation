"""Check paper comparison detector candidates against local runnable assets."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import yaml

from runtime.config import resolve_path


LOCAL_STATUS = {"external_required", "local_required"}
BUILTIN_STATUS = {"ultralytics_available_check", "already_in_queue"}


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def candidate_weight_paths(model: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    paths.extend(as_list(model.get("weights")))
    paths.extend(as_list(model.get("fallback_weights")))
    return paths


def find_local_weight(paths: list[str]) -> Path | None:
    for item in paths:
        path = resolve_path(item)
        if path.exists():
            return path
    return None


def is_builtin_or_remote_weight(path: str) -> bool:
    return path.endswith(".pt") and "/" not in path and "\\" not in path


def classify_model(model: dict[str, Any]) -> dict[str, str]:
    paths = candidate_weight_paths(model)
    local = find_local_weight(paths)
    status = str(model.get("status") or "")
    has_builtin_hint = any(is_builtin_or_remote_weight(path) for path in paths)

    if local is not None:
        runnable = "local_weight_found"
        action = "Queue after active VisDrone/proposed jobs if the adapter matches the current trainer."
    elif status in LOCAL_STATUS:
        runnable = "blocked_external_assets"
        action = "Stage compatible code/checkpoint first; do not count as executed comparison yet."
    elif status in BUILTIN_STATUS or has_builtin_hint:
        runnable = "ultralytics_or_queue_candidate"
        action = "Can be checked by the training launcher with CHECK_MODELS=1 once GPUs are idle."
    else:
        runnable = "needs_manual_review"
        action = "Confirm model format, adapter, and checkpoint before adding to the queue."

    return {
        "name": str(model.get("name") or ""),
        "family": str(model.get("family") or ""),
        "architecture_group": str(model.get("architecture_group") or "yolo"),
        "size": str(model.get("size") or ""),
        "status": status,
        "weights": ";".join(paths),
        "local_weight_found": "true" if local is not None else "false",
        "local_weight_path": str(local) if local is not None else "",
        "runnable_status": runnable,
        "recommended_action": action,
        "source": str(model.get("source") or ""),
        "code": str(model.get("code") or ""),
    }


def markdown_table(rows: list[dict[str, str]]) -> str:
    headers = ["Model", "Family", "Group", "Size", "Status", "Runnable", "Action"]
    if not rows:
        return "_No model candidates found._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["name"],
                    row["family"] or "-",
                    row["architecture_group"] or "-",
                    row["size"] or "-",
                    row["status"] or "-",
                    row["runnable_status"] or "-",
                    row["recommended_action"],
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name",
        "family",
        "architecture_group",
        "size",
        "status",
        "weights",
        "local_weight_found",
        "local_weight_path",
        "runnable_status",
        "recommended_action",
        "source",
        "code",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], config_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    runnable = [row for row in rows if row["runnable_status"] in {"local_weight_found", "ultralytics_or_queue_candidate"}]
    blocked = [row for row in rows if row["runnable_status"] == "blocked_external_assets"]
    lines = [
        "# Paper Model Availability",
        "",
        f"Source config: `{config_path.as_posix()}`",
        "",
        "This file separates runnable comparison candidates from models that still need external code, adapters, or checkpoints.",
        "",
        f"- Runnable or queue-check candidates: `{len(runnable)}`",
        f"- External-asset blocked candidates: `{len(blocked)}`",
        f"- Total candidates: `{len(rows)}`",
        "",
        "## Recommendation",
        "",
        "Use the already queued YOLO/RT-DETR family as the primary reproducible comparison set.",
        "For the paper-specific comparison row, add only 2-3 external models after local weights/adapters are staged:",
        "`LRDS-YOLO` or another YOLO-specialized UAV model, one DETR/D-FINE family model, and optionally `UAVDet`.",
        "",
        "## Candidate Table",
        "",
        markdown_table(rows),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local availability of paper comparison detector candidates.")
    parser.add_argument("--config", default="configs/experiments/paper_detector_comparison.yaml")
    parser.add_argument("--out-csv", default="outputs/experiments/paper_model_availability.csv")
    parser.add_argument("--out-md", default="outputs/reports/server_with_proposed/paper_model_availability.md")
    args = parser.parse_args()

    config_path = resolve_path(args.config)
    config = load_config(config_path)
    rows = [classify_model(model) for model in config.get("models", [])]
    write_csv(resolve_path(args.out_csv), rows)
    write_markdown(resolve_path(args.out_md), rows, Path(args.config))
    print(f"Wrote {resolve_path(args.out_csv)}")
    print(f"Wrote {resolve_path(args.out_md)}")


if __name__ == "__main__":
    main()
