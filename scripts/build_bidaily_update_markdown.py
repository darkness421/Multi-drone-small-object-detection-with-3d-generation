"""Build a compact bi-daily ACCV project update as Markdown.

The generated file is meant to be committed to GitHub and optionally appended
to the project Notion page. It intentionally avoids secrets and only summarizes
metrics already present in local CSV/JSON artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


DEFAULT_SUMMARY_CSVS = [
    Path("outputs/experiments/server_with_proposed_summary.csv"),
    Path("outputs/experiments/server_with_proposed/server_with_proposed_summary.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_summary.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/server_baseline_summary.csv"),
]

DEFAULT_RESULTS_CSVS = [
    Path("outputs/experiments/server_with_proposed_results.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_results.csv"),
]

DEFAULT_STAGE_GATE_JSON = Path("outputs/experiments/detector_stage_gate.json")
DEFAULT_PROPOSED_GATE_JSON = Path("outputs/experiments/proposed_overwhelm_gate.json")


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
    if value in (None, ""):
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


def model_name(row: dict[str, str]) -> str:
    method = row.get("method") or Path(row.get("model", "")).stem or "-"
    ablation = row.get("ablation") or row.get("proposed_module") or ""
    if ablation and ablation.lower() not in {"none", "baseline", "control"}:
        return f"{method} + {ablation}"
    return method


def row_score(row: dict[str, str], key: str = "best_AP_mean") -> float:
    return as_float(row.get(key)) if as_float(row.get(key)) is not None else float("-inf")


def dedupe_summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("dataset", ""),
            row.get("method") or row.get("model") or "",
            row.get("ablation") or row.get("proposed_module") or "",
        )
        old = best.get(key)
        if old is None or row_score(row) > row_score(old):
            best[key] = row
    return list(best.values())


def top_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    scored = [row for row in rows if as_float(row.get("best_AP_mean")) is not None]
    scored.sort(key=row_score, reverse=True)
    return scored[:limit]


def proposed_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [
        row
        for row in rows
        if row.get("is_proposed") == "true" or (row.get("method") or "").startswith("Proposed-")
    ]
    selected.sort(key=row_score, reverse=True)
    return selected


def comparison_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    proposed = set(id(row) for row in proposed_rows(rows))
    selected = [row for row in rows if id(row) not in proposed]
    selected.sort(key=row_score, reverse=True)
    return selected


def incomplete_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [row for row in rows if row.get("status") and row.get("status") != "completed"]
    selected.sort(key=lambda row: row.get("run_dir", ""))
    return selected[-5:]


def days_until(target: date, today: date) -> int:
    return (target - today).days


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def status_line(best_proposed: dict[str, str] | None, best_comparison: dict[str, str] | None) -> str:
    if not best_proposed:
        return "No completed proposed detector has passed the current comparison gate yet."
    if not best_comparison:
        return "Completed proposed detector exists, but no comparison baseline was found."
    ap_delta = (as_float(best_proposed.get("best_AP_mean")) or 0.0) - (
        as_float(best_comparison.get("best_AP_mean")) or 0.0
    )
    ap50_delta = (as_float(best_proposed.get("best_AP50_mean")) or 0.0) - (
        as_float(best_comparison.get("best_AP50_mean")) or 0.0
    )
    if ap_delta > 0 and ap50_delta >= 0:
        return (
            f"Gate passed: {model_name(best_proposed)} is ahead of "
            f"{model_name(best_comparison)} by AP {ap_delta:.4f} and AP50 {ap50_delta:.4f}."
        )
    return (
        f"Gate not passed yet: best proposed is behind the best comparison by "
        f"AP {abs(ap_delta):.4f} and AP50 {abs(ap50_delta):.4f}."
    )


def build_markdown(args: argparse.Namespace) -> str:
    summary_rows = dedupe_summary_rows(
        [row for path in args.summary_csv for row in read_csv(Path(path))]
    )
    result_rows = [row for path in args.results_csv for row in read_csv(Path(path))]
    comparisons = comparison_rows(summary_rows)
    proposed = proposed_rows(summary_rows)
    best_comparison = comparisons[0] if comparisons else None
    best_proposed = proposed[0] if proposed else None
    stage_gate = read_json(Path(args.stage_gate_json))
    proposed_gate = read_json(Path(args.proposed_gate_json))
    generated = datetime.now().astimezone()
    today = generated.date()

    lines: list[str] = [
        f"# ACCV Bi-daily Update - {generated.strftime('%Y-%m-%d %H:%M %Z')}",
        "",
        "## Deadline",
        f"- Main paper due: 2026-07-05 ({days_until(date(2026, 7, 5), today)} days left).",
        f"- Supplementary due: 2026-07-08 ({days_until(date(2026, 7, 8), today)} days left).",
        "",
        "## Current Gate",
        f"- {status_line(best_proposed, best_comparison)}",
    ]

    if best_comparison:
        lines.append(
            "- Best comparison: "
            f"{model_name(best_comparison)} AP {fmt(best_comparison.get('best_AP_mean'))}, "
            f"AP50 {fmt(best_comparison.get('best_AP50_mean'))}, "
            f"F1 {fmt(best_comparison.get('best_F1_mean'))}, "
            f"Params {fmt_params(best_comparison.get('Params_mean'))}, "
            f"GFLOPs {fmt(best_comparison.get('GFLOPs_mean'), 1)}."
        )
    if best_proposed:
        lines.append(
            "- Best proposed: "
            f"{model_name(best_proposed)} AP {fmt(best_proposed.get('best_AP_mean'))}, "
            f"AP50 {fmt(best_proposed.get('best_AP50_mean'))}, "
            f"F1 {fmt(best_proposed.get('best_F1_mean'))}, "
            f"Params {fmt_params(best_proposed.get('Params_mean'))}, "
            f"GFLOPs {fmt(best_proposed.get('GFLOPs_mean'), 1)}."
        )
    if stage_gate:
        lines.append(
            "- Detector stage gate: "
            f"{stage_gate.get('recommended_next_stage', 'not generated')}."
        )
    if proposed_gate:
        lines.append(f"- Proposed overwhelm gate file status: {proposed_gate.get('status', 'not generated')}.")

    active = incomplete_rows(result_rows)
    lines.extend(["", "## Active Or Recent Runs"])
    if active:
        lines.extend(
            table(
                ["Method", "Seed", "Status", "Epoch", "Best AP", "Best AP50", "F1"],
                [
                    [
                        row.get("method") or row.get("model") or "-",
                        row.get("seed") or "-",
                        row.get("status") or "-",
                        f"{row.get('final_epoch') or '-'} / {row.get('protocol_epochs') or '-'}",
                        fmt(row.get("best_AP")),
                        fmt(row.get("best_AP50")),
                        fmt(row.get("best_F1")),
                    ]
                    for row in active
                ],
            )
        )
    else:
        lines.append("- No incomplete run was found in the selected result CSV files.")

    lines.extend(["", "## Detector Leaderboard"])
    leaders = top_rows(summary_rows, args.top_k)
    if leaders:
        lines.extend(
            table(
                ["Rank", "Method", "Scale", "Seeds", "AP", "AP50", "F1", "Params", "GFLOPs"],
                [
                    [
                        index,
                        model_name(row),
                        row.get("model_scale") or row.get("size_group") or "-",
                        row.get("seed_count") or "-",
                        fmt(row.get("best_AP_mean")),
                        fmt(row.get("best_AP50_mean")),
                        fmt(row.get("best_F1_mean")),
                        fmt_params(row.get("Params_mean")),
                        fmt(row.get("GFLOPs_mean"), 1),
                    ]
                    for index, row in enumerate(leaders, start=1)
                ],
            )
        )
    else:
        lines.append("- No summary rows were found.")

    lines.extend(
        [
            "",
            "## Next 48 Hours",
            "- Keep GPU0 on detector baseline/proposed screening and collect per-epoch AP/AP50/F1.",
            "- Queue YOLOv11l/P2, TinySpatialFReLU, and NMS variants after the current proposed run clears.",
            "- Keep GPU1 reserved for 3D/simulator/reasoner work after the CUDA allocation issue is reset.",
            "- Export paper tables and figures into the Overleaf-linked repository.",
            "- Append this status to Notion when NOTION_TOKEN and NOTION_PAGE_ID are available.",
            "",
            "## Updated Artifacts",
            "- GitHub: commit scoped experiment status, automation scripts, Notion exports, and result snapshots.",
            "- Paper: update auto detector table, auto experiment status section, and copied result figures.",
            "- Notion: append this bi-daily update to the project/proposed-method page.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-csv", action="append", default=[str(path) for path in DEFAULT_SUMMARY_CSVS])
    parser.add_argument("--results-csv", action="append", default=[str(path) for path in DEFAULT_RESULTS_CSVS])
    parser.add_argument("--stage-gate-json", default=str(DEFAULT_STAGE_GATE_JSON))
    parser.add_argument("--proposed-gate-json", default=str(DEFAULT_PROPOSED_GATE_JSON))
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--output-dir", default="notion_exports/bidaily")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    generated = datetime.now().astimezone()
    output = Path(args.output) if args.output else Path(args.output_dir) / (
        f"ACCV_Bidaily_Update_{generated.strftime('%Y-%m-%d_%H%M%S')}.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(args), encoding="utf-8")
    print(output.as_posix())


if __name__ == "__main__":
    main()
