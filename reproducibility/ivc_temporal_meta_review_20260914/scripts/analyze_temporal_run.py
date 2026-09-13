#!/usr/bin/env python3
"""Derive paired temporal-refinement summaries without modifying raw results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


METRICS = ("HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW", "FP", "FN", "Frag")
SCORE_METRICS = ("HOTA", "AssA", "IDF1")
COUNT_METRICS = ("IDSW",)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def number(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value in {"", "None", "nan", "NaN"}:
        return None
    return float(value)


def truth(value: str) -> bool:
    return value.lower() in {"true", "1", "yes"}


def paired_ci(values: list[float], seed: int, repeats: int) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    array = np.asarray(values, dtype=float)
    indices = rng.integers(0, len(array), size=(repeats, len(array)))
    means = array[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate", type=Path, required=True)
    parser.add_argument("--per-sequence", type=Path, required=True)
    parser.add_argument("--link-summary", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline", default="no_refinement")
    parser.add_argument("--bootstrap-seed", type=int, default=20260914)
    parser.add_argument("--bootstrap-repeats", type=int, default=10000)
    args = parser.parse_args()

    aggregate = read_csv(args.aggregate)
    per_sequence = read_csv(args.per_sequence)
    aggregate_index = {
        (row["scope"], row["tracker"], row["method"], row["aggregation"]): row
        for row in aggregate
    }
    delta_rows = []
    for key, row in sorted(aggregate_index.items()):
        baseline_key = (key[0], key[1], args.baseline, key[3])
        baseline = aggregate_index.get(baseline_key)
        output = {
            "scope": key[0], "tracker": key[1], "method": key[2],
            "aggregation": key[3], "valid_output": row.get("valid_output", "True"),
            "sequence_count": row.get("sequence_count", ""),
        }
        for metric in METRICS:
            value = number(row, metric)
            base = number(baseline, metric) if baseline else None
            output[metric] = value
            output[f"delta_{metric}"] = value - base if value is not None and base is not None else None
        delta_rows.append(output)

    sequence_index = {
        (row["family"], row["sequence"], row["tracker"], row["method"]): row
        for row in per_sequence
    }
    paired = defaultdict(list)
    sequence_delta_rows = []
    for key, row in sorted(sequence_index.items()):
        if key[3] == args.baseline:
            continue
        base = sequence_index.get((key[0], key[1], key[2], args.baseline))
        if not base or not truth(row.get("valid_output", "True")) or not truth(base.get("valid_output", "True")):
            continue
        output = {"family": key[0], "sequence": key[1], "tracker": key[2], "method": key[3]}
        for metric in SCORE_METRICS + COUNT_METRICS:
            delta = float(row[metric]) - float(base[metric])
            output[f"delta_{metric}"] = delta
            paired[(key[0], key[2], key[3], metric)].append(delta)
            paired[("all_sequences", key[2], key[3], metric)].append(delta)
        sequence_delta_rows.append(output)

    paired_rows = []
    for (scope, tracker, method, metric), values in sorted(paired.items()):
        lower, upper = paired_ci(values, args.bootstrap_seed, args.bootstrap_repeats)
        if metric in SCORE_METRICS:
            improved = sum(value > 1e-12 for value in values)
            worsened = sum(value < -1e-12 for value in values)
        else:
            improved = sum(value < -1e-12 for value in values)
            worsened = sum(value > 1e-12 for value in values)
        paired_rows.append({
            "scope": scope, "tracker": tracker, "method": method, "metric": metric,
            "sequence_count": len(values), "improved": improved,
            "unchanged": len(values) - improved - worsened, "worsened": worsened,
            "mean_delta": float(np.mean(values)), "median_delta": float(np.median(values)),
            "min_delta": float(np.min(values)), "max_delta": float(np.max(values)),
            "bootstrap_ci95_lower": lower, "bootstrap_ci95_upper": upper,
            "bootstrap_seed": args.bootstrap_seed, "bootstrap_repeats": args.bootstrap_repeats,
        })

    proposed_pairwise = defaultdict(list)
    proposed_method = "com3d_reciprocal_guard"
    for key, proposed in sorted(sequence_index.items()):
        if key[3] != proposed_method or not truth(proposed.get("valid_output", "True")):
            continue
        for comparator in sorted({candidate[3] for candidate in sequence_index if candidate[:3] == key[:3]} - {proposed_method}):
            reference = sequence_index.get((key[0], key[1], key[2], comparator))
            if not reference or not truth(reference.get("valid_output", "True")):
                continue
            for metric in SCORE_METRICS + COUNT_METRICS:
                delta = float(proposed[metric]) - float(reference[metric])
                proposed_pairwise[(key[0], key[2], comparator, metric)].append(delta)
                proposed_pairwise[("all_sequences", key[2], comparator, metric)].append(delta)
    proposed_pairwise_rows = []
    for (scope, tracker, comparator, metric), values in sorted(proposed_pairwise.items()):
        lower, upper = paired_ci(values, args.bootstrap_seed, args.bootstrap_repeats)
        if metric in SCORE_METRICS:
            proposed_better = sum(value > 1e-12 for value in values)
            proposed_worse = sum(value < -1e-12 for value in values)
        else:
            proposed_better = sum(value < -1e-12 for value in values)
            proposed_worse = sum(value > 1e-12 for value in values)
        proposed_pairwise_rows.append({
            "scope": scope, "tracker": tracker, "proposed_method": proposed_method,
            "comparator": comparator, "metric": metric, "sequence_count": len(values),
            "proposed_better": proposed_better,
            "equal": len(values) - proposed_better - proposed_worse,
            "proposed_worse": proposed_worse,
            "mean_proposed_minus_comparator": float(np.mean(values)),
            "median_proposed_minus_comparator": float(np.median(values)),
            "bootstrap_ci95_lower": lower, "bootstrap_ci95_upper": upper,
            "bootstrap_seed": args.bootstrap_seed, "bootstrap_repeats": args.bootstrap_repeats,
        })

    write_csv(args.output_dir / "aggregate_with_baseline_deltas.csv", delta_rows)
    write_csv(args.output_dir / "per_sequence_deltas.csv", sequence_delta_rows)
    write_csv(args.output_dir / "paired_sequence_summary.csv", paired_rows)
    write_csv(args.output_dir / "proposed_vs_comparator_summary.csv", proposed_pairwise_rows)
    inputs = [args.aggregate, args.per_sequence]
    if args.link_summary:
        link_rows = read_csv(args.link_summary)
        write_csv(args.output_dir / "link_summary_copy.csv", link_rows)
        inputs.append(args.link_summary)
    outputs = sorted(args.output_dir.glob("*.csv"))
    manifest = {
        "status": "COMPLETE",
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
        "baseline": args.baseline,
        "bootstrap": {
            "unit": "sequence", "paired": True,
            "seed": args.bootstrap_seed, "repeats": args.bootstrap_repeats,
            "interval": "percentile 95% CI of the mean paired delta",
        },
        "inputs": {str(path): sha256(path) for path in inputs},
        "outputs": {path.name: sha256(path) for path in outputs},
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "aggregate_rows": len(delta_rows), "paired_rows": len(paired_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
