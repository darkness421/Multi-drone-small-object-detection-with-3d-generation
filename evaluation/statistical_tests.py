"""Paired seed statistical tests for detector baselines."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from evaluation.stats import paired_t_test, wilcoxon_signed_rank
from runtime.config import resolve_path


DEFAULT_METRICS = ["best_AP", "best_AP50", "best_recall", "best_F1"]


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


def group_metric_by_seed(rows: list[dict[str, str]], metric: str) -> dict[str, dict[int, float]]:
    grouped: dict[str, dict[int, float]] = defaultdict(dict)
    for row in rows:
        if row.get("status", "completed") != "completed":
            continue
        method = row.get("method") or row.get("model") or ""
        seed_value = row.get("seed")
        value = as_float(row.get(metric))
        if not method or not seed_value or value is None:
            continue
        try:
            seed = int(float(seed_value))
        except ValueError:
            continue
        grouped[method][seed] = value
    return grouped


def best_method(rows: list[dict[str, str]], metric: str) -> str:
    grouped = group_metric_by_seed(rows, metric)
    means = {method: mean(values.values()) for method, values in grouped.items() if values}
    if not means:
        return ""
    return max(means, key=means.get)


def compare_against_baseline(rows: list[dict[str, str]], metrics: list[str], baseline_method: str | None = None) -> list[dict[str, Any]]:
    baseline_method = baseline_method or best_method(rows, metrics[0])
    out: list[dict[str, Any]] = []
    for metric in metrics:
        grouped = group_metric_by_seed(rows, metric)
        baseline = grouped.get(baseline_method, {})
        for method, candidate in sorted(grouped.items()):
            if method == baseline_method:
                continue
            seeds = sorted(set(baseline) & set(candidate))
            if not seeds:
                continue
            baseline_values = [baseline[seed] for seed in seeds]
            candidate_values = [candidate[seed] for seed in seeds]
            t_test = paired_t_test(candidate_values, baseline_values)
            wilcoxon = wilcoxon_signed_rank(candidate_values, baseline_values)
            out.append(
                {
                    "metric": metric,
                    "baseline_method": baseline_method,
                    "candidate_method": method,
                    "paired_seeds": ",".join(str(seed) for seed in seeds),
                    "seed_count": len(seeds),
                    "analysis_level": "main" if len(seeds) >= 5 else "preliminary",
                    "baseline_mean": mean(baseline_values),
                    "candidate_mean": mean(candidate_values),
                    "delta_candidate_minus_baseline": mean([b - a for a, b in zip(baseline_values, candidate_values)]),
                    "paired_t_statistic": t_test["statistic"],
                    "paired_t_pvalue": t_test["pvalue"],
                    "wilcoxon_statistic": wilcoxon["statistic"],
                    "wilcoxon_pvalue": wilcoxon["pvalue"],
                }
            )
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = [
        "metric",
        "baseline_method",
        "candidate_method",
        "paired_seeds",
        "seed_count",
        "analysis_level",
        "baseline_mean",
        "candidate_mean",
        "delta_candidate_minus_baseline",
        "paired_t_statistic",
        "paired_t_pvalue",
        "wilcoxon_statistic",
        "wilcoxon_pvalue",
    ]
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute paired statistical tests for detector seed results.")
    parser.add_argument("--results-csv", default="outputs/experiments/server_baseline_results.csv")
    parser.add_argument("--baseline-method", default=None, help="Default: best mean method on the first metric.")
    parser.add_argument("--metrics", default=",".join(DEFAULT_METRICS))
    parser.add_argument("--out", default="outputs/experiments/server_baseline_pvalues.csv")
    args = parser.parse_args()

    metrics = [metric.strip() for metric in args.metrics.split(",") if metric.strip()]
    rows = compare_against_baseline(read_rows(args.results_csv), metrics, args.baseline_method)
    out_path = resolve_path(args.out)
    write_csv(out_path, rows)
    print(f"Wrote {out_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
