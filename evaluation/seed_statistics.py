"""Aggregate seed metrics and compute paired p-values between methods."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from evaluation.stats import paired_t_test, wilcoxon_signed_rank
from runtime.config import resolve_path


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with resolve_path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def numeric_by_seed(rows: list[dict[str, str]], metric: str) -> dict[int, float]:
    values: dict[int, float] = {}
    for row in rows:
        if not row.get("seed") or row.get(metric) in {None, ""}:
            continue
        try:
            values[int(float(row["seed"]))] = float(row[metric])
        except ValueError:
            continue
    return values


def describe(values: list[float]) -> dict[str, float]:
    return {
        "mean": float(mean(values)) if values else 0.0,
        "std": float(stdev(values)) if len(values) > 1 else 0.0,
        "n": float(len(values)),
    }


def compare_seed_csvs(baseline_csv: str | Path, candidate_csv: str | Path, metric: str) -> dict[str, Any]:
    baseline = numeric_by_seed(read_rows(baseline_csv), metric)
    candidate = numeric_by_seed(read_rows(candidate_csv), metric)
    seeds = sorted(set(baseline) & set(candidate))
    if not seeds:
        raise ValueError("No matching seeds found between the two CSV files.")
    baseline_values = [baseline[seed] for seed in seeds]
    candidate_values = [candidate[seed] for seed in seeds]
    return {
        "metric": metric,
        "paired_seeds": seeds,
        "baseline": describe(baseline_values),
        "candidate": describe(candidate_values),
        "delta_candidate_minus_baseline": describe([b - a for a, b in zip(baseline_values, candidate_values)]),
        "paired_t_test": paired_t_test(candidate_values, baseline_values),
        "wilcoxon_signed_rank": wilcoxon_signed_rank(candidate_values, baseline_values),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute p-value-ready statistics from seed metric CSVs.")
    parser.add_argument("--baseline-csv", required=True)
    parser.add_argument("--candidate-csv", required=True)
    parser.add_argument("--metric", default="AP")
    parser.add_argument("--out", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = compare_seed_csvs(args.baseline_csv, args.candidate_csv, args.metric)
    text = json.dumps(summary, indent=2)
    if args.out:
        out_path = resolve_path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
