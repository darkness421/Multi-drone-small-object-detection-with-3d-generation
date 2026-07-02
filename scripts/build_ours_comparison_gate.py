"""Build a paper-facing gate for the selected Ours detector.

The older proposed-overwhelm gate reads experiment summaries where some
paper-faithful reimplementations are marked as proposed because they patch a
YOLO backbone.  This gate is stricter: only the final paper row named
``Ours: P2P4-SelfAttnFR`` is treated as ours, and all other completed rows are
comparison models.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


OURS_METHOD = "Ours: P2P4-SelfAttnFR"
MAIN_SECTION = "main_1280_completed_3seed"


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def best_by(rows: list[dict[str, str]], metric: str) -> dict[str, str] | None:
    valid = [row for row in rows if as_float(row.get(metric)) is not None]
    if not valid:
        return None
    return max(valid, key=lambda row: as_float(row.get(metric)) or -1.0)


def slim(row: dict[str, str] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "rank": row.get("rank"),
        "group": row.get("group"),
        "method": row.get("method"),
        "protocol": row.get("protocol"),
        "seeds": row.get("seeds"),
        "seed_count": int(as_float(row.get("seed_count")) or 0),
        "AP": as_float(row.get("AP")),
        "AP_std": as_float(row.get("AP_std")),
        "AP50": as_float(row.get("AP50")),
        "AP50_std": as_float(row.get("AP50_std")),
        "precision": as_float(row.get("precision")),
        "recall": as_float(row.get("recall")),
        "F1": as_float(row.get("F1")),
        "params_m": as_float(row.get("params_m")),
        "gflops": as_float(row.get("gflops")),
        "note": row.get("note"),
    }


def delta(ours: dict[str, str], other: dict[str, str] | None, metric: str) -> float | None:
    if other is None:
        return None
    ours_value = as_float(ours.get(metric))
    other_value = as_float(other.get(metric))
    if ours_value is None or other_value is None:
        return None
    return ours_value - other_value


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    rows = [row for row in read_rows(Path(args.table_csv)) if row.get("section") == args.section]
    ours_rows = [row for row in rows if row.get("method") == args.ours_method]
    if not ours_rows:
        raise RuntimeError(f"Could not find ours method: {args.ours_method}")
    ours = ours_rows[0]
    comparisons = [row for row in rows if row.get("method") != args.ours_method]
    related = [row for row in comparisons if row.get("group") == "Cited related work"]

    best_overall_ap = best_by(comparisons, "AP")
    best_overall_ap50 = best_by(comparisons, "AP50")
    best_overall_f1 = best_by(comparisons, "F1")
    best_related_ap = best_by(related, "AP")
    best_related_ap50 = best_by(related, "AP50")
    best_related_f1 = best_by(related, "F1")

    checks = {
        "beats_best_overall_AP": (delta(ours, best_overall_ap, "AP") or 0.0) > args.min_delta,
        "beats_best_overall_AP50": (delta(ours, best_overall_ap50, "AP50") or 0.0) > args.min_delta,
        "beats_best_overall_F1": (delta(ours, best_overall_f1, "F1") or 0.0) > args.min_delta,
        "beats_best_related_AP": (delta(ours, best_related_ap, "AP") or 0.0) > args.min_delta,
        "beats_best_related_AP50": (delta(ours, best_related_ap50, "AP50") or 0.0) > args.min_delta,
        "beats_best_related_F1": (delta(ours, best_related_f1, "F1") or 0.0) > args.min_delta,
    }
    status = "overwhelmed" if all(checks.values()) else "partial"
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "section": args.section,
        "ours_method": args.ours_method,
        "ours": slim(ours),
        "best_overall": {
            "AP": slim(best_overall_ap),
            "AP50": slim(best_overall_ap50),
            "F1": slim(best_overall_f1),
        },
        "best_related_work": {
            "AP": slim(best_related_ap),
            "AP50": slim(best_related_ap50),
            "F1": slim(best_related_f1),
        },
        "deltas_vs_best_overall": {
            "AP": delta(ours, best_overall_ap, "AP"),
            "AP50": delta(ours, best_overall_ap50, "AP50"),
            "F1": delta(ours, best_overall_f1, "F1"),
            "params_m_vs_best_AP": delta(ours, best_overall_ap, "params_m"),
        },
        "deltas_vs_best_related_work": {
            "AP": delta(ours, best_related_ap, "AP"),
            "AP50": delta(ours, best_related_ap50, "AP50"),
            "F1": delta(ours, best_related_f1, "F1"),
            "params_m_vs_best_AP": delta(ours, best_related_ap, "params_m"),
        },
        "checks": checks,
        "comparison_count": len(comparisons),
        "related_work_count": len(related),
    }


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ours = report["ours"]
    overall_delta = report["deltas_vs_best_overall"]
    related_delta = report["deltas_vs_best_related_work"]
    comparison_rows = [
        ("Best overall comparison by AP", report["best_overall"]["AP"]),
        ("Best overall comparison by AP50", report["best_overall"]["AP50"]),
        ("Best overall comparison by F1", report["best_overall"]["F1"]),
        ("Best cited related work by AP", report["best_related_work"]["AP"]),
        ("Best cited related work by AP50", report["best_related_work"]["AP50"]),
        ("Best cited related work by F1", report["best_related_work"]["F1"]),
    ]
    lines = [
        "# Ours vs Comparison Gate",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Status: `{report['status']}`",
        f"Section: `{report['section']}`",
        "",
        "| Role | Method | AP | AP50 | F1 | Params(M) | Seeds |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        (
            f"| Ours | {ours['method']} | {fmt(ours['AP'])} | {fmt(ours['AP50'])} | "
            f"{fmt(ours['F1'])} | {fmt(ours['params_m'], 2)} | {ours['seeds']} |"
        ),
    ]
    for role, row in comparison_rows:
        lines.append(
            f"| {role} | {row['method']} | {fmt(row['AP'])} | {fmt(row['AP50'])} | "
            f"{fmt(row['F1'])} | {fmt(row['params_m'], 2)} | {row['seeds']} |"
        )
    lines += [
        "",
        "## Deltas",
        "",
        (
            f"- Vs best overall comparison per metric: AP `{fmt(overall_delta['AP'])}`, "
            f"AP50 `{fmt(overall_delta['AP50'])}`, F1 `{fmt(overall_delta['F1'])}`, "
            f"Params vs best-AP model `{fmt(overall_delta['params_m_vs_best_AP'], 2)}M`."
        ),
        (
            f"- Vs best cited related work per metric: AP `{fmt(related_delta['AP'])}`, "
            f"AP50 `{fmt(related_delta['AP50'])}`, F1 `{fmt(related_delta['F1'])}`, "
            f"Params vs best-AP related model `{fmt(related_delta['params_m_vs_best_AP'], 2)}M`."
        ),
        "",
        "## Checks",
        "",
    ]
    for key, value in report["checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Ours-vs-comparison detector gate.")
    parser.add_argument("--table-csv", default="outputs/reports/final_detector_table_preview.csv")
    parser.add_argument("--section", default=MAIN_SECTION)
    parser.add_argument("--ours-method", default=OURS_METHOD)
    parser.add_argument("--min-delta", type=float, default=0.0)
    parser.add_argument("--out-json", default="outputs/experiments/ours_vs_comparison_gate.json")
    parser.add_argument("--out-md", default="outputs/experiments/ours_vs_comparison_gate.md")
    args = parser.parse_args()

    report = build_report(args)
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, Path(args.out_md))
    print(report["status"])
    print(args.out_json)
    print(args.out_md)


if __name__ == "__main__":
    main()
