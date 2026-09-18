#!/usr/bin/env python3
"""Audit development failures without exposing GT identity to the linker."""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


FINAL_SEARCH_NAME = "s2_t_cond_w3_scale_c50_r100"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_predictions(path: Path) -> dict[int, list[dict]]:
    output = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            output[int(row.pop("frame"))].append(row)
    return dict(output)


def load_descriptors(path: Path) -> dict[int, np.ndarray]:
    with np.load(path) as payload:
        return {int(key): payload[key] for key in payload.files}


def spans(predictions: dict[int, list[dict]]) -> dict[int, tuple[int, int]]:
    values: dict[int, list[int]] = defaultdict(list)
    for frame, rows in predictions.items():
        for row in rows:
            values[int(row["id"])].append(int(frame))
    return {identity: (min(group), max(group)) for identity, group in values.items()}


def nearest_future_pairs(
    predictions: dict[int, list[dict]], labels: dict[int, dict]
) -> list[tuple[int, int, int]]:
    support = spans(predictions)
    by_actor: dict[int, list[int]] = defaultdict(list)
    for identity, label in labels.items():
        if identity in support:
            by_actor[int(label["majority_gt_identity"])].append(int(identity))
    pairs = []
    for actor, identities in by_actor.items():
        for source in identities:
            future = [
                destination for destination in identities
                if support[destination][0] > support[source][1]
            ]
            if future:
                destination = min(future, key=lambda value: (support[value][0], value))
                pairs.append((source, destination, actor))
    return pairs


def audit_opportunities(
    dataset: str,
    context: dict,
    predictions: dict[int, list[dict]],
    labels: dict[int, dict],
    candidates: list[dict],
    core,
) -> list[dict]:
    all_edges = {(int(edge["earlier"]), int(edge["later"])): edge for edge in candidates}
    fixed_edges = {core.edge_id(edge) for edge in core.fixed_gated(candidates)}
    track_spans = spans(predictions)
    rows = []
    for source, destination, actor in nearest_future_pairs(predictions, labels):
        identity = (source, destination)
        if identity not in all_edges:
            status = "absent_from_candidate_builder"
        elif identity not in fixed_edges:
            status = "removed_by_fixed_gates"
        else:
            status = "available_in_fixed_graph"
        rows.append({
            "dataset": dataset,
            **context,
            "source_tracklet": source,
            "destination_tracklet": destination,
            "posthoc_actor_id": actor,
            "source_end": track_spans[source][1],
            "destination_start": track_spans[destination][0],
            "gap_frames": track_spans[destination][0] - track_spans[source][1],
            "status": status,
        })
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def decision_failures(path: Path, dataset: str) -> list[dict]:
    rows = [row for row in read_csv(path) if row["method"] == FINAL_SEARCH_NAME]
    context_fields = (
        ("sequence", "class_name", "tracker") if dataset == "MMOT-dev6"
        else ("sequence", "tracker")
    )
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(field, "") for field in context_fields)].append(row)
    output = []
    for context, group in grouped.items():
        accepted_false = [
            row for row in group
            if row["accepted_after_component_check"] == "True"
            and row["posthoc_gt_correctness"] == "false"
        ]
        for row in group:
            relation = row["posthoc_gt_correctness"]
            accepted = row["accepted_after_component_check"] == "True"
            reason = row.get("decision_reason", "")
            if relation == "correct" and accepted:
                category = "correct_candidate_accepted"
            elif relation == "correct" and reason == "conditional_reliable_motion_inconsistent":
                category = "guard_removed_correct_candidate"
            elif relation == "correct":
                source, destination = int(row["earlier"]), int(row["later"])
                collision = any(
                    int(edge["earlier"]) == source or int(edge["later"]) == destination
                    for edge in accepted_false
                )
                category = (
                    "correct_candidate_lost_to_competing_false_edge"
                    if collision else "correct_candidate_lost_to_component_or_order"
                )
            elif relation == "false" and accepted:
                category = "false_candidate_passed_and_accepted"
            elif relation == "false" and reason == "conditional_reliable_motion_inconsistent":
                category = "guard_removed_false_candidate"
            else:
                continue
            output.append({
                "dataset": dataset,
                **{field: value for field, value in zip(context_fields, context)},
                "category": category,
                "earlier": row["earlier"],
                "later": row["later"],
                "gap": row["gap"],
                "cosine_distance": row["cosine_distance"],
                "endpoint_distance_pixels": row["endpoint_center_distance_pixels"],
                "motion_confidence": row.get("motion_confidence", ""),
                "motion_normalized_residual": row.get("motion_normalized_residual", ""),
            })
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--baseline-script", type=Path, required=True)
    parser.add_argument("--diagnostic-script", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--mmot-root", type=Path, required=True)
    parser.add_argument("--mmot-cache", type=Path, required=True)
    parser.add_argument("--mmot-decisions", type=Path, required=True)
    parser.add_argument("--m3ot-manifest", type=Path, required=True)
    parser.add_argument("--m3ot-cache", type=Path, required=True)
    parser.add_argument("--m3ot-decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    baseline = load_module("regr_failure_baseline", args.baseline_script)
    mmot = load_module("regr_failure_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py")
    diagnostic = load_module("regr_failure_m3ot_diagnostic", args.diagnostic_script)
    m3ot = load_module("regr_failure_m3ot", args.workspace / "scripts/run_m3ot_ambiguity_aware.py")
    core = load_module("regr_failure_core", args.core)
    opportunities = []

    class_names = ("car", "bike", "pedestrian", "van", "truck", "bus", "tricycle", "awning-bike")
    for sequence_dir in sorted(path for path in args.mmot_root.iterdir() if path.is_dir()):
        frames, _, _, _ = mmot.load_sequence(sequence_dir)
        for class_id, class_name in enumerate(class_names):
            gt = mmot.class_frames(frames, class_id)
            if not gt:
                continue
            for tracker in ("bytetrack", "ocsort"):
                relative = Path("train_dev6") / sequence_dir.name / class_name / tracker
                prediction_path = args.mmot_cache / "tracker_outputs" / relative.with_suffix(".jsonl.gz")
                descriptor_path = args.mmot_cache / "descriptors" / relative.with_suffix(".npz")
                predictions = baseline.load_predictions(prediction_path)
                descriptors = baseline.load_descriptors(descriptor_path)
                labels = mmot.M3OT_GRAPH.tracklet_gt_labels(gt, predictions)
                candidates, _ = baseline.build_candidates(predictions, descriptors)
                opportunities.extend(audit_opportunities(
                    "MMOT-dev6",
                    {"sequence": sequence_dir.name, "class_name": class_name, "tracker": tracker},
                    predictions, labels, candidates, core,
                ))

    manifest = json.loads(args.m3ot_manifest.read_text(encoding="utf-8"))
    root = Path(manifest["data_root"])
    for spec in manifest["sequences"]:
        sequence = spec["sequence_relative_path"]
        gt = m3ot.COMMON.parse_gt(root / spec["gt_relative_path"])
        cache_sequence = sequence.replace("/", "__")
        for tracker in ("bytetrack", "ocsort"):
            prediction_path = args.m3ot_cache / "tracker_outputs" / "development" / cache_sequence / f"{tracker}.jsonl.gz"
            descriptor_path = args.m3ot_cache / "descriptors" / "development" / cache_sequence / f"{tracker}.npz"
            predictions = load_predictions(prediction_path)
            descriptors = load_descriptors(descriptor_path)
            labels = m3ot.tracklet_gt_labels(gt, predictions)
            candidates = diagnostic.complete_temporal_edges(predictions, descriptors)
            opportunities.extend(audit_opportunities(
                "M3OT-dev08", {"sequence": sequence, "class_name": "vehicle", "tracker": tracker},
                predictions, labels, candidates, core,
            ))

    failures = decision_failures(args.mmot_decisions, "MMOT-dev6")
    failures.extend(decision_failures(args.m3ot_decisions, "M3OT-dev08"))
    write_csv(args.output_dir / "continuation_opportunities.csv", opportunities)
    write_csv(args.output_dir / "decision_failures.csv", failures)
    summary = []
    for dataset in ("MMOT-dev6", "M3OT-dev08"):
        opportunity_counts = Counter(row["status"] for row in opportunities if row["dataset"] == dataset)
        failure_counts = Counter(row["category"] for row in failures if row["dataset"] == dataset)
        for category, count in sorted(opportunity_counts.items()):
            summary.append({"dataset": dataset, "audit_stage": "candidate_graph", "category": category, "count": count})
        for category, count in sorted(failure_counts.items()):
            summary.append({"dataset": dataset, "audit_stage": "decision", "category": category, "count": count})
    write_csv(args.output_dir / "failure_summary.csv", summary)
    print(json.dumps({"status": "COMPLETE", "opportunities": len(opportunities), "decisions": len(failures)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
