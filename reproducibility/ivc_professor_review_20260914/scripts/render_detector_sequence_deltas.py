#!/usr/bin/env python3
"""Render full-release detector-input IDF1 changes from frozen MMOT results.

The script performs no tracking or tuning. It reads the completed per-sequence
evaluation CSV, verifies the expected common-input rows, and plots
CoM3D-ACE minus no-refinement IDF1 for every released sequence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


TRACKERS = ("bytetrack", "ocsort", "deepocsort")
TRACKER_LABELS = {
    "bytetrack": "ByteTrack",
    "ocsort": "OC-SORT",
    "deepocsort": "Deep OC-SORT",
}
METHODS = ("no_refinement", "com3d_reciprocal_guard")
FAMILY_ORDER = {"legacy12": 0, "confirmation38": 1}
POSITIVE = "#087F5B"
NEGATIVE = "#C2413B"
TIE = "#737B87"
MEAN = "#2457A6"
TEXT = "#172033"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-sequence-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def natural_key(value: str) -> tuple:
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validated_deltas(rows: list[dict[str, str]]) -> tuple[list[tuple[str, str]], dict[str, list[dict]]]:
    selected = [
        row
        for row in rows
        if row.get("tracker") in TRACKERS
        and row.get("method") in METHODS
        and row.get("IDF1") not in {None, ""}
        and row.get("valid_output", "True").lower() == "true"
    ]
    keyed: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in selected:
        key = (row["family"], row["sequence"], row["tracker"], row["method"])
        if key in keyed:
            raise RuntimeError(f"duplicate metric row: {key}")
        keyed[key] = row

    sequences = sorted(
        {(row["family"], row["sequence"]) for row in selected},
        key=lambda item: (FAMILY_ORDER.get(item[0], 99), natural_key(item[1])),
    )
    if len(sequences) != 50:
        raise RuntimeError(f"expected 50 released sequences, found {len(sequences)}")
    if sum(family == "legacy12" for family, _ in sequences) != 12:
        raise RuntimeError("legacy12 partition is not 12 sequences")
    if sum(family == "confirmation38" for family, _ in sequences) != 38:
        raise RuntimeError("confirmation38 partition is not 38 sequences")

    output: dict[str, list[dict]] = {tracker: [] for tracker in TRACKERS}
    for tracker in TRACKERS:
        for family, sequence in sequences:
            baseline_key = (family, sequence, tracker, "no_refinement")
            method_key = (family, sequence, tracker, "com3d_reciprocal_guard")
            if baseline_key not in keyed or method_key not in keyed:
                raise RuntimeError(f"missing common-input row: {family}/{sequence}/{tracker}")
            baseline = float(keyed[baseline_key]["IDF1"])
            method = float(keyed[method_key]["IDF1"])
            delta = method - baseline
            outcome = "improved" if delta > 1e-12 else "worsened" if delta < -1e-12 else "tied"
            output[tracker].append(
                {
                    "family": family,
                    "sequence": sequence,
                    "tracker": tracker,
                    "no_refinement_idf1": baseline,
                    "com3d_ace_idf1": method,
                    "delta_idf1_pp": delta,
                    "outcome": outcome,
                }
            )
    return sequences, output


def write_delta_csv(path: Path, by_tracker: dict[str, list[dict]]) -> None:
    fields = (
        "family",
        "sequence",
        "tracker",
        "no_refinement_idf1",
        "com3d_ace_idf1",
        "delta_idf1_pp",
        "outcome",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for tracker in TRACKERS:
            writer.writerows(by_tracker[tracker])


def render(path_png: Path, path_pdf: Path, sequences: list[tuple[str, str]], by_tracker: dict[str, list[dict]]) -> dict:
    x = np.arange(len(sequences))
    labels = [sequence.removeprefix("data") for _, sequence in sequences]
    figure, axes = plt.subplots(3, 1, figsize=(7.25, 5.65), sharex=True, constrained_layout=True)
    summary = {}

    for index, (axis, tracker) in enumerate(zip(axes, TRACKERS)):
        values = np.asarray([row["delta_idf1_pp"] for row in by_tracker[tracker]], dtype=float)
        colors = [POSITIVE if value > 1e-12 else NEGATIVE if value < -1e-12 else TIE for value in values]
        counts = {
            "improved": int(np.sum(values > 1e-12)),
            "tied": int(np.sum(np.abs(values) <= 1e-12)),
            "worsened": int(np.sum(values < -1e-12)),
        }
        mean = float(values.mean())
        summary[tracker] = {"mean_delta_idf1_pp": mean, **counts}

        axis.axvspan(-0.5, 11.5, color="#EEF1F4", zorder=0)
        axis.bar(x, values, width=0.78, color=colors, edgecolor="none", zorder=2)
        axis.axhline(0.0, color="#454B54", linewidth=0.7, zorder=3)
        axis.axhline(mean, color=MEAN, linewidth=0.9, linestyle=(0, (4, 2)), zorder=3)
        axis.axvline(11.5, color="#8B929C", linewidth=0.7, linestyle=(0, (2, 2)), zorder=3)
        axis.grid(axis="y", color="#D9DEE5", linewidth=0.45, zorder=0)
        axis.set_axisbelow(True)
        axis.set_ylabel("Delta IDF1 (pp)", fontsize=7.5, color=TEXT)
        axis.tick_params(axis="y", labelsize=6.8, colors=TEXT)
        axis.tick_params(axis="x", length=0)
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#9097A1")
        axis.set_title(
            f"{TRACKER_LABELS[tracker]}: mean {mean:+.2f} pp | "
            f"{counts['improved']} improved, {counts['tied']} tied, {counts['worsened']} worsened",
            loc="left",
            fontsize=8.2,
            fontweight="bold",
            color=TEXT,
            pad=3,
        )
        if index == 0:
            axis.text(5.5, 0.98, "Legacy12", transform=axis.get_xaxis_transform(), ha="center", va="top", fontsize=6.5, color="#555D68")
            axis.text(30.5, 0.98, "Confirmation38", transform=axis.get_xaxis_transform(), ha="center", va="top", fontsize=6.5, color="#555D68")
        for position, value in enumerate(values):
            if value < -1e-12 and index < len(TRACKERS) - 1:
                axis.annotate(
                    labels[position],
                    (position, value),
                    xytext=(0, -3),
                    textcoords="offset points",
                    ha="center",
                    va="top",
                    rotation=90,
                    fontsize=4.8,
                    color=NEGATIVE,
                )

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=90, fontsize=4.9, color=TEXT)
    axes[-1].set_xlabel("MMOT sequence (fixed partition order)", fontsize=7.5, color=TEXT, labelpad=3)
    figure.suptitle(
        "Per-sequence detector-input IDF1 change: CoM3D-ACE minus no refinement",
        fontsize=9.5,
        fontweight="bold",
        color=TEXT,
    )
    figure.savefig(path_png, dpi=400, bbox_inches="tight", facecolor="white")
    figure.savefig(path_pdf, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return summary


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_rows(args.per_sequence_csv)
    sequences, by_tracker = validated_deltas(rows)

    delta_csv = args.output_dir / "detector_sequence_idf1_deltas.csv"
    figure_png = args.output_dir / "mmot_detector_sequence_idf1_delta.png"
    figure_pdf = args.output_dir / "mmot_detector_sequence_idf1_delta.pdf"
    write_delta_csv(delta_csv, by_tracker)
    summary = render(figure_png, figure_pdf, sequences, by_tracker)

    manifest = {
        "source_csv": str(args.per_sequence_csv.resolve()),
        "source_sha256": sha256(args.per_sequence_csv),
        "operation": "IDF1(CoM3D-ACE) - IDF1(no refinement), per sequence",
        "unit": "percentage points",
        "input_condition": "one shared official MMOT YOLO11L-3ch detector cache",
        "aggregation": "50 per-sequence differences; panel means are equal-sequence means",
        "sequence_order": [
            {"family": family, "sequence": sequence} for family, sequence in sequences
        ],
        "summary": summary,
        "outputs": [path.name for path in (delta_csv, figure_png, figure_pdf)],
        "experiment_status": "rendered from completed frozen results; no new training or tracking",
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
