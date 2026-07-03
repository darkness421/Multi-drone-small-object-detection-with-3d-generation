"""Build confidence-threshold sensitivity for MarineCity closed-loop recapture."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_REOBS_TOKENS = ROOT / "outputs/evidence/marinecity_targeted_reobservation_fresh_20260703/evidence_tokens.jsonl"
DEFAULT_OUT = ROOT / "outputs/reports/live/closed_loop_reobservation_confidence_sensitivity"
DEFAULT_PAPER_TABLE = ROOT / "paper/tables/marinecity_closed_loop_confidence_sensitivity_table.tex"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def threshold_slug(value: float) -> str:
    return f"conf_{value:.2f}".replace(".", "p")


def run_threshold(threshold: float, reobserve_tokens: Path, out_dir: Path) -> dict[str, Any]:
    run_dir = out_dir / "runs" / threshold_slug(threshold)
    cmd = [
        sys.executable,
        str(ROOT / "scripts/build_marinecity_closed_loop_reobservation.py"),
        "--reobserve-tokens",
        str(reobserve_tokens),
        "--out-dir",
        str(run_dir),
        "--min-reobserve-confidence",
        str(threshold),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    summary = read_json(run_dir / "closed_loop_reobservation_summary.json")
    return {
        "min_confidence": threshold,
        "routed_hypotheses": summary["routed_hypotheses"],
        "matched_reobservation_tokens": summary["matched_reobservation_tokens"],
        "resolved_hypotheses": summary["resolved_hypotheses"],
        "mean_before_ambiguity": summary["mean_before_ambiguity"],
        "mean_after_raw_ambiguity": summary["mean_after_raw_ambiguity"],
        "mean_after_closed_loop_ambiguity": summary["mean_after_closed_loop_ambiguity"],
        "after_monitor": summary["after_action_counts"].get("monitor", 0),
        "after_targeted_reobserve": summary["after_action_counts"].get("targeted_reobserve", 0),
        "run_dir": str(run_dir),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Closed-loop Re-observation Confidence Sensitivity",
        "",
        "This diagnostic tests whether the targeted evidence-update result relies on very low-confidence detector tokens.",
        "It should be used as reviewer-facing sensitivity evidence, not as the main result figure.",
        "",
        "| Min conf. | Matched | Resolved | Mean A(loop) | After monitor | After reobserve |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['min_confidence']:.2f} | {row['matched_reobservation_tokens']} | "
            f"{row['resolved_hypotheses']} | {row['mean_after_closed_loop_ambiguity']:.3f} | "
            f"{row['after_monitor']} | {row['after_targeted_reobserve']} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: the default closed-loop artifact keeps a permissive detector threshold because the re-observation token is used as support evidence, not as a final class decision. Higher thresholds can be reported as a conservative sensitivity check.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tex(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "% Candidate table only. Do not include this file directly without manual review.",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Min conf. & Matched & Resolved & $\\bar{A}_{after}$ & Monitor & Reobserve \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['min_confidence']:.2f} & {row['matched_reobservation_tokens']} & "
            f"{row['resolved_hypotheses']} & {row['mean_after_closed_loop_ambiguity']:.3f} & "
            f"{row['after_monitor']} & {row['after_targeted_reobserve']} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plot(path: Path, rows: list[dict[str, Any]]) -> None:
    x = [row["min_confidence"] for row in rows]
    matched = [row["matched_reobservation_tokens"] for row in rows]
    resolved = [row["resolved_hypotheses"] for row in rows]
    ambiguity = [row["mean_after_closed_loop_ambiguity"] for row in rows]
    fig, ax1 = plt.subplots(figsize=(8.8, 4.6), dpi=200)
    ax1.plot(x, matched, marker="o", color="#0ea5e9", linewidth=2, label="matched")
    ax1.plot(x, resolved, marker="s", color="#16a34a", linewidth=2, label="resolved")
    ax1.set_xlabel("minimum re-observation confidence")
    ax1.set_ylabel("hypothesis count")
    ax1.set_ylim(0, 9.5)
    ax1.grid(axis="y", color="#e2e8f0")
    ax2 = ax1.twinx()
    ax2.plot(x, ambiguity, marker="^", color="#f97316", linewidth=2, label="mean A(loop)")
    ax2.set_ylabel("mean closed-loop ambiguity")
    ax2.set_ylim(0.65, 0.95)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="upper right", frameon=False)
    ax1.set_title("Confidence sensitivity for fresh targeted re-observation evidence")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build closed-loop confidence sensitivity artifacts.")
    parser.add_argument("--reobserve-tokens", type=Path, default=DEFAULT_REOBS_TOKENS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--paper-table", type=Path, default=DEFAULT_PAPER_TABLE)
    parser.add_argument("--thresholds", nargs="*", type=float, default=[0.0, 0.01, 0.05, 0.10, 0.25, 0.50])
    args = parser.parse_args()

    rows = [run_threshold(threshold, args.reobserve_tokens, args.out_dir) for threshold in args.thresholds]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "closed_loop_confidence_sensitivity.csv", rows)
    (args.out_dir / "closed_loop_confidence_sensitivity.json").write_text(
        json.dumps(rows, indent=2),
        encoding="utf-8",
    )
    write_markdown(args.out_dir / "closed_loop_confidence_sensitivity.md", rows)
    write_tex(args.paper_table, rows)
    write_plot(args.out_dir / "closed_loop_confidence_sensitivity.png", rows)
    print(json.dumps({"status": "ok", "rows": rows, "out_dir": str(args.out_dir)}, indent=2))


if __name__ == "__main__":
    main()

