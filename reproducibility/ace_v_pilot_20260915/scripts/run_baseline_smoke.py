#!/usr/bin/env python3
"""Recompute a cached MMOT smoke sequence and compare every stored metric."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path


METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_greedy_guard",
    "com3d_reciprocal_guard",
    "geometry_reid_hungarian",
    "controlled_cost_greedy",
    "controlled_cost_reciprocal",
)
METRICS = (
    "HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW", "FP", "FN", "TP", "Frag",
    "accepted_correct", "accepted_false", "accepted_unknown", "eligible_source_tracklets",
    "input_rows", "output_rows", "valid_gt_boxes", "predicted_boxes",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prediction_count(predictions: dict[int, list[dict]]) -> int:
    return sum(len(rows) for rows in predictions.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-script", type=Path, required=True)
    parser.add_argument("--audit-script", type=Path, required=True)
    parser.add_argument("--ace-core", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--sequence-root", type=Path, required=True)
    parser.add_argument("--sequence", default="data28-1")
    parser.add_argument("--oracle-cache", type=Path, required=True)
    parser.add_argument("--detector-cache", type=Path, required=True)
    parser.add_argument("--stored-metrics", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    bench = load_module("ace_smoke_bench", args.benchmark_script)
    audit = load_module("ace_smoke_audit", args.audit_script)
    ace = load_module("ace_smoke_core", args.ace_core)
    mmot = load_module(
        "ace_smoke_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py"
    )

    stored_rows = read_csv(args.stored_metrics)
    stored = {
        (row["protocol"], row["sequence"], row["tracker"], row["method"]): row
        for row in stored_rows
    }
    sequence_dir = args.sequence_root / args.sequence
    frames, _, _, _ = mmot.load_sequence(sequence_dir)
    cache_by_protocol = {
        "oracle_aabb": args.oracle_cache,
        "official_detector": args.detector_cache,
    }
    per_sequence: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    invariant_rows = []
    symmetric_equivalence = []
    synthetic_tests = {}

    for protocol, cache_root in cache_by_protocol.items():
        for class_id, class_name in enumerate(bench.CLASS_NAMES):
            gt = mmot.class_frames(frames, class_id)
            if gt and not synthetic_tests:
                perfect = {
                    frame: [dict(row) for row in rows]
                    for frame, rows in gt.items()
                }
                permuted = {
                    frame: [{**row, "id": int(row["id"]) + 100000} for row in rows]
                    for frame, rows in gt.items()
                }
                perfect_metrics = bench.extended_metrics(
                    mmot.COMMON, mmot.COMMON.metric_data(gt, perfect)
                )
                permutation_metrics = bench.extended_metrics(
                    mmot.COMMON, mmot.COMMON.metric_data(gt, permuted)
                )
                synthetic_tests = {
                    "class": class_name,
                    "perfect_prediction": perfect_metrics,
                    "global_id_permutation": permutation_metrics,
                    "passed": all(
                        metrics["HOTA"] == 100.0
                        and metrics["AssA"] == 100.0
                        and metrics["IDF1"] == 100.0
                        and metrics["IDSW"] == 0
                        for metrics in (perfect_metrics, permutation_metrics)
                    ),
                }
            for tracker in ("bytetrack", "ocsort", "deepocsort"):
                relative = Path("tracker_outputs/legacy12") / args.sequence / class_name / f"{tracker}.jsonl.gz"
                prediction_path = cache_root / relative
                descriptor_path = cache_root / "descriptors/legacy12" / args.sequence / class_name / f"{tracker}.npz"
                if not prediction_path.is_file():
                    if protocol == "oracle_aabb" and not gt:
                        continue
                    raise FileNotFoundError(prediction_path)
                predictions = bench.load_predictions(prediction_path)
                descriptors = bench.load_descriptors(descriptor_path)
                labels = mmot.M3OT_GRAPH.tracklet_gt_labels(gt, predictions)
                candidates, eligible_sources = bench.build_candidates(predictions, descriptors)
                gated = audit.gated_edges(bench, candidates, audit.FIXED_APPEARANCE)
                old_h = bench.hungarian_with_unmatched(gated)
                new_h = ace.partial_hungarian(gated)
                old_pairs = {ace.pair(edge) for edge in old_h}
                new_pairs = {ace.pair(edge) for edge in new_h}
                symmetric_equivalence.append({
                    "protocol": protocol,
                    "class_name": class_name,
                    "tracker": tracker,
                    "old_edge_count": len(old_pairs),
                    "symmetric_edge_count": len(new_pairs),
                    "selected_pairs_identical": old_pairs == new_pairs,
                })
                for method in METHODS:
                    output, accepted, _ = audit.method_output(
                        bench, method, predictions, candidates, []
                    )
                    _, counts = bench.edge_audit(accepted, labels)
                    duplicate_count = bench.duplicate_frame_identity_count(output)
                    box_preserving = (
                        bench.geometry_multiset(predictions)
                        == bench.geometry_multiset(output)
                    )
                    strict_time = all(
                        max(bench.prediction_tracklets(predictions)[0][int(edge["earlier"])])
                        < min(bench.prediction_tracklets(predictions)[0][int(edge["later"])])
                        for edge in accepted
                    )
                    no_refinement_exact = (
                        audit.output_signature(predictions) == audit.output_signature(output)
                        if method == "no_refinement" else None
                    )
                    invariant_rows.append({
                        "protocol": protocol,
                        "sequence": args.sequence,
                        "class_name": class_name,
                        "tracker": tracker,
                        "method": method,
                        "input_rows": prediction_count(predictions),
                        "output_rows": prediction_count(output),
                        "box_preserving": box_preserving,
                        "duplicate_frame_identity_count": duplicate_count,
                        "strict_forward_accepted_edges": strict_time,
                        "no_refinement_exact": no_refinement_exact,
                    })
                    per_sequence[(protocol, tracker, method)].append({
                        "metric_data": mmot.COMMON.metric_data(gt, output),
                        "duplicate_frame_identity_count": duplicate_count,
                        "input_rows": prediction_count(predictions),
                        "output_rows": prediction_count(output),
                        "box_preserving": box_preserving,
                        "duplicate_free": duplicate_count == 0,
                        "accepted_correct": counts["correct"],
                        "accepted_false": counts["false"],
                        "accepted_unknown": counts["unknown"],
                        "eligible_source_tracklets": len(eligible_sources),
                    })

    comparison_rows = []
    for (protocol, tracker, method), records in sorted(per_sequence.items()):
        rerun = audit.summarize_sequence(bench, mmot.COMMON, records)
        reference = stored[(protocol, args.sequence, tracker, method)]
        for metric in METRICS:
            actual = float(rerun[metric])
            expected = float(reference[metric])
            difference = actual - expected
            comparison_rows.append({
                "protocol": protocol,
                "family": "legacy12",
                "sequence": args.sequence,
                "tracker": tracker,
                "method": method,
                "metric": metric,
                "stored_value": expected,
                "rerun_value": actual,
                "absolute_difference": abs(difference),
                "passed": abs(difference) <= 1e-9,
            })

    all_passed = (
        all(row["passed"] for row in comparison_rows)
        and all(row["box_preserving"] for row in invariant_rows)
        and all(row["duplicate_frame_identity_count"] == 0 for row in invariant_rows)
        and all(row["strict_forward_accepted_edges"] for row in invariant_rows)
        and all(row["selected_pairs_identical"] for row in symmetric_equivalence)
        and synthetic_tests.get("passed", False)
    )
    write_csv(args.output_dir / "baseline_reproduction.csv", comparison_rows)
    write_csv(args.output_dir / "smoke_invariants.csv", invariant_rows)
    write_csv(args.output_dir / "partial_hungarian_equivalence.csv", symmetric_equivalence)
    summary = {
        "status": "PASS" if all_passed else "FAIL",
        "sequence": args.sequence,
        "metric_comparisons": len(comparison_rows),
        "metric_mismatches": sum(not row["passed"] for row in comparison_rows),
        "invariant_rows": len(invariant_rows),
        "symmetric_partial_hungarian_instances": len(symmetric_equivalence),
        "symmetric_partial_hungarian_mismatches": sum(
            not row["selected_pairs_identical"] for row in symmetric_equivalence
        ),
        "synthetic_evaluator_tests": synthetic_tests,
        "class_namespace_policy": (
            "Tracker IDs are class-local; metric-data concatenation offsets each class "
            "namespace before sequence-level evaluation."
        ),
    }
    (args.output_dir / "smoke_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
