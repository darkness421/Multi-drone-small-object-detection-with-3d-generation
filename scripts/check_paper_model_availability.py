"""Check paper comparison detector candidates against local runnable assets."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.config import resolve_path


LOCAL_STATUS = {"external_required", "local_required"}
BUILTIN_STATUS = {"ultralytics_available_check", "already_in_queue"}
CITATION_ONLY_STATUS = {"citation_only_until_code"}


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


def has_public_code_hint(model: dict[str, Any]) -> bool:
    code = str(model.get("code") or "").lower()
    source = str(model.get("source") or "").lower()
    return "github.com" in code or "github.com" in source


def classify_model(model: dict[str, Any]) -> dict[str, str]:
    paths = candidate_weight_paths(model)
    local = find_local_weight(paths)
    status = str(model.get("status") or "")
    has_builtin_hint = any(is_builtin_or_remote_weight(path) for path in paths)
    has_code = has_public_code_hint(model)

    if local is not None:
        runnable = "local_weight_found"
        action = "Queue after active VisDrone/proposed jobs if the adapter matches the current trainer."
    elif status in CITATION_ONLY_STATUS:
        runnable = "citation_only_until_code"
        action = "Do not queue yet; cite the paper or stage compatible code/weights first."
    elif status in LOCAL_STATUS and has_code:
        runnable = "github_code_needs_adapter_or_checkpoint"
        action = "Prioritize this candidate: stage repo/checkpoint or build a small adapter before running."
    elif status in LOCAL_STATUS:
        runnable = "pass_no_public_github"
        action = "Pass full reproduction for now; only test simple transferable mechanisms as our own ablations."
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
        "public_code_hint": "true" if has_code else "false",
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
        "public_code_hint",
        "runnable_status",
        "recommended_action",
        "source",
        "code",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], config_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    runnable = [row for row in rows if row["runnable_status"] in {"local_weight_found", "ultralytics_or_queue_candidate"}]
    github_backed = [row for row in rows if row["runnable_status"] == "github_code_needs_adapter_or_checkpoint"]
    passed = [row for row in rows if row["runnable_status"] == "pass_no_public_github"]
    lines = [
        "# Paper Model Availability",
        "",
        f"Source config: `{config_path.as_posix()}`",
        "",
        "This file separates runnable comparison candidates, GitHub-backed candidates that need adapters/checkpoints, and no-code papers that should be passed for full reproduction.",
        "",
        f"- Runnable or queue-check candidates: `{len(runnable)}`",
        f"- GitHub-backed but adapter/checkpoint-needed candidates: `{len(github_backed)}`",
        f"- Passed for full reproduction because no public GitHub/code is staged: `{len(passed)}`",
        f"- Total candidates: `{len(rows)}`",
        "",
        "## Recommendation",
        "",
        "Run models with public GitHub/code and staged assets first. If code exists but the format differs, build only the adapter needed for fair evaluation.",
        "Pass no-code/no-weight papers for full reproduction, but keep simple transferable mechanisms such as NMS, activation, wavelet/DCT, attention, and P2-head changes as lightweight ablations inside our proposed detector.",
        "For the paper-specific comparison row, prioritize `CSFPR-RTDETR`, `LEAF-YOLO`, and `DR-YOLO` before lower-priority generic or modality-mismatched models.",
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
