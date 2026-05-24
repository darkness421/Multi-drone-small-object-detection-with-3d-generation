"""Create a human-readable report bundle for server detector experiments."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


DEFAULT_METRICS = [
    ("best_AP_mean", "AP"),
    ("best_AP50_mean", "AP50"),
    ("best_precision_mean", "P"),
    ("best_recall_mean", "R"),
    ("best_F1_mean", "F1"),
    ("FPS_mean", "FPS"),
    ("Params_mean", "Params"),
    ("GFLOPs_mean", "GFLOPs"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: Any, digits: int = 4) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.{digits}f}"


def fmt_params(value: Any) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "-"
    return f"{parsed / 1_000_000:.2f}M"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def copy_if_exists(src: Path, dst: Path) -> Path | None:
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        return dst
    shutil.copy2(src, dst)
    return dst


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status") or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def top_summary_rows(rows: list[dict[str, str]], limit: int = 12) -> list[dict[str, str]]:
    rows = sorted(rows, key=lambda row: as_float(row.get("best_AP_mean")) or -1.0, reverse=True)
    return rows[:limit]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows yet._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def summary_table(rows: list[dict[str, str]]) -> str:
    headers = ["Rank", "Method", "Family", "Size", "Seeds", "Level", "AP", "AP50", "P", "R", "F1", "FPS", "Params", "GFLOPs"]
    body: list[list[str]] = []
    for idx, row in enumerate(top_summary_rows(rows), start=1):
        body.append(
            [
                str(idx),
                row.get("method") or row.get("model") or "-",
                row.get("detector_family") or "-",
                row.get("param_size_group") or row.get("model_scale") or "-",
                row.get("seed_count") or "-",
                row.get("analysis_level") or "-",
                fmt(row.get("best_AP_mean")),
                fmt(row.get("best_AP50_mean")),
                fmt(row.get("best_precision_mean")),
                fmt(row.get("best_recall_mean")),
                fmt(row.get("best_F1_mean")),
                fmt(row.get("FPS_mean"), 2),
                fmt_params(row.get("Params_mean")),
                fmt(row.get("GFLOPs_mean"), 1),
            ]
        )
    return markdown_table(headers, body)


def pvalue_table(rows: list[dict[str, str]], limit: int = 12) -> str:
    headers = ["Metric", "Baseline", "Candidate", "Seeds", "Level", "Delta", "t-test p", "Wilcoxon p"]
    focused = [row for row in rows if row.get("metric") in {"best_AP", "best_AP50", "best_recall", "best_F1"}]
    focused = sorted(
        focused,
        key=lambda row: (
            row.get("metric") or "",
            as_float(row.get("paired_t_pvalue")) if as_float(row.get("paired_t_pvalue")) is not None else 999.0,
        ),
    )
    body = []
    for row in focused[:limit]:
        body.append(
            [
                row.get("metric") or "-",
                row.get("baseline_method") or "-",
                row.get("candidate_method") or "-",
                row.get("seed_count") or "-",
                row.get("analysis_level") or "-",
                fmt(row.get("delta_candidate_minus_baseline")),
                fmt(row.get("paired_t_pvalue")),
                fmt(row.get("wilcoxon_pvalue")),
            ]
        )
    return markdown_table(headers, body)


def figure_table(report_dir: Path, copied: dict[str, Path]) -> str:
    figure_dir = report_dir / "figures"
    descriptions = {
        "server_baseline_dashboard.png": "Combined overview dashboard for quick monitoring",
        "ap_ap50_by_model.png": "Separated AP and AP50 bar chart",
        "precision_recall_f1_by_model.png": "Separated precision, recall, and F1 chart",
        "seed_ap_distribution_by_model.png": "Seed-level AP distribution",
        "params_vs_ap.png": "Parameter-count and AP tradeoff",
        "gflops_vs_ap.png": "GFLOPs and AP tradeoff",
        "speed_vs_ap.png": "FPS and AP tradeoff, or placeholder until FPS is collected",
    }
    rows = []
    for path in sorted(figure_dir.glob("*.png")):
        rel = path.relative_to(report_dir)
        rows.append([f"[{path.name}]({rel.as_posix()})", descriptions.get(path.name, "Report figure")])
    if not rows and copied.get("dashboard"):
        rows.append([f"[Dashboard]({copied['dashboard'].as_posix()})", descriptions["server_baseline_dashboard.png"]])
    return markdown_table(["Figure", "Purpose"], rows)


def write_readme(
    report_dir: Path,
    copied: dict[str, Path],
    results_rows: list[dict[str, str]],
    summary_rows_data: list[dict[str, str]],
    pvalue_rows: list[dict[str, str]],
    stage_gate: dict[str, Any],
) -> Path:
    counts = status_counts(results_rows)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    best = top_summary_rows(summary_rows_data, limit=1)
    best_text = "n/a"
    if best:
        best_text = f"{best[0].get('method', 'n/a')} AP={fmt(best[0].get('best_AP_mean'))}, AP50={fmt(best[0].get('best_AP50_mean'))}"
    recommended = stage_gate.get("recommended_next_stage") or "n/a"
    rows = [
        "# Server Baseline Report Bundle",
        "",
        f"Generated: `{generated}`",
        "",
        "This folder is the compact, Git-friendly report bundle for server detector baselines.",
        "Raw datasets, model weights, raw training runs, and caches stay outside Git.",
        "",
        "## Current Snapshot",
        "",
        f"- Recommended next stage: `{recommended}`",
        f"- Best completed baseline: `{best_text}`",
        f"- Run status counts: `{json.dumps(counts, sort_keys=True)}`",
        "",
        "## Files",
        "",
        markdown_table(
            ["File", "Purpose"],
            [
                [f"[Dashboard]({copied.get('dashboard', Path('figures/server_baseline_dashboard.png')).as_posix()})", "Main AP/AP50/seed distribution/complexity dashboard"],
                [f"[Summary CSV]({copied.get('summary', Path('tables/server_baseline_summary.csv')).as_posix()})", "Mean/std by method, model size, family, and seed count"],
                [f"[Results CSV]({copied.get('results', Path('tables/server_baseline_results.csv')).as_posix()})", "Per-run detector metrics and status"],
                [f"[P-values CSV]({copied.get('pvalues', Path('tables/server_baseline_pvalues.csv')).as_posix()})", "Paired t-test and Wilcoxon comparisons"],
                [f"[Stage Gate](stage_gate.md)", "Current decision gate for baseline/proposed/3D next stage"],
            ],
        ),
        "",
        "## Figures",
        "",
        figure_table(report_dir, copied),
        "",
        "## Top Models",
        "",
        summary_table(summary_rows_data),
        "",
        "## Statistical Snapshot",
        "",
        "Seed count `3` is preliminary; seed count `5+` is the main statistical setting.",
        "",
        pvalue_table(pvalue_rows),
        "",
        "## Metric Notes",
        "",
        "- `AP` is mAP50-95 and is used as the detector accuracy proxy.",
        "- `AP50`, `P` precision, `R` recall, and `F1` are reported alongside AP.",
        "- `FPS` and `latency_ms` appear when validation/inference speed is available.",
        "- `Params` and `GFLOPs` are used to separate nano/small/medium/large comparisons.",
        "- Incomplete, cancelled, or failed runs should be interpreted separately from completed seed summaries.",
    ]
    out = report_dir / "README.md"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return out


def organize_reports(args: argparse.Namespace) -> Path:
    report_dir = resolve_path(args.report_dir)
    tables_dir = report_dir / "tables"
    figures_dir = report_dir / "figures"
    report_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    sources = {
        "results": resolve_path(args.results_csv),
        "summary": resolve_path(args.summary_csv),
        "pvalues": resolve_path(args.pvalues_csv),
        "dashboard": resolve_path(args.dashboard),
        "stage_gate_json": resolve_path(args.stage_gate_json),
        "stage_gate_md": resolve_path(args.stage_gate_md),
    }
    copied_abs = {
        "results": copy_if_exists(sources["results"], tables_dir / "server_baseline_results.csv"),
        "summary": copy_if_exists(sources["summary"], tables_dir / "server_baseline_summary.csv"),
        "pvalues": copy_if_exists(sources["pvalues"], tables_dir / "server_baseline_pvalues.csv"),
        "dashboard": copy_if_exists(sources["dashboard"], figures_dir / "server_baseline_dashboard.png"),
        "stage_gate_json": copy_if_exists(sources["stage_gate_json"], report_dir / "stage_gate.json"),
        "stage_gate_md": copy_if_exists(sources["stage_gate_md"], report_dir / "stage_gate.md"),
    }
    copied = {key: value.relative_to(report_dir) for key, value in copied_abs.items() if value is not None}

    results_rows = read_csv(copied_abs.get("results") or sources["results"])
    summary_rows_data = read_csv(copied_abs.get("summary") or sources["summary"])
    pvalue_rows = read_csv(copied_abs.get("pvalues") or sources["pvalues"])
    stage_gate = {}
    stage_gate_path = copied_abs.get("stage_gate_json") or sources["stage_gate_json"]
    if stage_gate_path.exists():
        try:
            stage_gate = json.loads(stage_gate_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            stage_gate = {}

    return write_readme(report_dir, copied, results_rows, summary_rows_data, pvalue_rows, stage_gate)


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize server detector reports into one compact folder.")
    parser.add_argument("--report-dir", default="outputs/reports/server_baselines")
    parser.add_argument("--results-csv", default="outputs/experiments/server_baseline_results.csv")
    parser.add_argument("--summary-csv", default="outputs/experiments/server_baseline_summary.csv")
    parser.add_argument("--pvalues-csv", default="outputs/experiments/server_baseline_pvalues.csv")
    parser.add_argument("--dashboard", default="outputs/reports/server_baseline_dashboard.png")
    parser.add_argument("--stage-gate-json", default="outputs/experiments/detector_stage_gate.json")
    parser.add_argument("--stage-gate-md", default="outputs/experiments/detector_stage_gate.md")
    args = parser.parse_args()
    print(organize_reports(args))


if __name__ == "__main__":
    main()
