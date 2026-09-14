#!/usr/bin/env python3
"""Verify displayed manuscript numbers against the cached-audit CSV outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


METHOD_LABELS = {
    "no_refinement": "None",
    "geometry_greedy": "Geometry greedy",
    "geometry_reid_greedy_guard": "Geo.+ReID greedy",
    "geometry_reid_hungarian": "Partial Hung.",
    "aflink_cached_overlap_safe": "AFLink+VA",
    "com3d_reciprocal_guard": "CoM3D-ACE",
}
TRACKERS = ("bytetrack", "ocsort", "deepocsort")
PROTOCOLS = ("oracle_aabb", "official_detector")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f2(value: str | float) -> str:
    return f"{float(value):.2f}"


def f1(value: str | float) -> str:
    return f"{float(value):,.1f}"


def integer(value: str | int | float) -> str:
    return f"{int(float(value)):,}"


def signed2(value: str | float) -> str:
    number = float(value)
    return f"{number:+.2f}" if number >= 0 else f"{number:.2f}"


def tex_rows(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", text)
    return [re.sub(r"\s+", " ", row).strip() for row in text.split(r"\\")]


def has_in_order(row: str, tokens: list[str]) -> bool:
    offset = 0
    for token in tokens:
        offset = row.find(token, offset)
        if offset < 0:
            return False
        offset += len(token)
    return True


def find_one(rows: list[str], label: str, occurrence: int) -> str:
    matches = [row for row in rows if f"& {label} &" in row]
    if occurrence >= len(matches):
        return ""
    return matches[occurrence]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-root", type=Path, required=True)
    parser.add_argument("--paper-root", type=Path, required=True)
    args = parser.parse_args()

    report_root = args.report_root.resolve()
    paper_root = args.paper_root.resolve()
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    main_rows = read_csv(report_root / "main_comparison.csv")
    main_lookup = {
        (row["protocol"], row["tracker"], row["method"]): row for row in main_rows
    }
    aggregate_rows = read_csv(
        report_root
        / "results_raw/mmot_cached_solver_audit_v1/solver_metrics_aggregate.csv"
    )
    for row in aggregate_rows:
        if row["scope"] != "all_sequences":
            continue
        normalized = dict(row)
        normalized.update(
            {
                "HOTA_equal_sequence_mean": row["HOTA"],
                "AssA_equal_sequence_mean": row["AssA"],
                "IDF1_equal_sequence_mean": row["IDF1"],
                "IDSW_total": row["IDSW"],
            }
        )
        main_lookup.setdefault(
            (row["protocol"], row["tracker"], row["method"]), normalized
        )

    # Main compact table: one method row carries all three trackers per protocol.
    table_rows = tex_rows(paper_root / "ivc_tables/temporal/main_refinement_gains.tex")
    for method, label in METHOD_LABELS.items():
        for protocol_index, protocol in enumerate(PROTOCOLS):
            row = find_one(table_rows, label, protocol_index)
            expected: list[str] = []
            for tracker in TRACKERS:
                source = main_lookup[(protocol, tracker, method)]
                expected.extend(
                    [f2(source["IDF1_equal_sequence_mean"]), integer(source["IDSW_total"])]
                )
            check(
                f"main table {protocol}/{method}",
                bool(row) and has_in_order(row, expected),
                " | ".join(expected),
            )

    # Full tables include HOTA and AssA. Method occurrences follow tracker order.
    for protocol, filename in (
        ("oracle_aabb", "oracle_full50.tex"),
        ("official_detector", "detector_full50.tex"),
    ):
        rows = tex_rows(paper_root / "ivc_tables/temporal" / filename)
        for method, label in METHOD_LABELS.items():
            for tracker_index, tracker in enumerate(TRACKERS):
                row = find_one(rows, label, tracker_index)
                source = main_lookup[(protocol, tracker, method)]
                expected = [
                    f2(source["HOTA_equal_sequence_mean"]),
                    f2(source["AssA_equal_sequence_mean"]),
                    f2(source["IDF1_equal_sequence_mean"]),
                    integer(source["IDSW_total"]),
                ]
                check(
                    f"full table {protocol}/{tracker}/{method}",
                    bool(row) and has_in_order(row, expected),
                    " | ".join(expected),
                )

    # Common-cost controls use the same cached candidate graph.
    controlled_rows = tex_rows(paper_root / "ivc_tables/temporal/controlled_solver.tex")
    controlled_methods = (
        "com3d_reciprocal_guard",
        "controlled_cost_greedy",
        "controlled_cost_reciprocal",
        "geometry_reid_hungarian",
    )
    data_rows = [
        row
        for row in controlled_rows
        if re.search(r"& (?:ByteTrack|OC-SORT|Deep OC-SORT) &", row)
    ]
    for protocol_index, protocol in enumerate(PROTOCOLS):
        for tracker_index, tracker in enumerate(TRACKERS):
            row = data_rows[protocol_index * 3 + tracker_index] if len(data_rows) >= 6 else ""
            expected = []
            for method in controlled_methods:
                source = main_lookup[(protocol, tracker, method)]
                expected.append(
                    f"{f2(source['IDF1_equal_sequence_mean'])}/{integer(source['IDSW_total'])}"
                )
            check(
                f"controlled solver {protocol}/{tracker}",
                bool(row) and has_in_order(row, expected),
                " | ".join(expected),
            )

    # Paired all-50 intervals against the two principal competing linkers.
    paired_lookup = {
        (row["protocol"], row["tracker"], row["comparator"]): row
        for row in read_csv(report_root / "paired_linker_deltas.csv")
        if row["scope"] == "all50"
    }
    paired_text = (paper_root / "ivc_tables/temporal/paired_key_linkers.tex").read_text(encoding="utf-8")
    for protocol in PROTOCOLS:
        for tracker in TRACKERS:
            for comparator in ("geometry_reid_greedy_guard", "geometry_reid_hungarian"):
                source = paired_lookup[(protocol, tracker, comparator)]
                expected = (
                    f"{signed2(source['delta_IDF1_mean'])}"
                    f" [{signed2(source['delta_IDF1_ci_low'])},{signed2(source['delta_IDF1_ci_high'])}]"
                )
                plain = paired_text.replace("$", "").replace(" ", "")
                check(
                    f"paired CI {protocol}/{tracker}/{comparator}",
                    expected.replace(" ", "") in plain,
                    expected,
                )

    # Fixed-threshold accepted-link audit.
    risk_rows = read_csv(
        report_root / "results_raw/mmot_cached_solver_audit_v1/risk_coverage.csv"
    )
    risk_lookup = {
        (row["protocol"], row["tracker"], row["method"]): row
        for row in risk_rows
        if row["scope"] == "all_sequences" and abs(float(row["appearance_threshold"]) - 0.30) < 1e-12
    }
    risk_tex = (paper_root / "ivc_tables/temporal/error_coverage_fixed.tex").read_text(encoding="utf-8")
    for protocol in PROTOCOLS:
        for tracker in TRACKERS:
            for method in ("com3d_reciprocal_guard", "controlled_cost_reciprocal"):
                source = risk_lookup[(protocol, tracker, method)]
                expected = [
                    f"{100 * float(source['all_accepted_coverage']):.1f}\\%",
                    f"{100 * float(source['known_link_error_rate']):.1f}\\%",
                    f"{integer(source['accepted_correct'])}/{integer(source['accepted_false'])}",
                    integer(source["accepted_unknown"]),
                ]
                check(
                    f"link audit {protocol}/{tracker}/{method}",
                    has_in_order(re.sub(r"\s+", " ", risk_tex), expected),
                    " | ".join(expected),
                )

    # M3OT aggregate metrics and post-hoc accepted correct/false counts.
    m3ot_rows = read_csv(
        report_root / "results_raw/m3ot_linker_diagnostic_v2/m3ot_linker_comparison.csv"
    )
    m3ot_lookup = {(row["split"], row["tracker"], row["method"]): row for row in m3ot_rows}
    m3ot_tex = (paper_root / "ivc_tables/temporal/m3ot_transfer.tex").read_text(encoding="utf-8")
    split_names = {"development": "Development", "held_out": "Held-out"}
    m3ot_methods = (
        "no_refinement",
        "historical_geometry_first_reciprocal",
        "controlled_cost_greedy",
        "controlled_cost_reciprocal",
        "controlled_cost_partial_hungarian",
    )
    for split, split_label in split_names.items():
        for tracker, tracker_label in zip(TRACKERS[:2], ("ByteTrack", "OC-SORT")):
            metric_expected = []
            edge_expected = []
            for method in m3ot_methods:
                source = m3ot_lookup[(split, tracker, method)]
                metric_expected.append(f"{f2(source['IDF1'])}/{integer(source['IDSW'])}")
                if method != "no_refinement":
                    edge_expected.append(
                        f"{integer(source['accepted_correct'])}/{integer(source['accepted_false'])}"
                    )
            compact = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", m3ot_tex)
            compact = re.sub(r"\s+", " ", compact)
            check(
                f"M3OT metrics {split}/{tracker}",
                has_in_order(compact, metric_expected),
                f"{split_label}/{tracker_label}: " + " | ".join(metric_expected),
            )
            check(
                f"M3OT edge audit {split}/{tracker}",
                has_in_order(compact, edge_expected),
                f"{split_label}/{tracker_label}: " + " | ".join(edge_expected),
            )

    # Solver replay time and traced Python peak memory.
    runtime_rows = read_csv(report_root / "runtime_summary.csv")
    runtime_lookup = {(row["protocol"], row["tracker"], row["method"]): row for row in runtime_rows}
    runtime_tex = re.sub(
        r"\s+",
        " ",
        (paper_root / "ivc_tables/temporal/solver_runtime.tex").read_text(encoding="utf-8"),
    )
    for protocol in PROTOCOLS:
        for tracker in TRACKERS:
            hist = runtime_lookup[(protocol, tracker, "com3d_reciprocal_guard")]
            hung = runtime_lookup[(protocol, tracker, "geometry_reid_hungarian")]
            expected = [
                f1(hist["candidate_build_ms_sum"]),
                f"{f1(hist['solver_ms_sum_of_instance_means'])}/{float(hist['solver_peak_memory_max_bytes']) / 1_000_000:.1f}",
                f"{f1(hung['solver_ms_sum_of_instance_means'])}/{float(hung['solver_peak_memory_max_bytes']) / 1_000_000:.1f}",
            ]
            check(
                f"solver runtime {protocol}/{tracker}",
                has_in_order(runtime_tex, expected),
                " | ".join(expected),
            )

    # Recompute the headline no-refinement changes from full-precision values.
    abstract = (paper_root / "ivc_sections/00_abstract.tex").read_text(encoding="utf-8")
    results = (paper_root / "ivc_sections/06_results.tex").read_text(encoding="utf-8")
    for protocol in PROTOCOLS:
        idf1_delta = []
        idsw_delta = []
        for tracker in TRACKERS:
            base = main_lookup[(protocol, tracker, "no_refinement")]
            ours = main_lookup[(protocol, tracker, "com3d_reciprocal_guard")]
            idf1_delta.append(f2(float(ours["IDF1_equal_sequence_mean"]) - float(base["IDF1_equal_sequence_mean"])))
            idsw_delta.append(integer(int(base["IDSW_total"]) - int(ours["IDSW_total"])))
        check(
            f"headline deltas {protocol}",
            all(token in abstract and token in results for token in idf1_delta + idsw_delta),
            "IDF1 " + ", ".join(idf1_delta) + "; IDSW " + ", ".join(idsw_delta),
        )

    failed = [item for item in checks if not item["passed"]]
    payload = {
        "status": "PASS" if not failed else "FAIL",
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "checks": checks,
    }
    (report_root / "manuscript_number_verification.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Manuscript number verification",
        "",
        f"Status: **{payload['status']}**",
        "",
        f"Checks: {payload['checks_passed']}/{payload['checks_total']} passed.",
        "",
    ]
    if failed:
        lines.extend(["## Failures", ""])
        lines.extend(f"- {item['name']}: expected {item['detail']}" for item in failed)
    else:
        lines.append("All displayed table values and headline deltas covered by this verifier match the source CSVs after direct final-value rounding.")
    (report_root / "manuscript_number_verification.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: payload[key] for key in ("status", "checks_total", "checks_passed", "checks_failed")}))
    if failed:
        for item in failed:
            print(f"FAIL {item['name']}: {item['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
