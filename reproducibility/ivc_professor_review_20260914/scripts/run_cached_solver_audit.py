#!/usr/bin/env python3
"""Audit MMOT refiners from immutable tracklet and descriptor caches.

This script never runs a detector, tracker, or descriptor network. It evaluates
historical and controlled assignment rules on identical cached inputs, audits
the AFLink post-assignment stages, and checks reciprocal-path invariants.
Ground-truth identities are used only for metrics and post-hoc edge labels.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import importlib.util
import json
import os
import platform
import statistics
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np


METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_greedy_guard",
    "com3d_reciprocal_guard",
    "geometry_reid_hungarian",
    "controlled_cost_greedy",
    "controlled_cost_reciprocal",
    "aflink_cached_no_dedup",
    "aflink_cached_native_dedup",
    "aflink_cached_native_saved",
    "aflink_cached_overlap_safe",
)
RISK_METHODS = (
    "geometry_reid_greedy_guard",
    "com3d_reciprocal_guard",
    "controlled_cost_reciprocal",
    "geometry_reid_hungarian",
)
APPEARANCE_GRID = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
FIXED_APPEARANCE = 0.30


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fields:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_optional_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def load_aflink_edges(path: Path) -> dict[tuple[str, str, str, str], list[dict]]:
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["method"] != "aflink_official":
                continue
            key = (row["family"], row["sequence"], row["class_name"], row["tracker"])
            grouped[key].append({
                "earlier": int(row["earlier"]),
                "later": int(row["later"]),
                "gap": int(row["gap"]),
                "aflink_cost": float(row["aflink_cost"]),
                "aflink_probability": float(row["aflink_probability"]),
                "endpoint_top_left_distance_pixels": parse_optional_float(
                    row.get("endpoint_top_left_distance_pixels")
                ),
            })
    return dict(grouped)


def gated_edges(bench, candidates: list[dict], appearance_threshold: float) -> list[dict]:
    return [
        edge for edge in candidates
        if edge["cosine_distance"] is not None
        and edge["endpoint_center_distance_pixels"] <= bench.GEOMETRY_RADIUS
        and edge["cosine_distance"] <= appearance_threshold
        and edge["controlled_cost"] < 1.0
    ]


def reciprocal_by_cost(edges: list[dict]) -> list[dict]:
    outgoing: dict[int, list[dict]] = defaultdict(list)
    incoming: dict[int, list[dict]] = defaultdict(list)
    for edge in edges:
        outgoing[edge["earlier"]].append(edge)
        incoming[edge["later"]].append(edge)
    key = lambda edge: (
        edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"]
    )
    best_out = {identity: min(values, key=key) for identity, values in outgoing.items()}
    best_in = {identity: min(values, key=key) for identity, values in incoming.items()}
    return [
        edge for edge in edges
        if best_out[edge["earlier"]] is edge and best_in[edge["later"]] is edge
    ]


def controlled_output(bench, method: str, predictions: dict, candidates: list[dict]):
    gated = gated_edges(bench, candidates, FIXED_APPEARANCE)
    key = lambda edge: (
        edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"]
    )
    if method == "controlled_cost_greedy":
        proposed = gated
    elif method == "controlled_cost_reciprocal":
        proposed = reciprocal_by_cost(gated)
    else:
        raise ValueError(method)
    output, accepted, rejected = bench.apply_union_edges(
        predictions, proposed, True, key
    )
    return output, accepted, rejected


def flatten_predictions(predictions: dict[int, list[dict]]) -> list[dict]:
    return [
        {"frame": int(frame), **row}
        for frame in sorted(predictions)
        for row in predictions[frame]
    ]


def unflatten_predictions(rows: Iterable[dict]) -> dict[int, list[dict]]:
    output: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        copied = dict(row)
        frame = int(copied.pop("frame"))
        output[frame].append(copied)
    return dict(output)


def native_deduplicate(predictions: dict[int, list[dict]]) -> tuple[dict, list[dict]]:
    """Replicate AFLink's first-row retention for unique (frame, identity)."""
    kept = []
    dropped = []
    observed: set[tuple[int, int]] = set()
    for row in flatten_predictions(predictions):
        key = (int(row["frame"]), int(row["id"]))
        if key in observed:
            dropped.append(row)
            continue
        observed.add(key)
        kept.append(row)
    return unflatten_predictions(kept), dropped


def save_roundtrip(predictions: dict[int, list[dict]]) -> tuple[dict, int]:
    """Model official two-decimal text serialization without deleting rows."""
    changed = 0
    rounded: dict[int, list[dict]] = defaultdict(list)
    for frame, rows in predictions.items():
        for row in rows:
            copied = dict(row)
            for key in ("x", "y", "w", "h", "conf"):
                if key in copied:
                    value = float(copied[key])
                    updated = round(value, 2)
                    changed += int(updated != value)
                    copied[key] = updated
            rounded[int(frame)].append(copied)
    return dict(rounded), changed


def output_signature(predictions: dict[int, list[dict]]) -> tuple:
    return tuple(
        sorted(
            (int(frame), int(row["id"]), round(float(row["x"]), 7),
             round(float(row["y"]), 7), round(float(row["w"]), 7),
             round(float(row["h"]), 7))
            for frame, rows in predictions.items() for row in rows
        )
    )


def count_rows(predictions: dict[int, list[dict]]) -> int:
    return sum(len(rows) for rows in predictions.values())


def method_output(
    bench,
    method: str,
    predictions: dict,
    candidates: list[dict],
    aflink_edges: list[dict],
):
    if method in {
        "no_refinement", "geometry_greedy", "geometry_reid_greedy_guard",
        "com3d_reciprocal_guard", "geometry_reid_hungarian",
    }:
        output, accepted, rejected, _ = bench.method_output(
            method, predictions, candidates, None, 0
        )
        return output, accepted, rejected
    if method in {"controlled_cost_greedy", "controlled_cost_reciprocal"}:
        return controlled_output(bench, method, predictions, candidates)
    if method == "aflink_cached_no_dedup":
        return (*bench.apply_aflink_mapping(predictions, aflink_edges)[:3],)
    if method == "aflink_cached_native_dedup":
        remapped, accepted, _ = bench.apply_aflink_mapping(predictions, aflink_edges)
        deduplicated, dropped = native_deduplicate(remapped)
        rejected = [{"rejection": "native_deduplicate_box_drop", **row} for row in dropped]
        return deduplicated, accepted, rejected
    if method == "aflink_cached_native_saved":
        remapped, accepted, _ = bench.apply_aflink_mapping(predictions, aflink_edges)
        deduplicated, dropped = native_deduplicate(remapped)
        saved, _ = save_roundtrip(deduplicated)
        rejected = [{"rejection": "native_deduplicate_box_drop", **row} for row in dropped]
        return saved, accepted, rejected
    if method == "aflink_cached_overlap_safe":
        return bench.apply_union_edges(
            predictions,
            aflink_edges,
            True,
            lambda edge: (
                edge["aflink_cost"], edge["gap"], edge["earlier"], edge["later"]
            ),
        )
    raise ValueError(method)


def has_cycle(edges: list[dict]) -> bool:
    outgoing = {int(edge["earlier"]): int(edge["later"]) for edge in edges}
    for start in outgoing:
        seen = set()
        current = start
        while current in outgoing:
            if current in seen:
                return True
            seen.add(current)
            current = outgoing[current]
    return False


def degree_maxima(edges: list[dict]) -> tuple[int, int]:
    outgoing = Counter(int(edge["earlier"]) for edge in edges)
    incoming = Counter(int(edge["later"]) for edge in edges)
    return max(outgoing.values(), default=0), max(incoming.values(), default=0)


def ranks(edges: list[dict], key: Callable[[dict], tuple]) -> tuple[dict, dict]:
    outgoing: dict[int, list[dict]] = defaultdict(list)
    incoming: dict[int, list[dict]] = defaultdict(list)
    for edge in edges:
        outgoing[edge["earlier"]].append(edge)
        incoming[edge["later"]].append(edge)
    out_rank = {}
    in_rank = {}
    for values in outgoing.values():
        for index, edge in enumerate(sorted(values, key=key), start=1):
            out_rank[(edge["earlier"], edge["later"])] = index
    for values in incoming.values():
        for index, edge in enumerate(sorted(values, key=key), start=1):
            in_rank[(edge["earlier"], edge["later"])] = index
    return out_rank, in_rank


def selected_pairs(edges: list[dict]) -> set[tuple[int, int]]:
    return {(int(edge["earlier"]), int(edge["later"])) for edge in edges}


def timed_call(call: Callable[[], Any], repeats: int) -> tuple[list[float], int]:
    call()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    values = []
    try:
        for _ in range(repeats):
            started = time.perf_counter_ns()
            call()
            values.append((time.perf_counter_ns() - started) / 1e6)
    finally:
        if gc_was_enabled:
            gc.enable()
    tracemalloc.start()
    call()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return values, int(peak)


def risk_selection(bench, method: str, predictions: dict, candidates: list[dict], threshold: float):
    gated = gated_edges(bench, candidates, threshold)
    if method == "geometry_reid_greedy_guard":
        proposed = gated
        key = lambda edge: (
            edge["cosine_distance"], edge["gap"], edge["earlier"], edge["later"]
        )
    elif method == "com3d_reciprocal_guard":
        proposed = bench.reciprocal(gated, use_appearance=True)
        key = lambda edge: (
            edge["cosine_distance"], edge["gap"], edge["earlier"], edge["later"]
        )
    elif method == "controlled_cost_reciprocal":
        proposed = reciprocal_by_cost(gated)
        key = lambda edge: (
            edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"]
        )
    elif method == "geometry_reid_hungarian":
        proposed = bench.hungarian_with_unmatched(gated)
        key = lambda edge: (
            edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"]
        )
    else:
        raise ValueError(method)
    return bench.apply_union_edges(predictions, proposed, True, key)


def summarize_sequence(bench, common, class_records: list[dict]) -> dict:
    metric_data = bench.common_module_concatenate(
        common, [record["metric_data"] for record in class_records]
    )
    metrics = bench.extended_metrics(common, metric_data)
    return {
        **metrics,
        "class_instances": len(class_records),
        "duplicate_frame_identity_count": sum(
            record["duplicate_frame_identity_count"] for record in class_records
        ),
        "input_rows": sum(record["input_rows"] for record in class_records),
        "output_rows": sum(record["output_rows"] for record in class_records),
        "box_preserving": all(record["box_preserving"] for record in class_records),
        "duplicate_free": all(record["duplicate_free"] for record in class_records),
        "valid_common_box_protocol": all(
            record["box_preserving"] and record["duplicate_free"]
            for record in class_records
        ),
        "accepted_correct": sum(record["accepted_correct"] for record in class_records),
        "accepted_false": sum(record["accepted_false"] for record in class_records),
        "accepted_unknown": sum(record["accepted_unknown"] for record in class_records),
        "eligible_source_tracklets": sum(
            record["eligible_source_tracklets"] for record in class_records
        ),
    }


def aggregate_sequences(sequence_rows: list[dict]) -> list[dict]:
    output = []
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in sequence_rows:
        groups[(row["protocol"], row["tracker"], row["method"])].append(row)
    for (protocol, tracker, method), rows in sorted(groups.items()):
        known = sum(row["accepted_correct"] + row["accepted_false"] for row in rows)
        eligible = sum(row["eligible_source_tracklets"] for row in rows)
        accepted = known + sum(row["accepted_unknown"] for row in rows)
        output.append({
            "protocol": protocol,
            "scope": "all_sequences",
            "tracker": tracker,
            "method": method,
            "sequence_count": len(rows),
            "aggregation": "equal_sequence_mean_metrics_total_counts",
            **{
                key: float(np.mean([row[key] for row in rows]))
                for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
            },
            **{
                key: int(sum(row[key] for row in rows))
                for key in ("IDSW", "FP", "FN", "TP", "Frag", "valid_gt_boxes", "predicted_boxes")
            },
            "input_rows": int(sum(row["input_rows"] for row in rows)),
            "output_rows": int(sum(row["output_rows"] for row in rows)),
            "valid_common_box_protocol": all(row["valid_common_box_protocol"] for row in rows),
            "invalid_sequences": sum(not row["valid_common_box_protocol"] for row in rows),
            "accepted_correct": sum(row["accepted_correct"] for row in rows),
            "accepted_false": sum(row["accepted_false"] for row in rows),
            "accepted_unknown": sum(row["accepted_unknown"] for row in rows),
            "eligible_source_tracklets": eligible,
            "known_link_error_rate": (
                sum(row["accepted_false"] for row in rows) / known if known else None
            ),
            "known_link_coverage": known / eligible if eligible else None,
            "all_accepted_coverage": accepted / eligible if eligible else None,
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-script", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--oracle-cache-dir", type=Path, required=True)
    parser.add_argument("--detector-cache-dir", type=Path, required=True)
    parser.add_argument("--oracle-accepted-links", type=Path, required=True)
    parser.add_argument("--detector-accepted-links", type=Path, required=True)
    parser.add_argument(
        "--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    bench = load_module("professor_review_benchmark", args.benchmark_script)
    mmot = load_module(
        "professor_review_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py"
    )
    try:
        from scipy import __version__ as scipy_version
    except ImportError:
        scipy_version = "unavailable"

    family_roots = {name: Path(path) for name, path in args.family_root}
    aflink_by_protocol = {
        "oracle_aabb": load_aflink_edges(args.oracle_accepted_links),
        "official_detector": load_aflink_edges(args.detector_accepted_links),
    }
    cache_by_protocol = {
        "oracle_aabb": args.oracle_cache_dir,
        "official_detector": args.detector_cache_dir,
    }

    sequence_rows = []
    runtime_rows = []
    decision_rows = []
    property_rows = []
    aflink_stage_rows = []
    aflink_failure_details = []
    risk_counters: dict[tuple, Counter] = defaultdict(Counter)
    risk_eligible: dict[tuple, int] = defaultdict(int)
    minimal_written = False
    started_all = time.perf_counter()

    for protocol, cache_root in cache_by_protocol.items():
        for family, family_root in family_roots.items():
            for sequence_dir in sorted(path for path in family_root.iterdir() if path.is_dir()):
                print(f"{protocol} {family}/{sequence_dir.name}", flush=True)
                frames, _, _, _ = mmot.load_sequence(sequence_dir)
                per_sequence: dict[tuple[str, str], list[dict]] = defaultdict(list)
                class_outputs: dict[tuple[str, str], list[tuple[str, dict]]] = defaultdict(list)
                for class_id, class_name in enumerate(bench.CLASS_NAMES):
                    gt = mmot.class_frames(frames, class_id)
                    for tracker in ("bytetrack", "ocsort", "deepocsort"):
                        relative = Path("tracker_outputs") / family / sequence_dir.name / class_name / f"{tracker}.jsonl.gz"
                        prediction_path = cache_root / relative
                        descriptor_path = (
                            cache_root / "descriptors" / family / sequence_dir.name /
                            class_name / f"{tracker}.npz"
                        )
                        if not prediction_path.is_file():
                            if protocol == "oracle_aabb" and not gt:
                                continue
                            raise FileNotFoundError(prediction_path)
                        if not descriptor_path.is_file():
                            raise FileNotFoundError(descriptor_path)
                        predictions = bench.load_predictions(prediction_path)
                        descriptors = bench.load_descriptors(descriptor_path)
                        labels = mmot.M3OT_GRAPH.tracklet_gt_labels(gt, predictions)
                        build_started = time.perf_counter_ns()
                        candidates, eligible_sources = bench.build_candidates(predictions, descriptors)
                        build_ms = (time.perf_counter_ns() - build_started) / 1e6
                        context = {
                            "protocol": protocol,
                            "family": family,
                            "sequence": sequence_dir.name,
                            "class_name": class_name,
                            "tracker": tracker,
                        }
                        af_edges = aflink_by_protocol[protocol].get(
                            (family, sequence_dir.name, class_name, tracker), []
                        )

                        gated = gated_edges(bench, candidates, FIXED_APPEARANCE)
                        historical_proposed = bench.reciprocal(gated, use_appearance=True)
                        controlled_proposed = reciprocal_by_cost(gated)
                        historical_output_guard, historical_accepted, historical_rejected = (
                            bench.apply_union_edges(
                                predictions,
                                historical_proposed,
                                True,
                                lambda edge: (
                                    edge["cosine_distance"], edge["gap"],
                                    edge["earlier"], edge["later"],
                                ),
                            )
                        )
                        historical_output_no_guard, _, _ = bench.apply_union_edges(
                            predictions,
                            historical_proposed,
                            False,
                            lambda edge: (
                                edge["cosine_distance"], edge["gap"],
                                edge["earlier"], edge["later"],
                            ),
                        )
                        prediction_frames, _ = bench.prediction_tracklets(predictions)
                        strict_violations = sum(
                            not (
                                max(prediction_frames[edge["earlier"]])
                                < min(prediction_frames[edge["later"]])
                            )
                            for edge in candidates
                        )
                        out_degree, in_degree = degree_maxima(historical_proposed)
                        property_rows.append({
                            **context,
                            "input_duplicate_frame_identity_count": bench.duplicate_frame_identity_count(predictions),
                            "temporal_candidate_count": len(candidates),
                            "strict_time_order_violations": strict_violations,
                            "reciprocal_proposal_count": len(historical_proposed),
                            "maximum_outdegree": out_degree,
                            "maximum_indegree": in_degree,
                            "proposal_cycle_present": has_cycle(historical_proposed),
                            "component_guard_rejections": len(historical_rejected),
                            "guard_and_no_guard_outputs_identical": (
                                output_signature(historical_output_guard)
                                == output_signature(historical_output_no_guard)
                            ),
                        })

                        geo_key = lambda edge: (
                            edge["endpoint_center_distance_pixels"],
                            edge["cosine_distance"], edge["gap"],
                            edge["earlier"], edge["later"],
                        )
                        cost_key = lambda edge: (
                            edge["controlled_cost"], edge["gap"],
                            edge["earlier"], edge["later"],
                        )
                        geo_out, geo_in = ranks(gated, geo_key)
                        cost_out, cost_in = ranks(gated, cost_key)
                        hungarian_pairs = selected_pairs(bench.hungarian_with_unmatched(gated))
                        hist_pairs = selected_pairs(historical_proposed)
                        controlled_pairs = selected_pairs(controlled_proposed)
                        historical_accepted_pairs = selected_pairs(historical_accepted)
                        controlled_out, controlled_accepted, _ = controlled_output(
                            bench, "controlled_cost_reciprocal", predictions, candidates
                        )
                        del controlled_out
                        controlled_accepted_pairs = selected_pairs(controlled_accepted)
                        greedy_out, greedy_accepted, _ = controlled_output(
                            bench, "controlled_cost_greedy", predictions, candidates
                        )
                        del greedy_out
                        greedy_accepted_pairs = selected_pairs(greedy_accepted)

                        for edge in candidates:
                            pair = (edge["earlier"], edge["later"])
                            left = labels.get(edge["earlier"])
                            right = labels.get(edge["later"])
                            correctness = "unknown"
                            if left is not None and right is not None:
                                correctness = (
                                    "correct" if left["majority_gt_identity"]
                                    == right["majority_gt_identity"] else "false"
                                )
                            selected_any = pair in (
                                hist_pairs | controlled_pairs | hungarian_pairs
                                | greedy_accepted_pairs
                            )
                            if correctness != "correct" and not selected_any:
                                continue
                            pass_geometry = (
                                edge["endpoint_center_distance_pixels"] <= bench.GEOMETRY_RADIUS
                            )
                            pass_appearance = (
                                edge["cosine_distance"] is not None
                                and edge["cosine_distance"] <= FIXED_APPEARANCE
                            )
                            decision_rows.append({
                                **context,
                                **edge,
                                "posthoc_gt_correctness": correctness,
                                "source_majority_gt_identity": (
                                    left.get("majority_gt_identity") if left else None
                                ),
                                "destination_majority_gt_identity": (
                                    right.get("majority_gt_identity") if right else None
                                ),
                                "source_gt_purity": left.get("purity") if left else None,
                                "destination_gt_purity": right.get("purity") if right else None,
                                "passes_geometry_gate": pass_geometry,
                                "passes_appearance_gate": pass_appearance,
                                "enters_fixed_candidate_graph": pass_geometry and pass_appearance,
                                "geometry_first_out_rank": geo_out.get(pair),
                                "geometry_first_in_rank": geo_in.get(pair),
                                "controlled_cost_out_rank": cost_out.get(pair),
                                "controlled_cost_in_rank": cost_in.get(pair),
                                "historical_reciprocal_proposed": pair in hist_pairs,
                                "historical_reciprocal_accepted": pair in historical_accepted_pairs,
                                "controlled_reciprocal_proposed": pair in controlled_pairs,
                                "controlled_reciprocal_accepted": pair in controlled_accepted_pairs,
                                "controlled_greedy_accepted": pair in greedy_accepted_pairs,
                                "partial_hungarian_selected": pair in hungarian_pairs,
                            })

                        runtime_methods = (
                            "geometry_greedy", "geometry_reid_greedy_guard",
                            "com3d_reciprocal_guard", "geometry_reid_hungarian",
                            "controlled_cost_greedy", "controlled_cost_reciprocal",
                            "aflink_cached_no_dedup", "aflink_cached_overlap_safe",
                        )
                        for method in runtime_methods:
                            call = lambda method=method: method_output(
                                bench, method, predictions, candidates, af_edges
                            )
                            values, peak = timed_call(call, args.repeats)
                            valid_hungarian = gated_edges(bench, candidates, FIXED_APPEARANCE)
                            sources = {edge["earlier"] for edge in valid_hungarian}
                            destinations = {edge["later"] for edge in valid_hungarian}
                            matrix_bytes = (
                                8 * len(sources) * (len(destinations) + len(sources))
                                if method == "geometry_reid_hungarian" else 0
                            )
                            runtime_rows.append({
                                **context,
                                "method": method,
                                "candidate_build_ms": build_ms,
                                "repeat_count": args.repeats,
                                "solver_ms_mean": statistics.fmean(values),
                                "solver_ms_median": statistics.median(values),
                                "solver_ms_min": min(values),
                                "solver_ms_max": max(values),
                                "tracemalloc_peak_bytes": peak,
                                "hungarian_dense_matrix_bytes": matrix_bytes,
                                "tracklet_count": len(prediction_frames),
                                "temporal_candidate_count": len(candidates),
                                "fixed_gated_edge_count": len(gated),
                                "aflink_selected_edge_count": len(af_edges),
                                "descriptor_extraction_included": False,
                                "aflink_model_scoring_included": False,
                            })

                        for threshold in APPEARANCE_GRID:
                            for method in RISK_METHODS:
                                _, accepted, _ = risk_selection(
                                    bench, method, predictions, candidates, threshold
                                )
                                _, counts = bench.edge_audit(accepted, labels)
                                key = (protocol, tracker, method, threshold)
                                risk_counters[key].update(counts)
                                risk_eligible[key] += len(eligible_sources)

                        for method in METHODS:
                            output, accepted, rejected = method_output(
                                bench, method, predictions, candidates, af_edges
                            )
                            audited, counts = bench.edge_audit(accepted, labels)
                            del audited
                            duplicates = bench.duplicate_frame_identity_count(output)
                            box_preserving = (
                                bench.geometry_multiset(predictions)
                                == bench.geometry_multiset(output)
                            )
                            record = {
                                **context,
                                "method": method,
                                "metric_data": mmot.COMMON.metric_data(gt, output),
                                "input_rows": count_rows(predictions),
                                "output_rows": count_rows(output),
                                "duplicate_frame_identity_count": duplicates,
                                "box_preserving": box_preserving,
                                "duplicate_free": duplicates == 0,
                                "accepted_correct": counts["correct"],
                                "accepted_false": counts["false"],
                                "accepted_unknown": counts["unknown"],
                                "eligible_source_tracklets": len(eligible_sources),
                            }
                            per_sequence[(tracker, method)].append(record)
                            class_outputs[(tracker, method)].append((class_name, output))

                        historical_af, _, _ = bench.apply_aflink_mapping(predictions, af_edges)
                        if bench.duplicate_frame_identity_count(historical_af):
                            native_af, dropped = native_deduplicate(historical_af)
                            saved_af, rounding_changes = save_roundtrip(native_af)
                            overlap_af, overlap_accepted, overlap_rejected = bench.apply_union_edges(
                                predictions,
                                af_edges,
                                True,
                                lambda edge: (
                                    edge["aflink_cost"], edge["gap"],
                                    edge["earlier"], edge["later"],
                                ),
                            )
                            stages = (
                                ("input", predictions, 0, 0),
                                ("post_id_remap", historical_af, 0, 0),
                                ("post_native_deduplicate", native_af, len(dropped), 0),
                                ("post_save_roundtrip", saved_af, len(dropped), rounding_changes),
                                ("overlap_safe_adapter", overlap_af, len(overlap_rejected), 0),
                            )
                            for stage, stage_output, removed_or_rejected, rounded_values in stages:
                                aflink_stage_rows.append({
                                    **context,
                                    "stage": stage,
                                    "selected_edges": len(af_edges),
                                    "rows": count_rows(stage_output),
                                    "row_delta_from_input": count_rows(stage_output) - count_rows(predictions),
                                    "duplicate_frame_identity_count": bench.duplicate_frame_identity_count(stage_output),
                                    "geometry_multiset_preserved": (
                                        bench.geometry_multiset(predictions)
                                        == bench.geometry_multiset(stage_output)
                                    ),
                                    "removed_or_rejected_count": removed_or_rejected,
                                    "rounded_scalar_values": rounded_values,
                                })
                            aflink_failure_details.append({
                                **context,
                                "selected_edges": len(af_edges),
                                "native_dropped_boxes": len(dropped),
                                "overlap_safe_rejected_edges": len(overlap_rejected),
                                "overlap_safe_accepted_edges": len(overlap_accepted),
                            })
                            if (
                                not minimal_written and protocol == "oracle_aabb"
                                and family == "legacy12" and sequence_dir.name == "data30-3"
                                and class_name == "car" and tracker == "deepocsort"
                            ):
                                minimal = args.output_dir / "minimal_failure_case"
                                relevant_frames = sorted({
                                    int(frame)
                                    for edge in af_edges
                                    for identity in (edge["earlier"], edge["later"])
                                    for frame in prediction_frames[identity]
                                    if frame in (
                                        max(prediction_frames[edge["earlier"]]),
                                        min(prediction_frames[edge["later"]]),
                                    )
                                })
                                def select_rows(values):
                                    return [
                                        {"stage": "", **row}
                                        for row in flatten_predictions(values)
                                        if row["frame"] in relevant_frames
                                    ]
                                write_csv(minimal / "input_rows.csv", select_rows(predictions))
                                write_csv(minimal / "post_id_remap_rows.csv", select_rows(historical_af))
                                write_csv(minimal / "post_native_deduplicate_rows.csv", select_rows(native_af))
                                write_csv(minimal / "post_save_roundtrip_rows.csv", select_rows(saved_af))
                                write_csv(minimal / "selected_edges.csv", [{**context, **edge} for edge in af_edges])
                                write_json(minimal / "summary.json", {
                                    **context,
                                    "relevant_frames": relevant_frames,
                                    "input_rows": count_rows(predictions),
                                    "post_remap_duplicates": bench.duplicate_frame_identity_count(historical_af),
                                    "native_dropped_boxes": len(dropped),
                                    "native_drop_rows": dropped,
                                    "overlap_safe_rejected_edges": overlap_rejected,
                                })
                                minimal_written = True

                for (tracker, method), records in sorted(per_sequence.items()):
                    summary = summarize_sequence(bench, mmot.COMMON, records)
                    sequence_rows.append({
                        "protocol": protocol,
                        "family": family,
                        "sequence": sequence_dir.name,
                        "tracker": tracker,
                        "method": method,
                        **summary,
                    })

                # Class-local IDs are valid because evaluation namespaces classes.
                # Record whether an unscoped merge would collide, without treating it
                # as a class-scoped invariant failure.
                for (tracker, method), values in sorted(class_outputs.items()):
                    scoped = Counter()
                    unscoped = Counter()
                    for class_name, output in values:
                        for frame, rows in output.items():
                            for row in rows:
                                scoped[(frame, class_name, int(row["id"]))] += 1
                                unscoped[(frame, int(row["id"]))] += 1
                    if method == "aflink_cached_native_dedup":
                        aflink_stage_rows.append({
                            "protocol": protocol,
                            "family": family,
                            "sequence": sequence_dir.name,
                            "class_name": "ALL_CLASS_SCOPED",
                            "tracker": tracker,
                            "stage": "post_class_merge_audit",
                            "selected_edges": "",
                            "rows": sum(scoped.values()),
                            "row_delta_from_input": "",
                            "duplicate_frame_identity_count": sum(
                                count - 1 for count in scoped.values() if count > 1
                            ),
                            "unscoped_cross_class_id_reuse_count": sum(
                                count - 1 for count in unscoped.values() if count > 1
                            ),
                            "geometry_multiset_preserved": "",
                            "removed_or_rejected_count": "",
                            "rounded_scalar_values": "",
                        })

    aggregate_rows = aggregate_sequences(sequence_rows)
    risk_rows = []
    for key, counts in sorted(risk_counters.items()):
        protocol, tracker, method, threshold = key
        eligible = risk_eligible[key]
        known = counts["correct"] + counts["false"]
        accepted = known + counts["unknown"]
        risk_rows.append({
            "protocol": protocol,
            "scope": "all_sequences",
            "tracker": tracker,
            "method": method,
            "appearance_threshold": threshold,
            "eligible_source_tracklets": eligible,
            "accepted_correct": counts["correct"],
            "accepted_false": counts["false"],
            "accepted_unknown": counts["unknown"],
            "accepted_known": known,
            "accepted_total": accepted,
            "known_link_error_rate": counts["false"] / known if known else None,
            "known_link_precision": counts["correct"] / known if known else None,
            "known_link_coverage": known / eligible if eligible else None,
            "all_accepted_coverage": accepted / eligible if eligible else None,
            "ground_truth_use": "post-hoc edge labels only; grid is descriptive and not selected",
        })

    write_csv(args.output_dir / "solver_metrics_per_sequence.csv", sequence_rows)
    write_csv(args.output_dir / "solver_metrics_aggregate.csv", aggregate_rows)
    write_csv(args.output_dir / "solver_cost_control.csv", aggregate_rows)
    write_csv(args.output_dir / "edge_decision_trace.csv", decision_rows)
    write_csv(args.output_dir / "risk_coverage.csv", risk_rows)
    write_csv(args.output_dir / "refiner_runtime.csv", runtime_rows)
    write_csv(args.output_dir / "reciprocal_property_instances.csv", property_rows)
    write_csv(args.output_dir / "aflink_stage_audit.csv", aflink_stage_rows)
    write_csv(args.output_dir / "aflink_failure_summary.csv", aflink_failure_details)

    property_summary = {
        "status": "PASS" if all(
            row["input_duplicate_frame_identity_count"] == 0
            and row["strict_time_order_violations"] == 0
            and row["maximum_outdegree"] <= 1
            and row["maximum_indegree"] <= 1
            and not row["proposal_cycle_present"]
            and row["component_guard_rejections"] == 0
            and row["guard_and_no_guard_outputs_identical"]
            for row in property_rows
        ) else "FAIL",
        "instances": len(property_rows),
        "input_duplicate_instances": sum(
            row["input_duplicate_frame_identity_count"] > 0 for row in property_rows
        ),
        "strict_time_order_violations": sum(
            row["strict_time_order_violations"] for row in property_rows
        ),
        "maximum_observed_outdegree": max(
            (row["maximum_outdegree"] for row in property_rows), default=0
        ),
        "maximum_observed_indegree": max(
            (row["maximum_indegree"] for row in property_rows), default=0
        ),
        "cycle_instances": sum(row["proposal_cycle_present"] for row in property_rows),
        "component_guard_rejections": sum(
            row["component_guard_rejections"] for row in property_rows
        ),
        "guard_output_difference_instances": sum(
            not row["guard_and_no_guard_outputs_identical"] for row in property_rows
        ),
        "interpretation": (
            "For the implemented one-shot reciprocal graph, strict temporal edges "
            "and degree at most one form disjoint directed paths. The overlap guard "
            "is a defensive validation assertion, not an independently active MMOT module."
        ),
    }
    write_json(args.output_dir / "property_test_results.json", property_summary)

    manifest = {
        "status": "COMPLETE" if property_summary["status"] == "PASS" else "COMPLETE_WITH_PROPERTY_FAILURE",
        "claim_scope": (
            "Cache-only controlled MMOT assignment, AFLink stage, risk-coverage, "
            "runtime, and reciprocal-invariant audit. No detector, tracker, or "
            "descriptor network was executed."
        ),
        "methods": list(METHODS),
        "risk_methods": list(RISK_METHODS),
        "appearance_grid": list(APPEARANCE_GRID),
        "fixed_thresholds": {
            "maximum_gap_frames": bench.MAX_GAP,
            "geometry_radius_pixels": bench.GEOMETRY_RADIUS,
            "appearance_cosine_distance": bench.APPEARANCE_DISTANCE,
            "hungarian_unmatched_cost": 1.0,
        },
        "ground_truth_use": "metrics and post-hoc edge audit only; no threshold selection",
        "coverage_denominator": (
            "source tracklets with at least one strictly later non-overlapping "
            "tracklet within 30 released frames, before geometry/appearance gates"
        ),
        "runtime_protocol": {
            "candidate_graph_reused": True,
            "warmup_calls_per_method_instance": 1,
            "timed_repeats": args.repeats,
            "descriptor_extraction_included": False,
            "aflink_model_scoring_included": False,
            "timer": "time.perf_counter_ns",
            "peak_memory": "tracemalloc peak for one additional solver call",
        },
        "inputs": {
            "benchmark_script": {"path": str(args.benchmark_script), "sha256": sha256(args.benchmark_script)},
            "mmot_source": {
                "path": str(args.workspace / "scripts/run_mmot_locked_temporal.py"),
                "sha256": sha256(args.workspace / "scripts/run_mmot_locked_temporal.py"),
            },
            "oracle_accepted_links": {"path": str(args.oracle_accepted_links), "sha256": sha256(args.oracle_accepted_links)},
            "detector_accepted_links": {"path": str(args.detector_accepted_links), "sha256": sha256(args.detector_accepted_links)},
            "oracle_cache": str(args.oracle_cache_dir),
            "detector_cache": str(args.detector_cache_dir),
            "families": {name: str(path) for name, path in family_roots.items()},
        },
        "outputs": {},
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "numpy": np.__version__,
            "scipy": scipy_version,
            "cuda_used": False,
        },
        "aflink": {
            "assignment_source": "cached official-model/checkpoint scores and selected edges",
            "native_stage_replication": "ID remap followed by unique (frame, ID) first-row retention",
            "overlap_safe_adapter": "reject selected component merges with any frame-support overlap; no GT used",
            "failure_contexts": len(aflink_failure_details),
        },
        "property_summary": property_summary,
        "runtime_seconds": time.perf_counter() - started_all,
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
    }
    for path in sorted(args.output_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest["outputs"][path.name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"],
        "sequence_rows": len(sequence_rows),
        "aggregate_rows": len(aggregate_rows),
        "decision_rows": len(decision_rows),
        "aflink_failure_contexts": len(aflink_failure_details),
        "property_status": property_summary["status"],
        "runtime_seconds": manifest["runtime_seconds"],
    }, indent=2))
    return 0 if property_summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
