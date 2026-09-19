#!/usr/bin/env python3
"""Stratify final REGR accepted links using inference-time evidence only."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path


METHODS = ("regr_final_no_motion", "regr_final")


def edge_id(row: dict[str, str]) -> tuple[int, int]:
    return int(row["earlier"]), int(row["later"])


def read_filtered(path: Path, methods: tuple[str, ...] = METHODS) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row["method"] in methods]


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def gap_bin(gap: int) -> str:
    if gap <= 5:
        return "1-5 frames"
    if gap <= 15:
        return "6-15 frames"
    return "16-30 frames"


def area_bin(area: float) -> str:
    if area < 32.0 ** 2:
        return "tiny (<32^2 px)"
    if area < 96.0 ** 2:
        return "small (32^2-96^2 px)"
    return "larger (>=96^2 px)"


def reciprocal_consensus(rows: list[dict[str, str]]) -> set[tuple[int, int]]:
    def ids_for(key):
        outgoing: dict[int, list[dict[str, str]]] = defaultdict(list)
        incoming: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            source, destination = edge_id(row)
            outgoing[source].append(row)
            incoming[destination].append(row)
        best_out = {identity: min(group, key=key) for identity, group in outgoing.items()}
        best_in = {identity: min(group, key=key) for identity, group in incoming.items()}
        return {
            edge_id(row) for row in rows
            if best_out[edge_id(row)[0]] is row and best_in[edge_id(row)[1]] is row
        }

    geometry = lambda row: (
        float(row["endpoint_center_distance_pixels"]), float(row["cosine_distance"]),
        int(row["gap"]), *edge_id(row),
    )
    appearance = lambda row: (
        float(row["cosine_distance"]), int(row["gap"]),
        float(row["endpoint_center_distance_pixels"]), *edge_id(row),
    )
    return ids_for(geometry) & ids_for(appearance)


def load_mmot_areas(path: Path) -> dict[int, float]:
    values: dict[int, list[float]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            values[int(row["id"])].append(float(row["w"]) * float(row["h"]))
    return {identity: float(statistics.median(group)) for identity, group in values.items()}


def aggregate(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        for dimension in ("gap", "object_size", "motion_reliability", "reciprocal_support"):
            grouped[(row["panel"], row["tracker"], row["method"], dimension, row[dimension])].append(row)
    output = []
    for (panel, tracker, method, dimension, value), group in sorted(grouped.items()):
        counts = Counter(row["relation"] for row in group)
        auditable = counts["correct"] + counts["false"]
        output.append({
            "panel": panel,
            "tracker": tracker,
            "method": method,
            "dimension": dimension,
            "bin": value,
            "accepted_links": len(group),
            "correct": counts["correct"],
            "false": counts["false"],
            "unknown": counts["unknown"],
            "auditable_link_precision": counts["correct"] / auditable if auditable else "N/A",
        })
    return output


def process_mmot(panel: str, result_dir: Path, cache_root: Path) -> list[dict]:
    decisions = read_filtered(result_dir / "results" / "candidate_decisions.csv", ("regr_final",))
    contexts: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        contexts[(row["family"], row["sequence"], row["class_name"], row["tracker"])].append(row)
    metadata = {}
    for context, group in contexts.items():
        consensus = reciprocal_consensus(group)
        for row in group:
            metadata[(*context, *edge_id(row))] = {
                "gap": gap_bin(int(row["gap"])),
                "motion_reliability": (
                    "reliable" if row.get("motion_informative") == "True" else "uninformative"
                ),
                "reciprocal_support": (
                    "consensus" if edge_id(row) in consensus else "non-consensus"
                ),
            }
    areas = {}
    output = []
    for row in read_filtered(result_dir / "results" / "accepted_links.csv"):
        context = (row["family"], row["sequence"], row["class_name"], row["tracker"])
        key = (*context, *edge_id(row))
        evidence = metadata[key]
        if context not in areas:
            prediction_path = (
                cache_root / "tracker_outputs" / row["family"] / row["sequence"]
                / row["class_name"] / f"{row['tracker']}.jsonl.gz"
            )
            areas[context] = load_mmot_areas(prediction_path)
        link_area = min(areas[context][edge_id(row)[0]], areas[context][edge_id(row)[1]])
        output.append({
            "panel": panel,
            "tracker": row["tracker"],
            "method": row["method"],
            "relation": row["posthoc_gt_correctness"],
            "object_size": area_bin(link_area),
            **evidence,
        })
    return output


def process_m3ot(result_dir: Path) -> list[dict]:
    decisions = read_filtered(result_dir / "candidate_decisions.csv", ("regr_final",))
    contexts: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        contexts[(row["sequence"], row["tracker"])].append(row)
    metadata = {}
    for context, group in contexts.items():
        consensus = reciprocal_consensus(group)
        for row in group:
            metadata[(*context, *edge_id(row))] = {
                "gap": gap_bin(int(row["gap"])),
                "motion_reliability": (
                    "reliable" if row.get("motion_informative") == "True" else "uninformative"
                ),
                "reciprocal_support": (
                    "consensus" if edge_id(row) in consensus else "non-consensus"
                ),
            }
    output = []
    for row in read_filtered(result_dir / "accepted_links.csv"):
        evidence = metadata[(row["sequence"], row["tracker"], *edge_id(row))]
        link_area = min(float(row["source_median_area"]), float(row["destination_median_area"]))
        output.append({
            "panel": "m3ot_oracle",
            "tracker": row["tracker"],
            "method": row["method"],
            "relation": row["posthoc_gt_correctness"],
            "object_size": area_bin(link_area),
            **evidence,
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-dir", type=Path, required=True)
    parser.add_argument("--oracle-cache", type=Path, required=True)
    parser.add_argument("--detector-dir", type=Path, required=True)
    parser.add_argument("--detector-cache", type=Path, required=True)
    parser.add_argument("--m3ot-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    links = []
    links.extend(process_mmot("mmot_oracle", args.oracle_dir, args.oracle_cache))
    links.extend(process_mmot("mmot_detector", args.detector_dir, args.detector_cache))
    links.extend(process_m3ot(args.m3ot_dir))
    write_csv(args.output_dir / "condition_link_audit.csv", aggregate(links))
    (args.output_dir / "manifest.json").write_text(
        json.dumps({
            "status": "COMPLETE",
            "scope": "accepted-link audit; not conditional tracking metrics",
            "methods": list(METHODS),
            "dimensions": ["gap", "object_size", "motion_reliability", "reciprocal_support"],
            "gt_use": "post-hoc correct/false/unknown labels only",
            "inference_evidence": "gap, tracker-box area, motion confidence, and reciprocal support",
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "COMPLETE", "accepted_link_rows": len(links)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
