#!/usr/bin/env python3
"""Measure native MMOT box sizes and size-stratified post-hoc link outcomes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def area_bin(area: float) -> str:
    if area < 32.0 ** 2:
        return "tiny_lt_32sq"
    if area < 96.0 ** 2:
        return "small_32sq_to_96sq"
    return "larger_ge_96sq"


def short_side_bin(value: float) -> str:
    if value < 16:
        return "lt_16px"
    if value < 32:
        return "16_to_32px"
    if value < 64:
        return "32_to_64px"
    return "ge_64px"


def valid_boxes(annotation: Path):
    with annotation.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        for values in csv.reader(handle):
            try:
                if len(values) < 12:
                    continue
                frame = int(float(values[0]))
                identity = int(float(values[1]))
                polygon = np.asarray([float(value) for value in values[2:10]], dtype=float).reshape(4, 2)
                class_id = int(float(values[11]))
            except (ValueError, IndexError):
                continue
            x1, y1 = polygon.min(axis=0)
            x2, y2 = polygon.max(axis=0)
            if frame < 1 or identity < 0 or not 0 <= class_id < 8:
                continue
            if not np.isfinite(polygon).all() or x2 <= x1 or y2 <= y1:
                continue
            yield float((x2 - x1) * (y2 - y1)), float(min(x2 - x1, y2 - y1))


def distribution_row(scope: str, sequence: str, values: list[tuple[float, float]]) -> dict:
    areas = np.asarray([value[0] for value in values], dtype=float)
    short = np.asarray([value[1] for value in values], dtype=float)
    area_counts = Counter(area_bin(value) for value in areas)
    short_counts = Counter(short_side_bin(value) for value in short)
    row = {
        "scope": scope, "sequence": sequence, "box_count": len(values),
        "area_mean_px2": float(areas.mean()), "short_side_mean_px": float(short.mean()),
    }
    for percentile in (10, 25, 50, 75, 90):
        row[f"area_p{percentile}_px2"] = float(np.percentile(areas, percentile))
        row[f"short_side_p{percentile}_px"] = float(np.percentile(short, percentile))
    for label in ("tiny_lt_32sq", "small_32sq_to_96sq", "larger_ge_96sq"):
        row[f"area_{label}_count"] = area_counts[label]
        row[f"area_{label}_fraction"] = area_counts[label] / len(values)
    for label in ("lt_16px", "16_to_32px", "32_to_64px", "ge_64px"):
        row[f"short_{label}_count"] = short_counts[label]
        row[f"short_{label}_fraction"] = short_counts[label] / len(values)
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True)
    parser.add_argument("--candidate-edges", type=Path)
    parser.add_argument("--accepted-links", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    by_sequence = {}
    all_values = defaultdict(list)
    for family, raw_root in args.family_root:
        for sequence_dir in sorted(path for path in Path(raw_root).iterdir() if path.is_dir()):
            values = [item for annotation in sorted(sequence_dir.glob("*.txt")) for item in valid_boxes(annotation)]
            if not values:
                raise SystemExit(f"no valid boxes: {sequence_dir}")
            by_sequence[(family, sequence_dir.name)] = values
            all_values[family].extend(values)
            all_values["all_sequences"].extend(values)

    sequence_rows = [
        distribution_row(family, sequence, values)
        for (family, sequence), values in sorted(by_sequence.items())
    ]
    aggregate_rows = [distribution_row(scope, "ALL", values) for scope, values in sorted(all_values.items())]
    write_csv(args.output_dir / "native_box_size_per_sequence.csv", sequence_rows)
    write_csv(args.output_dir / "native_box_size_distribution.csv", aggregate_rows)

    input_paths = []
    if args.candidate_edges and args.accepted_links:
        candidates = read_csv(args.candidate_edges)
        accepted = read_csv(args.accepted_links)
        input_paths.extend((args.candidate_edges, args.accepted_links))
        eligible = defaultdict(set)
        for row in candidates:
            size = area_bin(float(row["source_area_median_px2"]))
            source = (row["family"], row["sequence"], row["class_name"], row["tracker"], row["earlier"])
            for scope in (row["family"], "all_sequences"):
                eligible[(scope, row["tracker"], size)].add(source)
        outcomes = defaultdict(Counter)
        for row in accepted:
            size = area_bin(float(row["source_area_median_px2"]))
            for scope in (row["family"], "all_sequences"):
                outcomes[(scope, row["tracker"], row["method"], size)][row["posthoc_gt_correctness"]] += 1
        audit_rows = []
        for key, counts in sorted(outcomes.items()):
            known = counts["correct"] + counts["false"]
            denominator = len(eligible[(key[0], key[1], key[3])])
            audit_rows.append({
                "scope": key[0], "tracker": key[1], "method": key[2], "source_size_bin": key[3],
                "eligible_source_tracklets": denominator,
                "accepted_correct": counts["correct"], "accepted_false": counts["false"],
                "accepted_unknown": counts["unknown"],
                "known_link_precision": counts["correct"] / known if known else None,
                "all_accepted_coverage": sum(counts.values()) / denominator if denominator else None,
            })
        write_csv(args.output_dir / "size_stratified_link_audit.csv", audit_rows)

    outputs = sorted(args.output_dir.glob("*.csv"))
    roots = {name: str(Path(path)) for name, path in args.family_root}
    manifest = {
        "status": "COMPLETE",
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
        "families": roots,
        "bin_policy": {
            "area": ["<32^2 px^2", "32^2 to <96^2 px^2", ">=96^2 px^2"],
            "short_side": ["<16 px", "16 to <32 px", "32 to <64 px", ">=64 px"],
            "selection_note": "Fixed conventional area thresholds and fixed powers-of-two short-side bins; no result-dependent bin search.",
        },
        "ground_truth_use": "Object-size characterization and post-hoc link correctness only.",
        "inputs": {str(path): sha256(path) for path in input_paths},
        "outputs": {path.name: sha256(path) for path in outputs},
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "sequences": len(sequence_rows), "boxes": len(all_values["all_sequences"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
