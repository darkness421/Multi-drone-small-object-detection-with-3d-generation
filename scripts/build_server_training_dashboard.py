"""Build a compact PNG dashboard for server detector baselines."""

from __future__ import annotations

import argparse
import csv
import os
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

MODEL_VERSION_COLORS = {
    "v5": "#0072B2",
    "v6": "#56B4E9",
    "v7": "#009E73",
    "v8": "#E69F00",
    "v9": "#D55E00",
    "v10": "#CC79A7",
    "v11": "#6A3D9A",
    "v12": "#1B9E77",
    "v26": "#E7298A",
    "RT-DETR": "#4B5563",
    "LRDS-YOLO": "#A6761D",
    "D-FINE": "#66A61E",
    "DETR": "#7570B3",
    "unknown": "#6B7280",
}

PROPOSED_COLORS = {
    "full": "#111827",
    "cbam": "#7C3AED",
    "se": "#059669",
    "wavelet": "#D97706",
    "deformable": "#DC2626",
    "tiling": "#0891B2",
    "control": "#64748B",
    "proposed": "#BE123C",
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


def model_color_from_row(row: dict[str, str]) -> str:
    method_blob = " ".join(
        [
            row.get("method", ""),
            row.get("ablation", ""),
            row.get("proposed_module", ""),
            row.get("is_proposed", ""),
        ]
    ).lower()
    if "proposed" in method_blob or row.get("is_proposed") == "true":
        for token, color in PROPOSED_COLORS.items():
            if token in method_blob:
                return color
        return PROPOSED_COLORS["proposed"]
    family = row.get("detector_family", "") or ""
    version = row.get("yolo_version") or row.get("model_version") or "unknown"
    if family == "YOLO" and version:
        return MODEL_VERSION_COLORS.get(version, MODEL_VERSION_COLORS["unknown"])
    return MODEL_VERSION_COLORS.get(version, FAMILY_COLORS.get(family, FAMILY_COLORS["Other"]))


def model_color(label: str, meta: dict[str, dict[str, str]]) -> str:
    return model_color_from_row(meta.get(label, {}))


def means_and_stds(groups: dict[str, list[float]], meta: dict[str, dict[str, str]]) -> tuple[list[str], list[float], list[float]]:
    labels = sort_methods(list(groups), meta)
    means = [float(mean(groups[label])) for label in labels]
    stds = [float(stdev(groups[label])) if len(groups[label]) > 1 else 0.0 for label in labels]
    return labels, means, stds


def summary_metric(row: dict[str, str], metric: str) -> float | None:
    value = as_float(row.get(f"{metric}_mean"))
    return value if value is not None else as_float(row.get(metric))


def summary_std(row: dict[str, str], metric: str) -> float:
    value = as_float(row.get(f"{metric}_std"))
    return value if value is not None else 0.0


def summary_from_results(rows: list[dict[str, str]], include_dataset: bool) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row_key(row, include_dataset)].append(row)

    summaries: list[dict[str, str]] = []
    metrics = ["best_AP", "best_AP50", "best_precision", "best_recall", "best_F1", "ROC-AUC", "Params", "GFLOPs", "FPS"]
    for group_rows in grouped.values():
        base = dict(group_rows[0])
        base["seed_count"] = str(len(group_rows))
        for metric in metrics:
            values = [value for value in (as_float(row.get(metric)) for row in group_rows) if value is not None]
            if not values:
                continue
            base[f"{metric}_mean"] = f"{mean(values):.10g}"
            base[f"{metric}_std"] = f"{stdev(values):.10g}" if len(values) > 1 else "0"
        summaries.append(base)
    return summaries


def dashboard_model_label(row: dict[str, str], include_dataset: bool = False) -> str:
    method = row.get("method") or row.get("model") or "unknown"
    size = row.get("param_size_group") or row.get("model_scale") or ""
    seeds = row.get("seed_count") or ""
    prefix = f"{row.get('dataset')}\n" if include_dataset and row.get("dataset") else ""
    detail = ", ".join(part for part in [size, f"n={seeds}" if seeds else ""] if part)
    return f"{prefix}{method}\n{detail}" if detail else f"{prefix}{method}"


def summary_sort_key(row: dict[str, str]) -> tuple[float, int, str]:
    size = row.get("param_size_group") or row.get("model_scale") or ""
    return (-(summary_metric(row, "best_AP") or -1.0), SIZE_ORDER.get(size, 99), row.get("method") or row.get("model") or "")


def score_xlim(values: list[float], pad: float = 0.08) -> tuple[float, float]:
    if not values:
        return (0.0, 1.0)
    high = min(1.0, max(values) + pad)
    return (0.0, max(high, 0.1))


def add_horizontal_value_labels(ax: Any, values: list[float], y_values: list[float], fmt: str = "{:.3f}") -> None:
    if len(values) > 12:
        return
    x_min, x_max = ax.get_xlim()
    pad = (x_max - x_min) * 0.01
    for value, y_value in zip(values, y_values):
        if value <= 0:
            continue
        ax.text(value + pad, y_value, fmt.format(value), va="center", ha="left", fontsize=7.5, color="#111827")


def dashboard_label_offset(method: str) -> tuple[int, int]:
    offsets = {
        "YOLOv8n": (10, -14),
        "YOLOv11n": (10, -22),
        "YOLOv12n": (12, 12),
        "YOLOv12s": (-88, -18),
        "YOLOv5su": (-78, -2),
        "YOLOv11s": (12, -24),
        "YOLOv8s": (14, 8),
        "YOLOv9s": (24, 24),
        "RT-DETR-L": (-90, 18),
    }
    return offsets.get(method, (8, 8))


def build_dashboard(results_csv: str | Path, summary_csv: str | Path, out: str | Path, dataset: str | None = None) -> Path:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))

    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    plt.rcParams.update(
        {
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.22,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    all_rows = read_rows(results_csv)
    if dataset:
        all_rows = [row for row in all_rows if row.get("dataset") == dataset]
    completed_rows = [row for row in all_rows if row.get("status", "completed") == "completed"]
    incomplete_count = len(all_rows) - len(completed_rows)
    out_path = resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    datasets = sorted({row.get("dataset") or "unknown" for row in completed_rows}, key=lambda item: DATASET_ORDER.get(item, 50))
    include_dataset = len(datasets) > 1
    title_suffix = f" ({dataset})" if dataset else (" (cross-dataset)" if include_dataset else "")

    summary_rows = read_rows(summary_csv)
    if dataset:
        summary_rows = [row for row in summary_rows if row.get("dataset") == dataset]
    summary_rows = [row for row in summary_rows if summary_metric(row, "best_AP") is not None]
    if not summary_rows and completed_rows:
        summary_rows = summary_from_results(completed_rows, include_dataset=include_dataset)
    summary_rows = sorted(summary_rows, key=summary_sort_key)

    fig_width = 16.5 if include_dataset else 15.5
    fig, axes = plt.subplots(2, 2, figsize=(fig_width, 10.5), constrained_layout=False)
    fig.subplots_adjust(left=0.14, right=0.985, top=0.90, bottom=0.18, hspace=0.38, wspace=0.24)
    fig.suptitle(f"CoM3D-ACE Server Detector Baselines{title_suffix}", fontsize=17, y=0.965)

    if not summary_rows:
        for ax in axes.ravel():
            ax.axis("off")
        axes[0, 0].text(0.5, 0.5, "No completed result rows yet", ha="center", va="center", fontsize=14)
        if incomplete_count:
            axes[0, 0].text(0.5, 0.38, f"{incomplete_count} incomplete/failed rows excluded", ha="center", va="center", fontsize=11)
        fig.savefig(out_path, dpi=180)
        plt.close(fig)
        return out_path

    labels = [dashboard_model_label(row, include_dataset=include_dataset) for row in summary_rows]
    y_values = list(range(len(summary_rows)))
    colors = [model_color_from_row(row) for row in summary_rows]

    ap_ax = axes[0, 0]
    ap_values = [summary_metric(row, "best_AP") or 0.0 for row in summary_rows]
    ap50_values = [summary_metric(row, "best_AP50") or 0.0 for row in summary_rows]
    ap_errors = [summary_std(row, "best_AP") for row in summary_rows]
    ap50_errors = [summary_std(row, "best_AP50") for row in summary_rows]
    bar_height = 0.34
    ap_ax.barh([y + bar_height / 2 for y in y_values], ap_values, bar_height, xerr=ap_errors, capsize=3, color="#2563EB", label="AP")
    ap_ax.barh([y - bar_height / 2 for y in y_values], ap50_values, bar_height, xerr=ap50_errors, capsize=3, color="#F97316", alpha=0.88, label="AP50")
    ap_ax.set_yticks(y_values)
    ap_ax.set_yticklabels(labels)
    ap_ax.invert_yaxis()
    ap_ax.set_title("Detection Accuracy")
    ap_ax.set_xlabel("score")
    ap_ax.set_xlim(score_xlim(ap_values + ap50_values, pad=0.06))
    ap_ax.legend(loc="lower right", frameon=True)
    add_horizontal_value_labels(ap_ax, ap_values, [y + bar_height / 2 for y in y_values])
    add_horizontal_value_labels(ap_ax, ap50_values, [y - bar_height / 2 for y in y_values])

    prf_ax = axes[0, 1]
    pr_metrics = [
        ("P", "best_precision", "#4C78A8"),
        ("R", "best_recall", "#54A24B"),
        ("F1", "best_F1", "#E45756"),
    ]
    pr_height = 0.24
    for offset, (label, metric, color) in zip([pr_height, 0.0, -pr_height], pr_metrics):
        values = [summary_metric(row, metric) or 0.0 for row in summary_rows]
        prf_ax.barh([y + offset for y in y_values], values, pr_height, color=color, label=label, alpha=0.94)
    prf_ax.set_yticks(y_values)
    prf_ax.set_yticklabels(labels)
    prf_ax.invert_yaxis()
    prf_ax.set_title("Precision / Recall / F1")
    prf_ax.set_xlabel("score")
    pr_values = [summary_metric(row, metric) or 0.0 for row in summary_rows for _, metric, _ in pr_metrics]
    prf_ax.set_xlim(score_xlim(pr_values, pad=0.06))
    prf_ax.legend(loc="lower right", frameon=True)

    stability_ax = axes[1, 0]
    stability_ax.errorbar(ap_values, y_values, xerr=ap_errors, fmt="none", ecolor="#94A3B8", elinewidth=1.2, capsize=3, zorder=1)
    for row, y, ap, color in zip(summary_rows, y_values, ap_values, colors):
        size = row.get("param_size_group") or row.get("model_scale") or "unknown"
        marker = SIZE_MARKERS.get(size, "o")
        stability_ax.scatter(ap, y, marker=marker, s=82, color=color, edgecolor="#111827", linewidth=0.8, zorder=3)
        seed_count = row.get("seed_count") or row.get("best_AP_n") or ""
        if seed_count:
            stability_ax.text(ap + 0.0015, y, f"n={seed_count}", va="center", fontsize=7.5, color="#374151")
    stability_ax.set_yticks(y_values)
    stability_ax.set_yticklabels(labels)
    stability_ax.invert_yaxis()
    stability_ax.set_title("Seed Stability: AP mean +/- std")
    stability_ax.set_xlabel("AP (mAP50-95)")
    ap_min = min(ap_values) if ap_values else 0.0
    ap_max = max(ap_values) if ap_values else 1.0
    stability_ax.set_xlim(max(0.0, ap_min - 0.025), min(1.0, ap_max + 0.04))

    scatter_ax = axes[1, 1]
    x_metric = "FPS" if any(summary_metric(row, "FPS") is not None for row in summary_rows) else "GFLOPs"
    x_label = "FPS" if x_metric == "FPS" else "GFLOPs"
    plotted = False
    for row in summary_rows:
        ap = summary_metric(row, "best_AP")
        x_value = summary_metric(row, x_metric)
        if ap is None or x_value is None:
            continue
        method = row.get("method") or row.get("model") or "unknown"
        family = row.get("detector_family", "Other") or "Other"
        size_group = row.get("param_size_group") or row.get("model_scale") or "unknown"
        marker = SIZE_MARKERS.get(size_group, "o")
        color = model_color_from_row(row)
        scatter_ax.errorbar(
            x_value,
            ap,
            xerr=summary_std(row, x_metric) or None,
            yerr=summary_std(row, "best_AP") or None,
            fmt=marker,
            markersize=8,
            color=color,
            markeredgecolor="#111827",
            markeredgewidth=0.8,
            ecolor="#94A3B8",
            elinewidth=1.0,
            capsize=3,
            alpha=0.9,
        )
        scatter_ax.annotate(
            method,
            (x_value, ap),
            xytext=dashboard_label_offset(method),
            textcoords="offset points",
            fontsize=8.0,
            weight="bold",
            color="#111827",
            annotation_clip=False,
            arrowprops={"arrowstyle": "-", "color": "#94A3B8", "lw": 0.8, "alpha": 0.65},
        )
        plotted = True
    scatter_ax.set_title(f"{x_label} / Accuracy Tradeoff")
    scatter_ax.set_xlabel(x_label)
    scatter_ax.set_ylabel("AP")
    scatter_ax.margins(x=0.18, y=0.14)
    if not plotted:
        scatter_ax.text(0.5, 0.5, f"{x_label} not collected yet", ha="center", va="center", transform=scatter_ax.transAxes)

    for ax in axes.ravel():
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="x", alpha=0.18)
        ax.grid(axis="y", alpha=0.12)

    version_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markeredgecolor="#111827", markersize=8, label=f"version: {version}")
        for version, color in sorted({(row.get("yolo_version") or row.get("model_version") or row.get("detector_family") or "unknown"): model_color_from_row(row) for row in summary_rows}.items(), key=lambda item: item[0])
    ]
    size_handles = [
        Line2D([0], [0], marker=SIZE_MARKERS.get(size, "o"), color="#111827", linestyle="none", markersize=8, label=f"size: {size}")
        for size in sorted({row.get("param_size_group") or row.get("model_scale") or "unknown" for row in summary_rows}, key=lambda item: SIZE_ORDER.get(item, 99))
    ]
    if version_handles or size_handles:
        fig.legend(
            handles=version_handles + size_handles,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.055),
            ncol=min(len(version_handles + size_handles), 6),
            frameon=True,
        )
    if incomplete_count:
        fig.text(0.012, 0.015, f"Excluded incomplete/failed runs: {incomplete_count}", fontsize=9)

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
