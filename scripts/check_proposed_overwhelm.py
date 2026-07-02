"""Check whether a proposed detector beats all comparison models."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_proposed(row: dict[str, str]) -> bool:
    return row.get("is_proposed") == "true" or (row.get("method") or "").startswith("Proposed")


def best_row(rows: list[dict[str, str]], metric: str) -> dict[str, str] | None:
    valid = [row for row in rows if as_float(row.get(metric)) is not None]
    if not valid:
        return None
    return max(valid, key=lambda row: as_float(row.get(metric)) or -1)


def slim(row: dict[str, str] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "method": row.get("method") or row.get("model"),
        "dataset": row.get("dataset"),
        "scale": row.get("model_scale") or row.get("param_size_group"),
        "seed_count": row.get("seed_count"),
        "best_AP_mean": as_float(row.get("best_AP_mean")),
        "best_AP50_mean": as_float(row.get("best_AP50_mean")),
        "best_F1_mean": as_float(row.get("best_F1_mean")),
        "Params_mean": as_float(row.get("Params_mean")),
        "GFLOPs_mean": as_float(row.get("GFLOPs_mean")),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    rows = read_csv(Path(args.summary_csv))
    if args.dataset:
        rows = [row for row in rows if row.get("dataset") == args.dataset]
    proposed = [row for row in rows if is_proposed(row)]
    comparisons = [row for row in rows if not is_proposed(row)]
    best_proposed = best_row(proposed, args.primary_metric)
    best_comparison = best_row(comparisons, args.primary_metric)
    best_comparison_ap50 = best_row(comparisons, args.secondary_metric)

    primary_delta = None
    secondary_delta = None
    if best_proposed and best_comparison:
        primary_delta = (as_float(best_proposed.get(args.primary_metric)) or 0.0) - (
            as_float(best_comparison.get(args.primary_metric)) or 0.0
        )
    if best_proposed and best_comparison_ap50:
        secondary_delta = (as_float(best_proposed.get(args.secondary_metric)) or 0.0) - (
            as_float(best_comparison_ap50.get(args.secondary_metric)) or 0.0
        )

    overwhelmed = (
        best_proposed is not None
        and best_comparison is not None
        and primary_delta is not None
        and secondary_delta is not None
        and primary_delta > args.min_delta
        and secondary_delta >= args.secondary_min_delta
    )
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dataset": args.dataset or "all",
        "primary_metric": args.primary_metric,
        "secondary_metric": args.secondary_metric,
        "min_delta": args.min_delta,
        "secondary_min_delta": args.secondary_min_delta,
        "status": "overwhelmed" if overwhelmed else "not_yet",
        "best_proposed": slim(best_proposed),
        "best_comparison_primary": slim(best_comparison),
        "best_comparison_secondary": slim(best_comparison_ap50),
        "primary_delta": primary_delta,
        "secondary_delta": secondary_delta,
        "proposed_rows": [slim(row) for row in sorted(proposed, key=lambda r: as_float(r.get(args.primary_metric)) or -1, reverse=True)],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best_prop = report.get("best_proposed") or {}
    best_base = report.get("best_comparison_primary") or {}
    lines = [
        "# Proposed Overwhelm Gate",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Status: `{report['status']}`",
        "",
        "| Role | Method | AP | AP50 | F1 |",
        "| --- | --- | ---: | ---: | ---: |",
        (
            f"| Best proposed | {best_prop.get('method', '-')} | {best_prop.get('best_AP_mean', '-')} | "
            f"{best_prop.get('best_AP50_mean', '-')} | {best_prop.get('best_F1_mean', '-')} |"
        ),
        (
            f"| Best comparison | {best_base.get('method', '-')} | {best_base.get('best_AP_mean', '-')} | "
            f"{best_base.get('best_AP50_mean', '-')} | {best_base.get('best_F1_mean', '-')} |"
        ),
        "",
        f"Primary delta: `{report.get('primary_delta')}`",
        f"Secondary delta: `{report.get('secondary_delta')}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether proposed detector beats all comparisons.")
    parser.add_argument("--summary-csv", default="outputs/experiments/server_with_proposed_summary.csv")
    parser.add_argument("--dataset", default="VisDrone2019-DET")
    parser.add_argument("--primary-metric", default="best_AP_mean")
    parser.add_argument("--secondary-metric", default="best_AP50_mean")
    parser.add_argument("--min-delta", type=float, default=0.0)
    parser.add_argument("--secondary-min-delta", type=float, default=0.0)
    parser.add_argument("--out-json", default="outputs/experiments/proposed_overwhelm_gate.json")
    parser.add_argument("--out-md", default="outputs/experiments/proposed_overwhelm_gate.md")
    args = parser.parse_args()

    report = build_report(args)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, Path(args.out_md))
    if report["status"] == "overwhelmed":
        print("NOTICE: proposed model has overwhelmed all comparison models.")
    else:
        print("Proposed model has not overwhelmed all comparison models yet.")
    print(args.out_json)
    print(args.out_md)


if __name__ == "__main__":
    main()
