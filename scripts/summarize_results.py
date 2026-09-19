#!/usr/bin/env python3
"""Create reported REGR tables from frozen raw evaluation CSV files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


METRICS = ("IDF1", "HOTA", "AssA")
MAIN_METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_greedy",
    "partial_hungarian_u100",
    "aflink",
    "regr_final",
)
ABLATIONS = (
    "regr_final",
    "regr_final_no_gap",
    "regr_final_no_reciprocal",
    "regr_final_no_motion",
    "regr_final_motion_always",
    "s2_h_cond_w3_endpoint_c50_r100",
)
COMPARATORS = (
    "no_refinement",
    "geometry_reid_greedy",
    "partial_hungarian_u100",
    "regr_final_no_motion",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate(rows: list[dict[str, str]], unit_key: str) -> list[dict]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["tracker"], row["method"])].append(row)
    output = []
    for (tracker, method), values in sorted(groups.items()):
        output.append({
            "tracker": tracker,
            "method": method,
            "unit_count": len({row[unit_key] for row in values}),
            **{
                metric: float(np.mean([float(row[metric]) for row in values]))
                for metric in METRICS
            },
            "IDSW": int(sum(int(float(row["IDSW"])) for row in values)),
        })
    return output


def load_panel(directory: Path, panel: str) -> tuple[list[dict], list[dict[str, str]], str]:
    if panel.startswith("mmot"):
        per_unit = read_csv(directory / "results" / "metrics_per_sequence.csv")
        return aggregate(per_unit, "sequence"), per_unit, "sequence"
    per_unit = read_csv(directory / "metrics_per_scene_group.csv")
    return aggregate(per_unit, "scene_group"), per_unit, "scene_group"


def append_aflink(
    panel: str,
    aggregate_rows: list[dict],
    per_unit_rows: list[dict[str, str]],
    aflink_path: Path,
) -> None:
    rows = read_csv(aflink_path)
    old_name = "aflink_va" if panel == "m3ot_oracle" else "aflink_official"
    valid = [
        row for row in rows
        if row["method"] == old_name and row.get("valid_output", "True") == "True"
    ]
    expected = 7 if panel == "m3ot_oracle" else 50
    unit_key = "scene_group" if panel == "m3ot_oracle" else "sequence"
    for tracker in sorted({row["tracker"] for row in rows if row["method"] == old_name}):
        tracker_rows = [row for row in valid if row["tracker"] == tracker]
        count = len({row[unit_key] for row in tracker_rows})
        if count == expected:
            renamed = [{**row, "method": "aflink"} for row in tracker_rows]
            per_unit_rows.extend(renamed)
            aggregate_rows.extend(aggregate(renamed, unit_key))
        else:
            aggregate_rows.append({
                "tracker": tracker,
                "method": "aflink",
                "unit_count": count,
                "IDF1": "N/A",
                "HOTA": "N/A",
                "AssA": "N/A",
                "IDSW": "N/A",
                "invalid_output_note": f"valid on {count}/{expected} units; excluded from full-split aggregate",
            })


def bootstrap(delta: np.ndarray, repeats: int, seed: int) -> tuple[float, float]:
    generator = np.random.default_rng(seed)
    indices = generator.integers(0, len(delta), size=(repeats, len(delta)))
    means = delta[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def paired_rows(
    panel: str,
    rows: list[dict[str, str]],
    unit_key: str,
    repeats: int,
    seed: int,
) -> list[dict]:
    output = []
    trackers = sorted({row["tracker"] for row in rows})
    for tracker in trackers:
        by_method = {
            method: {row[unit_key]: float(row["IDF1"]) for row in rows if row["tracker"] == tracker and row["method"] == method}
            for method in ("regr_final",) + COMPARATORS
        }
        final = by_method["regr_final"]
        for baseline in COMPARATORS:
            common = sorted(set(final) & set(by_method[baseline]))
            if len(common) != len(final):
                raise ValueError(f"incomplete pairing for {panel}/{tracker}/{baseline}")
            delta = np.asarray([final[key] - by_method[baseline][key] for key in common])
            lower, upper = bootstrap(delta, repeats, seed)
            output.append({
                "panel": panel,
                "tracker": tracker,
                "comparison": f"regr_final-minus-{baseline}",
                "unit": unit_key,
                "unit_count": len(common),
                "mean_delta_IDF1_pp": float(delta.mean()),
                "ci95_low": lower,
                "ci95_high": upper,
                "wins": int(np.sum(delta > 1e-12)),
                "ties": int(np.sum(np.abs(delta) <= 1e-12)),
                "losses": int(np.sum(delta < -1e-12)),
                "bootstrap_repeats": repeats,
                "bootstrap_seed": seed,
            })
    return output


def relation_counts(path: Path, panel: str) -> list[dict]:
    rows = read_csv(path)
    methods = {"regr_final", "regr_final_no_motion"}
    key_fields = (
        ("family", "sequence", "class_name", "tracker", "earlier", "later")
        if panel.startswith("mmot")
        else ("sequence", "tracker", "earlier", "later")
    )
    indexed: dict[str, dict[tuple[str, ...], str]] = {}
    for method in methods:
        indexed[method] = {
            tuple(row.get(field, "") for field in key_fields): row["posthoc_gt_correctness"]
            for row in rows if row["method"] == method
        }
    output = []
    for tracker in sorted({row["tracker"] for row in rows}):
        tracker_index = {}
        for method in methods:
            tracker_index[method] = {
                key: relation for key, relation in indexed[method].items()
                if key[key_fields.index("tracker")] == tracker
            }
        base, final = tracker_index["regr_final_no_motion"], tracker_index["regr_final"]
        removed = Counter(base[key] for key in set(base) - set(final))
        added = Counter(final[key] for key in set(final) - set(base))
        output.append({
            "panel": panel,
            "tracker": tracker,
            "base_links": len(base),
            "final_links": len(final),
            "removed_correct": removed["correct"],
            "removed_false": removed["false"],
            "removed_unknown": removed["unknown"],
            "added_correct": added["correct"],
            "added_false": added["false"],
            "added_unknown": added["unknown"],
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-dir", type=Path, required=True)
    parser.add_argument("--detector-dir", type=Path, required=True)
    parser.add_argument("--m3ot-dir", type=Path, required=True)
    parser.add_argument("--oracle-aflink", type=Path, required=True)
    parser.add_argument("--detector-aflink", type=Path, required=True)
    parser.add_argument("--m3ot-aflink", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-repeats", type=int, default=20000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260918)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    specs = (
        ("mmot_oracle", args.oracle_dir, args.oracle_aflink),
        ("mmot_detector", args.detector_dir, args.detector_aflink),
        ("m3ot_oracle", args.m3ot_dir, args.m3ot_aflink),
    )
    panel_data = {}
    main = []
    ablation = []
    pairs = []
    for panel, directory, aflink in specs:
        aggregate_rows, per_unit, unit_key = load_panel(directory, panel)
        append_aflink(panel, aggregate_rows, per_unit, aflink)
        panel_data[panel] = (aggregate_rows, per_unit, unit_key)
        lookup = {(row["tracker"], row["method"]): row for row in aggregate_rows}
        for tracker in sorted({row["tracker"] for row in aggregate_rows}):
            strong = max(
                (lookup[(tracker, method)] for method in ("geometry_reid_greedy", "partial_hungarian_u100")),
                key=lambda row: float(row["IDF1"]),
            )
            for method in MAIN_METHODS:
                row = lookup.get((tracker, method))
                if row is None:
                    continue
                final_idf1 = row["IDF1"]
                main.append({
                    "panel": panel,
                    "aggregation_unit": unit_key,
                    "tracker": tracker,
                    "method": method,
                    "unit_count": row["unit_count"],
                    "IDF1": final_idf1,
                    "HOTA": row["HOTA"],
                    "AssA": row["AssA"],
                    "IDSW": row["IDSW"],
                    "strong_baseline_method": strong["method"],
                    "delta_vs_strong_IDF1_pp": (
                        float(final_idf1) - float(strong["IDF1"])
                        if final_idf1 != "N/A" else "N/A"
                    ),
                    "note": row.get("invalid_output_note", ""),
                })
            final = lookup[(tracker, "regr_final")]
            for method in ABLATIONS:
                row = lookup[(tracker, method)]
                ablation.append({
                    "panel": panel,
                    "tracker": tracker,
                    "method": method,
                    "IDF1": row["IDF1"],
                    "HOTA": row["HOTA"],
                    "AssA": row["AssA"],
                    "IDSW": row["IDSW"],
                    "delta_vs_full_IDF1_pp": float(row["IDF1"]) - float(final["IDF1"]),
                })
        pairs.extend(paired_rows(panel, per_unit, unit_key, args.bootstrap_repeats, args.bootstrap_seed))

    write_csv(args.output_dir / "main_comparison.csv", main)
    write_csv(args.output_dir / "ablation.csv", ablation)
    write_csv(args.output_dir / "paired_idf1.csv", pairs)
    links = []
    links.extend(relation_counts(args.oracle_dir / "results" / "accepted_links.csv", "mmot_oracle"))
    links.extend(relation_counts(args.detector_dir / "results" / "accepted_links.csv", "mmot_detector"))
    links.extend(relation_counts(args.m3ot_dir / "accepted_links.csv", "m3ot_oracle"))
    write_csv(args.output_dir / "guard_link_effect.csv", links)

    selected = json.loads(args.selection.read_text(encoding="utf-8"))
    manifest = {
        "status": "COMPLETE",
        "selected_method": selected["selected_method"],
        "method": "regr_final",
        "bootstrap_repeats": args.bootstrap_repeats,
        "bootstrap_seed": args.bootstrap_seed,
        "aggregation": {
            "mmot": "equal-sequence means; IDSW summed over 50 sequences",
            "m3ot": "equal-scene means after four-stream averaging; IDSW summed over seven scenes",
        },
        "inputs": {
            str(path): sha256(path)
            for path in (
                args.oracle_dir / "results" / "metrics_per_sequence.csv",
                args.detector_dir / "results" / "metrics_per_sequence.csv",
                args.m3ot_dir / "metrics_per_scene_group.csv",
                args.oracle_aflink,
                args.detector_aflink,
                args.m3ot_aflink,
                args.selection,
            )
        },
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
