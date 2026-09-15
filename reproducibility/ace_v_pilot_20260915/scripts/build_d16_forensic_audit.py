#!/usr/bin/env python3
"""Trace Table D.16 to immutable artifacts and audit its verifier effects.

This script does not run a tracker, extract a descriptor, select a threshold, or
modify an experiment result.  It derives review-facing tables from the committed
MMOT and M3OT CSV files and reconstructs final ID partitions from frozen MMOT
tracklet/candidate caches solely to disambiguate the three different greedy
controls used in the manuscript and appendices.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable


ACE_ROOT = Path(__file__).resolve().parents[1]
REPRO_ROOT = ACE_ROOT.parent
EXPERIMENT_COMMIT = "9cd5fb8c319e40cb3f25b469f0bf8dbb8e63bc0b"
REVIEW_PACK_COMMIT = "a98cac208fc1638966202ac8658356b78ccf753f"
PAPER_TABLE_COMMIT = "20fa424e51420e0aa20c3dfc4edeeda81096dd71"
REQUESTED_METHODS = (
    "no_refinement",
    "ace_v1",
    "cost_h",
    "cost_h_full_reassign",
    "path_g",
    "path_g_full_reassign",
)
METHOD_LABELS = {
    "no_refinement": "None",
    "ace_v1": "v1",
    "cost_h": "H",
    "cost_h_full_reassign": "H+V",
    "path_g": "P-G",
    "path_g_full_reassign": "P-G+V",
}
PARENT_METHOD = {
    "no_refinement": "no_refinement",
    "ace_v1": "no_refinement",
    "cost_h": "no_refinement",
    "cost_h_full_reassign": "cost_h",
    "path_g": "no_refinement",
    "path_g_full_reassign": "path_g",
}
CONFIGURABLE_M3OT_METHODS = {
    "cost_h_margin_reassign",
    "cost_h_motion_reassign",
    "cost_h_full_postfilter",
    "cost_h_full_reassign",
    "path_g_full_reassign",
}
METRICS = ("IDF1", "AssA", "IDSW")


def read_csv(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    fields = list(rows[0])
    if any(set(row) != set(fields) for row in rows):
        raise ValueError(f"nonuniform fields in {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, lines: Iterable[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def selected_m3ot_rows(path: Path, tau_a: float, tau_m: float) -> list[dict]:
    selected = []
    for row in read_csv(path):
        if row["method"] not in CONFIGURABLE_M3OT_METHODS:
            selected.append(row)
        elif float(row["tau_a"]) == tau_a and float(row["tau_m"]) == tau_m:
            selected.append(row)
    return selected


def scope_metadata(dataset: str, protocol: str) -> tuple[str, str, str]:
    if dataset == "MMOT":
        input_name = "oracle AABB" if protocol == "oracle_aabb" else "official detector"
        return "test", input_name, "exposed exploratory retest"
    input_name = "oracle-box tracker output; direct tracker-box BaseReID crops"
    role = "development selection" if protocol == "development" else "exposed exploratory retest"
    return protocol, input_name, role


def absolute_per_sequence(
    rows: list[dict], dataset: str, protocol_field: str
) -> list[dict]:
    rows = [row for row in rows if row["method"] in REQUESTED_METHODS]
    lookup = {
        (row[protocol_field], row["sequence"], row["tracker"], row["method"]): row
        for row in rows
    }
    if len(lookup) != len(rows):
        raise ValueError(f"duplicate selected {dataset} result rows")
    output = []
    for protocol in sorted({row[protocol_field] for row in rows}):
        split, input_name, role = scope_metadata(dataset, protocol)
        sequences = sorted({row["sequence"] for row in rows if row[protocol_field] == protocol})
        trackers = sorted({row["tracker"] for row in rows if row[protocol_field] == protocol})
        for sequence in sequences:
            for tracker in trackers:
                none = lookup[(protocol, sequence, tracker, "no_refinement")]
                for method in REQUESTED_METHODS:
                    row = lookup[(protocol, sequence, tracker, method)]
                    parent_method = PARENT_METHOD[method]
                    parent = lookup[(protocol, sequence, tracker, parent_method)]
                    result = {
                        "dataset": dataset,
                        "split": split,
                        "protocol": protocol,
                        "data_role": role,
                        "input": input_name,
                        "sequence": sequence,
                        "tracker": tracker,
                        "method": METHOD_LABELS[method],
                        "internal_method": method,
                        "parent_method": METHOD_LABELS[parent_method],
                    }
                    for metric in METRICS:
                        caster = int if metric == "IDSW" else float
                        value = caster(row[metric])
                        none_value = caster(none[metric])
                        parent_value = caster(parent[metric])
                        result[metric] = value
                        result[f"delta_{metric}_vs_None"] = value - none_value
                        result[f"delta_{metric}_vs_parent"] = value - parent_value
                    output.append(result)
    return output


def absolute_by_tracker(per_sequence: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in per_sequence:
        groups[(
            row["dataset"], row["split"], row["protocol"], row["data_role"],
            row["input"], row["tracker"], row["method"], row["internal_method"],
            row["parent_method"],
        )].append(row)
    output = []
    for key, values in sorted(groups.items()):
        (
            dataset, split, protocol, role, input_name, tracker, method,
            internal_method, parent_method,
        ) = key
        sequences = sorted(row["sequence"] for row in values)
        output.append({
            "dataset": dataset,
            "split": split,
            "protocol": protocol,
            "data_role": role,
            "input": input_name,
            "tracker": tracker,
            "method": method,
            "internal_method": internal_method,
            "parent_method": parent_method,
            "sequence_count": len(sequences),
            "sequences": ";".join(sequences),
            "aggregation": "equal-sequence mean for IDF1/AssA; total for IDSW",
            "IDF1": sum(float(row["IDF1"]) for row in values) / len(values),
            "delta_IDF1_vs_None": sum(float(row["delta_IDF1_vs_None"]) for row in values) / len(values),
            "delta_IDF1_vs_parent": sum(float(row["delta_IDF1_vs_parent"]) for row in values) / len(values),
            "AssA": sum(float(row["AssA"]) for row in values) / len(values),
            "delta_AssA_vs_None": sum(float(row["delta_AssA_vs_None"]) for row in values) / len(values),
            "delta_AssA_vs_parent": sum(float(row["delta_AssA_vs_parent"]) for row in values) / len(values),
            "IDSW": sum(int(row["IDSW"]) for row in values),
            "delta_IDSW_vs_None": sum(int(row["delta_IDSW_vs_None"]) for row in values),
            "delta_IDSW_vs_parent": sum(int(row["delta_IDSW_vs_parent"]) for row in values),
        })
    return output


def sequence_inventory(per_sequence: list[dict]) -> list[dict]:
    groups: dict[tuple, set[str]] = defaultdict(set)
    trackers: dict[tuple, set[str]] = defaultdict(set)
    for row in per_sequence:
        key = (
            row["dataset"], row["split"], row["protocol"], row["data_role"],
            row["input"],
        )
        groups[key].add(row["sequence"])
        trackers[key].add(row["tracker"])
    return [
        {
            "dataset": key[0],
            "split": key[1],
            "protocol": key[2],
            "data_role": key[3],
            "input": key[4],
            "sequence_count": len(sequences),
            "tracker_count": len(trackers[key]),
            "trackers": ";".join(sorted(trackers[key])),
            "sequences": ";".join(sorted(sequences)),
            "family_breakdown": (
                "legacy12=12; confirmation38=38" if key[0] == "MMOT" else "N/A"
            ),
        }
        for key, sequences in sorted(groups.items())
    ]


def build_absolute_markdown(path: Path, rows: list[dict], inventory: list[dict]) -> None:
    lines = [
        "# Table D.16 absolute results by tracker",
        "",
        "IDF1 and AssA are equal-sequence means; IDSW is summed over the listed sequences. "
        "Deltas in parentheses are versus None, except H+V and P-G+V, whose second delta is versus their parent linker.",
        "",
    ]
    for item in inventory:
        lines.extend([
            f"## {item['dataset']} / {item['protocol']} / {item['input']}",
            "",
            f"Sequences ({item['sequence_count']}): `{item['sequences']}`",
            "",
            "| Tracker | Method | IDF1 | AssA | IDSW | Delta IDF1 vs None | Delta IDF1 vs parent | Delta IDSW vs None | Delta IDSW vs parent |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        values = [
            row for row in rows
            if row["dataset"] == item["dataset"] and row["protocol"] == item["protocol"]
        ]
        method_order = {label: index for index, label in enumerate(METHOD_LABELS.values())}
        for row in sorted(values, key=lambda value: (value["tracker"], method_order[value["method"]])):
            lines.append(
                f"| {row['tracker']} | {row['method']} | {row['IDF1']:.3f} | "
                f"{row['AssA']:.3f} | {row['IDSW']} | {row['delta_IDF1_vs_None']:+.3f} | "
                f"{row['delta_IDF1_vs_parent']:+.3f} | {row['delta_IDSW_vs_None']:+d} | "
                f"{row['delta_IDSW_vs_parent']:+d} |"
            )
        lines.append("")
    write_text(path, lines)


def historical_m3ot_comparison(
    direct_rows: list[dict], historical_path: Path
) -> tuple[list[dict], list[dict]]:
    historical_rows = read_csv(historical_path)
    mapping = {
        "no_refinement": "no_refinement",
        "historical_geometry_first_reciprocal": "ace_v1",
        "controlled_cost_partial_hungarian": "cost_h",
        "controlled_cost_greedy": "cost_g_legacy",
    }
    direct_lookup = {
        (row["split"], row["sequence"], row["tracker"], row["method"]): row
        for row in direct_rows
    }
    output = []
    for old in historical_rows:
        if old["method"] not in mapping:
            continue
        direct_method = mapping[old["method"]]
        key = (old["split"], old["sequence"], old["tracker"], direct_method)
        direct = direct_lookup[key]
        row = {
            "split": old["split"],
            "sequence": old["sequence"],
            "modality": old["modality"],
            "tracker": old["tracker"],
            "historical_protocol": "GT IoU>=0.9 descriptor-crop admission",
            "direct_protocol": "all valid direct tracker-box crops; no GT admission",
            "historical_method": old["method"],
            "direct_method": direct_method,
        }
        for metric in METRICS:
            caster = int if metric == "IDSW" else float
            old_value = caster(old[metric])
            direct_value = caster(direct[metric])
            row[f"historical_{metric}"] = old_value
            row[f"direct_{metric}"] = direct_value
            row[f"direct_minus_historical_{metric}"] = direct_value - old_value
        output.append(row)

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in output:
        groups[(
            row["split"], row["tracker"], row["historical_method"], row["direct_method"]
        )].append(row)
    summary = []
    for key, values in sorted(groups.items()):
        summary.append({
            "split": key[0],
            "tracker": key[1],
            "historical_method": key[2],
            "direct_method": key[3],
            "sequence_count": len(values),
            "mean_historical_IDF1": sum(row["historical_IDF1"] for row in values) / len(values),
            "mean_direct_IDF1": sum(row["direct_IDF1"] for row in values) / len(values),
            "mean_direct_minus_historical_IDF1": sum(row["direct_minus_historical_IDF1"] for row in values) / len(values),
            "mean_historical_AssA": sum(row["historical_AssA"] for row in values) / len(values),
            "mean_direct_AssA": sum(row["direct_AssA"] for row in values) / len(values),
            "mean_direct_minus_historical_AssA": sum(row["direct_minus_historical_AssA"] for row in values) / len(values),
            "total_historical_IDSW": sum(row["historical_IDSW"] for row in values),
            "total_direct_IDSW": sum(row["direct_IDSW"] for row in values),
            "total_direct_minus_historical_IDSW": sum(row["direct_minus_historical_IDSW"] for row in values),
        })
    none_rows = [row for row in output if row["direct_method"] == "no_refinement"]
    if not all(
        row[f"direct_minus_historical_{metric}"] == 0
        for row in none_rows for metric in METRICS
    ):
        raise AssertionError("historical and direct M3OT runs do not share tracker outputs")
    return output, summary


def load_tracklet_frames(path: Path) -> dict[int, set[int]]:
    frames: dict[int, set[int]] = defaultdict(set)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            frames[int(row["id"])].add(int(row["frame"]))
    return dict(frames)


def edge_pair(edge: dict) -> tuple[int, int]:
    return int(edge["earlier"]), int(edge["later"])


def path_greedy(edges: list[dict]) -> list[dict]:
    selected = []
    used_sources: set[int] = set()
    used_destinations: set[int] = set()
    for edge in sorted(
        edges,
        key=lambda value: (
            float(value["controlled_cost"]), int(value["gap"]), *edge_pair(value)
        ),
    ):
        source, destination = edge_pair(edge)
        if float(edge["controlled_cost"]) >= 1.0:
            continue
        if source in used_sources or destination in used_destinations:
            continue
        used_sources.add(source)
        used_destinations.add(destination)
        selected.append(edge)
    return selected


def union_partition(
    tracklet_frames: dict[int, set[int]],
    proposed: list[dict],
    sort_key: Callable[[dict], tuple],
) -> tuple[set[tuple[int, int]], tuple[tuple[int, ...], ...]]:
    parent = {identity: identity for identity in tracklet_frames}
    component_frames = {identity: set(frames) for identity, frames in tracklet_frames.items()}

    def find(identity: int) -> int:
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    accepted: set[tuple[int, int]] = set()
    for edge in sorted(proposed, key=sort_key):
        source, destination = edge_pair(edge)
        source_root = find(source)
        destination_root = find(destination)
        if source_root == destination_root:
            continue
        if component_frames[source_root] & component_frames[destination_root]:
            continue
        parent[destination_root] = source_root
        component_frames[source_root] |= component_frames[destination_root]
        accepted.add((source, destination))
    components: dict[int, list[int]] = defaultdict(list)
    for identity in sorted(parent):
        components[find(identity)].append(identity)
    partition = tuple(sorted(tuple(values) for values in components.values()))
    return accepted, partition


def mmot_g_partition_audit(
    feature_path: Path, mmot_manifest_path: Path
) -> tuple[list[dict], list[dict]]:
    features: dict[tuple, list[dict]] = defaultdict(list)
    for row in read_csv(feature_path):
        key = (
            row["protocol"], row["family"], row["sequence"], row["class_name"],
            row["tracker"],
        )
        features[key].append(row)
    manifest = json.loads(mmot_manifest_path.read_text(encoding="utf-8"))
    output = []
    for protocol, cache_name in sorted(manifest["cache_protocols"].items()):
        tracker_root = Path(cache_name) / "tracker_outputs"
        for prediction_path in sorted(tracker_root.glob("*/*/*/*.jsonl.gz")):
            relative = prediction_path.relative_to(tracker_root)
            family, sequence, class_name = relative.parts[:3]
            tracker = prediction_path.name.removesuffix(".jsonl.gz")
            key = (protocol, family, sequence, class_name, tracker)
            current = features.get(key, [])
            tracklet_frames = load_tracklet_frames(prediction_path)
            table4_edges, table4_partition = union_partition(
                tracklet_frames,
                current,
                lambda edge: (
                    float(edge["cosine_distance"]), int(edge["gap"]), *edge_pair(edge)
                ),
            )
            cost_g_edges, cost_g_partition = union_partition(
                tracklet_frames,
                current,
                lambda edge: (
                    float(edge["controlled_cost"]), int(edge["gap"]), *edge_pair(edge)
                ),
            )
            path_edges, path_partition = union_partition(
                tracklet_frames,
                path_greedy(current),
                lambda edge: (
                    float(edge["controlled_cost"]), int(edge["gap"]), *edge_pair(edge)
                ),
            )
            output.append({
                "protocol": protocol,
                "family": family,
                "sequence": sequence,
                "class_name": class_name,
                "tracker": tracker,
                "input_tracklets": len(tracklet_frames),
                "fixed_candidate_edges": len(current),
                "table4_method": "geometry_reid_greedy_guard",
                "table4_ranking": "cosine_distance,gap,earlier,later; component-overlap guard",
                "table4_accepted_edges": len(table4_edges),
                "d16_method": "path_g",
                "d16_ranking": "controlled_cost,gap,earlier,later; one predecessor/successor",
                "d16_accepted_edges": len(path_edges),
                "table4_vs_d16_edge_sets_identical": table4_edges == path_edges,
                "table4_vs_d16_final_partitions_identical": table4_partition == path_partition,
                "cost_g_method": "controlled_cost_greedy",
                "cost_g_accepted_edges": len(cost_g_edges),
                "cost_g_vs_d16_edge_sets_identical": cost_g_edges == path_edges,
                "cost_g_vs_d16_final_partitions_identical": cost_g_partition == path_partition,
            })
    summary_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in output:
        summary_groups[(row["protocol"], row["tracker"])].append(row)
    summary = []
    for key, values in sorted(summary_groups.items()):
        candidate_values = [row for row in values if row["fixed_candidate_edges"] > 0]
        summary.append({
            "protocol": key[0],
            "tracker": key[1],
            "class_instances": len(values),
            "candidate_bearing_class_instances": len(candidate_values),
            "table4_vs_d16_same_edge_sets_all": sum(row["table4_vs_d16_edge_sets_identical"] for row in values),
            "table4_vs_d16_same_partitions_all": sum(row["table4_vs_d16_final_partitions_identical"] for row in values),
            "table4_vs_d16_same_edge_sets_candidate_bearing": sum(row["table4_vs_d16_edge_sets_identical"] for row in candidate_values),
            "table4_vs_d16_same_partitions_candidate_bearing": sum(row["table4_vs_d16_final_partitions_identical"] for row in candidate_values),
            "cost_g_vs_d16_same_edge_sets_candidate_bearing": sum(row["cost_g_vs_d16_edge_sets_identical"] for row in candidate_values),
            "cost_g_vs_d16_same_partitions_candidate_bearing": sum(row["cost_g_vs_d16_final_partitions_identical"] for row in candidate_values),
        })
    return output, summary


def g_metric_lineage(
    d16_rows: list[dict], historical_metrics_path: Path, partition_rows: list[dict]
) -> list[dict]:
    historical_rows = read_csv(historical_metrics_path)
    historical = {
        (row["protocol"], row["family"], row["sequence"], row["tracker"]): row
        for row in historical_rows if row["method"] == "geometry_reid_greedy_guard"
    }
    partition_counts: dict[tuple, dict[str, int]] = defaultdict(
        lambda: {"table4": 0, "cost_g": 0, "d16": 0}
    )
    for row in partition_rows:
        key = (row["protocol"], row["family"], row["sequence"], row["tracker"])
        partition_counts[key]["table4"] += int(row["table4_accepted_edges"])
        partition_counts[key]["cost_g"] += int(row["cost_g_accepted_edges"])
        partition_counts[key]["d16"] += int(row["d16_accepted_edges"])
    output = []
    for d16 in d16_rows:
        if d16["method"] != "path_g":
            continue
        key = (d16["protocol"], d16["family"], d16["sequence"], d16["tracker"])
        table4 = historical[key]
        row = {
            "protocol": key[0],
            "family": key[1],
            "sequence": key[2],
            "tracker": key[3],
            "table4_method": "geometry_reid_greedy_guard",
            "d16_method": "path_g",
        }
        for metric in METRICS:
            caster = int if metric == "IDSW" else float
            old_value = caster(table4[metric])
            new_value = caster(d16[metric])
            row[f"table4_{metric}"] = old_value
            row[f"d16_{metric}"] = new_value
            row[f"d16_minus_table4_{metric}"] = new_value - old_value
        table4_stored_count = sum(
            int(table4[field])
            for field in ("accepted_correct", "accepted_false", "accepted_unknown")
        )
        d16_stored_count = sum(
            int(d16[field])
            for field in ("accepted_correct", "accepted_false", "accepted_unknown")
        )
        row["table4_reconstructed_accepted_edges"] = partition_counts[key]["table4"]
        row["table4_stored_accepted_edges"] = table4_stored_count
        row["table4_reconstruction_count_matches"] = (
            partition_counts[key]["table4"] == table4_stored_count
        )
        row["d16_reconstructed_accepted_edges"] = partition_counts[key]["d16"]
        row["d16_stored_accepted_edges"] = d16_stored_count
        row["d16_reconstruction_count_matches"] = (
            partition_counts[key]["d16"] == d16_stored_count
        )
        output.append(row)
    if not all(
        row["table4_reconstruction_count_matches"]
        and row["d16_reconstruction_count_matches"]
        for row in output
    ):
        raise AssertionError("G partition reconstruction does not match stored edge counts")
    return output


def full_verifier_pass(row: dict, tau_a: float, tau_m: float) -> bool:
    ambiguity_ok = float(row["competition_ambiguity"]) <= tau_a
    motion_available = row["motion_available"] == "True"
    if motion_available:
        motion_ok = float(row["motion_residual"]) <= tau_m
    else:
        motion_ok = float(row["outgoing_margin"]) > 0 and float(row["incoming_margin"]) > 0
    return ambiguity_ok and motion_ok


def relation_bucket(relation: str) -> str:
    return relation if relation in {"correct", "false"} else "unresolved"


def mmot_edge_transitions(
    feature_path: Path,
    accepted_path: Path,
    per_sequence_path: Path,
    tau_a: float,
    tau_m: float,
) -> tuple[list[dict], list[dict]]:
    relation: dict[tuple, str] = {}
    passing: set[tuple] = set()
    for row in read_csv(feature_path):
        key = (
            row["protocol"], row["family"], row["sequence"], row["class_name"],
            row["tracker"], int(row["earlier"]), int(row["later"]),
        )
        relation[key] = row["posthoc_gt_relation_ties_excluded"]
        if full_verifier_pass(row, tau_a, tau_m):
            passing.add(key)

    accepted: dict[tuple, set[tuple]] = defaultdict(set)
    for row in read_csv(accepted_path):
        group = (
            row["protocol"], row["family"], row["sequence"], row["tracker"],
            row["method"],
        )
        accepted[group].add((
            row["protocol"], row["family"], row["sequence"], row["class_name"],
            row["tracker"], int(row["earlier"]), int(row["later"]),
        ))

    sequence_groups = sorted({
        (row["protocol"], row["family"], row["sequence"], row["tracker"])
        for row in read_csv(per_sequence_path)
    })
    solvers = (
        ("H", "cost_h", "cost_h_full_reassign", "cost_h_full_postfilter"),
        ("P-G", "path_g", "path_g_full_reassign", None),
    )
    output = []
    for protocol, family, sequence, tracker in sequence_groups:
        group_prefix = (protocol, family, sequence, tracker)
        for solver, base_method, reassign_method, stored_post_method in solvers:
            base = accepted.get((*group_prefix, base_method), set())
            post = base & passing
            reassigned = accepted.get((*group_prefix, reassign_method), set())
            if stored_post_method:
                stored_post = accepted.get((*group_prefix, stored_post_method), set())
                if post != stored_post:
                    raise AssertionError(
                        f"derived post-filter does not match stored output: {group_prefix}"
                    )

            rejected = base - post
            added = reassigned - post
            dropped = post - reassigned

            def count(edges: set[tuple], label: str) -> int:
                return sum(relation_bucket(relation[edge]) == label for edge in edges)

            output.append({
                "protocol": protocol,
                "family": family,
                "sequence": sequence,
                "tracker": tracker,
                "base_solver": solver,
                "base_method": base_method,
                "reassignment_method": reassign_method,
                "tau_a": tau_a,
                "tau_m": tau_m,
                "audit_label": "post-hoc majority actor at IoU>=0.9; majority ties excluded",
                "base_edges": len(base),
                "postfilter_edges": len(post),
                "reassigned_edges": len(reassigned),
                "base_correct_rejected_by_verifier": count(rejected, "correct"),
                "base_false_removed_by_verifier": count(rejected, "false"),
                "base_unresolved_rejected_by_verifier": count(rejected, "unresolved"),
                "reassignment_added_correct": count(added, "correct"),
                "reassignment_added_false": count(added, "false"),
                "reassignment_added_unresolved": count(added, "unresolved"),
                "reassignment_dropped_postfilter_correct": count(dropped, "correct"),
                "reassignment_dropped_postfilter_false": count(dropped, "false"),
                "reassignment_dropped_postfilter_unresolved": count(dropped, "unresolved"),
                "stored_H_postfilter_exact": True if stored_post_method else "N/A",
            })

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in output:
        groups[(row["protocol"], row["tracker"], row["base_solver"])].append(row)
        groups[(row["protocol"], "all_trackers", row["base_solver"])].append(row)
    count_fields = [
        "base_edges", "postfilter_edges", "reassigned_edges",
        "base_correct_rejected_by_verifier", "base_false_removed_by_verifier",
        "base_unresolved_rejected_by_verifier", "reassignment_added_correct",
        "reassignment_added_false", "reassignment_added_unresolved",
        "reassignment_dropped_postfilter_correct",
        "reassignment_dropped_postfilter_false",
        "reassignment_dropped_postfilter_unresolved",
    ]
    summary = []
    for key, values in sorted(groups.items()):
        summary.append({
            "protocol": key[0],
            "tracker": key[1],
            "base_solver": key[2],
            "sequence_rows": len(values),
            "sequence_count": len({row["sequence"] for row in values}),
            "audit_label": values[0]["audit_label"],
            **{field: sum(int(row[field]) for row in values) for field in count_fields},
        })
    return output, summary


def build_verifier_markdown(path: Path, base_off_path: Path) -> None:
    base_off = read_csv(base_off_path)
    identical = sum(row["selected_pairs_identical"] == "True" for row in base_off)
    lines = [
        "# Verifier implementation audit",
        "",
        "## Candidate graph and base cost",
        "",
        "Candidates are same-class, strictly forward links with gap <= 30 frames, endpoint-center distance <= 55 pixels, and BaseReID cosine distance <= 0.30. The dimensionless controlled cost is",
        "",
        "`c_ij = mean(d_xy / 55 px, d_app / 0.30, gap / 30 frames)`.",
        "",
        "## Competition margin",
        "",
        "For edge `(i,j)`, the outgoing and incoming alternative costs include a null alternative of 1.0:",
        "",
        "`a_out = min(1.0, min_{k != j} c_ik)`, `a_in = min(1.0, min_{k != i} c_kj)`.",
        "",
        "`m_out = a_out - c_ij`, `m_in = a_in - c_ij`, and `A = max(0, -min(m_out, m_in))`.",
        "",
        "All margin quantities are dimensionless. The margin gate passes when `A <= tau_a`; the selected fixed value is `tau_a=0.10`. Therefore a smaller value is preferred.",
        "",
        "## Motion cue",
        "",
        "Independent least-squares lines are fitted to x/y box centers over the last up to three source observations and first up to three destination observations. Each side needs at least two distinct frames. The two fits are evaluated at the temporal midpoint. Pixel disagreement is divided by the mean diagonal length of the two endpoint boxes, yielding dimensionless residual `rho`. The motion gate passes when `rho <= tau_m`, with fixed `tau_m=4.0`; smaller is preferred.",
        "",
        "For motion-only verification, a missing motion cue passes. For the full verifier, a missing cue passes only when both margins are strictly positive. Thus full-V is:",
        "",
        "`A <= 0.10 and (rho <= 4.0 if motion is available else m_out > 0 and m_in > 0)`.",
        "",
        "## Application stage",
        "",
        "- `post-filter`: run H first and remove selected edges that fail full-V; no reassignment.",
        "- `full reassign`: filter the complete fixed candidate graph with full-V, then rerun the same H or P-G solver.",
        "- `margin-only` and `motion-only`: filter the complete graph by only that cue, then rerun H.",
        "- `same-cue cost-only`: rerun H with `mean(c_ij, min(A/0.10,1), min(rho/8,1))`; missing motion contributes 1. This is a cost control, not the hard verifier.",
        "",
        "H is partial Hungarian with 0.5 outgoing and 0.5 incoming null costs. P-G sorts by controlled cost and permits at most one predecessor and one successor. GT is not used by the candidate graph, cue calculation, verifier, or solver.",
        "",
        "## Verifier-off invariant",
        "",
        f"`V_off` returned every candidate and reproduced the corresponding base selection in {identical}/{len(base_off)} cached solver instances.",
    ]
    write_text(path, lines)


def build_g_lineage_markdown(
    path: Path, partition_summary: list[dict], metric_rows: list[dict]
) -> None:
    candidate_instances = sum(row["candidate_bearing_class_instances"] for row in partition_summary)
    same_partitions = sum(row["table4_vs_d16_same_partitions_candidate_bearing"] for row in partition_summary)
    same_edges = sum(row["table4_vs_d16_same_edge_sets_candidate_bearing"] for row in partition_summary)
    metric_identical = sum(
        abs(row["d16_minus_table4_IDF1"]) <= 1e-12
        and abs(row["d16_minus_table4_AssA"]) <= 1e-12
        and row["d16_minus_table4_IDSW"] == 0
        for row in metric_rows
    )
    lines = [
        "# Table 4 versus Table D.16 greedy lineage",
        "",
        "The two rows denoted informally by G are not the same implementation.",
        "",
        "- Table 4 `Geo.+ReID-G` is `geometry_reid_greedy_guard`: it ranks all gated candidates by cosine distance, then merges components unless their frame sets overlap. It does not enforce one predecessor and one successor at edge selection.",
        "- Table D.16 used `path_g`: it ranks by the normalized controlled cost and enforces at most one outgoing and one incoming edge before component merging.",
        "- The separate controlled-solver table's `Cost-G` is `controlled_cost_greedy`: it ranks all gated candidates by controlled cost and applies only the component-overlap guard. It is also not `path_g`.",
        "",
        f"Across {candidate_instances} candidate-bearing MMOT class/tracker instances, Table 4 and D.16 have identical accepted-edge sets in {same_edges} and identical final ID partitions in {same_partitions}. Across {len(metric_rows)} sequence/tracker rows, all three displayed metrics (IDF1, AssA, IDSW) match in {metric_identical}. The global answer is therefore **not equivalent**.",
        "",
        "The D.16 label should be `P-G` (controlled-cost path-constrained greedy), not the Table 4 `Geo.+ReID-G` label.",
    ]
    write_text(path, lines)


def build_m3ot_markdown(path: Path, summary: list[dict]) -> None:
    lines = [
        "# M3OT preprocessing control",
        "",
        "The historical diagnostic admitted tracker observations to descriptor crops only after one-to-one oracle-GT IoU >= 0.9 matching. The D.16 run crops every valid tracker box directly, without GT crop admission. Both retain oracle-box upstream tracker inputs. None is identical in every sequence/tracker row, confirming the same tracker trajectories; changes below arise from descriptor admission/crops and downstream linking.",
        "",
        "| Split | Tracker | Method mapping | Direct - historical IDF1 | Direct - historical AssA | Direct - historical IDSW |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in summary:
        lines.append(
            f"| {row['split']} | {row['tracker']} | {row['historical_method']} -> {row['direct_method']} | "
            f"{row['mean_direct_minus_historical_IDF1']:+.3f} | "
            f"{row['mean_direct_minus_historical_AssA']:+.3f} | "
            f"{row['total_direct_minus_historical_IDSW']:+d} |"
        )
    lines.extend([
        "",
        "The historical cache has no path-constrained P-G row, so a historical GT-admission P-G comparison is unavailable and is not inferred. H/P-G verifier deltas are reported only within the direct-crop run.",
    ])
    write_text(path, lines)


def build_edge_markdown(path: Path, summary: list[dict]) -> None:
    lines = [
        "# MMOT verifier edge-transition audit",
        "",
        "Labels are post-hoc majority-actor relations from one-to-one same-class GT matching at IoU >= 0.9. Majority ties and unmatched endpoints are retained as unresolved; they are not forced into correct/false counts. GT is not used by linking or verification.",
        "",
        "| Input | Tracker | Base | Correct base links rejected | False base links removed | Correct links added by reassignment | False links added by reassignment | Unresolved rejected/added |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary:
        if row["tracker"] == "all_trackers":
            continue
        lines.append(
            f"| {row['protocol']} | {row['tracker']} | {row['base_solver']} | "
            f"{row['base_correct_rejected_by_verifier']} | "
            f"{row['base_false_removed_by_verifier']} | "
            f"{row['reassignment_added_correct']} | "
            f"{row['reassignment_added_false']} | "
            f"{row['base_unresolved_rejected_by_verifier']}/{row['reassignment_added_unresolved']} |"
        )
    lines.extend([
        "",
        "These are edge diagnostics, not independent identity-recovery claims. The mixed final IDF1 results remain authoritative because removing a false edge can also break useful continuity, and adding a locally correct edge need not improve the final trajectory partition.",
    ])
    write_text(path, lines)


def build_provenance(
    path: Path,
    paper_root: Path | None,
    mmot_manifest: dict,
    m3ot_manifest: dict,
) -> None:
    paper_table = paper_root / "ivc_tables/temporal/ace_v_strong_linker.tex" if paper_root else None
    generated_table = ACE_ROOT / "results_raw/review_response_20260916/paper_table_ace_v_strong_linker.tex"
    lines = [
        "# Table D.16 provenance",
        "",
        f"- Experiment implementation and immutable result artifacts: `{EXPERIMENT_COMMIT}`.",
        f"- Review-pack and LaTeX table generator: `{REVIEW_PACK_COMMIT}` (`scripts/build_review_response.py`).",
        f"- Manuscript commit that includes Table D.16: `{PAPER_TABLE_COMMIT}`.",
        "- Frozen configuration: `reproducibility/ace_v_pilot_20260915/protocol_freeze.yaml`.",
        "- Selected development configuration: `results_raw/m3ot_direct_crop_v1/selected_config.json` (`tau_a=0.10`, `tau_m=4.0`).",
        "- MMOT sequence results: `results_raw/mmot_full50_v1/hybrid_results_per_sequence.csv`.",
        "- M3OT sequence results: `results_raw/m3ot_direct_crop_v1/hybrid_results_per_sequence.csv`.",
        "- Table generator output: `results_raw/review_response_20260916/paper_table_ace_v_strong_linker.tex`.",
        "- Reconstructed non-overwriting commands: `results_raw/review_response_20260916/reproduction_commands.md`.",
        "",
        "## Execution record",
        "",
        f"- MMOT manifest status `{mmot_manifest['status']}`, runtime `{float(mmot_manifest['runtime_seconds']):.3f} s`, result hashes recorded in `results_raw/mmot_full50_v1/manifest.json`.",
        f"- M3OT manifest status `{m3ot_manifest['status']}`, runtime `{float(m3ot_manifest['runtime_seconds']):.3f} s`, result hashes recorded in `results_raw/m3ot_direct_crop_v1/manifest.json`.",
        "- The exact historical shell strings, scheduler IDs, and stdout/stderr logs for these two runs were not persisted. They cannot be truthfully supplied after the fact. The manifest parameters and current CLI contracts reconstruct executable commands, but those commands are not represented as historical logs.",
        "- No experiment is currently running, and this forensic audit does not rerun either experiment.",
    ]
    if paper_table and paper_table.is_file():
        lines.extend([
            "",
            "## LaTeX linkage",
            "",
            f"- Manuscript table path: `{paper_table}`.",
            f"- Current generated/table SHA-256: `{sha256(generated_table)}` / `{sha256(paper_table)}`.",
            f"- Byte-identical: `{generated_table.read_bytes() == paper_table.read_bytes()}`.",
        ])
    write_text(path, lines)


def build_forensic_report(
    path: Path,
    partition_summary: list[dict],
    edge_summary: list[dict],
    review_dir: Path,
) -> None:
    candidate_instances = sum(row["candidate_bearing_class_instances"] for row in partition_summary)
    same_partitions = sum(
        row["table4_vs_d16_same_partitions_candidate_bearing"]
        for row in partition_summary
    )
    edge_lookup = {
        (row["protocol"], row["tracker"], row["base_solver"]): row
        for row in edge_summary
    }
    lines = [
        "# Table D.16 forensic audit report",
        "",
        "## Verdict",
        "",
        "The D.16 experiments are complete, but their result remains mixed/negative. The fixed full verifier does not establish a solver-agnostic gain: both H and P-G worsen on MMOT. No threshold was selected or changed in this audit.",
        "",
        "A concrete naming error was found: D.16's `path_g` is not Table 4's `Geo.+ReID-G`. The D.16 control must be named `P-G` to prevent a false implementation equivalence.",
        "",
        "## Requested checks",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
        "| D.16 commit/config/commands/results lineage | Partially resolved | Commits, manifests, reconstructed commands, CSV and table paths are recorded; historical stdout/stderr and scheduler IDs were not persisted. |",
        "| Absolute None/v1/H/H+V/P-G/P-G+V by tracker | Resolved | `d16_absolute_metrics_by_tracker.csv`, `d16_absolute_metrics_per_sequence.csv`, and `d16_absolute_results.md`. |",
        "| Verifier equations, units, directions, stage, reassignment | Resolved | `verifier_implementation_audit.md` is traced directly to `ace_v_core.py` and both runners. |",
        "| V-off base reproduction | Resolved | `review_response_20260916/base_off_equivalence.csv`: 1,630/1,630 candidate-bearing solver instances identical. |",
        f"| D.16 P-G versus Table 4 G | Resolved as non-equivalent | Only {same_partitions}/{candidate_instances} candidate-bearing final ID partitions match; see `g_lineage_audit.md`. |",
        "| M3OT GT-admission versus direct crop | Partially resolved | Same tracker outputs verified and v1/H/legacy Cost-G compared. Historical cache has no P-G row, so that cross-preprocessing contrast is unavailable. |",
        "| Margin-only/motion-only/cost-only/post-filter/reassignment | Resolved | `../review_response_20260916/requested_contrasts_per_sequence.csv`, `requested_contrasts_summary.csv`, and `component_comparison_summary.md`. |",
        "| MMOT verifier edge transitions | Partially resolved | Counts are complete under the post-hoc audit labels, but many edges have unmatched/tied endpoints and remain unresolved rather than being treated as GT. |",
        "| Solver-agnostic verifier advantage | Unresolved/unsupported | MMOT IDF1 is negative for both fixed primary contrasts. |",
        "",
        "## MMOT all-tracker edge totals",
        "",
        "| Input | Base | Correct rejected | False removed | Correct added by reassignment | False added by reassignment | Unresolved rejected/added |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for protocol in ("oracle_aabb", "official_detector"):
        for solver in ("H", "P-G"):
            row = edge_lookup[(protocol, "all_trackers", solver)]
            lines.append(
                f"| {protocol} | {solver} | {row['base_correct_rejected_by_verifier']} | "
                f"{row['base_false_removed_by_verifier']} | {row['reassignment_added_correct']} | "
                f"{row['reassignment_added_false']} | "
                f"{row['base_unresolved_rejected_by_verifier']}/{row['reassignment_added_unresolved']} |"
            )
    lines.extend([
        "",
        "The edge audit explains why lower conditional error is not enough: the verifier removes both correct and false links, while reassignment adds both correct and false alternatives. Final trajectory metrics, not favorable edge subsets, determine the conclusion.",
        "",
        "## Manuscript action",
        "",
        "Only the confirmed naming issue should change the manuscript: use `P-G` for D.16 and retain Table 4's `Geo.+ReID-G` as a distinct method. The negative D.16 values and limitations remain unchanged.",
        "",
        "Control summary source: `../review_response_20260916/component_comparison_summary.md`.",
    ])
    write_text(path, lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ACE_ROOT / "results_raw/d16_forensic_audit_20260916",
    )
    parser.add_argument("--paper-root", type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    mmot_dir = ACE_ROOT / "results_raw/mmot_full50_v1"
    m3ot_dir = ACE_ROOT / "results_raw/m3ot_direct_crop_v1"
    review_dir = ACE_ROOT / "results_raw/review_response_20260916"
    historical_m3ot_dir = REPRO_ROOT / "ivc_professor_review_20260914/results_raw/m3ot_linker_diagnostic_v2"
    historical_mmot_dir = REPRO_ROOT / "ivc_professor_review_20260914/results_raw/mmot_cached_solver_audit_v1"
    selected = json.loads((m3ot_dir / "selected_config.json").read_text(encoding="utf-8"))
    tau_a = float(selected["tau_a"])
    tau_m = float(selected["tau_m"])

    mmot_rows = read_csv(mmot_dir / "hybrid_results_per_sequence.csv")
    m3ot_rows = selected_m3ot_rows(
        m3ot_dir / "hybrid_results_per_sequence.csv", tau_a, tau_m
    )
    per_sequence = absolute_per_sequence(mmot_rows, "MMOT", "protocol")
    per_sequence.extend(absolute_per_sequence(m3ot_rows, "M3OT", "split"))
    per_sequence.sort(key=lambda row: (
        row["dataset"], row["protocol"], row["sequence"], row["tracker"],
        REQUESTED_METHODS.index(row["internal_method"]),
    ))
    absolute = absolute_by_tracker(per_sequence)
    inventory = sequence_inventory(per_sequence)

    m3ot_old_vs_direct, m3ot_old_vs_direct_summary = historical_m3ot_comparison(
        m3ot_rows, historical_m3ot_dir / "m3ot_linker_per_sequence.csv"
    )
    partition_rows, partition_summary = mmot_g_partition_audit(
        mmot_dir / "verification_features.csv", mmot_dir / "manifest.json"
    )
    g_metrics = g_metric_lineage(
        mmot_rows,
        historical_mmot_dir / "solver_metrics_per_sequence.csv",
        partition_rows,
    )
    edge_rows, edge_summary = mmot_edge_transitions(
        mmot_dir / "verification_features.csv",
        mmot_dir / "accepted_link_audit.csv.gz",
        mmot_dir / "hybrid_results_per_sequence.csv",
        tau_a,
        tau_m,
    )

    outputs = {
        "d16_absolute_metrics_per_sequence.csv": per_sequence,
        "d16_absolute_metrics_by_tracker.csv": absolute,
        "d16_sequence_inventory.csv": inventory,
        "m3ot_gt_admission_vs_direct_per_sequence.csv": m3ot_old_vs_direct,
        "m3ot_gt_admission_vs_direct_summary.csv": m3ot_old_vs_direct_summary,
        "g_partition_equivalence_by_class.csv": partition_rows,
        "g_partition_equivalence_summary.csv": partition_summary,
        "g_metric_lineage_per_sequence.csv": g_metrics,
        "mmot_verifier_edge_transitions_per_sequence.csv": edge_rows,
        "mmot_verifier_edge_transitions_summary.csv": edge_summary,
    }
    for name, rows in outputs.items():
        write_csv(output_dir / name, rows)

    build_absolute_markdown(output_dir / "d16_absolute_results.md", absolute, inventory)
    build_verifier_markdown(
        output_dir / "verifier_implementation_audit.md",
        review_dir / "base_off_equivalence.csv",
    )
    build_g_lineage_markdown(
        output_dir / "g_lineage_audit.md", partition_summary, g_metrics
    )
    build_m3ot_markdown(
        output_dir / "m3ot_preprocessing_audit.md", m3ot_old_vs_direct_summary
    )
    build_edge_markdown(output_dir / "mmot_edge_transition_audit.md", edge_summary)

    mmot_manifest_path = mmot_dir / "manifest.json"
    m3ot_manifest_path = m3ot_dir / "manifest.json"
    mmot_manifest = json.loads(mmot_manifest_path.read_text(encoding="utf-8"))
    m3ot_manifest = json.loads(m3ot_manifest_path.read_text(encoding="utf-8"))
    build_provenance(
        output_dir / "d16_provenance.md",
        args.paper_root,
        mmot_manifest,
        m3ot_manifest,
    )
    build_forensic_report(
        output_dir / "d16_forensic_report.md",
        partition_summary,
        edge_summary,
        review_dir,
    )

    input_paths = [
        ACE_ROOT / "protocol_freeze.yaml",
        mmot_dir / "hybrid_results_per_sequence.csv",
        mmot_dir / "verification_features.csv",
        mmot_dir / "accepted_link_audit.csv.gz",
        mmot_manifest_path,
        m3ot_dir / "hybrid_results_per_sequence.csv",
        m3ot_dir / "m3ot_direct_crop_diagnostic.csv",
        m3ot_dir / "selected_config.json",
        m3ot_manifest_path,
        historical_m3ot_dir / "m3ot_linker_per_sequence.csv",
        historical_m3ot_dir / "manifest.json",
        historical_mmot_dir / "solver_metrics_per_sequence.csv",
        review_dir / "base_off_equivalence.csv",
        review_dir / "requested_contrasts_per_sequence.csv",
        review_dir / "requested_contrasts_summary.csv",
    ]
    generated = sorted(path for path in output_dir.iterdir() if path.name != "manifest.json")
    manifest = {
        "status": "COMPLETE_FORENSIC_AUDIT",
        "new_experiment_executed": False,
        "threshold_selection_or_tuning_performed": False,
        "source_result_files_modified": False,
        "experiment_commit": EXPERIMENT_COMMIT,
        "review_pack_commit": REVIEW_PACK_COMMIT,
        "paper_table_commit": PAPER_TABLE_COMMIT,
        "selected_config": {"tau_a": tau_a, "tau_m": tau_m},
        "input_sha256": {str(path): sha256(path) for path in input_paths},
        "output_sha256": {path.name: sha256(path) for path in generated},
        "row_counts": {name: len(rows) for name, rows in outputs.items()},
        "historical_stdout_stderr_available": False,
        "historical_scheduler_id_available": False,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": manifest["status"],
        "absolute_per_sequence_rows": len(per_sequence),
        "partition_instances": len(partition_rows),
        "mmot_edge_transition_rows": len(edge_rows),
        "new_experiment_executed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
