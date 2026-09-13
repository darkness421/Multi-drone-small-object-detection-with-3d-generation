#!/usr/bin/env python3
"""Generate paper-ready CoM3D-ACE tables directly from frozen CSV artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


TRACKERS = ("bytetrack", "ocsort", "deepocsort")
TRACKER_LABEL = {
    "bytetrack": "ByteTrack",
    "ocsort": "OC-SORT",
    "deepocsort": "Deep OC-SORT",
}
METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_hungarian",
    "aflink_official",
    "com3d_reciprocal_guard",
)
METHOD_LABEL = {
    "no_refinement": "None",
    "geometry_greedy": "Geometry greedy",
    "geometry_reciprocal_guard": "Geometry reciprocal",
    "geometry_reid_greedy_guard": "Geometry+ReID greedy",
    "geometry_reid_hungarian": "Partial Hungarian",
    "geometry_reid_reciprocal_no_guard": "+ReID reciprocal, no guard",
    "aflink_official": "AFLink (official)",
    "com3d_reciprocal_guard": "CoM3D-ACE",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_records(frame: pd.DataFrame) -> list[dict]:
    """Convert DataFrame rows to strict-JSON records with null for missing values."""
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def valid_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def aggregate_row(frame: pd.DataFrame, scope: str, tracker: str, method: str) -> pd.Series:
    rows = frame[
        (frame["scope"] == scope)
        & (frame["tracker"] == tracker)
        & (frame["method"] == method)
    ]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one row for {scope}/{tracker}/{method}, found {len(rows)}")
    return rows.iloc[0]


def fmt_score(value, bold: bool = False) -> str:
    if pd.isna(value):
        return "--"
    text = f"{float(value):.2f}"
    return f"\\textbf{{{text}}}" if bold else text


def fmt_count(value, bold: bool = False) -> str:
    if pd.isna(value):
        return "--"
    text = f"{int(value):,}"
    return f"\\textbf{{{text}}}" if bold else text


def build_main_table(frame: pd.DataFrame, output: Path) -> pd.DataFrame:
    records = []
    for tracker in TRACKERS:
        for method in METHODS:
            row = aggregate_row(frame, "all_sequences", tracker, method)
            valid = valid_bool(row["valid_output"])
            records.append({
                "tracker": tracker,
                "method": method,
                "valid_output": valid,
                "HOTA": row.get("HOTA") if valid else None,
                "AssA": row.get("AssA") if valid else None,
                "IDF1": row.get("IDF1") if valid else None,
                "IDSW": row.get("IDSW") if valid else None,
                "invalid_sequences": int(row.get("invalid_sequences", 0)),
            })
    result = pd.DataFrame(records)
    result.to_csv(output.with_suffix(".csv"), index=False)

    lines = [
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Upstream & Refiner & HOTA & AssA & IDF1 & IDSW \\\\",
        "\\midrule",
    ]
    for tracker_index, tracker in enumerate(TRACKERS):
        selected = result[(result["tracker"] == tracker) & result["valid_output"]]
        maxima = {metric: selected[metric].max() for metric in ("HOTA", "AssA", "IDF1")}
        min_idsw = selected["IDSW"].min()
        for row_index, method in enumerate(METHODS):
            row = result[(result["tracker"] == tracker) & (result["method"] == method)].iloc[0]
            tracker_text = TRACKER_LABEL[tracker] if row_index == 0 else ""
            if row["valid_output"]:
                values = [
                    fmt_score(row[metric], abs(row[metric] - maxima[metric]) < 1e-10)
                    for metric in ("HOTA", "AssA", "IDF1")
                ]
                values.append(fmt_count(row["IDSW"], abs(row["IDSW"] - min_idsw) < 1e-10))
            else:
                values = ["--", "--", "--", "--"]
            method_text = METHOD_LABEL[method]
            if method == "com3d_reciprocal_guard":
                method_text = "\\textbf{CoM3D-ACE}"
            lines.append(
                f"{tracker_text} & {method_text} & " + " & ".join(values) + " \\\\"
            )
        if tracker_index != len(TRACKERS) - 1:
            lines.append("\\midrule")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def paired(frame: pd.DataFrame, scope: str, tracker: str, metric: str, method: str = "com3d_reciprocal_guard") -> pd.Series:
    rows = frame[
        (frame["scope"] == scope)
        & (frame["tracker"] == tracker)
        & (frame["method"] == method)
        & (frame["metric"] == metric)
    ]
    if len(rows) != 1:
        raise RuntimeError(f"Expected paired row {scope}/{tracker}/{method}/{metric}")
    return rows.iloc[0]


def build_confirmation_table(
    oracle_paired: pd.DataFrame,
    detector_paired: pd.DataFrame,
    oracle_agg: pd.DataFrame,
    detector_agg: pd.DataFrame,
    output: Path,
) -> pd.DataFrame:
    records = []
    for input_name, paired_frame, agg in (
        ("Oracle AABB", oracle_paired, oracle_agg),
        ("Official detector", detector_paired, detector_agg),
    ):
        for tracker in TRACKERS:
            rows = {metric: paired(paired_frame, "confirmation38", tracker, metric) for metric in ("HOTA", "AssA", "IDF1")}
            base = aggregate_row(agg, "confirmation38", tracker, "no_refinement")
            ours = aggregate_row(agg, "confirmation38", tracker, "com3d_reciprocal_guard")
            idf1 = rows["IDF1"]
            records.append({
                "input": input_name,
                "tracker": tracker,
                "delta_HOTA": rows["HOTA"]["mean_delta"],
                "delta_AssA": rows["AssA"]["mean_delta"],
                "delta_IDF1": idf1["mean_delta"],
                "IDF1_ci_lower": idf1["bootstrap_ci95_lower"],
                "IDF1_ci_upper": idf1["bootstrap_ci95_upper"],
                "delta_IDSW_total": int(ours["IDSW"] - base["IDSW"]),
                "improved": int(idf1["improved"]),
                "unchanged": int(idf1["unchanged"]),
                "worsened": int(idf1["worsened"]),
            })
    result = pd.DataFrame(records)
    result.to_csv(output.with_suffix(".csv"), index=False)
    lines = [
        "\\begin{tabular}{llrrrrl}",
        "\\toprule",
        "Input & Tracker & $\\Delta$HOTA & $\\Delta$AssA & $\\Delta$IDF1 (95\\% CI) & $\\Delta$IDSW & I/T/W \\\\",
        "\\midrule",
    ]
    input_labels = {"Oracle AABB": "Oracle", "Official detector": "Official det."}
    for input_index, input_name in enumerate(("Oracle AABB", "Official detector")):
        subset = result[result["input"] == input_name]
        for row_index, (_, row) in enumerate(subset.iterrows()):
            input_text = input_labels[input_name] if row_index == 0 else ""
            interval = f"{row['delta_IDF1']:+.2f} [{row['IDF1_ci_lower']:.2f}, {row['IDF1_ci_upper']:.2f}]"
            lines.append(
                f"{input_text} & {TRACKER_LABEL[row['tracker']]} & {row['delta_HOTA']:+.2f} & "
                f"{row['delta_AssA']:+.2f} & {interval} & {int(row['delta_IDSW_total']):+,} & "
                f"{int(row['improved'])}/{int(row['unchanged'])}/{int(row['worsened'])} \\\\"
            )
        if input_index == 0:
            lines.append("\\midrule")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def build_ablation_table(frame: pd.DataFrame, main_frame: pd.DataFrame, output: Path) -> pd.DataFrame:
    methods = (
        "no_refinement",
        "geometry_reciprocal_guard",
        "geometry_reid_reciprocal_no_guard",
        "com3d_reciprocal_guard",
        "geometry_reid_greedy_guard",
        "geometry_reid_hungarian",
    )
    records = []
    for method in methods:
        record = {"method": method}
        for tracker in TRACKERS:
            source = main_frame if method == "geometry_reid_hungarian" else frame
            row = aggregate_row(source, "all_sequences", tracker, method)
            record[f"{tracker}_IDF1"] = row["IDF1"]
            record[f"{tracker}_IDSW"] = int(row["IDSW"])
        records.append(record)
    result = pd.DataFrame(records)
    result.to_csv(output.with_suffix(".csv"), index=False)
    lines = [
        "\\begin{tabular}{lrr@{\\hspace{7pt}}rr@{\\hspace{7pt}}rr}",
        "\\toprule",
        "& \\multicolumn{2}{c}{ByteTrack} & \\multicolumn{2}{c}{OC-SORT} & \\multicolumn{2}{c}{Deep OC-SORT} \\\\",
        "Variant & IDF1 & IDSW & IDF1 & IDSW & IDF1 & IDSW \\\\",
        "\\midrule",
    ]
    for _, row in result.iterrows():
        label = METHOD_LABEL[row["method"]]
        lines.append(
            f"{label} & {row['bytetrack_IDF1']:.2f} & {int(row['bytetrack_IDSW']):,} & "
            f"{row['ocsort_IDF1']:.2f} & {int(row['ocsort_IDSW']):,} & "
            f"{row['deepocsort_IDF1']:.2f} & {int(row['deepocsort_IDSW']):,} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def build_m3ot_table(frame: pd.DataFrame, output: Path) -> pd.DataFrame:
    records = []
    for split in ("development", "held_out"):
        for tracker in ("bytetrack", "ocsort"):
            rows = frame[(frame["split"] == split) & (frame["tracker"] == tracker)]
            records.append({
                "split": split,
                "tracker": tracker,
                "sequence_count": len(rows),
                "baseline_HOTA": rows["baseline_HOTA"].mean(),
                "refined_HOTA": rows["refined_HOTA"].mean(),
                "baseline_IDF1": rows["baseline_IDF1"].mean(),
                "refined_IDF1": rows["refined_IDF1"].mean(),
                "delta_IDF1": rows["delta_IDF1"].mean(),
                "baseline_IDSW": int(rows["baseline_IDSW"].sum()),
                "refined_IDSW": int(rows["refined_IDSW"].sum()),
                "accepted_correct": int(rows["accepted_correct"].sum()),
                "accepted_false": int(rows["accepted_false"].sum()),
                "correct_fragment_opportunities": int(rows["correct_fragment_opportunities_gap_le_30"].sum()),
            })
    result = pd.DataFrame(records)
    result.to_csv(output.with_suffix(".csv"), index=False)
    metric_lines = [
        "\\begin{tabular}{llccc}",
        "\\toprule",
        "Split & Tracker & HOTA base$\\rightarrow$ref. & IDF1 base$\\rightarrow$ref. & IDSW base$\\rightarrow$ref. \\\\",
        "\\midrule",
    ]
    audit_lines = [
        "\\begin{tabular}{llrrr}",
        "\\toprule",
        "Split & Tracker & Correct links & False links & Opportunities \\\\",
        "\\midrule",
    ]
    for split_index, split in enumerate(("development", "held_out")):
        subset = result[result["split"] == split]
        for row_index, (_, row) in enumerate(subset.iterrows()):
            split_text = "Development" if split == "development" else "Held-out"
            split_text = split_text if row_index == 0 else ""
            metric_lines.append(
                f"{split_text} & {TRACKER_LABEL[row['tracker']]} & "
                f"{row['baseline_HOTA']:.2f}$\\rightarrow${row['refined_HOTA']:.2f} & "
                f"{row['baseline_IDF1']:.2f}$\\rightarrow${row['refined_IDF1']:.2f} & "
                f"{int(row['baseline_IDSW'])}$\\rightarrow${int(row['refined_IDSW'])} \\\\"
            )
            audit_lines.append(
                f"{split_text} & {TRACKER_LABEL[row['tracker']]} & "
                f"{int(row['accepted_correct'])} & "
                f"{int(row['accepted_false'])} & "
                f"{int(row['correct_fragment_opportunities'])} \\\\"
            )
        if split_index == 0:
            metric_lines.append("\\midrule")
            audit_lines.append("\\midrule")
    metric_lines.extend(["\\bottomrule", "\\end{tabular}"])
    audit_lines.extend(["\\bottomrule", "\\end{tabular}"])
    output.write_text(
        "\n".join(metric_lines)
        + "\n\\par\\smallskip\n"
        + "\n".join(audit_lines)
        + "\n",
        encoding="utf-8",
    )
    return result


def build_size_table(frame: pd.DataFrame, output: Path) -> pd.DataFrame:
    order = ("all_sequences", "legacy12", "confirmation38")
    result = frame.set_index("scope").loc[list(order)].reset_index()
    result.to_csv(output.with_suffix(".csv"), index=False)
    lines = [
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Partition & Boxes & $A<32^2$ & $32^2\\le A<96^2$ & Side $<16$ & Median side \\\\",
        "\\midrule",
    ]
    labels = {"all_sequences": "All 50", "legacy12": "Legacy 12", "confirmation38": "Confirm. 38"}
    for _, row in result.iterrows():
        lines.append(
            f"{labels[row['scope']]} & {int(row['box_count']):,} & "
            f"{100*row['area_tiny_lt_32sq_fraction']:.1f}\\% & "
            f"{100*row['area_small_32sq_to_96sq_fraction']:.1f}\\% & "
            f"{100*row['short_lt_16px_fraction']:.1f}\\% & {row['short_side_p50_px']:.0f} px \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def build_runtime_table(reid: pd.DataFrame, graph: pd.DataFrame, output: Path) -> pd.DataFrame:
    result = reid.merge(graph, on="tracker", suffixes=("_reid", "_graph"))
    result["total_overhead_seconds"] = result["runtime_seconds_sum"] + result["graph_seconds_sum"]
    result["total_overhead_ms_per_frame"] = 1000.0 * result["total_overhead_seconds"] / 5466.0
    result.to_csv(output.with_suffix(".csv"), index=False)
    lines = [
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Tracker & Crops & Desc. & ReID (s) & Cand. & Graph (s) & Total (ms/fr.) \\\\",
        "\\midrule",
    ]
    for _, row in result.iterrows():
        lines.append(
            f"{TRACKER_LABEL[row['tracker']]} & {int(row['sampled_crops']):,} & "
            f"{int(row['descriptors']):,} & {row['runtime_seconds_sum']:.1f} & "
            f"{int(row['candidate_edges']):,} & {row['graph_seconds_sum']:.2f} & "
            f"{row['total_overhead_ms_per_frame']:.1f} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def build_fixed_error_table(link: pd.DataFrame, trajectory: pd.DataFrame, output: Path) -> pd.DataFrame:
    fixed = {"com3d_reciprocal_guard": 0.30, "geometry_reid_hungarian": 0.30, "aflink_official": 0.05}
    records = []
    for tracker in TRACKERS:
        for method, threshold in fixed.items():
            links = link[
                (link["scope"] == "all_sequences") & (link["tracker"] == tracker)
                & (link["method"] == method) & ((link["threshold"] - threshold).abs() < 1e-10)
            ].iloc[0]
            trajectories = trajectory[
                (trajectory["scope"] == "all_sequences") & (trajectory["tracker"] == tracker)
                & (trajectory["method"] == method) & ((trajectory["threshold"] - threshold).abs() < 1e-10)
            ].iloc[0]
            records.append({
                "tracker": tracker,
                "method": method,
                "threshold": threshold,
                "accepted_coverage": links["all_accepted_coverage"],
                "known_error_rate": links["accepted_link_error_rate"],
                "accepted_unknown": int(links["accepted_unknown"]),
                "trajectory_valid": valid_bool(trajectories["valid_output"]),
                "IDF1": trajectories.get("IDF1"),
            })
    result = pd.DataFrame(records)
    result.to_csv(output.with_suffix(".csv"), index=False)
    lines = [
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Tracker & Refiner & Gate & Coverage & Link error & IDF1 \\\\",
        "\\midrule",
    ]
    for tracker_index, tracker in enumerate(TRACKERS):
        subset = result[result["tracker"] == tracker]
        for row_index, (_, row) in enumerate(subset.iterrows()):
            tracker_text = TRACKER_LABEL[tracker] if row_index == 0 else ""
            idf1 = f"{row['IDF1']:.2f}" if row["trajectory_valid"] and not pd.isna(row["IDF1"]) else "--"
            lines.append(
                f"{tracker_text} & {METHOD_LABEL[row['method']]} & {row['threshold']:.2f} & "
                f"{100*row['accepted_coverage']:.1f}\\% & {100*row['known_error_rate']:.1f}\\% & {idf1} \\\\"
            )
        if tracker_index != len(TRACKERS) - 1:
            lines.append("\\midrule")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main() -> int:
    args = parse_args()
    root = args.experiment_root
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    sources = {
        "oracle_aggregate": root / "results_raw/e1_direct_full50_v2_equal/results/linker_comparison_aggregate.csv",
        "oracle_paired": root / "results_raw/derived/e1_direct_full50_v2_equal/paired_sequence_summary.csv",
        "oracle_ablation": root / "results_raw/e1_direct_full50_v2_equal/results/temporal_ablation.csv",
        "detector_aggregate": root / "results_raw/e3_temporal_full50_v2_equal/results/detector_input_temporal_results.csv",
        "detector_paired": root / "results_raw/derived/e3_temporal_full50_v2_equal/paired_sequence_summary.csv",
        "m3ot": root / "results_raw/e2_m3ot_failure_attempt2/m3ot_sequence_diagnostics.csv",
        "sizes": root / "results_raw/derived/e1_direct_full50_v2_equal_sizes/native_box_size_distribution.csv",
        "reid_runtime": root / "results_raw/e2_runtime_reid_full50_v1/reid_runtime_summary.csv",
        "graph_runtime": root / "results_raw/e2_runtime_graph_full50_v1/graph_runtime_summary.csv",
        "error_links": root / "results_raw/e2_error_coverage_direct_full50_v1/link_error_coverage.csv",
        "error_trajectory": root / "results_raw/e2_error_coverage_direct_full50_v1/trajectory_error_coverage_aggregate.csv",
    }
    frames = {name: pd.read_csv(path) for name, path in sources.items()}

    oracle_table = build_main_table(frames["oracle_aggregate"], output / "table_oracle_full50.tex")
    detector_table = build_main_table(frames["detector_aggregate"], output / "table_detector_full50.tex")
    confirmation = build_confirmation_table(
        frames["oracle_paired"], frames["detector_paired"],
        frames["oracle_aggregate"], frames["detector_aggregate"],
        output / "table_confirmation38.tex",
    )
    ablation = build_ablation_table(
        frames["oracle_ablation"], frames["oracle_aggregate"],
        output / "table_temporal_ablation.tex",
    )
    m3ot = build_m3ot_table(frames["m3ot"], output / "table_m3ot_transfer.tex")
    sizes = build_size_table(frames["sizes"], output / "table_mmot_sizes.tex")
    runtime = build_runtime_table(frames["reid_runtime"], frames["graph_runtime"], output / "table_runtime.tex")
    error = build_fixed_error_table(
        frames["error_links"], frames["error_trajectory"], output / "table_error_coverage_fixed.tex"
    )

    key_numbers = {
        "oracle_full50": json_records(oracle_table),
        "detector_full50": json_records(detector_table),
        "confirmation38": json_records(confirmation),
        "temporal_ablation": json_records(ablation),
        "m3ot_transfer": json_records(m3ot),
        "sizes": json_records(sizes),
        "runtime": json_records(runtime),
        "fixed_error_coverage": json_records(error),
    }
    (output / "key_numbers.json").write_text(
        json.dumps(key_numbers, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    manifest = {
        "status": "COMPLETE",
        "policy": "All table values are parsed from frozen CSVs; no manual result entry.",
        "sources": {
            name: {"path": str(path.resolve()), "sha256": sha256(path)} for name, path in sources.items()
        },
        "outputs": {
            path.name: {"path": str(path.resolve()), "sha256": sha256(path)}
            for path in sorted(output.iterdir()) if path.is_file()
        },
        "rounding": "Display-only rounding from full-precision source values.",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "COMPLETE", "output_dir": str(output), "files": len(list(output.iterdir()))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
