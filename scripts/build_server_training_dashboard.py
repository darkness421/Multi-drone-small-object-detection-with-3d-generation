"""Build a compact PNG dashboard for server detector baselines."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from runtime.config import resolve_path


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


def grouped_values(rows: list[dict[str, str]], metric: str) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        method = row.get("method") or row.get("model") or "unknown"
        value = as_float(row.get(metric))
        if value is not None:
            groups[method].append(value)
    return dict(groups)


def means_and_stds(groups: dict[str, list[float]]) -> tuple[list[str], list[float], list[float]]:
    labels = sorted(groups)
    means = [float(mean(groups[label])) for label in labels]
    stds = [float(stdev(groups[label])) if len(groups[label]) > 1 else 0.0 for label in labels]
    return labels, means, stds


def build_dashboard(results_csv: str | Path, summary_csv: str | Path, out: str | Path) -> Path:
    import matplotlib.pyplot as plt

    rows = read_rows(results_csv)
    out_path = resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    fig.suptitle("CoM3D-ACE Server Detector Baselines", fontsize=16)

    if not rows:
        for ax in axes.ravel():
            ax.axis("off")
        axes[0, 0].text(0.5, 0.5, "No completed result rows yet", ha="center", va="center", fontsize=14)
        fig.savefig(out_path, dpi=180)
        plt.close(fig)
        return out_path

    for ax, metric, title in [
        (axes[0, 0], "best_AP", "AP / mAP50-95"),
        (axes[0, 1], "best_AP50", "AP50"),
    ]:
        groups = grouped_values(rows, metric)
        labels, values, errors = means_and_stds(groups)
        ax.bar(labels, values, yerr=errors, capsize=4, color="#4C78A8")
        ax.set_title(title)
        ax.set_ylim(0, max(values + [1.0]) * 1.15)
        ax.tick_params(axis="x", labelrotation=35)
        if values:
            best_idx = max(range(len(values)), key=values.__getitem__)
            ax.bar(labels[best_idx], values[best_idx], yerr=errors[best_idx], capsize=4, color="#F58518")

    dist_ax = axes[1, 0]
    groups = grouped_values(rows, "best_AP")
    dist_ax.boxplot([groups[label] for label in sorted(groups)], labels=sorted(groups), showmeans=True)
    dist_ax.set_title("Seed Distribution: AP")
    dist_ax.tick_params(axis="x", labelrotation=35)

    scatter_ax = axes[1, 1]
    for row in rows:
        ap = as_float(row.get("best_AP"))
        fps = as_float(row.get("FPS"))
        if ap is None or fps is None:
            continue
        scatter_ax.scatter(fps, ap, label=row.get("method") or row.get("model"))
    scatter_ax.set_title("Speed / Accuracy Tradeoff")
    scatter_ax.set_xlabel("FPS")
    scatter_ax.set_ylabel("AP")
    handles, labels = scatter_ax.get_legend_handles_labels()
    if handles:
        by_label = dict(zip(labels, handles))
        scatter_ax.legend(by_label.values(), by_label.keys(), fontsize=8)
    else:
        scatter_ax.text(0.5, 0.5, "FPS not collected yet", ha="center", va="center", transform=scatter_ax.transAxes)

    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build server detector baseline dashboard PNG.")
    parser.add_argument("--results-csv", default="outputs/experiments/server_baseline_results.csv")
    parser.add_argument("--summary-csv", default="outputs/experiments/server_baseline_summary.csv")
    parser.add_argument("--out", default="outputs/reports/server_baseline_dashboard.png")
    args = parser.parse_args()
    print(build_dashboard(args.results_csv, args.summary_csv, args.out))


if __name__ == "__main__":
    main()
