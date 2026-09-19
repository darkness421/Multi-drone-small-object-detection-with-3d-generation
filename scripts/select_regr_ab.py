#!/usr/bin/env python3
"""Apply the frozen two-dataset development selection rule.

This script reads completed development metrics only. It does not inspect any
test or confirmation split, and it writes a self-contained frozen-method
record before the selected method is evaluated elsewhere.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def unique_rows(rows: list[dict[str, str]], scope: str | None) -> list[dict[str, str]]:
    if scope is not None:
        rows = [row for row in rows if row.get("scope") == scope]
    output: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["tracker"], row["method"])
        if key in output:
            raise ValueError(f"duplicate aggregate row: {key}")
        output[key] = row
    return list(output.values())


def metric_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["tracker"], row["method"]): row for row in rows}


def runtime_index(rows: list[dict[str, str]], scope: str | None) -> dict[tuple[str, str], float]:
    values: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        if scope is not None and row.get("scope") != scope:
            continue
        key = (row["tracker"], row["method"])
        values.setdefault(key, []).append(
            float(row.get("selection_ms", 0.0))
            + float(row.get("assignment_ms_median", 0.0))
        )
    return {key: sum(group) / len(group) for key, group in values.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--mmot-metrics", type=Path, required=True)
    parser.add_argument("--mmot-runtime", type=Path, required=True)
    parser.add_argument("--mmot-scope", default="train_dev6")
    parser.add_argument("--m3ot-metrics", type=Path, required=True)
    parser.add_argument("--m3ot-runtime", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(args.config.read_text(encoding="utf-8"))
    candidates = [row["name"] for row in protocol["configurations"]]
    trackers = tuple(protocol["development_data"]["mmot_trackers"])
    if tuple(protocol["development_data"]["m3ot_trackers"]) != trackers:
        raise ValueError("the frozen rule requires the same tracker set for both datasets")

    mmot_rows = unique_rows(read_csv(args.mmot_metrics), args.mmot_scope)
    m3ot_rows = unique_rows(read_csv(args.m3ot_metrics), None)
    mmot = metric_index(mmot_rows)
    m3ot = metric_index(m3ot_rows)
    mmot_runtime = runtime_index(read_csv(args.mmot_runtime), args.mmot_scope)
    m3ot_runtime = runtime_index(read_csv(args.m3ot_runtime), None)
    baselines = tuple(protocol["strong_baseline_envelope"])

    baseline_values: dict[tuple[str, str], tuple[str, float]] = {}
    for dataset, index in (("mmot", mmot), ("m3ot", m3ot)):
        for tracker in trackers:
            available = [
                (method, float(index[(tracker, method)]["IDF1"]))
                for method in baselines
            ]
            baseline_values[(dataset, tracker)] = max(available, key=lambda item: (item[1], item[0]))

    ranking = []
    for method in candidates:
        mmot_tracker_deltas = [
            float(mmot[(tracker, method)]["IDF1"]) - baseline_values[("mmot", tracker)][1]
            for tracker in trackers
        ]
        m3ot_tracker_deltas = [
            float(m3ot[(tracker, method)]["IDF1"]) - baseline_values[("m3ot", tracker)][1]
            for tracker in trackers
        ]
        mmot_delta = sum(mmot_tracker_deltas) / len(mmot_tracker_deltas)
        m3ot_delta = sum(m3ot_tracker_deltas) / len(m3ot_tracker_deltas)
        total_idsw = sum(
            int(float(index[(tracker, method)]["IDSW"]))
            for index in (mmot, m3ot)
            for tracker in trackers
        )
        graph_ms = sum(
            runtime.get((tracker, method), 0.0)
            for runtime in (mmot_runtime, m3ot_runtime)
            for tracker in trackers
        ) / (2 * len(trackers))
        ranking.append({
            "method": method,
            "family": next(row["family"] for row in protocol["configurations"] if row["name"] == method),
            "mmot_delta_idf1_pp": mmot_delta,
            "m3ot_delta_idf1_pp": m3ot_delta,
            "minimum_delta_idf1_pp": min(mmot_delta, m3ot_delta),
            "mean_delta_idf1_pp": (mmot_delta + m3ot_delta) / 2.0,
            "total_idsw": total_idsw,
            "mean_graph_stage_ms": graph_ms,
            **{
                f"mmot_{tracker}_idf1": float(mmot[(tracker, method)]["IDF1"])
                for tracker in trackers
            },
            **{
                f"m3ot_{tracker}_idf1": float(m3ot[(tracker, method)]["IDF1"])
                for tracker in trackers
            },
        })

    ranking.sort(
        key=lambda row: (
            -row["minimum_delta_idf1_pp"],
            -row["mean_delta_idf1_pp"],
            row["total_idsw"],
            row["mean_graph_stage_ms"],
            row["method"],
        )
    )
    for rank, row in enumerate(ranking, start=1):
        row["rank"] = rank
    ranking = [{"rank": row.pop("rank"), **row} for row in ranking]
    write_csv(args.output_dir / "development_selection_ranking.csv", ranking)

    winner = ranking[0]
    selected_spec = next(
        row for row in protocol["configurations"] if row["name"] == winner["method"]
    )
    frozen = {
        "status": "FROZEN_BEFORE_CONFIRMATION_EVALUATION",
        "protocol_id": protocol["protocol_id"],
        "selected_method": winner["method"],
        "selected_configuration": selected_spec,
        "selection_metrics": winner,
        "strong_baseline_envelope": list(baselines),
        "baseline_values": {
            f"{dataset}_{tracker}": {"method": value[0], "IDF1": value[1]}
            for (dataset, tracker), value in baseline_values.items()
        },
        "input_sha256": {
            "config": sha256(args.config),
            "core": sha256(args.core),
            "mmot_metrics": sha256(args.mmot_metrics),
            "mmot_runtime": sha256(args.mmot_runtime),
            "m3ot_metrics": sha256(args.m3ot_metrics),
            "m3ot_runtime": sha256(args.m3ot_runtime),
        },
    }
    (args.output_dir / "frozen_final_method.json").write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(frozen, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
