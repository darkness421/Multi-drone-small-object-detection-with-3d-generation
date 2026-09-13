#!/usr/bin/env python3
"""Validate and finalize a completed MMOT error--coverage computation.

The original computation writes all CSV files before writing its manifest.
This utility validates the complete Cartesian product and records hashes when
that final metadata write was interrupted by a missing source manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


TRACKERS = ("bytetrack", "ocsort", "deepocsort")
METHODS = ("com3d_reciprocal_guard", "geometry_reid_hungarian", "aflink_official")
METHOD_LABELS = {
    "com3d_reciprocal_guard": "CoM3D-ACE",
    "geometry_reid_hungarian": "Partial Hungarian",
    "aflink_official": "AFLink",
}
COLORS = {
    "com3d_reciprocal_guard": "#16865a",
    "geometry_reid_hungarian": "#285f9e",
    "aflink_official": "#c25a33",
}
MARKERS = {
    "com3d_reciprocal_guard": "o",
    "geometry_reid_hungarian": "s",
    "aflink_official": "^",
}
FIXED_THRESHOLD = {
    "com3d_reciprocal_guard": 0.30,
    "geometry_reid_hungarian": 0.30,
    "aflink_official": 0.05,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--failed-log", type=Path)
    parser.add_argument("--figure-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(input_dir: Path) -> dict:
    names = (
        "trajectory_error_coverage_per_sequence.csv",
        "trajectory_error_coverage_aggregate.csv",
        "link_error_coverage.csv",
        "accepted_links_by_curve_point.csv",
        "aflink_score_runtime.csv",
    )
    frames = {name: pd.read_csv(input_dir / name) for name in names}
    per_sequence = frames[names[0]]
    link = frames[names[2]]

    expected_family_counts = {"legacy12": 12, "confirmation38": 38}
    observed = (
        per_sequence.groupby(["family", "tracker", "method", "parameter", "threshold"])
        .size()
        .to_dict()
    )
    expected_combinations = 0
    errors: list[str] = []
    for family, sequence_count in expected_family_counts.items():
        for tracker in TRACKERS:
            for method in METHODS:
                values = sorted(
                    link.loc[
                        (link["scope"] == family)
                        & (link["tracker"] == tracker)
                        & (link["method"] == method),
                        "threshold",
                    ].unique()
                )
                if len(values) != 6:
                    errors.append(f"{family}/{tracker}/{method}: expected 6 thresholds, got {values}")
                parameter = "aflink_cost" if method == "aflink_official" else "appearance_cosine"
                for threshold in values:
                    expected_combinations += 1
                    count = observed.get((family, tracker, method, parameter, threshold), 0)
                    if count != sequence_count:
                        errors.append(
                            f"{family}/{tracker}/{method}/{threshold}: "
                            f"expected {sequence_count} sequences, got {count}"
                        )

    expected_rows = 50 * len(TRACKERS) * len(METHODS) * 6
    if len(per_sequence) != expected_rows:
        errors.append(f"per-sequence rows: expected {expected_rows}, got {len(per_sequence)}")
    if len(link) != 3 * len(TRACKERS) * len(METHODS) * 6:
        errors.append(f"link rows: expected 162, got {len(link)}")
    if len(frames["aflink_score_runtime.csv"]) != 789:
        errors.append(
            "AFLink runtime rows: expected 789, got "
            f"{len(frames['aflink_score_runtime.csv'])}"
        )
    if errors:
        raise RuntimeError("; ".join(errors))
    return {
        "row_counts": {name: len(frame) for name, frame in frames.items()},
        "expected_per_sequence_rows": expected_rows,
        "validated_family_counts": expected_family_counts,
        "validated_threshold_combinations": expected_combinations,
    }


def render(input_dir: Path, figure_dir: Path) -> list[str]:
    link = pd.read_csv(input_dir / "link_error_coverage.csv")
    trajectory = pd.read_csv(input_dir / "trajectory_error_coverage_aggregate.csv")
    link = link[link["scope"] == "all_sequences"].copy()
    trajectory = trajectory[trajectory["scope"] == "all_sequences"].copy()
    joined = link.merge(
        trajectory[["tracker", "method", "parameter", "threshold", "IDF1", "valid_output"]],
        on=["tracker", "method", "parameter", "threshold"],
        suffixes=("_link", "_trajectory"),
    )

    fig, axes = plt.subplots(2, 3, figsize=(12.0, 6.7), constrained_layout=True)
    for column, tracker in enumerate(TRACKERS):
        for method in METHODS:
            rows = joined[(joined["tracker"] == tracker) & (joined["method"] == method)].sort_values("threshold")
            x = 100.0 * rows["all_accepted_coverage"]
            error = 100.0 * rows["accepted_link_error_rate"]
            valid = rows["valid_output_trajectory"].astype(bool)
            axes[0, column].plot(
                x, error, color=COLORS[method], marker=MARKERS[method], linewidth=1.7,
                markersize=5, label=METHOD_LABELS[method],
            )
            axes[1, column].plot(
                x[valid], rows.loc[valid, "IDF1"], color=COLORS[method], marker=MARKERS[method],
                linewidth=1.7, markersize=5, label=METHOD_LABELS[method],
            )
            fixed = rows[(rows["threshold"] - FIXED_THRESHOLD[method]).abs() < 1e-9]
            if not fixed.empty:
                axes[0, column].scatter(
                    100.0 * fixed["all_accepted_coverage"],
                    100.0 * fixed["accepted_link_error_rate"],
                    s=95, facecolors="none", edgecolors=COLORS[method], linewidths=2.0, zorder=5,
                )
                fixed_valid = fixed[fixed["valid_output_trajectory"].astype(bool)]
                if not fixed_valid.empty:
                    axes[1, column].scatter(
                        100.0 * fixed_valid["all_accepted_coverage"], fixed_valid["IDF1"],
                        s=95, facecolors="none", edgecolors=COLORS[method], linewidths=2.0, zorder=5,
                    )
        title = {"bytetrack": "ByteTrack", "ocsort": "OC-SORT", "deepocsort": "Deep OC-SORT"}[tracker]
        axes[0, column].set_title(title, fontsize=11, fontweight="bold")
        axes[0, column].set_xlabel("Accepted-link coverage (%)")
        axes[0, column].set_ylabel("Error among GT-auditable links (%)" if column == 0 else "")
        axes[1, column].set_xlabel("Accepted-link coverage (%)")
        axes[1, column].set_ylabel("Equal-sequence mean IDF1" if column == 0 else "")
        for row in range(2):
            axes[row, column].grid(True, alpha=0.22, linewidth=0.7)
            axes[row, column].tick_params(labelsize=8.5)
    axes[0, 0].legend(frameon=False, fontsize=8.5, loc="best")
    fig.suptitle(
        "MMOT full-test descriptive error--coverage audit (fixed gates circled)",
        fontsize=13, fontweight="bold",
    )
    figure_dir.mkdir(parents=True, exist_ok=True)
    png = figure_dir / "mmot_error_coverage.png"
    pdf = figure_dir / "mmot_error_coverage.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [str(png.resolve()), str(pdf.resolve())]


def main() -> int:
    args = parse_args()
    validation = validate(args.input_dir)
    figures = render(args.input_dir, args.figure_dir)
    files = sorted(args.input_dir.glob("*.csv"))
    manifest = {
        "status": "COMPLETE_AFTER_METADATA_RECOVERY",
        "claim_scope": "Descriptive full-test error--coverage audit; no threshold selection.",
        "recovery_reason": (
            "The computation wrote all expected CSVs, then failed while hashing the absent manifest "
            "of an intentionally preserved interrupted cache-producing run. This utility validates "
            "the full Cartesian product and records the complete-run manifest used for provenance."
        ),
        "fixed_operating_points": FIXED_THRESHOLD,
        "coverage_denominator": (
            "Source tracklets with at least one temporally admissible non-overlapping successor "
            "within 30 frames; fixed across curve points."
        ),
        "error_denominator": "Accepted links with post-hoc auditable GT identities.",
        "ground_truth_use": "Post-hoc link audit and trajectory metrics only.",
        "validation": validation,
        "source_manifest": {
            "path": str(args.source_manifest.resolve()),
            "sha256": sha256(args.source_manifest),
        },
        "failed_computation_log": (
            {"path": str(args.failed_log.resolve()), "sha256": sha256(args.failed_log)}
            if args.failed_log and args.failed_log.exists() else None
        ),
        "outputs": {
            path.name: {"path": str(path.resolve()), "sha256": sha256(path)} for path in files
        },
        "figures": figures,
    }
    manifest_path = args.input_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.figure_dir / "manifest.json").write_text(
        json.dumps({
            "status": "COMPLETE",
            "source_manifest": str(manifest_path.resolve()),
            "source_manifest_sha256": sha256(manifest_path),
            "outputs": figures,
            "fixed_operating_points_are_circled": True,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": manifest["status"], **validation, "figures": figures}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
