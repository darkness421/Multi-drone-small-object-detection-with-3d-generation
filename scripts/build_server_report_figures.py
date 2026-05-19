"""Build separate report figures for server detector baselines."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from runtime.config import resolve_path
from scripts.build_server_training_dashboard import (
    SIZE_MARKERS,
    SIZE_ORDER,
    as_float,
    model_color_from_row,
    read_rows,
)


FIGURE_SPECS = [
    ("ap_ap50_by_model.png", "AP / AP50 by model"),
    ("precision_recall_f1_by_model.png", "Precision / recall / F1 by model"),
    ("seed_ap_distribution_by_model.png", "Seed AP distribution by model"),
    ("params_vs_ap.png", "Parameter count vs AP"),
    ("gflops_vs_ap.png", "GFLOPs vs AP"),
    ("speed_vs_ap.png", "FPS vs AP"),
]

LABEL_OFFSETS = {
    "YOLOv8n": (8, -12),
    "YOLOv11n": (8, -22),
    "YOLOv12n": (8, 12),
    "YOLOv12s": (-78, 22),
    "YOLOv5su": (8, 10),
    "YOLOv11s": (8, -18),
    "YOLOv8s": (8, -10),
    "YOLOv9s": (-82, -20),
}


def method_label(row: dict[str, str]) -> str:
    method = row.get("method") or row.get("model") or "unknown"
    size = row.get("param_size_group") or row.get("model_scale") or ""
    seeds = row.get("seed_count") or ""
    detail = ", ".join(part for part in [size, f"n={seeds}" if seeds else ""] if part)
    return f"{method}\n{detail}" if detail else method


def short_label(row: dict[str, str]) -> str:
    return row.get("method") or row.get("model") or "unknown"


def method_key(row: dict[str, str]) -> tuple[float, int, str]:
    size = row.get("param_size_group") or row.get("model_scale") or ""
    return (-(as_float(row.get("best_AP_mean")) or -1.0), SIZE_ORDER.get(size, 99), row.get("method") or "")


def completed_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("status", "completed") == "completed"]


def summary_rows(rows: list[dict[str, str]], dataset: str | None) -> list[dict[str, str]]:
    if dataset:
        rows = [row for row in rows if row.get("dataset") == dataset]
    return sorted(rows, key=method_key)


def result_rows(rows: list[dict[str, str]], dataset: str | None) -> list[dict[str, str]]:
    if dataset:
        rows = [row for row in rows if row.get("dataset") == dataset]
    return completed_rows(rows)


def colors_for(rows: list[dict[str, str]]) -> list[str]:
    return [model_color_from_row(row) for row in rows]


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.25,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    return plt


def figure_size(count: int, height: float = 5.5) -> tuple[float, float]:
    return (max(9.0, min(18.0, 0.95 * count + 4.5)), height)


def polish_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.22)


def add_value_labels(ax: Any, bars: Any, values: list[float], fmt: str = "{:.3f}") -> None:
    if len(values) > 12:
        return
    for bar, value in zip(bars, values):
        if value == 0:
            continue
        ax.annotate(
            fmt.format(value),
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def save_empty(out: Path, title: str, message: str) -> Path:
    plt = setup_matplotlib()
    fig, ax = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
    ax.axis("off")
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_ap_ap50(rows: list[dict[str, str]], out: Path) -> Path:
    if not rows:
        return save_empty(out, "AP / AP50 by Model", "No summary rows yet")
    plt = setup_matplotlib()
    labels = [method_label(row) for row in rows]
    x_values = list(range(len(rows)))
    width = 0.38
    ap = [as_float(row.get("best_AP_mean")) or 0.0 for row in rows]
    ap50 = [as_float(row.get("best_AP50_mean")) or 0.0 for row in rows]
    ap_err = [as_float(row.get("best_AP_std")) or 0.0 for row in rows]
    ap50_err = [as_float(row.get("best_AP50_std")) or 0.0 for row in rows]
    fig, ax = plt.subplots(figsize=figure_size(len(rows)), constrained_layout=True)
    ap_bars = ax.bar([x - width / 2 for x in x_values], ap, width, yerr=ap_err, capsize=3, label="AP (mAP50-95)", color="#2563EB")
    ap50_bars = ax.bar([x + width / 2 for x in x_values], ap50, width, yerr=ap50_err, capsize=3, label="AP50", color="#F97316", alpha=0.86)
    ax.set_title("AP / AP50 by Model")
    ax.set_ylabel("score")
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylim(0, max(ap50 + ap + [1.0]) * 1.1)
    ax.legend()
    polish_axes(ax)
    add_value_labels(ax, ap_bars, ap)
    add_value_labels(ax, ap50_bars, ap50)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_prf(rows: list[dict[str, str]], out: Path) -> Path:
    if not rows:
        return save_empty(out, "Precision / Recall / F1 by Model", "No summary rows yet")
    plt = setup_matplotlib()
    labels = [method_label(row) for row in rows]
    x_values = list(range(len(rows)))
    width = 0.25
    metrics = [
        ("P", "best_precision_mean", "#4C78A8"),
        ("R", "best_recall_mean", "#54A24B"),
        ("F1", "best_F1_mean", "#E45756"),
    ]
    fig, ax = plt.subplots(figsize=figure_size(len(rows)), constrained_layout=True)
    for offset, (label, metric, color) in zip([-width, 0.0, width], metrics):
        values = [as_float(row.get(metric)) or 0.0 for row in rows]
        ax.bar([x + offset for x in x_values], values, width, label=label, color=color)
    ax.set_title("Precision / Recall / F1 by Model")
    ax.set_ylabel("score")
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylim(0, 1.0)
    ax.legend()
    polish_axes(ax)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_seed_distribution(rows: list[dict[str, str]], summary: list[dict[str, str]], out: Path) -> Path:
    if not rows:
        return save_empty(out, "Seed AP Distribution by Model", "No completed rows yet")
    plt = setup_matplotlib()
    order = [row.get("method") or row.get("model") or "unknown" for row in summary]
    grouped: dict[str, list[float]] = {method: [] for method in order}
    for row in rows:
        method = row.get("method") or row.get("model") or "unknown"
        value = as_float(row.get("best_AP"))
        if value is not None:
            grouped.setdefault(method, []).append(value)
    labels = [method for method in order if grouped.get(method)]
    if not labels:
        return save_empty(out, "Seed AP Distribution by Model", "No AP rows yet")
    values = [grouped[label] for label in labels]
    fig, ax = plt.subplots(figsize=figure_size(len(labels)), constrained_layout=True)
    try:
        ax.boxplot(values, tick_labels=labels, showmeans=True)
    except TypeError:
        ax.boxplot(values, labels=labels, showmeans=True)
    for idx, series in enumerate(values, start=1):
        ax.scatter([idx] * len(series), series, color="#111827", s=18, alpha=0.65, zorder=3)
    ax.set_title("Seed AP Distribution by Model")
    ax.set_ylabel("AP (mAP50-95)")
    ax.tick_params(axis="x", labelrotation=35)
    polish_axes(ax)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_tradeoff(rows: list[dict[str, str]], out: Path, x_metric: str, x_label: str, scale: float = 1.0) -> Path:
    available = [row for row in rows if as_float(row.get(x_metric)) is not None and as_float(row.get("best_AP_mean")) is not None]
    if not available:
        return save_empty(out, f"{x_label} vs AP", f"{x_label} not collected yet")
    plt = setup_matplotlib()
    from matplotlib.lines import Line2D

    fig, ax = plt.subplots(figsize=(9.4, 6.2), constrained_layout=True)
    available = sorted(available, key=lambda row: ((as_float(row.get(x_metric)) or 0.0), short_label(row)))
    label_offsets = [(7, 6), (7, -11), (-42, 7), (-42, -12), (10, 14), (-55, 14)]
    used_versions: dict[str, str] = {}
    used_sizes: set[str] = set()
    best_ap = max(as_float(row.get("best_AP_mean")) or 0.0 for row in available)
    for idx, row in enumerate(available):
        method = short_label(row)
        family = row.get("detector_family") or "Other"
        version = row.get("yolo_version") or row.get("model_version") or family or "unknown"
        size = row.get("param_size_group") or row.get("model_scale") or "unknown"
        x_value = (as_float(row.get(x_metric)) or 0.0) / scale
        ap = as_float(row.get("best_AP_mean")) or 0.0
        ap_std = as_float(row.get("best_AP_std")) or 0.0
        x_std = (as_float(row.get(x_metric.replace("_mean", "_std"))) or 0.0) / scale if "_mean" in x_metric else 0.0
        color = model_color_from_row(row)
        marker = SIZE_MARKERS.get(size, "o")
        ax.errorbar(
            x_value,
            ap,
            xerr=x_std if x_std > 0 else None,
            yerr=ap_std if ap_std > 0 else None,
            fmt=marker,
            markersize=9,
            color=color,
            markeredgecolor="#111827",
            markeredgewidth=0.8,
            ecolor="#94A3B8",
            elinewidth=1.0,
            capsize=3,
            alpha=0.9,
        )
        used_versions.setdefault(version, color)
        used_sizes.add(size)
        offset = LABEL_OFFSETS.get(method, label_offsets[idx % len(label_offsets)])
        ax.annotate(
            method,
            (x_value, ap),
            xytext=offset,
            textcoords="offset points",
            fontsize=8.5,
            weight="bold",
            color="#111827",
            arrowprops={"arrowstyle": "-", "color": "#94A3B8", "lw": 0.8, "alpha": 0.65},
        )
    if best_ap > 0:
        ax.axhline(best_ap, color="#CBD5E1", linestyle="--", linewidth=1.2, zorder=0)
    ax.set_title(f"{x_label} vs AP")
    ax.set_xlabel(x_label)
    ax.set_ylabel("AP (mAP50-95)")
    ax.margins(x=0.08, y=0.12)
    polish_axes(ax)
    version_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markeredgecolor="#111827", markersize=8, label=version)
        for version, color in sorted(used_versions.items(), key=lambda item: item[0])
    ]
    size_handles = [
        Line2D([0], [0], marker=SIZE_MARKERS.get(size, "o"), color="#111827", linestyle="none", markersize=8, label=size)
        for size in sorted(used_sizes, key=lambda item: SIZE_ORDER.get(item, 99))
    ]
    if version_handles:
        legend1 = ax.legend(handles=version_handles, title="model version", loc="lower right", frameon=True)
        ax.add_artist(legend1)
    if size_handles:
        ax.legend(handles=size_handles, title="param size", loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=len(size_handles), frameon=True)
    fig.savefig(out, dpi=220)
    plt.close(fig)
    return out


def build_report_figures(
    results_csv: str | Path,
    summary_csv: str | Path,
    out_dir: str | Path,
    dataset: str | None = None,
) -> list[Path]:
    out_path = resolve_path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    summary = summary_rows(read_rows(summary_csv), dataset)
    results = result_rows(read_rows(results_csv), dataset)
    written = [
        plot_ap_ap50(summary, out_path / "ap_ap50_by_model.png"),
        plot_prf(summary, out_path / "precision_recall_f1_by_model.png"),
        plot_seed_distribution(results, summary, out_path / "seed_ap_distribution_by_model.png"),
        plot_tradeoff(summary, out_path / "params_vs_ap.png", "Params_mean", "Params (M)", scale=1_000_000.0),
        plot_tradeoff(summary, out_path / "gflops_vs_ap.png", "GFLOPs_mean", "GFLOPs"),
        plot_tradeoff(summary, out_path / "speed_vs_ap.png", "FPS_mean", "FPS"),
    ]
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build separated server detector report figures.")
    parser.add_argument("--results-csv", default="outputs/experiments/server_baseline_results.csv")
    parser.add_argument("--summary-csv", default="outputs/experiments/server_baseline_summary.csv")
    parser.add_argument("--out-dir", default="outputs/reports/server_baselines/figures")
    parser.add_argument("--dataset", default=None)
    args = parser.parse_args()
    for path in build_report_figures(args.results_csv, args.summary_csv, args.out_dir, dataset=args.dataset):
        print(path)


if __name__ == "__main__":
    main()
