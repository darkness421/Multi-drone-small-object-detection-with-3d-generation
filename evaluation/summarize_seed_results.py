"""Summarize detector baseline seed results as mean/std rows."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from runtime.config import resolve_path


DEFAULT_METRICS = ["best_AP", "best_AP50", "best_APsmall", "best_recall", "best_F1", "ROC-AUC", "FPS", "Params", "GFLOPs"]


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with resolve_path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def describe(values: list[float]) -> tuple[float, float, int]:
    return float(mean(values)), float(stdev(values)) if len(values) > 1 else 0.0, len(values)


def summarize(rows: list[dict[str, str]], metrics: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("status", "completed") != "completed":
            continue
        groups[(row.get("method", ""), row.get("model", ""), row.get("dataset", ""))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (method, model, dataset), group_rows in sorted(groups.items()):
        first = group_rows[0]
        seeds = sorted({row.get("seed", "") for row in group_rows if row.get("seed", "")})
        out: dict[str, Any] = {
            "method": method,
            "model": model,
            "base_model": first.get("base_model", ""),
            "ablation": first.get("ablation", ""),
            "proposed_module": first.get("proposed_module", ""),
            "is_proposed": first.get("is_proposed", ""),
            "implementation_status": first.get("implementation_status", ""),
            "detector_family": first.get("detector_family", ""),
            "architecture_group": first.get("architecture_group", ""),
            "model_version": first.get("model_version", ""),
            "yolo_version": first.get("yolo_version", ""),
            "is_yolo": first.get("is_yolo", ""),
            "model_scale": first.get("model_scale", ""),
            "name_size_tag": first.get("name_size_tag", ""),
            "param_size_group": first.get("param_size_group", ""),
            "size_group": first.get("size_group", ""),
            "dataset": dataset,
            "seed_count": len(seeds),
            "seeds": ",".join(seeds),
            "analysis_level": "main" if len(seeds) >= 5 else "preliminary",
        }
        for metric in metrics:
            values = [value for row in group_rows if (value := as_float(row.get(metric))) is not None]
            if not values:
                continue
            metric_mean, metric_std, metric_n = describe(values)
            out[f"{metric}_mean"] = metric_mean
            out[f"{metric}_std"] = metric_std
            out[f"{metric}_n"] = metric_n
            out[f"{metric}_mean_std"] = f"{metric_mean:.4f} +/- {metric_std:.4f}"
        summary_rows.append(out)
    return summary_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = [
        "method",
        "model",
        "base_model",
        "ablation",
        "proposed_module",
        "is_proposed",
        "implementation_status",
        "detector_family",
        "architecture_group",
        "model_version",
        "yolo_version",
        "is_yolo",
        "model_scale",
        "name_size_tag",
        "param_size_group",
        "size_group",
        "dataset",
        "seed_count",
        "seeds",
        "analysis_level",
    ]
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize detector seed results.")
    parser.add_argument("--results-csv", default="outputs/experiments/server_baseline_results.csv")
    parser.add_argument("--out", default="outputs/experiments/server_baseline_summary.csv")
    parser.add_argument("--metrics", default=",".join(DEFAULT_METRICS))
    args = parser.parse_args()

    rows = summarize(read_rows(args.results_csv), [metric.strip() for metric in args.metrics.split(",") if metric.strip()])
    out_path = resolve_path(args.out)
    write_csv(out_path, rows)
    print(f"Wrote {out_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
