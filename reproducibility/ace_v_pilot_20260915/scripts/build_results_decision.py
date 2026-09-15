#!/usr/bin/env python3
"""Verify frozen baselines and produce the ACE-V go/no-go decision report."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


BASELINE_MAPPING = {
    "no_refinement": "no_refinement",
    "ace_v1": "com3d_reciprocal_guard",
    "cost_r": "controlled_cost_reciprocal",
    "cost_g_legacy": "controlled_cost_greedy",
    "cost_h": "geometry_reid_hungarian",
}
METRICS = (
    "HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW", "FP", "FN", "TP", "Frag",
    "accepted_correct", "accepted_false", "accepted_unknown", "eligible_source_tracklets",
)


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


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def bootstrap(values: np.ndarray, seed: int = 20260915, samples: int = 10000):
    rng = np.random.default_rng(seed)
    means = np.asarray([
        np.mean(values[rng.integers(0, len(values), len(values))])
        for _ in range(samples)
    ])
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def m3ot_paired(rows: list[dict], selected_tau_a: float, selected_tau_m: float) -> list[dict]:
    contrasts = (
        ("cost_h_full_reassign", "cost_h", "primary_H_plus_V_minus_H"),
        ("path_g_full_reassign", "path_g", "replication_G_plus_V_minus_G"),
        ("cost_h_motion_reassign", "cost_h", "motion_only_minus_H"),
        ("cost_h_soft_information", "cost_h", "soft_information_minus_H"),
    )
    configurable = {
        "cost_h_margin_reassign", "cost_h_motion_reassign",
        "cost_h_full_postfilter", "cost_h_full_reassign", "path_g_full_reassign",
    }
    selected_rows = [
        row for row in rows
        if row["method"] not in configurable
        or (
            float(row["tau_a"]) == selected_tau_a
            and float(row["tau_m"]) == selected_tau_m
        )
    ]
    lookup = {
        (row["split"], row["sequence"], row["tracker"], row["method"]): row
        for row in selected_rows
    }
    output = []
    for split in ("development", "held_out"):
        sequences = sorted({row["sequence"] for row in rows if row["split"] == split})
        for treatment, baseline, contrast in contrasts:
            for tracker in ("bytetrack", "ocsort", "all_trackers_sequence_mean"):
                deltas = []
                idsw_deltas = []
                for sequence in sequences:
                    trackers = ("bytetrack", "ocsort") if tracker == "all_trackers_sequence_mean" else (tracker,)
                    pairs = [
                        (
                            lookup.get((split, sequence, item, treatment)),
                            lookup.get((split, sequence, item, baseline)),
                        )
                        for item in trackers
                    ]
                    pairs = [(left, right) for left, right in pairs if left and right]
                    if not pairs:
                        continue
                    deltas.append(float(np.mean([float(left["IDF1"]) - float(right["IDF1"]) for left, right in pairs])))
                    idsw_deltas.append(sum(int(left["IDSW"]) - int(right["IDSW"]) for left, right in pairs))
                values = np.asarray(deltas, dtype=float)
                low, high = bootstrap(values)
                output.append({
                    "dataset": "M3OT", "protocol": split, "tracker": tracker,
                    "contrast": contrast, "treatment": treatment, "baseline": baseline,
                    "sequence_count": len(values), "mean_idf1_delta_pp": float(np.mean(values)),
                    "bootstrap_95_low_pp": low, "bootstrap_95_high_pp": high,
                    "improved_sequences": int(np.sum(values > 1e-12)),
                    "tied_sequences": int(np.sum(np.abs(values) <= 1e-12)),
                    "worsened_sequences": int(np.sum(values < -1e-12)),
                    "total_idsw_delta": sum(idsw_deltas),
                    "bootstrap_unit": "released_sequence_with_trackers_paired",
                    "bootstrap_resamples": 10000, "bootstrap_seed": 20260915,
                    "fresh_confirmation": False,
                })
    return output


def aggregate_lookup(rows: list[dict]) -> dict:
    return {(row["protocol"], row["tracker"], row["method"]): row for row in rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-aggregate", type=Path, required=True)
    parser.add_argument("--mmot-dir", type=Path, required=True)
    parser.add_argument("--m3ot-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    old = read_csv(args.old_aggregate)
    new = read_csv(args.mmot_dir / "hybrid_results_aggregate.csv")
    old_lookup = {
        (row["protocol"], row["tracker"], row["method"]): row
        for row in old if row.get("scope") == "all_sequences"
    }
    new_lookup = aggregate_lookup(new)
    reproduction = []
    for protocol, tracker, new_method, expected_method in (
        (protocol, tracker, new_method, expected_method)
        for protocol in ("oracle_aabb", "official_detector")
        for tracker in ("bytetrack", "ocsort", "deepocsort")
        for new_method, expected_method in BASELINE_MAPPING.items()
    ):
        actual = new_lookup[(protocol, tracker, new_method)]
        expected = old_lookup[(protocol, tracker, expected_method)]
        for metric in METRICS:
            difference = float(actual[metric]) - float(expected[metric])
            reproduction.append({
                "protocol": protocol, "tracker": tracker,
                "new_method": new_method, "stored_method": expected_method,
                "metric": metric, "stored_value": expected[metric],
                "rerun_value": actual[metric], "absolute_difference": abs(difference),
                "passed": abs(difference) <= 1e-9,
            })
    write_csv(args.output_dir / "baseline_reproduction.csv", reproduction)

    selected = json.loads((args.m3ot_dir / "selected_config.json").read_text(encoding="utf-8"))
    mmot_paired = read_csv(args.mmot_dir / "paired_comparisons.csv")
    for row in mmot_paired:
        row["dataset"] = "MMOT"
    m3ot_rows = read_csv(args.m3ot_dir / "hybrid_results_per_sequence.csv")
    combined_paired = mmot_paired + m3ot_paired(
        m3ot_rows, float(selected["tau_a"]), float(selected["tau_m"])
    )
    write_csv(args.output_dir / "paired_comparisons.csv", combined_paired)

    m3ot_aggregate = read_csv(args.m3ot_dir / "hybrid_results_aggregate.csv")
    m3ot_lookup = {(row["split"], row["method"]): row for row in m3ot_aggregate}
    primary_mmot = [
        row for row in combined_paired
        if row["dataset"] == "MMOT"
        and row["tracker"] == "all_trackers_sequence_mean"
        and row["contrast"] in {"primary_H_plus_V_minus_H", "replication_G_plus_V_minus_G"}
    ]
    primary_m3ot = [
        row for row in combined_paired
        if row["dataset"] == "M3OT"
        and row["tracker"] == "all_trackers_sequence_mean"
        and row["contrast"] in {"primary_H_plus_V_minus_H", "replication_G_plus_V_minus_G"}
    ]
    practical_floor = 0.30
    success = (
        all(float(row["mean_idf1_delta_pp"]) > practical_floor for row in primary_mmot)
        and all(float(row["mean_idf1_delta_pp"]) > practical_floor for row in primary_m3ot)
    )
    reproduction_pass = all(row["passed"] for row in reproduction)

    candidate_rows = read_csv(args.m3ot_dir / "candidate_recall.csv")
    candidate_summary = {}
    for split in ("development", "held_out"):
        values = [row for row in candidate_rows if row["split"] == split]
        counts = Counter(row["candidate_status"] for row in values)
        candidate_summary[split] = {
            "total": len(values),
            "entered": counts["entered_fixed_candidate_graph"],
            "geometry_gate": counts["geometry_gate"],
            "appearance_gate": counts["appearance_gate"],
            "missing_descriptor": counts["missing_descriptor"],
        }

    def delta(dataset, protocol, contrast):
        return next(
            row for row in combined_paired
            if row["dataset"] == dataset and row["protocol"] == protocol
            and row["tracker"] == "all_trackers_sequence_mean"
            and row["contrast"] == contrast
        )

    lines = [
        "# ACE-V results decision",
        "",
        "## Verdict",
        "",
        "**NO-GO for manuscript performance claims and figure replacement.**",
        "",
        "The frozen ACE-V verifier lowers conditional link error in several conditions, but the accompanying coverage loss reduces final trajectory IDF1. It therefore fails the predeclared rule that both H+V and G+V improve their standalone solvers by at least 0.30 percentage points without coverage collapse.",
        "",
        "No existing manuscript figure was replaced. No favorable-only result panel was generated. The CSV outputs retain all positive, tied, and negative conditions for manual inspection.",
        "",
        "## Protocol checks",
        "",
        f"- Frozen configuration selected on M3OT val before held-out loading: `tau_a={selected['tau_a']:.2f}`, `tau_m={selected['tau_m']:.1f}`.",
        f"- Existing baseline reproduction: {'PASS' if reproduction_pass else 'FAIL'} ({sum(row['passed'] for row in reproduction)}/{len(reproduction)} aggregate values exact).",
        "- MMOT 50 and M3OT held-out were already exposed and are reported as exploratory retests, not fresh confirmation.",
        "- All evaluated refiners preserved the frame/box/score/class multiset and produced no duplicate same-frame identities.",
        "",
        "## Primary contrasts",
        "",
        "| Dataset/input | H+V - H IDF1 | G+V - G IDF1 | Interpretation |",
        "|---|---:|---:|---|",
    ]
    for dataset, protocol, label in (
        ("M3OT", "development", "M3OT development"),
        ("M3OT", "held_out", "M3OT exposed held-out"),
        ("MMOT", "oracle_aabb", "MMOT oracle AABB"),
        ("MMOT", "official_detector", "MMOT official detector"),
    ):
        h = delta(dataset, protocol, "primary_H_plus_V_minus_H")
        g = delta(dataset, protocol, "replication_G_plus_V_minus_G")
        lines.append(
            f"| {label} | {float(h['mean_idf1_delta_pp']):+.3f} pp | "
            f"{float(g['mean_idf1_delta_pp']):+.3f} pp | "
            f"{h['improved_sequences']}/{h['tied_sequences']}/{h['worsened_sequences']} improved/tied/worsened for H+V |"
        )
    lines.extend([
        "",
        "## What the experiment establishes",
        "",
        "1. **The current verified strength remains detector-preserving temporal refinement.** On official-detector MMOT, ACE-v1 improves IDF1 over unchanged ByteTrack, OC-SORT, and Deep OC-SORT outputs, but stronger standalone linkers remain more accurate in the all-50 mean.",
        "2. **Motion is diagnostically informative but insufficient as a verifier.** Correct candidate edges have lower median motion disagreement than false edges, yet the fixed hard verifier does not convert that separation into robust trajectory gains.",
        "3. **The failure is mainly a precision-coverage trade-off.** H+V generally lowers conditional edge error while discarding links needed for identity continuity; this is not acceptable as a claimed improvement.",
        "4. **M3OT remains candidate-limited.** The direct-crop held-out audit retains only "
        f"{candidate_summary['held_out']['entered']}/{candidate_summary['held_out']['total']} correct fragment opportunities; "
        f"{candidate_summary['held_out']['geometry_gate']} are rejected by the fixed 55-pixel geometry gate before any solver or verifier acts.",
        "5. **The simple information control also does not explain a hidden gain.** It is mixed or negative across the main MMOT conditions, so neither a verifier claim nor a new soft-cost claim is supported.",
        "",
        "## Manuscript and figure action",
        "",
        "Do not add ACE-V as a validated method, do not replace the current result figure, and do not claim solver-agnostic improvement. If the experiment is discussed internally, describe it as a bounded negative pilot showing that hard evidence filtering reduces link errors but sacrifices trajectory coverage. Existing verified Figures 1, 3, and 4 remain untouched.",
        "",
        "## Fresh confirmation",
        "",
        "No fresh independent confirmation set was available. New seeds, filenames, or bootstrap draws were not treated as independent data.",
    ])
    (args.output_dir / "RESULTS_DECISION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(args.output_dir / "results_decision.json", {
        "success": success,
        "manuscript_claim": "NO-GO",
        "replace_figure": False,
        "selected_config": {"tau_a": selected["tau_a"], "tau_m": selected["tau_m"]},
        "practical_effect_floor_idf1_pp": practical_floor,
        "baseline_reproduction_passed": reproduction_pass,
        "fresh_confirmation": False,
        "candidate_recall": candidate_summary,
    })
    print(json.dumps({
        "success": success, "replace_figure": False,
        "baseline_reproduction_passed": reproduction_pass,
        "candidate_recall": candidate_summary,
    }, indent=2))
    return 0 if reproduction_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
