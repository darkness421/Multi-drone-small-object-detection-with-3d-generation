#!/usr/bin/env python3
"""Verify the headline REGR-T and REGR-TG claims from released CSV rows."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reproducibility" / "verified_tables"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    mmot = read_csv(TABLES / "mmot_test50_summary.csv")
    paired = read_csv(TABLES / "mmot_test50_paired_ci.csv")
    m3ot = read_csv(TABLES / "m3ot_transfer_summary.csv")

    by_key = {
        (row["input"], row["tracker"], row["method"]): row
        for row in mmot
    }
    selected = "regr_t_reliable_motion_min5"
    ranking = "regr_temporal_risk_05"
    greedy = "geometry_reid_greedy_guard"
    trackers = ("bytetrack", "ocsort", "deepocsort")
    inputs = ("oracle_aabb", "official_detector")

    gains = []
    ranking_gaps = []
    for input_name in inputs:
        for tracker in trackers:
            selected_row = by_key[(input_name, tracker, selected)]
            none_row = by_key[(input_name, tracker, "no_refinement")]
            ranking_row = by_key[(input_name, tracker, ranking)]
            greedy_row = by_key[(input_name, tracker, greedy)]
            gains.append(float(selected_row["IDF1"]) - float(none_row["IDF1"]))
            ranking_gaps.append(float(ranking_row["IDF1"]) - float(greedy_row["IDF1"]))

    selected_vs_none = [
        row
        for row in paired
        if row["method"] == selected and row["baseline"] == "no_refinement"
    ]
    all_intervals_positive = len(selected_vs_none) == 6 and all(
        float(row["ci95_low"]) > 0.0 for row in selected_vs_none
    )

    m3ot_lookup = {
        (row["split"], row["tracker"], row["method"]): row for row in m3ot
    }
    m3ot_deltas = {
        tracker: (
            float(m3ot_lookup[("held_out", tracker, selected)]["IDF1"])
            - float(m3ot_lookup[("held_out", tracker, "no_refinement")]["IDF1"])
        )
        for tracker in ("bytetrack", "ocsort")
    }

    report = {
        "mmot_regr_tg_gain_pp": gains,
        "mmot_regr_tg_positive_conditions": sum(value > 0.0 for value in gains),
        "mmot_regr_tg_conditions_above_2pp": sum(value > 2.0 for value in gains),
        "mmot_regr_tg_all_paired_ci_low_above_zero": all_intervals_positive,
        "mmot_regr_t_minus_greedy_pp": ranking_gaps,
        "mmot_regr_t_max_abs_gap_to_greedy_pp": max(abs(value) for value in ranking_gaps),
        "m3ot_heldout_regr_tg_delta_pp": m3ot_deltas,
        "claim_boundary": (
            "M3OT streams were exposed by an earlier diagnostic; positive deltas are "
            "exploratory transfer evidence, not fresh independent confirmation."
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    checks = (
        report["mmot_regr_tg_positive_conditions"] == 6,
        report["mmot_regr_tg_conditions_above_2pp"] == 5,
        report["mmot_regr_tg_all_paired_ci_low_above_zero"],
        report["mmot_regr_t_max_abs_gap_to_greedy_pp"] <= 0.0551,
        m3ot_deltas["bytetrack"] > 1.5,
        m3ot_deltas["ocsort"] > 0.0,
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
