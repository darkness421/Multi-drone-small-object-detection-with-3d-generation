#!/usr/bin/env python3
"""Apply the M3OT-selected ACE-V configuration to exposed MMOT caches."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment


METHODS = (
    "no_refinement", "ace_v1", "cost_r", "cost_g_legacy", "cost_h", "path_g",
    "cost_h_margin_reassign", "cost_h_motion_reassign", "cost_h_full_postfilter",
    "cost_h_full_reassign", "cost_h_soft_information", "path_g_full_reassign",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    handle_context = (
        gzip.open(path, "wt", encoding="utf-8", newline="")
        if path.suffix == ".gz"
        else path.open("w", encoding="utf-8", newline="")
    )
    with handle_context as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit_labels(common, gt: dict, predictions: dict) -> dict[int, dict]:
    matched: dict[int, Counter] = defaultdict(Counter)
    observations = Counter()
    for frame, prediction_rows in predictions.items():
        for row in prediction_rows:
            observations[int(row["id"])] += 1
        gt_rows = gt.get(frame, [])
        if not gt_rows or not prediction_rows:
            continue
        gt_boxes = np.asarray([
            [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"]]
            for row in gt_rows
        ], dtype=float)
        prediction_boxes = np.asarray([
            [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"]]
            for row in prediction_rows
        ], dtype=float)
        similarity = common.iou_matrix(gt_boxes, prediction_boxes)
        gt_indices, prediction_indices = linear_sum_assignment(-similarity)
        for gt_index, prediction_index in zip(gt_indices, prediction_indices):
            if similarity[gt_index, prediction_index] >= 0.9:
                matched[int(prediction_rows[prediction_index]["id"])][int(gt_rows[gt_index]["id"])] += 1
    output = {}
    for identity, counts in matched.items():
        maximum = max(counts.values())
        tied = sorted(label for label, count in counts.items() if count == maximum)
        total = sum(counts.values())
        output[identity] = {
            "majority_gt_identity": tied[0],
            "majority_count": maximum,
            "matched_observations": total,
            "tracklet_observations": observations[identity],
            "purity": maximum / total,
            "distinct_gt_identities": len(counts),
            "majority_tie_count": len(tied),
            "majority_tied": len(tied) > 1,
        }
    return output


def relation(edge: dict, labels: dict[int, dict], exclude_ties: bool = False) -> str:
    left = labels.get(int(edge["earlier"]))
    right = labels.get(int(edge["later"]))
    if left is None or right is None:
        return "unknown"
    if exclude_ties and (left["majority_tied"] or right["majority_tied"]):
        return "ambiguous_tie"
    return "correct" if left["majority_gt_identity"] == right["majority_gt_identity"] else "false"


def count_rows(predictions: dict) -> int:
    return sum(len(rows) for rows in predictions.values())


def selections(bench, audit, ace, features, tau_a, tau_m):
    geometry_key = lambda edge: (
        edge["endpoint_center_distance_pixels"], edge["cosine_distance"], edge["gap"],
        edge["earlier"], edge["later"],
    )
    baseline_h = ace.partial_hungarian(features)
    baseline_path = ace.path_constrained_greedy(features)
    return {
        "ace_v1": bench.reciprocal(features, use_appearance=True),
        "cost_r": audit.reciprocal_by_cost(features),
        "cost_g_legacy": features,
        "cost_h": baseline_h,
        "path_g": baseline_path,
        "cost_h_margin_reassign": ace.partial_hungarian(
            ace.filter_edges(features, "V_margin", tau_a, tau_m)
        ),
        "cost_h_motion_reassign": ace.partial_hungarian(
            ace.filter_edges(features, "V_motion", tau_a, tau_m)
        ),
        "cost_h_full_postfilter": ace.filter_edges(
            baseline_h, "V_full", tau_a, tau_m
        ),
        "cost_h_full_reassign": ace.partial_hungarian(
            ace.filter_edges(features, "V_full", tau_a, tau_m)
        ),
        "cost_h_soft_information": ace.partial_hungarian(
            features, cost=ace.soft_information_cost
        ),
        "path_g_full_reassign": ace.path_constrained_greedy(
            ace.filter_edges(features, "V_full", tau_a, tau_m)
        ),
    }


def aggregate_sequence_rows(rows: list[dict]) -> list[dict]:
    output = []
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["protocol"], row["tracker"], row["method"])].append(row)
    for (protocol, tracker, method), values in sorted(groups.items()):
        known = sum(row["accepted_correct"] + row["accepted_false"] for row in values)
        accepted = known + sum(row["accepted_unknown"] for row in values)
        eligible = sum(row["eligible_source_tracklets"] for row in values)
        output.append({
            "protocol": protocol, "scope": "all_50_sequences", "tracker": tracker,
            "method": method, "sequence_count": len(values),
            "aggregation": "equal_sequence_mean_metrics_total_counts",
            **{
                key: float(np.mean([row[key] for row in values]))
                for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
            },
            **{
                key: int(sum(row[key] for row in values))
                for key in ("IDSW", "FP", "FN", "TP", "Frag", "valid_gt_boxes", "predicted_boxes")
            },
            "accepted_correct": sum(row["accepted_correct"] for row in values),
            "accepted_false": sum(row["accepted_false"] for row in values),
            "accepted_unknown": sum(row["accepted_unknown"] for row in values),
            "tie_excluded_correct": sum(row["tie_excluded_correct"] for row in values),
            "tie_excluded_false": sum(row["tie_excluded_false"] for row in values),
            "tie_ambiguous": sum(row["tie_ambiguous"] for row in values),
            "eligible_source_tracklets": eligible,
            "auditable_fraction": known / accepted if accepted else "N/A",
            "conditional_error": sum(row["accepted_false"] for row in values) / known if known else "N/A",
            "accepted_coverage": accepted / eligible if eligible else "N/A",
            "all_box_multisets_preserved": all(row["box_preserving"] for row in values),
            "duplicate_frame_identity_count": sum(row["duplicate_frame_identity_count"] for row in values),
        })
    return output


def percentile_interval(values: np.ndarray, seed: int, samples: int = 10000):
    rng = np.random.default_rng(seed)
    means = np.empty(samples, dtype=float)
    for index in range(samples):
        means[index] = float(np.mean(values[rng.integers(0, len(values), len(values))]))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired_rows(sequence_rows: list[dict]) -> list[dict]:
    contrasts = (
        ("cost_h_full_reassign", "cost_h", "primary_H_plus_V_minus_H"),
        ("path_g_full_reassign", "path_g", "replication_G_plus_V_minus_G"),
        ("cost_h_motion_reassign", "cost_h", "motion_only_minus_H"),
        ("cost_h_soft_information", "cost_h", "soft_information_minus_H"),
    )
    lookup = {
        (row["protocol"], row["sequence"], row["tracker"], row["method"]): row
        for row in sequence_rows
    }
    protocols = sorted({row["protocol"] for row in sequence_rows})
    trackers = sorted({row["tracker"] for row in sequence_rows})
    sequences = sorted({row["sequence"] for row in sequence_rows})
    output = []
    for protocol in protocols:
        for treatment, baseline, label in contrasts:
            for tracker in [*trackers, "all_trackers_sequence_mean"]:
                deltas = []
                idsw_deltas = []
                available_sequences = []
                for sequence in sequences:
                    current_trackers = trackers if tracker == "all_trackers_sequence_mean" else [tracker]
                    pairs = [
                        (
                            lookup.get((protocol, sequence, item, treatment)),
                            lookup.get((protocol, sequence, item, baseline)),
                        )
                        for item in current_trackers
                    ]
                    pairs = [(left, right) for left, right in pairs if left is not None and right is not None]
                    if not pairs:
                        continue
                    deltas.append(float(np.mean([left["IDF1"] - right["IDF1"] for left, right in pairs])))
                    idsw_deltas.append(int(sum(left["IDSW"] - right["IDSW"] for left, right in pairs)))
                    available_sequences.append(sequence)
                values = np.asarray(deltas, dtype=float)
                low, high = percentile_interval(values, 20260915) if len(values) else (float("nan"), float("nan"))
                output.append({
                    "protocol": protocol, "tracker": tracker, "contrast": label,
                    "treatment": treatment, "baseline": baseline,
                    "sequence_count": len(values), "mean_idf1_delta_pp": float(np.mean(values)),
                    "bootstrap_95_low_pp": low, "bootstrap_95_high_pp": high,
                    "improved_sequences": int(np.sum(values > 1e-12)),
                    "tied_sequences": int(np.sum(np.abs(values) <= 1e-12)),
                    "worsened_sequences": int(np.sum(values < -1e-12)),
                    "total_idsw_delta": sum(idsw_deltas),
                    "bootstrap_unit": "released_sequence_with_tracker_variants_paired",
                    "bootstrap_resamples": 10000,
                    "bootstrap_seed": 20260915,
                    "fresh_confirmation": False,
                })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-script", type=Path, required=True)
    parser.add_argument("--audit-script", type=Path, required=True)
    parser.add_argument("--ace-core", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--oracle-cache", type=Path, required=True)
    parser.add_argument("--detector-cache", type=Path, required=True)
    parser.add_argument("--family-root", nargs=2, action="append", required=True)
    parser.add_argument("--selected-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.selected_config.read_text(encoding="utf-8"))
    tau_a, tau_m = float(config["tau_a"]), float(config["tau_m"])
    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    bench = load_module("ace_v_mmot_bench", args.benchmark_script)
    audit = load_module("ace_v_mmot_audit", args.audit_script)
    ace = load_module("ace_v_mmot_core", args.ace_core)
    mmot = load_module("ace_v_mmot_common", args.workspace / "scripts/run_mmot_locked_temporal.py")
    family_roots = {name: Path(path) for name, path in args.family_root}
    cache_by_protocol = {"oracle_aabb": args.oracle_cache, "official_detector": args.detector_cache}

    sequence_rows = []
    feature_rows = []
    link_rows = []
    runtime_rows = []
    started_all = time.perf_counter()
    for protocol, cache_root in cache_by_protocol.items():
        for family, family_root in family_roots.items():
            for sequence_dir in sorted(path for path in family_root.iterdir() if path.is_dir()):
                print(f"{protocol} {family}/{sequence_dir.name}", flush=True)
                frames, _, _, _ = mmot.load_sequence(sequence_dir)
                records: dict[tuple[str, str], list[dict]] = defaultdict(list)
                for class_id, class_name in enumerate(bench.CLASS_NAMES):
                    gt = mmot.class_frames(frames, class_id)
                    for tracker in ("bytetrack", "ocsort", "deepocsort"):
                        prediction_path = cache_root / "tracker_outputs" / family / sequence_dir.name / class_name / f"{tracker}.jsonl.gz"
                        descriptor_path = cache_root / "descriptors" / family / sequence_dir.name / class_name / f"{tracker}.npz"
                        if not prediction_path.is_file():
                            if protocol == "oracle_aabb" and not gt:
                                continue
                            raise FileNotFoundError(prediction_path)
                        predictions = bench.load_predictions(prediction_path)
                        descriptors = bench.load_descriptors(descriptor_path)
                        labels = audit_labels(mmot.COMMON, gt, predictions)
                        candidates, eligible_sources = bench.build_candidates(predictions, descriptors)
                        gated = audit.gated_edges(bench, candidates, audit.FIXED_APPEARANCE)
                        feature_started = time.perf_counter()
                        features = ace.add_verification_features(gated, predictions)
                        feature_seconds = time.perf_counter() - feature_started
                        selected = selections(bench, audit, ace, features, tau_a, tau_m)
                        for edge in features:
                            feature_rows.append({
                                "protocol": protocol, "family": family,
                                "sequence": sequence_dir.name, "class_name": class_name,
                                "tracker": tracker, **edge,
                                "posthoc_gt_relation": relation(edge, labels),
                                "posthoc_gt_relation_ties_excluded": relation(edge, labels, True),
                                "source_matched_observations": labels.get(int(edge["earlier"]), {}).get("matched_observations", "N/A"),
                                "destination_matched_observations": labels.get(int(edge["later"]), {}).get("matched_observations", "N/A"),
                                "source_label_purity": labels.get(int(edge["earlier"]), {}).get("purity", "N/A"),
                                "destination_label_purity": labels.get(int(edge["later"]), {}).get("purity", "N/A"),
                                "source_majority_tied": labels.get(int(edge["earlier"]), {}).get("majority_tied", "N/A"),
                                "destination_majority_tied": labels.get(int(edge["later"]), {}).get("majority_tied", "N/A"),
                            })
                        for method in METHODS:
                            method_started = time.perf_counter()
                            if method == "no_refinement":
                                output, accepted, rejected = predictions, [], []
                            else:
                                output, accepted, rejected = bench.apply_union_edges(
                                    predictions, selected[method], True, ace.edge_key
                                )
                            if method.startswith(("cost_h", "path_g")):
                                ace.assert_path_constraints(accepted)
                            solver_seconds = time.perf_counter() - method_started
                            counts = Counter(relation(edge, labels) for edge in accepted)
                            tie_counts = Counter(relation(edge, labels, True) for edge in accepted)
                            for edge in accepted:
                                link_rows.append({
                                    "protocol": protocol, "family": family,
                                    "sequence": sequence_dir.name, "class_name": class_name,
                                    "tracker": tracker, "method": method, **edge,
                                    "posthoc_gt_relation": relation(edge, labels),
                                    "posthoc_gt_relation_ties_excluded": relation(edge, labels, True),
                                })
                            duplicate = bench.duplicate_frame_identity_count(output)
                            box_preserving = bench.geometry_multiset(predictions) == bench.geometry_multiset(output)
                            records[(tracker, method)].append({
                                "metric_data": mmot.COMMON.metric_data(gt, output),
                                "duplicate_frame_identity_count": duplicate,
                                "input_rows": count_rows(predictions), "output_rows": count_rows(output),
                                "box_preserving": box_preserving, "duplicate_free": duplicate == 0,
                                "accepted_correct": counts["correct"], "accepted_false": counts["false"],
                                "accepted_unknown": counts["unknown"],
                                "tie_excluded_correct": tie_counts["correct"],
                                "tie_excluded_false": tie_counts["false"],
                                "tie_ambiguous": tie_counts["ambiguous_tie"],
                                "eligible_source_tracklets": len(eligible_sources),
                            })
                            runtime_rows.append({
                                "protocol": protocol, "family": family,
                                "sequence": sequence_dir.name, "class_name": class_name,
                                "tracker": tracker, "method": method,
                                "tracklet_count": len(bench.prediction_tracklets(predictions)[0]),
                                "candidate_count_before_fixed_gate": len(candidates),
                                "fixed_candidate_count": len(features),
                                "accepted_links": len(accepted),
                                "feature_seconds_shared": feature_seconds,
                                "solver_seconds": solver_seconds,
                                "descriptor_extraction_included": False,
                            })
                for (tracker, method), class_records in records.items():
                    # The historical helper ignores extra audit fields, which are added below.
                    base_records = [{key: value for key, value in row.items() if not key.startswith("tie_")} for row in class_records]
                    summary = audit.summarize_sequence(bench, mmot.COMMON, base_records)
                    sequence_rows.append({
                        "protocol": protocol, "family": family,
                        "sequence": sequence_dir.name, "tracker": tracker, "method": method,
                        **summary,
                        "tie_excluded_correct": sum(row["tie_excluded_correct"] for row in class_records),
                        "tie_excluded_false": sum(row["tie_excluded_false"] for row in class_records),
                        "tie_ambiguous": sum(row["tie_ambiguous"] for row in class_records),
                    })

    aggregate_rows = aggregate_sequence_rows(sequence_rows)
    comparisons = paired_rows(sequence_rows)
    quality_rows = []
    for row in aggregate_rows:
        quality_rows.append({
            key: row[key] for key in (
                "protocol", "scope", "tracker", "method", "accepted_correct",
                "accepted_false", "accepted_unknown", "tie_excluded_correct",
                "tie_excluded_false", "tie_ambiguous", "eligible_source_tracklets",
                "auditable_fraction", "conditional_error", "accepted_coverage",
            )
        })
    write_csv(args.output_dir / "hybrid_results_per_sequence.csv", sequence_rows)
    write_csv(args.output_dir / "hybrid_results_aggregate.csv", aggregate_rows)
    write_csv(args.output_dir / "paired_comparisons.csv", comparisons)
    write_csv(args.output_dir / "verification_features.csv", feature_rows)
    write_csv(args.output_dir / "accepted_link_audit.csv.gz", link_rows)
    write_csv(args.output_dir / "link_audit_label_quality.csv", quality_rows)
    write_csv(args.output_dir / "runtime_breakdown.csv", runtime_rows)
    manifest = {
        "status": "COMPLETE",
        "selected_config": {"tau_a": tau_a, "tau_m": tau_m},
        "selected_config_sha256": sha256(args.selected_config),
        "claim_scope": "Exploratory ACE-V retest on already exposed MMOT 50 sequences",
        "fresh_confirmation": False,
        "ground_truth_use": "metrics and post-hoc edge labels only",
        "cache_protocols": {name: str(path) for name, path in cache_by_protocol.items()},
        "family_roots": {name: str(path) for name, path in family_roots.items()},
        "runtime_seconds": time.perf_counter() - started_all,
        "environment": {"python": sys.version, "numpy": np.__version__},
        "inputs": {
            str(path): sha256(path) for path in (
                args.benchmark_script, args.audit_script, args.ace_core, args.selected_config,
                args.workspace / "scripts/run_mmot_locked_temporal.py",
            )
        },
        "outputs": {},
    }
    for path in sorted(args.output_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"], "runtime_seconds": manifest["runtime_seconds"],
        "sequence_rows": len(sequence_rows), "feature_rows": len(feature_rows),
        "paired_rows": len(comparisons),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
