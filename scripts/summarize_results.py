#!/usr/bin/env python3
"""Build paper-facing REGR-T/REGR-TG summaries from immutable result CSVs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


SELECTED = "regr_t_reliable_motion_min5"
RANKING_ONLY = "regr_temporal_risk_05"
BASELINES = ("no_refinement", "regr_v1", "geometry_reid_greedy_guard")
TRACKERS = ("bytetrack", "ocsort", "deepocsort")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def result_file(root: Path, name: str) -> Path:
    """Accept both a run root and its nested ``results`` directory."""
    direct = root / name
    return direct if direct.is_file() else root / "results" / name


def aggregate_lookup(path: Path) -> dict[tuple[str, str], dict]:
    rows = read_csv(path)
    return {
        (row["tracker"], row["method"]): row
        for row in rows
        if row.get("scope") == "all_sequences"
        and row["aggregation"] == "equal_sequence_mean_metrics_total_counts"
    }


def sequence_lookup(path: Path) -> dict[tuple[str, str, str], float]:
    return {
        (row["tracker"], row["method"], f'{row["family"]}/{row["sequence"]}'): float(row["IDF1"])
        for row in read_csv(path)
    }


def paired_interval(
    lookup: dict[tuple[str, str, str], float],
    tracker: str,
    method: str,
    baseline: str,
    rng: np.random.Generator,
    iterations: int,
) -> dict:
    sequence_names = sorted(
        sequence
        for candidate_tracker, candidate_method, sequence in lookup
        if candidate_tracker == tracker and candidate_method == method
    )
    differences = np.asarray([
        lookup[(tracker, method, sequence)] - lookup[(tracker, baseline, sequence)]
        for sequence in sequence_names
    ])
    sampled = rng.choice(differences, size=(iterations, len(differences)), replace=True).mean(axis=1)
    tolerance = 1e-12
    return {
        "sequence_count": len(sequence_names),
        "mean_delta_IDF1_pp": float(differences.mean()),
        "ci95_low": float(np.percentile(sampled, 2.5)),
        "ci95_high": float(np.percentile(sampled, 97.5)),
        "wins": int(np.sum(differences > tolerance)),
        "ties": int(np.sum(np.abs(differences) <= tolerance)),
        "losses": int(np.sum(differences < -tolerance)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-dir", type=Path, required=True)
    parser.add_argument("--detector-dir", type=Path, required=True)
    parser.add_argument("--m3ot-development-dir", type=Path, required=True)
    parser.add_argument("--m3ot-heldout-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-iterations", type=int, default=20_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260918)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    ci_rows = []
    rng = np.random.default_rng(args.bootstrap_seed)
    for input_name, root in (("oracle_aabb", args.oracle_dir), ("official_detector", args.detector_dir)):
        aggregates = aggregate_lookup(result_file(root, "metrics_aggregate.csv"))
        sequences = sequence_lookup(result_file(root, "metrics_per_sequence.csv"))
        for tracker in TRACKERS:
            selected = aggregates[(tracker, SELECTED)]
            for method in ("no_refinement", "geometry_reid_greedy_guard", "regr_v1", RANKING_ONLY, SELECTED):
                row = aggregates[(tracker, method)]
                summary_rows.append({
                    "input": input_name,
                    "tracker": tracker,
                    "method": method,
                    "HOTA": float(row["HOTA"]),
                    "AssA": float(row["AssA"]),
                    "IDF1": float(row["IDF1"]),
                    "IDSW": int(row["IDSW"]),
                    "delta_selected_IDF1_pp": float(selected["IDF1"]) - float(row["IDF1"]),
                    "delta_selected_IDSW": int(selected["IDSW"]) - int(row["IDSW"]),
                })
            for baseline in BASELINES:
                ci_rows.append({
                    "input": input_name,
                    "tracker": tracker,
                    "method": SELECTED,
                    "baseline": baseline,
                    **paired_interval(
                        sequences,
                        tracker,
                        SELECTED,
                        baseline,
                        rng,
                        args.bootstrap_iterations,
                    ),
                    "bootstrap_iterations": args.bootstrap_iterations,
                    "bootstrap_seed": args.bootstrap_seed,
                })

    m3ot_rows = []
    for split, root in (
        ("development", args.m3ot_development_dir),
        ("held_out", args.m3ot_heldout_dir),
    ):
        for row in read_csv(root / "metrics_aggregate.csv"):
            if row["method"] not in {
                "no_refinement",
                "geometry_reid_greedy_guard",
                "regr_v1",
                RANKING_ONLY,
                SELECTED,
            }:
                continue
            m3ot_rows.append({
                "split": split,
                "tracker": row["tracker"],
                "method": row["method"],
                "HOTA": float(row["HOTA"]),
                "AssA": float(row["AssA"]),
                "IDF1": float(row["IDF1"]),
                "IDSW": int(row["IDSW"]),
                "accepted_correct": int(row["accepted_correct"]),
                "accepted_false": int(row["accepted_false"]),
                "accepted_unknown": int(row["accepted_unknown"]),
            })

    write_csv(args.output_dir / "mmot_test50_summary.csv", summary_rows)
    write_csv(args.output_dir / "mmot_test50_paired_ci.csv", ci_rows)
    write_csv(args.output_dir / "m3ot_transfer_summary.csv", m3ot_rows)

    payload = {
        "selected_method": SELECTED,
        "paper_name": "REGR-TG",
        "ranking_only_ablation": RANKING_ONLY,
        "bootstrap": {
            "iterations": args.bootstrap_iterations,
            "seed": args.bootstrap_seed,
            "unit": "MMOT sequence",
            "aggregation": "paired equal-sequence-mean IDF1 difference",
        },
        "mmot_summary_rows": len(summary_rows),
        "mmot_ci_rows": len(ci_rows),
        "m3ot_summary_rows": len(m3ot_rows),
    }
    (args.output_dir / "summary_manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
