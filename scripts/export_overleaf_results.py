"""Export experiment summaries into an Overleaf-linked LaTeX repository."""

from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path


DEFAULT_SUMMARY_CANDIDATES = [
    Path("outputs/experiments/server_with_proposed/server_with_proposed_summary.csv"),
    Path("outputs/experiments/server_with_proposed_summary.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/server_baseline_summary.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_summary.csv"),
]

DEFAULT_FIGURE_DIRS = [
    Path("outputs/reports/server_with_proposed/figures"),
    Path("outputs/reports/server_fresh_baselines/large_20260524_140922/figures"),
    Path("outputs/reports/live/large_20260524_140922_figures"),
]


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str | None) -> float:
    if value in (None, ""):
        return float("-inf")
    try:
        return float(value)
    except ValueError:
        return float("-inf")


def latex_escape(value: object) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def metric(row: dict[str, str], key: str) -> str:
    value = row.get(f"{key}_mean_std") or row.get(f"{key}_mean") or ""
    if "+/-" in value:
        left, right = [part.strip() for part in value.split("+/-", 1)]
        try:
            return f"{float(left):.4f} $\\pm$ {float(right):.4f}"
        except ValueError:
            return latex_escape(value.replace("+/-", r"$\pm$"))
    try:
        if value != "":
            return f"{float(value):.4f}"
    except ValueError:
        pass
    return latex_escape(value)


def compact_name(row: dict[str, str]) -> str:
    method = row.get("method") or Path(row.get("model", "")).stem
    ablation = row.get("ablation") or row.get("proposed_module") or ""
    if ablation and ablation.lower() not in {"none", "baseline"}:
        return f"{method} + {ablation}"
    return method


def write_detector_table(summary_csv: Path, out_path: Path, top_k: int) -> None:
    rows = read_rows(summary_csv)
    rows = sorted(rows, key=lambda row: as_float(row.get("best_AP_mean")), reverse=True)[:top_k]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\caption{Automatically exported detector summary. Full per-seed results and supplementary plots are generated from the experiment logs.}",
        r"\label{tab:auto_detector_results}",
        r"\begin{tabular}{@{}llrrrr@{}}",
        r"\toprule",
        r"Method & Scale & AP & AP50 & Precision & Recall \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(
                [
                    latex_escape(compact_name(row)),
                    latex_escape(row.get("model_scale") or row.get("size_group") or ""),
                    metric(row, "best_AP"),
                    metric(row, "best_AP50"),
                    metric(row, "best_precision"),
                    metric(row, "best_recall"),
                ]
            )
            + r" \\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def copy_figures(figure_dirs: list[Path], overleaf_repo: Path) -> list[str]:
    figure_out = overleaf_repo / "figures" / "auto"
    figure_out.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    seen: set[str] = set()
    for figure_dir in figure_dirs:
        if not figure_dir.exists():
            continue
        for src in sorted(figure_dir.glob("*.png")):
            name = f"{figure_dir.name}_{src.name}"
            if name in seen:
                continue
            seen.add(name)
            dst = figure_out / name
            shutil.copy2(src, dst)
            copied.append(f"figures/auto/{name}")
    return copied


def write_status_section(
    out_path: Path,
    summary_csv: Path,
    copied_figures: list[str],
    stage_gate_md: Path | None,
    proposed_gate_md: Path | None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        r"\subsection{Current Automated Experiment Snapshot}",
        f"This snapshot was exported from the server results on {latex_escape(now)}.",
        r"It is a draft synchronization block and should be reviewed before final submission.",
        "",
        r"\input{tables/auto_detector_results}",
        "",
    ]
    if copied_figures:
        lines.extend(
            [
                r"\begin{figure*}[t]",
                r"\centering",
                rf"\includegraphics[width=0.92\textwidth]{{{copied_figures[0]}}}",
                r"\caption{Automatically exported detector dashboard from the latest result bundle.}",
                r"\label{fig:auto_detector_dashboard}",
                r"\end{figure*}",
                "",
            ]
        )
    lines.append(f"% Source summary CSV: {summary_csv}")
    if stage_gate_md:
        lines.append(f"% Stage gate report: {stage_gate_md}")
    if proposed_gate_md:
        lines.append(f"% Proposed overwhelm gate report: {proposed_gate_md}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_section_input(results_tex: Path, input_line: str) -> None:
    if not results_tex.exists():
        return
    text = results_tex.read_text(encoding="utf-8")
    if input_line in text:
        return
    marker = r"\subsection{Front-end Evidence Quality}"
    if marker in text:
        text = text.replace(marker, marker + "\n" + input_line + "\n", 1)
    else:
        text = input_line + "\n" + text
    results_tex.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overleaf-repo", default="/tmp/accv-overleaf")
    parser.add_argument("--summary-csv", default=None)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--figure-dir", action="append", default=[])
    parser.add_argument("--stage-gate-md", default=None)
    parser.add_argument("--proposed-gate-md", default=None)
    parser.add_argument("--update-results-section", action="store_true")
    args = parser.parse_args()

    overleaf_repo = Path(args.overleaf_repo).resolve()
    if not overleaf_repo.exists():
        raise SystemExit(f"Missing Overleaf repo: {overleaf_repo}")

    summary_csv = Path(args.summary_csv) if args.summary_csv else first_existing(DEFAULT_SUMMARY_CANDIDATES)
    if summary_csv is None or not summary_csv.exists():
        raise SystemExit("No summary CSV found. Run result collection first or pass --summary-csv.")

    figure_dirs = [Path(item) for item in args.figure_dir] if args.figure_dir else DEFAULT_FIGURE_DIRS
    stage_gate_md = Path(args.stage_gate_md) if args.stage_gate_md else None
    proposed_gate_md = Path(args.proposed_gate_md) if args.proposed_gate_md else None

    write_detector_table(summary_csv, overleaf_repo / "tables" / "auto_detector_results.tex", args.top_k)
    copied_figures = copy_figures(figure_dirs, overleaf_repo)
    write_status_section(
        overleaf_repo / "sections" / "auto_experiment_status.tex",
        summary_csv,
        copied_figures,
        stage_gate_md if stage_gate_md and stage_gate_md.exists() else None,
        proposed_gate_md if proposed_gate_md and proposed_gate_md.exists() else None,
    )
    if args.update_results_section:
        ensure_section_input(
            overleaf_repo / "sections" / "05_results.tex",
            r"\input{sections/auto_experiment_status}",
        )

    print(f"Overleaf export complete: {overleaf_repo}")
    print(f"Summary CSV: {summary_csv}")
    print("Generated: tables/auto_detector_results.tex")
    print("Generated: sections/auto_experiment_status.tex")
    if copied_figures:
        print(f"Copied figures: {len(copied_figures)}")


if __name__ == "__main__":
    main()
