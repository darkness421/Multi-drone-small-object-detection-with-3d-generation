"""Build MarineCity ambiguity-policy threshold sensitivity artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_HYPOTHESES = ROOT / "outputs/graphs/marinecity_viewer160_crossview_evidence_graph/hypotheses.json"
DEFAULT_OUT_DIR = ROOT / "outputs/reports/live/marinecity_threshold_sensitivity"
DEFAULT_PAPER_TABLE = ROOT / "paper/tables/marinecity_threshold_sensitivity_table.tex"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def route(row: dict[str, Any], *, finalize_threshold: float, reobserve_threshold: float) -> str:
    view_count = int(row.get("view_count", 0) or 0)
    ambiguity = float(row.get("ambiguity_score", 0.0) or 0.0)
    mean_confidence = float(row.get("mean_confidence", 0.0) or 0.0)
    if view_count < 2 and mean_confidence < 0.03:
        return "reject"
    if view_count >= 2 and ambiguity < finalize_threshold:
        return "finalize"
    if view_count >= 2 and ambiguity < reobserve_threshold:
        return "monitor"
    return "targeted_reobserve"


def summarize(hypotheses: list[dict[str, Any]], finalize_threshold: float, reobserve_threshold: float) -> dict[str, Any]:
    counts = Counter(route(row, finalize_threshold=finalize_threshold, reobserve_threshold=reobserve_threshold) for row in hypotheses)
    default_actions = [str(row.get("recommended_action", "")) for row in hypotheses]
    actions = [route(row, finalize_threshold=finalize_threshold, reobserve_threshold=reobserve_threshold) for row in hypotheses]
    high = [row for row in hypotheses if float(row.get("ambiguity_score", 0.0) or 0.0) >= 0.85]
    handled = 0
    for row in high:
        action = route(row, finalize_threshold=finalize_threshold, reobserve_threshold=reobserve_threshold)
        if action in {"reject", "targeted_reobserve"}:
            handled += 1
    changed = sum(1 for before, after in zip(default_actions, actions, strict=False) if before != after)
    active = counts["monitor"] + counts["targeted_reobserve"]
    return {
        "finalize_threshold": finalize_threshold,
        "reobserve_threshold": reobserve_threshold,
        "finalize": counts["finalize"],
        "monitor": counts["monitor"],
        "reject": counts["reject"],
        "reobserve": counts["targeted_reobserve"],
        "action_load": active,
        "high_handled_pct": 100.0 * handled / max(1, len(high)),
        "changed_vs_default": changed,
        "is_default": abs(finalize_threshold - 0.55) < 1e-9 and abs(reobserve_threshold - 0.75) < 1e-9,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_tex(path: Path, rows: list[dict[str, Any]]) -> None:
    selected = [row for row in rows if row["is_default"]]
    selected.extend(
        row
        for row in rows
        if (row["finalize_threshold"], row["reobserve_threshold"]) in {(0.50, 0.75), (0.55, 0.70), (0.55, 0.80), (0.60, 0.75)}
    )
    dedup: list[dict[str, Any]] = []
    seen: set[tuple[float, float]] = set()
    for row in selected:
        key = (float(row["finalize_threshold"]), float(row["reobserve_threshold"]))
        if key not in seen:
            dedup.append(row)
            seen.add(key)

    lines = [
        r"\begin{tabular}{ccccc}",
        r"\toprule",
        r"$\tau_f$ & $\tau_r$ & F/M/R/O & High handled & Load \\",
        r"\midrule",
    ]
    for row in dedup:
        label = r"\textbf{" if row["is_default"] else ""
        close = "}" if row["is_default"] else ""
        actions = f"{row['finalize']}/{row['monitor']}/{row['reject']}/{row['reobserve']}"
        lines.append(
            f"{label}{row['finalize_threshold']:.2f}{close} & "
            f"{label}{row['reobserve_threshold']:.2f}{close} & "
            f"{label}{actions}{close} & "
            f"{label}{row['high_handled_pct']:.1f}\\%{close} & "
            f"{label}{row['action_load']}{close} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_plot(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [f"{row['finalize_threshold']:.2f}/{row['reobserve_threshold']:.2f}" for row in rows]
    reobserve = [row["reobserve"] for row in rows]
    load = [row["action_load"] for row in rows]
    changed = [row["changed_vs_default"] for row in rows]
    colors = ["#111827" if row["is_default"] else "#2563eb" for row in rows]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4), dpi=180)
    axes[0].bar(labels, reobserve, color=colors)
    axes[0].set_title("targeted re-observation count")
    axes[1].bar(labels, load, color=colors)
    axes[1].set_title("active action load")
    axes[2].bar(labels, changed, color=colors)
    axes[2].set_title("action changes vs default")
    if max(changed) == 0:
        axes[2].text(
            0.5,
            0.5,
            "0 changes\nacross sweep",
            transform=axes[2].transAxes,
            ha="center",
            va="center",
            fontsize=13,
            color="#111827",
            fontweight="bold",
        )
        axes[2].set_ylim(0, 1)
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=45)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MarineCity threshold sensitivity artifacts.")
    parser.add_argument("--hypotheses", type=Path, default=DEFAULT_HYPOTHESES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--paper-table", type=Path, default=DEFAULT_PAPER_TABLE)
    args = parser.parse_args()

    hypotheses = read_json(args.hypotheses)
    rows = []
    for finalize_threshold in (0.50, 0.55, 0.60):
        for reobserve_threshold in (0.70, 0.75, 0.80):
            if finalize_threshold >= reobserve_threshold:
                continue
            rows.append(summarize(hypotheses, finalize_threshold, reobserve_threshold))

    csv_path = args.out_dir / "marinecity_threshold_sensitivity.csv"
    json_path = args.out_dir / "marinecity_threshold_sensitivity.json"
    png_path = args.out_dir / "marinecity_threshold_sensitivity.png"
    write_csv(csv_path, rows)
    json_path.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    write_tex(args.paper_table, rows)
    write_plot(png_path, rows)
    print(
        json.dumps(
            {
                "status": "marinecity_threshold_sensitivity_complete",
                "csv": str(csv_path.relative_to(ROOT)),
                "json": str(json_path.relative_to(ROOT)),
                "figure": str(png_path.relative_to(ROOT)),
                "paper_table": str(args.paper_table.relative_to(ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
