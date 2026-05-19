"""Build a compact PNG dashboard for server detector baselines."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from runtime.config import resolve_path


FAMILY_COLORS = {
    "YOLO": "#4C78A8",
    "LRDS-YOLO": "#72B7B2",
    "RT-DETR": "#F58518",
    "D-FINE": "#54A24B",
    "DETR": "#B279A2",
    "Other": "#9D755D",
}

SIZE_MARKERS = {
    "nano": "o",
    "small": "s",
    "medium": "^",
    "large": "D",
    "xlarge": "X",
    "base": "P",
    "r18": "v",
    "unknown": "o",
}

SIZE_ORDER = {
    "nano": 0,
    "small": 1,
    "medium": 2,
    "large": 3,
    "xlarge": 4,
    "base": 5,
    "r18": 6,
    "lightweight": 1,
    "unknown": 99,
    "": 99,
}


DATASET_ORDER = {
    "VisDrone2019-DET": 0,
    "UAVDT": 1,
    "CoM3D-MarineCity": 2,
    "unknown": 99,
    "": 99,
}


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_rows(path: str | Path) -> list[dict[str, str]]:
    path = resolve_path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_key(row: dict[str, str], include_dataset: bool) -> str:
    method = row.get("method") or row.get("model") or "unknown"
    if include_dataset:
        return f"{row.get('dataset') or 'unknown'}::{method}"
    return method


def grouped_values(rows: list[dict[str, str]], metric: str, include_dataset: bool = False) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = as_float(row.get(metric))
        if value is not None:
            groups[row_key(row, include_dataset)].append(value)
    return dict(groups)


def metadata_by_method(rows: list[dict[str, str]], include_dataset: bool = False) -> dict[str, dict[str, str]]:
    meta: dict[str, dict[str, str]] = {}
    for row in rows:
        meta.setdefault(row_key(row, include_dataset), row)
    return meta


def version_number(value: str) -> int:
    match = re.search(r"(\d+)", value or "")
    return int(match.group(1)) if match else 999


def sort_methods(labels: list[str], meta: dict[str, dict[str, str]]) -> list[str]:
    def key(label: str) -> tuple[int, int, int, int, str]:
        row = meta.get(label, {})
        dataset = row.get("dataset", "")
        family = row.get("detector_family", "")
        family_order = 0 if family == "YOLO" else 1
        version = row.get("yolo_version") or row.get("model_version") or ""
        size = row.get("param_size_group") or row.get("model_scale") or ""
        return (DATASET_ORDER.get(dataset, 50), family_order, version_number(version), SIZE_ORDER.get(size, 99), label)

    return sorted(labels, key=key)


def label_with_size(label: str, meta: dict[str, dict[str, str]]) -> str:
    row = meta.get(label, {})
    method = row.get("method") or row.get("model") or label.split("::")[-1]
    dataset = row.get("dataset") or ""
    size = row.get("param_size_group") or row.get("model_scale") or ""
    if "::" in label and dataset:
        return f"{dataset}\n{method}\n{size}" if size else f"{dataset}\n{method}"
    if size:
        return f"{method}\n{size}"
    return method


def family_color(label: str, meta: dict[str, dict[str, str]]) -> str:
    family = meta.get(label, {}).get("detector_family", "Other") or "Other"
    return FAMILY_COLORS.get(family, FAMILY_COLORS["Other"])


def means_and_stds(groups: dict[str, list[float]], meta: dict[str, dict[str, str]]) -> tuple[list[str], list[float], list[float]]:
    labels = sort_methods(list(groups), meta)
    means = [float(mean(groups[label])) for label in labels]
    stds = [float(stdev(groups[label])) if len(groups[label]) > 1 else 0.0 for label in labels]
    return labels, means, stds


def build_dashboard(results_csv: str | Path, summary_csv: str | Path, out: str | Path, dataset: str | None = None) -> Path:
    import matplotlib.pyplot as plt

    rows = read_rows(results_csv)
    if dataset:
        rows = [row for row in rows if row.get("dataset") == dataset]
    completed_rows = [row for row in rows if row.get("status", "completed") == "completed"]
    incomplete_count = len(rows) - len(completed_rows)
    rows = completed_rows
    out_path = resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    datasets = sorted({row.get("dataset") or "unknown" for row in rows}, key=lambda item: DATASET_ORDER.get(item, 50))
    include_dataset = len(datasets) > 1
    title_suffix = f" ({dataset})" if dataset else (" (cross-dataset)" if include_dataset else "")
    fig_width = 16 if include_dataset else 14
    fig, axes = plt.subplots(2, 2, figsize=(fig_width, 9), constrained_layout=True)
    fig.suptitle(f"CoM3D-ACE Server Detector Baselines{title_suffix}", fontsize=16)

    if not rows:
        for ax in axes.ravel():
            ax.axis("off")
        axes[0, 0].text(0.5, 0.5, "No completed result rows yet", ha="center", va="center", fontsize=14)
        if incomplete_count:
            axes[0, 0].text(0.5, 0.38, f"{incomplete_count} incomplete/failed rows excluded", ha="center", va="center", fontsize=11)
        fig.savefig(out_path, dpi=180)
        plt.close(fig)
        return out_path

    meta = metadata_by_method(rows, include_dataset=include_dataset)

    for ax, metric, title in [
        (axes[0, 0], "best_AP", "AP / mAP50-95"),
        (axes[0, 1], "best_AP50", "AP50"),
    ]:
        groups = grouped_values(rows, metric, include_dataset=include_dataset)
        labels, values, errors = means_and_stds(groups, meta)
        colors = [family_color(label, meta) for label in labels]
        plot_labels = [label_with_size(label, meta) if include_dataset else label for label in labels]
        bars = ax.bar(plot_labels, values, yerr=errors, capsize=4, color=colors)
        ax.set_title(title)
        ax.set_ylim(0, max(values + [1.0]) * 1.15)
        ax.tick_params(axis="x", labelrotation=35)
        if values:
            best_idx = max(range(len(values)), key=values.__getitem__)
            bars[best_idx].set_edgecolor("#111827")
            bars[best_idx].set_linewidth(2)

    dist_ax = axes[1, 0]
    groups = grouped_values(rows, "best_AP", include_dataset=include_dataset)
    labels = sort_methods(list(groups), meta)
    box_values = [groups[label] for label in labels]
    box_labels = [label_with_size(label, meta) for label in labels]
    try:
        dist_ax.boxplot(box_values, tick_labels=box_labels, showmeans=True)
    except TypeError:
        dist_ax.boxplot(box_values, labels=box_labels, showmeans=True)
    dist_ax.set_title("Seed Distribution: AP by Model and Parameter Size")
    dist_ax.tick_params(axis="x", labelrotation=35)

    scatter_ax = axes[1, 1]
    x_metric = "FPS" if any(as_float(row.get("FPS")) is not None for row in rows) else "GFLOPs"
    for row in rows:
        ap = as_float(row.get("best_AP"))
        x_value = as_float(row.get(x_metric))
        if ap is None or x_value is None:
            continue
        label = row_key(row, include_dataset)
        method = row.get("method") or row.get("model")
        dataset_label = row.get("dataset") or "unknown"
        family = row.get("detector_family", "Other") or "Other"
        size_group = row.get("param_size_group") or row.get("model_scale") or "unknown"
        marker = SIZE_MARKERS.get(size_group, "o")
        color = FAMILY_COLORS.get(family, FAMILY_COLORS["Other"])
        legend_label = f"{dataset_label}: {method} ({family}, {size_group})" if include_dataset else f"{method} ({family}, {size_group})"
        scatter_ax.scatter(x_value, ap, label=legend_label, marker=marker, color=color, alpha=0.75)
    scatter_ax.set_title("Complexity / Accuracy by Family and Parameter Size" if x_metric == "GFLOPs" else "Speed / Accuracy by Family and Size")
    scatter_ax.set_xlabel(x_metric)
    scatter_ax.set_ylabel("AP")
    handles, labels = scatter_ax.get_legend_handles_labels()
    if handles:
        by_label = dict(zip(labels, handles))
        scatter_ax.legend(by_label.values(), by_label.keys(), fontsize=8)
    else:
        scatter_ax.text(0.5, 0.5, f"{x_metric} not collected yet", ha="center", va="center", transform=scatter_ax.transAxes)
    if incomplete_count:
        fig.text(0.01, 0.01, f"Excluded incomplete/failed runs: {incomplete_count}", fontsize=9)

    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build server detector baseline dashboard PNG.")
    parser.add_argument("--results-csv", default="outputs/experiments/server_baseline_results.csv")
    parser.add_argument("--summary-csv", default="outputs/experiments/server_baseline_summary.csv")
    parser.add_argument("--out", default="outputs/reports/server_baseline_dashboard.png")
    parser.add_argument("--dataset", default=None, help="Optional dataset filter, for example UAVDT or VisDrone2019-DET.")
    args = parser.parse_args()
    print(build_dashboard(args.results_csv, args.summary_csv, args.out, dataset=args.dataset))


if __name__ == "__main__":
    main()
