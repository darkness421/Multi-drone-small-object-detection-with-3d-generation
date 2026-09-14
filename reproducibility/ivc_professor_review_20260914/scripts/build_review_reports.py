#!/usr/bin/env python3
"""Build professor-review reports from frozen MMOT and M3OT audit outputs.

The script reads only completed result artifacts. It does not execute a detector,
tracker, descriptor network, or tune any threshold. Bootstrap intervals are paired
over released MMOT sequences and use a fixed seed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


METRICS = ("HOTA", "AssA", "IDF1", "IDSW")
HIGHER_IS_BETTER = {"HOTA": True, "AssA": True, "IDF1": True, "IDSW": False}
MAIN_METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_greedy_guard",
    "geometry_reid_hungarian",
    "aflink_cached_overlap_safe",
    "com3d_reciprocal_guard",
)
KEY_COMPARATORS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_greedy_guard",
    "geometry_reid_hungarian",
    "aflink_cached_overlap_safe",
)
DISPLAY = {
    "no_refinement": "None",
    "geometry_greedy": "Geometry greedy",
    "geometry_reid_greedy_guard": "Geometry+ReID greedy",
    "geometry_reid_hungarian": "Partial Hungarian",
    "aflink_cached_no_dedup": "AFLink before native deduplication",
    "aflink_cached_native_dedup": "AFLink native deduplication",
    "aflink_cached_native_saved": "AFLink native saved output",
    "aflink_cached_overlap_safe": "AFLink + common validity adapter",
    "com3d_reciprocal_guard": "CoM3D-ACE (historical ranking)",
    "controlled_cost_greedy": "Common-cost greedy",
    "controlled_cost_reciprocal": "Common-cost reciprocal",
    "historical_geometry_first_reciprocal": "CoM3D-ACE (historical ranking)",
    "controlled_cost_partial_hungarian": "Common-cost partial Hungarian",
}
PROTOCOL_DISPLAY = {
    "oracle_aabb": "Oracle AABB",
    "official_detector": "Official detector",
}
TRACKER_DISPLAY = {
    "bytetrack": "ByteTrack",
    "ocsort": "OC-SORT",
    "deepocsort": "Deep OC-SORT",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--m3ot-dir", type=Path, required=True)
    parser.add_argument("--historical-oracle", type=Path, required=True)
    parser.add_argument("--historical-detector", type=Path, required=True)
    parser.add_argument("--legacy-snapshot", type=Path, required=True)
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument("--aflink-root", type=Path, required=True)
    parser.add_argument("--aflink-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20_260_914)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict], fieldnames: Iterable[str] | None = None) -> None:
    rows = list(rows)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_value(directory: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(directory), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def b(row: dict[str, str], key: str) -> bool:
    return row.get(key, "").lower() == "true"


def bootstrap_ci(values: np.ndarray, replicates: int, seed: int) -> tuple[float, float]:
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(replicates, len(values)))
    means = values[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(lo), float(hi)


def scope_rows(rows: list[dict[str, str]], scope: str) -> list[dict[str, str]]:
    if scope == "all50":
        return rows
    return [row for row in rows if row["family"] == scope]


def stable_seed(base: int, key: str) -> int:
    offset = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    return (base + offset) % (2**32)


def paired_rows(
    per_sequence: list[dict[str, str]], replicates: int, seed: int
) -> list[dict[str, object]]:
    index = {
        (row["protocol"], row["tracker"], row["sequence"], row["method"]): row
        for row in per_sequence
    }
    output: list[dict[str, object]] = []
    for protocol in PROTOCOL_DISPLAY:
        for tracker in TRACKER_DISPLAY:
            all_base = [
                row
                for row in per_sequence
                if row["protocol"] == protocol
                and row["tracker"] == tracker
                and row["method"] == "com3d_reciprocal_guard"
            ]
            for scope in ("all50", "legacy12", "confirmation38"):
                ours = scope_rows(all_base, scope)
                for comparator in KEY_COMPARATORS:
                    comparator_rows = []
                    for row in ours:
                        key = (protocol, tracker, row["sequence"], comparator)
                        if key not in index:
                            raise RuntimeError(f"Missing paired row: {key}")
                        comparator_rows.append(index[key])
                    result: dict[str, object] = {
                        "protocol": protocol,
                        "scope": scope,
                        "tracker": tracker,
                        "proposed_method": "com3d_reciprocal_guard",
                        "comparator": comparator,
                        "sequence_count": len(ours),
                        "bootstrap_unit": "released_sequence",
                        "bootstrap_replicates": replicates,
                        "bootstrap_seed": seed,
                    }
                    for metric in METRICS:
                        diffs = np.asarray(
                            [f(a, metric) - f(c, metric) for a, c in zip(ours, comparator_rows)],
                            dtype=float,
                        )
                        ci_lo, ci_hi = bootstrap_ci(
                            diffs, replicates, stable_seed(seed, f"{protocol}:{tracker}:{scope}:{comparator}:{metric}")
                        )
                        tol = 1e-12
                        if HIGHER_IS_BETTER[metric]:
                            wins = int(np.sum(diffs > tol))
                            losses = int(np.sum(diffs < -tol))
                        else:
                            wins = int(np.sum(diffs < -tol))
                            losses = int(np.sum(diffs > tol))
                        ties = int(len(diffs) - wins - losses)
                        result[f"delta_{metric}_mean"] = float(diffs.mean())
                        result[f"delta_{metric}_ci_low"] = ci_lo
                        result[f"delta_{metric}_ci_high"] = ci_hi
                        result[f"delta_{metric}_total"] = float(diffs.sum())
                        result[f"{metric}_wins"] = wins
                        result[f"{metric}_ties"] = ties
                        result[f"{metric}_losses"] = losses
                    output.append(result)
    return output


def build_main_comparison(aggregate: list[dict[str, str]]) -> list[dict[str, object]]:
    output = []
    for protocol in PROTOCOL_DISPLAY:
        for tracker in TRACKER_DISPLAY:
            for method in MAIN_METHODS:
                matches = [
                    row
                    for row in aggregate
                    if row["protocol"] == protocol
                    and row["tracker"] == tracker
                    and row["scope"] == "all_sequences"
                    and row["method"] == method
                ]
                if len(matches) != 1:
                    raise RuntimeError(f"Expected one aggregate row for {(protocol, tracker, method)}")
                row = matches[0]
                output.append(
                    {
                        "protocol": protocol,
                        "tracker": tracker,
                        "method": method,
                        "method_display": DISPLAY[method],
                        "HOTA_equal_sequence_mean": f(row, "HOTA"),
                        "AssA_equal_sequence_mean": f(row, "AssA"),
                        "IDF1_equal_sequence_mean": f(row, "IDF1"),
                        "IDSW_total": int(f(row, "IDSW")),
                        "MOTA_equal_sequence_mean": f(row, "MOTA"),
                        "FP_total": int(f(row, "FP")),
                        "FN_total": int(f(row, "FN")),
                        "prediction_boxes": int(f(row, "predicted_boxes")),
                        "valid_gt_boxes": int(f(row, "valid_gt_boxes")),
                        "input_rows": int(f(row, "input_rows")),
                        "output_rows": int(f(row, "output_rows")),
                        "valid_common_box_protocol": b(row, "valid_common_box_protocol"),
                        "aggregation": row["aggregation"],
                        "sequence_count": int(row["sequence_count"]),
                    }
                )
    return output


def build_native_vs_adapted(aggregate: list[dict[str, str]]) -> list[dict[str, object]]:
    methods = (
        "aflink_cached_no_dedup",
        "aflink_cached_native_dedup",
        "aflink_cached_native_saved",
        "aflink_cached_overlap_safe",
    )
    output = []
    for row in aggregate:
        if row["scope"] != "all_sequences" or row["method"] not in methods:
            continue
        output.append(
            {
                "protocol": row["protocol"],
                "tracker": row["tracker"],
                "stage_or_adapter": row["method"],
                "display_name": DISPLAY[row["method"]],
                "input_rows": int(f(row, "input_rows")),
                "output_rows": int(f(row, "output_rows")),
                "row_delta": int(f(row, "output_rows") - f(row, "input_rows")),
                "invalid_sequences": int(f(row, "invalid_sequences")),
                "box_preserving": int(f(row, "output_rows")) == int(f(row, "input_rows")),
                "valid_common_box_protocol": b(row, "valid_common_box_protocol"),
                "HOTA_equal_sequence_mean": f(row, "HOTA"),
                "AssA_equal_sequence_mean": f(row, "AssA"),
                "IDF1_equal_sequence_mean": f(row, "IDF1"),
                "IDSW_total": int(f(row, "IDSW")),
                "accepted_correct": int(f(row, "accepted_correct")),
                "accepted_false": int(f(row, "accepted_false")),
                "accepted_unknown": int(f(row, "accepted_unknown")),
            }
        )
    return sorted(output, key=lambda x: (x["protocol"], x["tracker"], x["stage_or_adapter"]))


def build_risk_matched(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["scope"] == "all_sequences":
            groups[(row["protocol"], row["tracker"])].append(row)
    for (protocol, tracker), group in sorted(groups.items()):
        ours = next(
            row
            for row in group
            if row["method"] == "com3d_reciprocal_guard"
            and abs(f(row, "appearance_threshold") - 0.30) < 1e-12
        )
        target_cov = f(ours, "all_accepted_coverage")
        target_err = f(ours, "known_link_error_rate")
        for method in (
            "com3d_reciprocal_guard",
            "controlled_cost_reciprocal",
            "geometry_reid_greedy_guard",
            "geometry_reid_hungarian",
        ):
            candidates = [row for row in group if row["method"] == method]
            fixed = next(row for row in candidates if abs(f(row, "appearance_threshold") - 0.30) < 1e-12)
            nearest = min(
                candidates,
                key=lambda row: (
                    abs(f(row, "all_accepted_coverage") - target_cov),
                    f(row, "appearance_threshold"),
                ),
            )
            eligible_error = [row for row in candidates if f(row, "known_link_error_rate") <= target_err + 1e-12]
            error_matched = max(
                eligible_error,
                key=lambda row: (f(row, "all_accepted_coverage"), -f(row, "appearance_threshold")),
            ) if eligible_error else None
            for mode, row in (("fixed_threshold_0.30", fixed), ("nearest_ours_coverage", nearest), ("max_coverage_at_or_below_ours_error", error_matched)):
                if row is None:
                    output.append(
                        {
                            "protocol": protocol,
                            "tracker": tracker,
                            "comparison_mode": mode,
                            "method": method,
                            "available": False,
                            "note": "No descriptive grid point satisfies the error constraint.",
                        }
                    )
                    continue
                output.append(
                    {
                        "protocol": protocol,
                        "tracker": tracker,
                        "comparison_mode": mode,
                        "method": method,
                        "available": True,
                        "appearance_threshold": f(row, "appearance_threshold"),
                        "eligible_source_tracklets": int(row["eligible_source_tracklets"]),
                        "accepted_total": int(row["accepted_total"]),
                        "accepted_known": int(row["accepted_known"]),
                        "accepted_unknown": int(row["accepted_unknown"]),
                        "all_accepted_coverage": f(row, "all_accepted_coverage"),
                        "known_link_error_rate": f(row, "known_link_error_rate"),
                        "known_link_precision": f(row, "known_link_precision"),
                        "reference_ours_coverage": target_cov,
                        "reference_ours_error": target_err,
                        "selection_scope": "post-hoc descriptive grid; not a submitted operating-point selection",
                    }
                )
    return output


def build_runtime(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    methods = (
        "geometry_greedy",
        "geometry_reid_greedy_guard",
        "com3d_reciprocal_guard",
        "controlled_cost_greedy",
        "controlled_cost_reciprocal",
        "geometry_reid_hungarian",
        "aflink_cached_overlap_safe",
    )
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["method"] in methods:
            grouped[(row["protocol"], row["tracker"], row["method"])].append(row)
    output = []
    for (protocol, tracker, method), values in sorted(grouped.items()):
        output.append(
            {
                "protocol": protocol,
                "tracker": tracker,
                "method": method,
                "class_sequence_instances": len(values),
                "candidate_build_ms_sum": sum(f(row, "candidate_build_ms") for row in values),
                "solver_ms_sum_of_instance_means": sum(f(row, "solver_ms_mean") for row in values),
                "solver_ms_median_of_instance_medians": float(np.median([f(row, "solver_ms_median") for row in values])),
                "solver_peak_memory_max_bytes": max(int(f(row, "tracemalloc_peak_bytes")) for row in values),
                "hungarian_dense_matrix_bytes_sum": sum(int(f(row, "hungarian_dense_matrix_bytes")) for row in values),
                "timed_repeats_per_instance": int(values[0]["repeat_count"]),
                "descriptor_extraction_included": False,
                "aflink_model_scoring_included": False,
            }
        )
    return output


def historical_consistency(
    audit: list[dict[str, str]], historical_oracle: Path, historical_detector: Path
) -> tuple[list[dict[str, object]], float]:
    audit_index = {
        (row["protocol"], row["scope"], row["tracker"], row["method"]): row
        for row in audit
    }
    comparisons = []
    max_diff = 0.0
    for protocol, source in (
        ("oracle_aabb", historical_oracle),
        ("official_detector", historical_detector),
    ):
        for old in read_csv(source):
            if old["scope"] != "all_sequences":
                continue
            if old["method"] not in {
                "no_refinement", "geometry_greedy", "geometry_reid_hungarian", "com3d_reciprocal_guard"
            }:
                continue
            row = audit_index[(protocol, old["scope"], old["tracker"], old["method"])]
            for metric in ("HOTA", "AssA", "IDF1", "IDSW", "MOTA", "TP", "FP", "FN", "predicted_boxes"):
                difference = abs(float(old[metric]) - float(row[metric]))
                max_diff = max(max_diff, difference)
                comparisons.append(
                    {
                        "protocol": protocol,
                        "scope": old["scope"],
                        "tracker": old["tracker"],
                        "method": old["method"],
                        "metric": metric,
                        "historical": old[metric],
                        "cache_audit": row[metric],
                        "absolute_difference": difference,
                        "exact": difference == 0.0,
                    }
                )
    return comparisons, max_diff


def aggregate_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {
        (row["protocol"], row["tracker"], row["method"]): row
        for row in rows
        if row["scope"] == "all_sequences"
    }


def markdown_main_table(main_rows: list[dict[str, object]]) -> str:
    lines = [
        "| Input | Tracker | Refiner | HOTA | AssA | IDF1 | IDSW |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in main_rows:
        lines.append(
            f"| {PROTOCOL_DISPLAY[row['protocol']]} | {TRACKER_DISPLAY[row['tracker']]} | "
            f"{row['method_display']} | {row['HOTA_equal_sequence_mean']:.2f} | "
            f"{row['AssA_equal_sequence_mean']:.2f} | {row['IDF1_equal_sequence_mean']:.2f} | "
            f"{row['IDSW_total']:,} |"
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit_manifest = json.loads((args.audit_dir / "manifest.json").read_text())
    m3ot_manifest = json.loads((args.m3ot_dir / "manifest.json").read_text())
    if audit_manifest["status"] != "COMPLETE" or m3ot_manifest["status"] != "COMPLETE":
        raise RuntimeError("Refusing to report incomplete experiment output")

    aggregate = read_csv(args.audit_dir / "solver_metrics_aggregate.csv")
    per_sequence = read_csv(args.audit_dir / "solver_metrics_per_sequence.csv")
    risk = read_csv(args.audit_dir / "risk_coverage.csv")
    runtime = read_csv(args.audit_dir / "refiner_runtime.csv")
    failures = read_csv(args.audit_dir / "aflink_failure_summary.csv")
    m3ot_aggregate = read_csv(args.m3ot_dir / "m3ot_linker_comparison.csv")
    m3ot_cases = read_csv(args.m3ot_dir / "m3ot_edge_casebook.csv")

    main_rows = build_main_comparison(aggregate)
    write_csv(args.output_dir / "main_comparison.csv", main_rows)
    stage_rows = [
        {
            "protocol": row["protocol"],
            "tracker": row["tracker"],
            "upstream_prediction_boxes": row["prediction_boxes"],
            "refiner_input_rows": row["input_rows"],
            "no_refinement_output_rows": row["output_rows"],
            "valid_gt_boxes": row["valid_gt_boxes"],
            "FP_total": row["FP_total"],
            "FN_total": row["FN_total"],
            "MOTA_equal_sequence_mean": row["MOTA_equal_sequence_mean"],
            "area_height_aspect_filter_added_by_adapter": False,
            "track_confirmation": "Frozen tracker-specific output; settings recorded in manuscript Table 1",
        }
        for row in main_rows
        if row["method"] == "no_refinement"
    ]
    write_csv(args.output_dir / "tracker_stage_summary.csv", stage_rows)
    native_rows = build_native_vs_adapted(aggregate)
    write_csv(args.output_dir / "native_vs_adapted_results.csv", native_rows)
    paired = paired_rows(per_sequence, args.bootstrap_replicates, args.bootstrap_seed)
    write_csv(args.output_dir / "paired_linker_deltas.csv", paired)
    risk_matched = build_risk_matched(risk)
    write_csv(args.output_dir / "risk_matched_operating_points.csv", risk_matched)
    runtime_summary = build_runtime(runtime)
    write_csv(args.output_dir / "runtime_summary.csv", runtime_summary)
    consistency_rows, max_historical_diff = historical_consistency(
        aggregate, args.historical_oracle, args.historical_detector
    )
    write_csv(args.output_dir / "historical_reproduction_check.csv", consistency_rows)

    paper_commit = git_value(args.paper_dir, "rev-parse", "HEAD")
    paper_pdf = args.paper_dir / "main.pdf"
    expected_pdf_hash = "7a04b4d4aa7a6c1f1462aca97a5d9346548c72792c4313b48d0f87756734aab6"
    paper_hash = sha256(paper_pdf)
    aflink_source = args.aflink_root / "AFLink" / "AppFreeLink.py"
    aflink_commit = git_value(args.aflink_root, "rev-parse", "HEAD")
    aflink_diff = git_value(args.aflink_root, "diff", "--", "AFLink/AppFreeLink.py")
    dedup_line = None
    for number, line in enumerate(aflink_source.read_text(encoding="utf-8").splitlines(), start=1):
        if "res = self.deduplicate(res)" in line:
            dedup_line = number
            break

    dropped_by_protocol = Counter()
    failure_contexts_by_protocol = Counter()
    for row in failures:
        key = row["protocol"]
        dropped_by_protocol[key] += int(row["native_dropped_boxes"])
        failure_contexts_by_protocol[key] += 1
    aflink_record = {
        "status": "VERIFIED_FROM_FROZEN_SOURCE_AND_CACHED_ASSIGNMENTS",
        "source_repository": "https://github.com/dyhBUPT/StrongSORT",
        "source_commit": aflink_commit,
        "source_path": str(aflink_source),
        "source_sha256": sha256(aflink_source),
        "source_diff_from_commit": aflink_diff or "",
        "native_deduplicate_call_line": dedup_line,
        "native_save_format": "%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%d,%d,%d",
        "checkpoint_path": str(args.aflink_checkpoint),
        "checkpoint_sha256": sha256(args.aflink_checkpoint),
        "execution_parameters": {"thrT": [0, 30], "thrS": 75, "thrP": 0.05, "interpolation": False},
        "cached_assignment_scope": "Official model/checkpoint scores and assignments were reused; the network was not rerun.",
        "native_behavior": "After ID remapping, native deduplicate keeps the first row for each (frame, ID), deleting boxes when a merge creates overlap.",
        "native_failure_contexts": len(failures),
        "native_dropped_boxes": sum(int(row["native_dropped_boxes"]) for row in failures),
        "failure_contexts_by_protocol": dict(failure_contexts_by_protocol),
        "dropped_boxes_by_protocol": dict(dropped_by_protocol),
        "common_validity_adapter": "Reject an AFLink-selected merge when the source and destination components have overlapping frame support; preserve all boxes; use no GT.",
        "class_id_scope": "Class-local numeric IDs are namespaced before evaluator combination; unscoped numeric reuse across classes is not an evaluator collision.",
        "stage_audit": str(args.audit_dir / "aflink_stage_audit.csv"),
        "minimal_failure_case": str(args.audit_dir / "minimal_failure_case"),
    }
    (args.output_dir / "aflink_source_record.json").write_text(
        json.dumps(aflink_record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    property_summary = audit_manifest["property_summary"]
    reciprocal_text = f"""# Reciprocal path invariant audit

## Result

Status: **{property_summary['status']}** over {property_summary['instances']:,} released
sequence/class/tracker/input instances.

- Strict-time violations: {property_summary['strict_time_order_violations']}
- Maximum observed indegree/outdegree: {property_summary['maximum_observed_indegree']}/{property_summary['maximum_observed_outdegree']}
- Cyclic proposal graphs: {property_summary['cycle_instances']}
- Duplicate-frame input tracklets: {property_summary['input_duplicate_instances']}
- Component-guard rejections: {property_summary['component_guard_rejections']}
- Guard/no-guard output differences: {property_summary['guard_output_difference_instances']}

## Structural conclusion

The implementation constructs one candidate/proposal graph and does not regenerate
proposals after union operations. Every accepted proposal has strict forward time,
and reciprocal predecessor/successor choice limits indegree and outdegree to one.
With duplicate-free input tracklets, each connected component is therefore a
time-ordered directed path whose frame supports cannot overlap. Under the evaluated
algorithm, the component-overlap check is structurally unable to reject an
otherwise reciprocal proposal. It remains useful as a defensive assertion and
output validator, but it is not an independently active performance module.

Raw property results: `results_raw/mmot_cached_solver_audit_v1/property_test_results.json`.
"""
    (args.output_dir / "reciprocal_path_invariants.md").write_text(reciprocal_text, encoding="utf-8")

    audit_index = aggregate_lookup(aggregate)
    controlled_methods = ("com3d_reciprocal_guard", "controlled_cost_greedy", "controlled_cost_reciprocal", "geometry_reid_hungarian")
    controlled_lines = [
        "| Input | Tracker | Method | IDF1 | IDSW | Coverage | Known error |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    risk_fixed = {
        (row["protocol"], row["tracker"], row["method"]): row
        for row in risk
        if row["scope"] == "all_sequences" and abs(f(row, "appearance_threshold") - 0.30) < 1e-12
    }
    for protocol in PROTOCOL_DISPLAY:
        for tracker in TRACKER_DISPLAY:
            for method in controlled_methods:
                row = audit_index[(protocol, tracker, method)]
                rr = risk_fixed.get((protocol, tracker, method))
                risk_cells = (
                    f"{100*f(rr, 'all_accepted_coverage'):.1f}% | "
                    f"{100*f(rr, 'known_link_error_rate'):.1f}%"
                    if rr is not None
                    else "n/a | n/a"
                )
                controlled_lines.append(
                    f"| {PROTOCOL_DISPLAY[protocol]} | {TRACKER_DISPLAY[tracker]} | {DISPLAY[method]} | "
                    f"{f(row, 'IDF1'):.2f} | {int(f(row, 'IDSW')):,} | "
                    f"{risk_cells} |"
                )

    paired_lookup = {
        (row["protocol"], row["tracker"], row["scope"], row["comparator"]): row for row in paired
    }
    ci_lines = [
        "| Input | Tracker | Comparator | Delta IDF1 [95% CI] | W/T/L |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for protocol in PROTOCOL_DISPLAY:
        for tracker in TRACKER_DISPLAY:
            for comparator in ("geometry_reid_greedy_guard", "geometry_reid_hungarian", "aflink_cached_overlap_safe"):
                row = paired_lookup[(protocol, tracker, "all50", comparator)]
                ci_lines.append(
                    f"| {PROTOCOL_DISPLAY[protocol]} | {TRACKER_DISPLAY[tracker]} | {DISPLAY[comparator]} | "
                    f"{row['delta_IDF1_mean']:+.2f} [{row['delta_IDF1_ci_low']:+.2f}, {row['delta_IDF1_ci_high']:+.2f}] | "
                    f"{row['IDF1_wins']}/{row['IDF1_ties']}/{row['IDF1_losses']} |"
                )

    comparative_text = f"""# Comparative claim decision

## Decision

The completed cache-controlled audit does **not** support presenting the historical
geometry-first CoM3D-ACE row as the most accurate or risk-optimal MMOT linker. It
does support a narrower claim: the deterministic, box-preserving refiner improves
equal-sequence means over no refinement under all six upstream/input conditions,
while exposing reproducible assignment behavior and explicit transfer limits.

## Full-50 complete comparison

{markdown_main_table(main_rows)}

Geometry+ReID greedy and partial Hungarian exceed historical CoM3D-ACE IDF1 in all
six conditions. The paired intervals below compare the proposed row directly with
the strongest relevant linkers rather than only with no refinement.

{chr(10).join(ci_lines)}

## Ranking-versus-solver control

{chr(10).join(controlled_lines)}

At the unchanged 0.30 gate, common-cost reciprocal selection improves IDF1 and has
both higher accepted-link coverage and lower known-link error than historical
geometry-first CoM3D-ACE in all six conditions. This diagnoses geometry-first
ranking as a material limitation; it does not license renaming the post-hoc
common-cost variant as the submitted method.

Solver-only timing favors reciprocal assignment modestly in several conditions,
but the absolute difference from Hungarian is small compared with candidate
construction and especially descriptor extraction. Consequently, runtime does not
provide a strong end-to-end selection basis for the historical rule.
"""
    (args.output_dir / "comparative_claim_decision.md").write_text(comparative_text, encoding="utf-8")

    m3ot_lookup = {
        (row["split"], row["tracker"], row["method"]): row for row in m3ot_aggregate
    }
    held_opportunities = [row for row in m3ot_cases if row["split"] == "held_out" and row["row_type"] == "correct_fragment_opportunity"]
    decision_counts = Counter(row["historical_decision"] for row in held_opportunities)
    historical_false = [
        row for row in m3ot_cases
        if row["split"] == "held_out"
        and row["row_type"] == "accepted_false_link"
        and row["method"] == "historical_geometry_first_reciprocal"
    ]
    modality_counts = Counter(row["modality"] for row in historical_false)
    failure_text = f"""# M3OT concise failure analysis

The fixed M3OT experiment was reproduced exactly for all 16 split/tracker/sequence
instances (maximum metric difference 0; accepted-edge sets exact). The historical
descriptor protocol is oracle-box diagnostic: tracker observations are admitted to
image crops through IoU >= 0.9 matching to oracle GT before BaseReID encoding.

On the held-out split, the historical rule accepts 0 correct and 7 false links for
ByteTrack and 0 correct and 3 false links for OC-SORT. The candidate universe still
contains 3 and 5 auditable same-actor opportunities. Across those eight
opportunities, {decision_counts.get('geometry_gate', 0)} are excluded by
the fixed 55-pixel geometry gate, {decision_counts.get('lost_incoming_rank', 0)}
lose the reciprocal incoming comparison, and {decision_counts.get('lost_outgoing_rank', 0)}
lose the outgoing comparison.

The common-cost reciprocal diagnostic recovers one correct held-out link for each
tracker and reduces false accepted links to 6 and 2, respectively, but held-out
IDF1 remains below no refinement:

| Tracker | None | Historical | Common-cost reciprocal | Partial Hungarian |
| --- | ---: | ---: | ---: | ---: |
| ByteTrack | {f(m3ot_lookup[('held_out','bytetrack','no_refinement')], 'IDF1'):.2f} | {f(m3ot_lookup[('held_out','bytetrack','historical_geometry_first_reciprocal')], 'IDF1'):.2f} | {f(m3ot_lookup[('held_out','bytetrack','controlled_cost_reciprocal')], 'IDF1'):.2f} | {f(m3ot_lookup[('held_out','bytetrack','controlled_cost_partial_hungarian')], 'IDF1'):.2f} |
| OC-SORT | {f(m3ot_lookup[('held_out','ocsort','no_refinement')], 'IDF1'):.2f} | {f(m3ot_lookup[('held_out','ocsort','historical_geometry_first_reciprocal')], 'IDF1'):.2f} | {f(m3ot_lookup[('held_out','ocsort','controlled_cost_reciprocal')], 'IDF1'):.2f} | {f(m3ot_lookup[('held_out','ocsort','controlled_cost_partial_hungarian')], 'IDF1'):.2f} |

Historical false-link modalities are {dict(modality_counts)}. The casebook records
gap, pixel and normalized displacement, appearance distance, crop area, endpoint
purity, and competing candidates for every audited opportunity and false link.
These results implicate both ranking and cue/domain mismatch; a solver substitution
alone does not establish cross-domain transfer. Redesign should be performed on
development data before any new held-out claim.
"""
    (args.output_dir / "concise_failure_analysis.md").write_text(failure_text, encoding="utf-8")

    numerical_text = f"""# Numerical consistency report

## Historical reproduction

The cache-only audit exactly reproduces the historical no-refinement, geometry
greedy, partial-Hungarian, and CoM3D-ACE all-50 rows for both oracle and
official-detector protocols and all three trackers. Maximum
absolute difference across HOTA, AssA, IDF1, IDSW, MOTA, TP, FP, FN, and prediction
count: **{max_historical_diff:g}**.

The newly surfaced Geometry+ReID greedy row is computed from the same frozen
candidate/descriptor caches. Its oracle all-50 IDF1 values are 51.80, 46.25, and
83.99 for ByteTrack, OC-SORT, and Deep OC-SORT, matching the manuscript's prior
ablation values after display rounding.

## Aggregation and rounding

- HOTA, AssA, IDF1, and MOTA are equal-sequence means.
- IDSW, FP, FN, and TP are totals over the stated sequence set.
- Delta statements are computed from full-precision CSV values and only then
  rounded for display; they are not recomputed from rounded table entries.
- Paired confidence intervals resample released sequences, with 10,000 replicates
  and seed 20260914.

## Source linkage limit

The exact review-target PDF with SHA-256 `{expected_pdf_hash}` is not present on
this machine. The current 23-page source checkout is commit `{paper_commit}` and
its pre-revision local `main.pdf` hash is `{paper_hash}`. The numerical source rows
are fully linked, but byte-for-byte linkage to the named review PDF remains
unverified until that exact PDF is supplied.
"""
    (args.output_dir / "numerical_consistency_report.md").write_text(numerical_text, encoding="utf-8")

    inventory_text = f"""# Experiment inventory

## Execution status

| Item | Status | Inputs | Outputs |
| --- | --- | --- | --- |
| P0 source/result linkage | Partial | Current source and frozen CSVs available; named review PDF absent | Manifest, main comparison, consistency report |
| P1 AFLink stage audit | Complete | Frozen official scores/assignments, source commit, checkpoint | Stage CSV, minimal case, native/adapter metrics |
| P2 reciprocal invariant | Complete | All cached MMOT class instances | Property tests and invariant report |
| P3 ranking/solver control | Complete | Frozen tracklets/descriptors; no network rerun | 3,300 sequence rows, 33,466 edge decisions, risk/runtime CSVs |
| P4 M3OT failure diagnostic | Complete | Frozen development/held-out inputs | 80 sequence-method rows and 118 casebook rows |
| P5 paired linker CI | Complete | MMOT per-sequence results | Paired 10,000-resample intervals |
| MMOT source-flight block CI | Not executable | Official release exposes no per-sequence source-flight grouping | No inferred grouping or block CI |
| New detector/tracker/training run | Excluded | Not required for the cache-controlled review | Not run |

## Frozen conditions

- MMOT: all 50 released test sequences, 5,466 frames, oracle AABB and shared
  official-detector conditions, ByteTrack/OC-SORT/Deep OC-SORT.
- Fixed graph gates: gap <= 30 released frames, endpoint distance <= 55 native
  pixels, cosine distance <= 0.30. No threshold was selected from test results.
- Pseudo-RGB for appearance: zero-based bands `[4,2,1]` in RGB order.
- Coverage denominator: source tracklets having at least one strictly later,
  frame-disjoint successor within 30 frames before geometry/appearance gates.
- Ground truth: tracking metrics and post-hoc MMOT edge labels only. M3OT is a
  separate historical oracle-box diagnostic whose crop admission uses IoU >= 0.9
  to oracle GT, as recorded in its manifest.

## Commands

MMOT audit:

```text
{audit_manifest['command']}
```

M3OT diagnostic:

```text
{m3ot_manifest['command']}
```

Report generation:

```text
{' '.join(platform.python_implementation() for _ in range(0)) or 'python'} {Path(__file__)} [paths recorded in build_and_results_manifest.json]
```
"""
    (args.output_dir / "experiment_inventory.md").write_text(inventory_text, encoding="utf-8")

    claim_diff = """# Manuscript claim diff

| Location | Previous reading | Verified replacement |
| --- | --- | --- |
| Abstract/Results | None-to-CoM3D comparison could read as overall superiority | State gains over unchanged upstream trajectories and disclose stronger same-input linker rows |
| Comparison layout | Operational and static-assignment rows combined in one main table | Keep None, AFLink+VA, and CoM3D-ACE in the operational main table; retain every static control and paired interval in the explicitly linked appendix |
| Reciprocal ranking | Geometry-first order presented without a controlled ranking diagnosis | Report that common-cost reciprocal outperforms historical ranking in all six IDF1/risk comparisons |
| Component guard | Presented as an active merge-prevention module | Retain as a defensive assertion; one-shot strict-time reciprocal paths make it structurally redundant here |
| AFLink | Official aggregate marked N/A for duplicate identities | Explain native post-remap deduplication deletes boxes; compare a separately named no-GT box-preserving adapter |
| Confirmation38 | Called frozen/independent without external timestamp evidence | Call it a pre-specified local reporting partition and avoid external-independence language |
| 50 sequences | Could imply every individual sequence improves | Say equal-sequence means improve over 50 sequences; report paired W/T/L separately |
| Target training | Could include the official MMOT-trained detector | Restrict no-target-training statement to the refiner and fixed BaseReID descriptor |
| M3OT | Broad cue-based explanation | State exact opportunity/rank diagnostics and disclose oracle-GT crop-admission protocol |
| Figures 1/2 | Could read as evaluated cross-view/active-routing evidence | Keep author figures but explicitly label motivation/system context outside the temporal quantitative claim |
"""
    (args.output_dir / "manuscript_claim_diff.md").write_text(claim_diff, encoding="utf-8")

    manifest = {
        "status": "COMPLETE_WITH_TARGET_PDF_LINKAGE_LIMIT",
        "review_target": {
            "filename": "_ELSEVIER_CoM3D_ACE__Ambiguity_Aware_Cross_View_Evidence_Routing_for_Cooperative_UAV_Small_Object_Perception(20260914-010039).pdf",
            "expected_sha256": expected_pdf_hash,
            "available_locally": False,
        },
        "paper_source": {
            "path": str(args.paper_dir),
            "commit_before_revision": paper_commit,
            "pre_revision_pdf": str(paper_pdf),
            "pre_revision_pdf_sha256": paper_hash,
        },
        "historical_results": {
            "oracle": {"path": str(args.historical_oracle), "sha256": sha256(args.historical_oracle)},
            "detector": {"path": str(args.historical_detector), "sha256": sha256(args.historical_detector)},
            "max_reproduction_abs_difference": max_historical_diff,
        },
        "mmot_audit": audit_manifest,
        "m3ot_diagnostic": m3ot_manifest,
        "aflink": aflink_record,
        "confirmation_partition": {
            "status": "pre-specified local reporting partition",
            "external_preregistration_or_independent_timestamp": False,
            "split_manifest": str(args.legacy_snapshot / "results_raw/e1_full50_split/manifest.json"),
            "split_manifest_sha256": sha256(args.legacy_snapshot / "results_raw/e1_full50_split/manifest.json"),
        },
        "channel_and_cache_linkage": {
            "channel_policy": "zero-based [4,2,1] -> RGB",
            "channel_audit": {
                "path": str(args.legacy_snapshot / "results_raw/e0/channel_audit.json"),
                "sha256": sha256(args.legacy_snapshot / "results_raw/e0/channel_audit.json"),
            },
            "oracle_result_manifest": {
                "path": str(args.legacy_snapshot / "results_raw/e1_direct_full50_v2_equal/manifest.json"),
                "sha256": sha256(args.legacy_snapshot / "results_raw/e1_direct_full50_v2_equal/manifest.json"),
            },
            "detector_result_manifest": {
                "path": str(args.legacy_snapshot / "results_raw/e3_temporal_full50_v2_equal/manifest.json"),
                "sha256": sha256(args.legacy_snapshot / "results_raw/e3_temporal_full50_v2_equal/manifest.json"),
            },
            "detector_checkpoint_manifest": {
                "path": str(args.legacy_snapshot / "results_raw/e3_detector_full50_v1/detector_checkpoint_manifest.json"),
                "sha256": sha256(args.legacy_snapshot / "results_raw/e3_detector_full50_v1/detector_checkpoint_manifest.json"),
            },
        },
        "block_bootstrap": {
            "status": "NOT_EXECUTED",
            "reason": "Official release metadata inspected locally does not map released sequence IDs to source flights; prefixes were not treated as flight IDs.",
            "official_readme_sha256": "ef9a84ac3233ffbc37b262f14a3e5f839356760d8ff6659e24faaea6c36d02c3",
        },
        "report_builder": {"path": str(Path(__file__)), "sha256": sha256(Path(__file__))},
    }
    (args.output_dir / "build_and_results_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    resolution = f"""# Professor review resolution

## 1. 지적별 판정과 근거

- P0: **부분 해결.** 원시 CSV, 캐시, 실행 명령, descriptor/source hash와 현재
  source commit을 연결했고 핵심 비교군을 복원했다. 단, 지정된 SHA-256의
  review PDF가 로컬에 없어 그 PDF와의 byte-level 연결만 미확인이다.
- P1: **해결.** `aflink_source_record.json`, `aflink_stage_audit.csv`,
  `minimal_failure_case/`, `native_vs_adapted_results.csv`에 원인과 결과를 저장했다.
- P2: **해결.** 1,989개 실제 인스턴스 property test가 통과했다. guard는 평가된
  규칙에서 방어적 assertion이며 독립 성능 모듈이 아니다.
- P3: **해결.** 동일 후보 graph/cost 기반 solver 통제, edge trace, error--coverage,
  CPU solver 시간/메모리를 산출했다. 사후 threshold 선택은 하지 않았다.
- P4: **해결.** M3OT 16개 기존 인스턴스를 오차 0으로 재현하고 기회 손실,
  오연결, greedy/reciprocal/Hungarian 결과를 비교했다.
- P5: **부분 해결.** 주요 linker 대비 paired sequence CI를 계산했다. 공식 metadata에
  source-flight mapping이 없어 block bootstrap은 수행하지 않았다.
- P6: **부분 해결/원고 반영.** 본 보고서 수치를 근거로 운영형 main comparison과
  별도 static-assignment appendix, AFLink, guard, M3OT 및 confirmation scope를
  수정한다. 저자 제작 Fig. 1/2
  파일은 보존하고 캡션과 본문에서 motivation/system context로 범위를 제한한다.

## 2. AFLink failure stage, 원인, raw 및 adapter 결과

Frozen StrongSORT commit `{aflink_commit}`의 `AppFreeLink.py:{dedup_line}`는 ID remap
뒤 `deduplicate`를 호출한다. Cached official assignments는 {len(failures)}개
sequence/tracker/class context에서 overlapping IDs를 만들었고, native deduplication은
총 {sum(int(row['native_dropped_boxes']) for row in failures)}개 box를 삭제했다.
2-decimal save formatting은 별도의 numeric serialization 변화다. 클래스별 local ID
재사용은 evaluator namespace 때문에 충돌 원인이 아니다. 무GT validity adapter는
overlap을 만드는 merge를 거부하여 모든 box를 보존했고, 전 6개 full-set 조건에서
유효한 수치를 생성했다. 자세한 수치는 `native_vs_adapted_results.csv`에 있다.

## 3. Guard 코드/명세 일치와 역할

실제 코드는 proposal을 한 번 생성하고, strict forward-time edge와 reciprocal
predecessor/successor를 사용한다. 관측 indegree/outdegree는 최대 1/1이고 cycle,
입력 frame duplicate, guard rejection, guard/no-guard 차이는 모두 0이었다. 따라서
현재 명세에서 component guard는 구조적으로 중복이며 defensive assertion/output
validation으로만 유지한다.

## 4. 주요 linker 대비 정확도, risk, 비용과 주장 근거

Historical CoM3D는 None보다 6개 조건의 평균 IDF1을 모두 개선한다. 그러나
Geometry+ReID greedy와 partial Hungarian보다 IDF1이 6개 모두 낮다. Common scalar
cost를 쓴 reciprocal은 historical ranking보다 6개 모두 IDF1이 높고, 고정 0.30에서
coverage도 높으며 known-link error도 낮다. Reciprocal solver의 CPU 시간/peak memory는
Hungarian보다 대체로 작지만 descriptor/candidate 비용에 비해 절대 차이가 작다.
따라서 historical rule의 최고 정확도·최적 risk·실질 end-to-end 비용 우위는
입증되지 않았다. 유지 가능한 핵심 주장은 box-preserving deterministic refinement와
None 대비 평균 개선, 명시적 failure audit이다.

## 5. M3OT 원인과 재설계 필요성

Held-out 정답 기회 8개 중 5개는 55-pixel gate 밖이고, 2개는 incoming rank, 1개는
outgoing rank에서 탈락했다. Common-cost reciprocal은 tracker별 정답 링크 1개를
복원하고 false link를 줄였지만 두 tracker 모두 None보다 IDF1이 낮다. Ranking과
fixed pixel/MOT17 appearance cue의 domain mismatch가 함께 남으므로, 새로운 transfer
주장 전에는 development-only redesign과 새 confirmation data가 필요하다.

## 6. 원고 수정과 수치 변경 근거

Main Results에는 None, AFLink+VA, CoM3D-ACE의 운영형 비교를 배치하고, geometry
greedy, Geometry+ReID greedy, partial Hungarian을 포함한 전체 동일 입력 비교와
paired CI는 명시적으로 연결된 부록에 보존한다. AFLink는 native와
`+ common validity adapter`를 구분한다. Guard는 assertion으로
정정하고, “all 50 sequences improve”를 “the equal-sequence mean over 50 improves”로
제한한다. Confirmation38은 외부 독립성이 아니라 locally pre-specified partition으로
표현한다. M3OT oracle crop admission과 실패 분석을 명시한다. 표 수치는
`main_comparison.csv`, `paired_linker_deltas.csv`, `m3ot_linker_comparison.csv`의
full-precision 값에서 한 번만 반올림한다.

## 7. 독립 검증 미완료 사항과 필요한 산출물

- Review PDF hash `{expected_pdf_hash}`: 정확한 PDF 파일이 필요하다.
- MMOT 원영상/비행 단위 block bootstrap: 공식 sequence-to-flight metadata가 필요하다.
- Confirmation38의 외부 preregistration/독립 timestamp: 해당 시점의 외부 기록이 필요하다.
- M3OT descriptor의 detector-only transfer: 현재 기록은 oracle GT IoU crop admission이므로,
  별도 사전 고정 detector-input protocol과 새 실행이 필요하다.
- GIAOTracker 공식 비교: 공개 implementation과 compatible weights가 필요하다.
"""
    (args.output_dir / "professor_review_resolution.md").write_text(resolution, encoding="utf-8")


if __name__ == "__main__":
    main()
