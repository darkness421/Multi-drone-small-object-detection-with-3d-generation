#!/usr/bin/env python3
"""Measure linker edge/partition complementarity from the frozen audit trace."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


METHOD_COLUMNS = {
    "ACE-v1": "historical_reciprocal_accepted",
    "Cost-R": "controlled_reciprocal_accepted",
    "Cost-G": "controlled_greedy_accepted",
    "Cost-H": "partial_hungarian_selected",
}
EDGE_ID_FIELDS = (
    "protocol", "family", "sequence", "class_name", "tracker", "earlier", "later"
)
ATOMIC_FIELDS = ("protocol", "family", "sequence", "class_name", "tracker")


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def edge_id(row: dict) -> tuple:
    return tuple(row[field] for field in EDGE_ID_FIELDS)


def atomic_id(row: dict) -> tuple:
    return tuple(row[field] for field in ATOMIC_FIELDS)


def selected_methods(row: dict) -> set[str]:
    return {method for method, column in METHOD_COLUMNS.items() if truth(row[column])}


def co_memberships(rows: list[dict], method: str) -> set[tuple]:
    column = METHOD_COLUMNS[method]
    by_atomic: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    for row in rows:
        if truth(row[column]):
            by_atomic[atomic_id(row)].append((int(row["earlier"]), int(row["later"])))
    output = set()
    for context, edges in by_atomic.items():
        nodes = {node for edge in edges for node in edge}
        parent = {node: node for node in nodes}

        def find(node):
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        for source, destination in edges:
            left, right = find(source), find(destination)
            if left != right:
                parent[right] = left
        components: dict[int, list[int]] = defaultdict(list)
        for node in nodes:
            components[find(node)].append(node)
        for values in components.values():
            for left, right in combinations(sorted(values), 2):
                output.add((*context, left, right))
    return output


def scope_rows(rows: list[dict]):
    protocols = sorted({row["protocol"] for row in rows})
    trackers = sorted({row["tracker"] for row in rows})
    families = sorted({row["family"] for row in rows})
    for protocol in protocols:
        for tracker in trackers:
            selected = [row for row in rows if row["protocol"] == protocol and row["tracker"] == tracker]
            if selected:
                yield {"protocol": protocol, "family": "all_sequences", "tracker": tracker}, selected
            for family in families:
                subset = [row for row in selected if row["family"] == family]
                if subset:
                    yield {"protocol": protocol, "family": family, "tracker": tracker}, subset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = read_csv(args.trace)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    complementarity = []
    quality = []
    for context, subset in scope_rows(rows):
        sets = {
            method: {edge_id(row) for row in subset if truth(row[column])}
            for method, column in METHOD_COLUMNS.items()
        }
        row_by_id = {edge_id(row): row for row in subset}
        union = set().union(*sets.values())
        for method, values in sets.items():
            correctness = Counter(row_by_id[value]["posthoc_gt_correctness"] for value in values)
            known = correctness["correct"] + correctness["false"]
            low_purity = 0
            missing_source = missing_destination = 0
            for value in values:
                row = row_by_id[value]
                try:
                    source_purity = float(row["source_gt_purity"])
                except ValueError:
                    source_purity = None
                    missing_source += 1
                try:
                    destination_purity = float(row["destination_gt_purity"])
                except ValueError:
                    destination_purity = None
                    missing_destination += 1
                if (
                    source_purity is not None and source_purity < 1.0
                ) or (
                    destination_purity is not None and destination_purity < 1.0
                ):
                    low_purity += 1
            complementarity.append({
                **context,
                "analysis": "method_summary",
                "method_a": method,
                "method_b": "N/A",
                "edge_count": len(values),
                "correct": correctness["correct"],
                "false": correctness["false"],
                "unknown": correctness["unknown"],
                "conditional_precision": correctness["correct"] / known if known else "N/A",
                "auditable_fraction": known / len(values) if values else "N/A",
            })
            quality.append({
                **context,
                "method": method,
                "selected_edges": len(values),
                "correct": correctness["correct"],
                "false": correctness["false"],
                "unknown": correctness["unknown"],
                "auditable_fraction": known / len(values) if values else "N/A",
                "conditional_error": correctness["false"] / known if known else "N/A",
                "source_label_missing": missing_source,
                "destination_label_missing": missing_destination,
                "either_endpoint_purity_below_one": low_purity,
                "matched_observation_count_available": False,
                "tie_label_count_available": False,
                "unavailable_reason": (
                    "The frozen edge trace stores majority label and purity but not matched-"
                    "observation or tied-majority counts; these are rebuilt in the ACE-V run."
                ),
            })

        for left, right in combinations(METHOD_COLUMNS, 2):
            common = sets[left] & sets[right]
            left_only = sets[left] - sets[right]
            right_only = sets[right] - sets[left]
            complementarity.append({
                **context,
                "analysis": "pairwise_edge_selection",
                "method_a": left,
                "method_b": right,
                "intersection": len(common),
                "a_only": len(left_only),
                "b_only": len(right_only),
                "union": len(sets[left] | sets[right]),
                "jaccard": len(common) / len(sets[left] | sets[right]) if sets[left] | sets[right] else "N/A",
                "a_only_correct": sum(row_by_id[value]["posthoc_gt_correctness"] == "correct" for value in left_only),
                "a_only_false": sum(row_by_id[value]["posthoc_gt_correctness"] == "false" for value in left_only),
                "b_only_correct": sum(row_by_id[value]["posthoc_gt_correctness"] == "correct" for value in right_only),
                "b_only_false": sum(row_by_id[value]["posthoc_gt_correctness"] == "false" for value in right_only),
            })
            left_components = co_memberships(subset, left)
            right_components = co_memberships(subset, right)
            complementarity.append({
                **context,
                "analysis": "pairwise_component_co_membership",
                "method_a": left,
                "method_b": right,
                "intersection": len(left_components & right_components),
                "a_only": len(left_components - right_components),
                "b_only": len(right_components - left_components),
                "union": len(left_components | right_components),
                "jaccard": (
                    len(left_components & right_components) / len(left_components | right_components)
                    if left_components | right_components else "N/A"
                ),
            })

        signature_counts: dict[tuple[str, str], int] = Counter()
        for value in union:
            signature = "+".join(sorted(method for method, values in sets.items() if value in values))
            correctness = row_by_id[value]["posthoc_gt_correctness"]
            signature_counts[(signature, correctness)] += 1
        for (signature, correctness), count in sorted(signature_counts.items()):
            complementarity.append({
                **context,
                "analysis": "selection_signature",
                "method_a": signature,
                "method_b": "N/A",
                "posthoc_gt_correctness": correctness,
                "edge_count": count,
            })
        any_correct = {
            value for value in union if row_by_id[value]["posthoc_gt_correctness"] == "correct"
        }
        complementarity.append({
            **context,
            "analysis": "oracle_union_upper_bound_not_deployable",
            "method_a": "any_linker_correct_edge",
            "method_b": "N/A",
            "edge_count": len(any_correct),
            "note": "Post-hoc GT upper bound only; never scored as a deployable method.",
        })

    union_by_atomic: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        if selected_methods(row):
            union_by_atomic[atomic_id(row)].append(row)
    disagreement = []
    for context, values in union_by_atomic.items():
        source_choices: dict[int, set[int]] = defaultdict(set)
        destination_choices: dict[int, set[int]] = defaultdict(set)
        for row in values:
            source_choices[int(row["earlier"])].add(int(row["later"]))
            destination_choices[int(row["later"])].add(int(row["earlier"]))
        for row in values:
            methods = selected_methods(row)
            if len(methods) == len(METHOD_COLUMNS):
                continue
            source = int(row["earlier"])
            destination = int(row["later"])
            disagreement.append({
                **row,
                "selected_methods": ";".join(sorted(methods)),
                "selection_count": len(methods),
                "source_choice_count_across_methods": len(source_choices[source]),
                "destination_choice_count_across_methods": len(destination_choices[destination]),
                "source_conflict": len(source_choices[source]) > 1,
                "destination_conflict": len(destination_choices[destination]) > 1,
                "atomic_context": "/".join(context),
            })

    write_csv(args.output_dir / "complementarity_by_condition.csv", complementarity)
    write_csv(args.output_dir / "disagreement_edges.csv", disagreement)
    write_csv(args.output_dir / "link_audit_label_quality.csv", quality)

    all_scope = [
        row for row in complementarity
        if row["family"] == "all_sequences" and row["analysis"] == "pairwise_edge_selection"
        and row["method_a"] == "ACE-v1" and row["method_b"] == "Cost-H"
    ]
    lines = [
        "# Frozen-linker complementarity audit",
        "",
        "This is a post-hoc GT audit of already frozen edge decisions. It is not a deployable oracle ensemble.",
        "",
        f"- Source trace rows: {len(rows):,}",
        f"- Selected-edge disagreements retained: {len(disagreement):,}",
        "- Component co-membership is reported separately because distinct edge sets can induce the same ID partition.",
        "- Unknown labels remain in the coverage count and are excluded only from conditional precision/error.",
        "",
        "## ACE-v1 versus Cost-H",
        "",
        "| Input | Tracker | Common | v1-only correct/false | H-only correct/false | Edge Jaccard |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in all_scope:
        lines.append(
            f"| {row['protocol']} | {row['tracker']} | {row['intersection']} | "
            f"{row['a_only_correct']}/{row['a_only_false']} | "
            f"{row['b_only_correct']}/{row['b_only_false']} | {float(row['jaccard']):.3f} |"
        )
    v1_unique_correct = sum(int(row["a_only_correct"]) for row in all_scope)
    h_unique_correct = sum(int(row["b_only_correct"]) for row in all_scope)
    lines.extend([
        "",
        "## Decision",
        "",
        f"Across the six input/tracker conditions, v1 has {v1_unique_correct} correct edges not selected by Cost-H, while Cost-H has {h_unique_correct} correct edges not selected by v1.",
        "This confirms edge-level complementarity but does not show that a GT-free verifier can identify the useful subset. ACE-V development therefore proceeds, and its success is judged only by final trajectory metrics against the standalone solvers.",
        "",
        "The frozen trace lacks matched-observation and tied-majority counts. That omission is explicit in `link_audit_label_quality.csv`; the new run must rebuild those fields rather than treating unknown edges as errors or successes.",
    ])
    (args.output_dir / "complementarity_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(complementarity)} summary rows and {len(disagreement)} disagreements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
