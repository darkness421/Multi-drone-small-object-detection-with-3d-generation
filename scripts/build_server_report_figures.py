"""Build separate report figures for server detector baselines."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from runtime.config import resolve_path
from scripts.build_server_training_dashboard import (
    FAMILY_COLORS,
    SIZE_MARKERS,
    SIZE_ORDER,
    as_float,
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


def method_label(row: dict[str, str]) -> str:
    method = row.get("method") or row.get("model") or "unknown"
    size = row.get("param_size_group") or row.get("model_scale") or ""
    seeds = row.get("seed_count") or ""
    detail = ", ".join(part for part in [size, f"n={seeds}" if seeds else ""] if part)
    return f"{method}\n{detail}" if detail else method


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
    return [FAMILY_COLORS.get(row.get("detector_family") or "Other", FAMILY_COLORS["Other"]) for row in rows]


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "axes.grid": True,
            "grid.alpha": 0.25,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
        }
    )
    return plt


def figure_size(count: int, height: float = 5.5) -> tuple[float, float]:
    return (max(9.0, min(18.0, 0.95 * count + 4.5)), height)


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
    ax.bar([x - width / 2 for x in x_values], ap, width, yerr=ap_err, capsize=3, label="AP (mAP50-95)", color="#4C78A8")
    ax.bar([x + width / 2 for x in x_values], ap50, width, yerr=ap50_err, capsize=3, label="AP50", color="#F58518")
    ax.set_title("AP / AP50 by Model")
    ax.set_ylabel("score")
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylim(0, max(ap50 + ap + [1.0]) * 1.1)
    ax.legend()
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
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_tradeoff(rows: list[dict[str, str]], out: Path, x_metric: str, x_label: str, scale: float = 1.0) -> Path:
    available = [row for row in rows if as_float(row.get(x_metric)) is not None and as_float(row.get("best_AP_mean")) is not None]
    if not available:
        return save_empty(out, f"{x_label} vs AP", f"{x_label} not collected yet")
    plt = setup_matplotlib()
    fig, ax = plt.subplots(figsize=(8.5, 5.8), constrained_layout=True)
    seen_labels: set[str] = set()
    for row in available:
        method = row.get("method") or row.get("model") or "unknown"
        family = row.get("detector_family") or "Other"
        size = row.get("param_size_group") or row.get("model_scale") or "unknown"
        x_value = (as_float(row.get(x_metric)) or 0.0) / scale
        ap = as_float(row.get("best_AP_mean")) or 0.0
        legend_label = f"{family}, {size}"
        ax.scatter(
            x_value,
            ap,
            s=90,
            marker=SIZE_MARKERS.get(size, "o"),
            color=FAMILY_COLORS.get(family, FAMILY_COLORS["Other"]),
            edgecolor="#111827",
            linewidth=0.7,
            alpha=0.82,
            label=legend_label if legend_label not in seen_labels else None,
        )
        seen_labels.add(legend_label)
        ax.annotate(method, (x_value, ap), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_title(f"{x_label} vs AP")
    ax.set_xlabel(x_label)
    ax.set_ylabel("AP (mAP50-95)")
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, title="family, size")
    fig.savefig(out, dpi=180)
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
