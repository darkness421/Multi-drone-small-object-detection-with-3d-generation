"""Build paper-ready final detector ablation tables and figures."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


SUMMARY_CSV = Path("outputs/experiments/final_p2p4_selfattnfr_ablation_summary.csv")
FINAL_TABLE_CSV = Path("outputs/reports/final_detector_table_preview.csv")
OUT_DIR = Path("outputs/reports/live")
SUPP_DIR = OUT_DIR / "supplementary_detector_analysis"
PAPER_TABLE_DIR = Path("paper/tables")

BASELINE_NAME = "YOLOv11l"
OURS_NAME = "Ours: P2P4-SelfAttnFR"
P2P4_PARAMS_M = 20.82
P2P4_GFLOPS = 109.3

MAIN_ABLATION_ROWS = [
    {
        "component": "YOLOv11l baseline",
        "short": "Baseline",
        "key": BASELINE_NAME,
        "source": "final",
        "note": "baseline detector",
    },
    {
        "component": "P2/P3/P4 heads",
        "short": "P2P4",
        "key": "p2p4_balanced_head_only",
        "source": "ablation",
        "note": "high-resolution heads",
    },
    {
        "component": "P2/P3/P4 + TinyFReLU",
        "short": "+ TinyFReLU",
        "key": "p2p4_balanced_tiny_frelu",
        "source": "ablation",
        "note": "activation only",
    },
    {
        "component": "P2/P3/P4 + SelfAttn",
        "short": "+ SelfAttn",
        "key": "p2p4_balanced_selfattn_only",
        "source": "ablation",
        "note": "attention refinement",
    },
    {
        "component": "P2/P3/P4 + SelfAttnFR",
        "short": "Ours",
        "key": OURS_NAME,
        "source": "final",
        "note": "final selected detector",
    },
]

SUPP_ABLATION_KEYS = {
    "p2p4_balanced_head_only": "P2/P3/P4 heads",
    "p2p4_balanced_tiny_frelu": "P2/P3/P4 + TinyFReLU",
    "p2p4_balanced_selfattn_only": "P2/P3/P4 + SelfAttn",
    "p2p4_balanced_selfattn_tiny_frelu": "P2/P3/P4 + SelfAttnFR",
    "p2p4_balanced_se_tiny_frelu": "P2/P3/P4 + SE + TinyFReLU",
    "p2p4_balanced_dynfreq_p2_tiny_frelu": "P2/P3/P4 + DynFreq-P2 + TinyFReLU",
    "p2p4_balanced_dynfreq_small_tiny_frelu": "P2/P3/P4 + DynFreq-small + TinyFReLU",
}


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#CBD5E1",
            "axes.labelcolor": "#111827",
            "xtick.color": "#334155",
            "ytick.color": "#334155",
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "font.size": 9,
        }
    )
    return plt


def read_csv(path: Path) -> list[dict[str, str]]:
    csv_path = resolve_path(path)
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> Path:
    out = resolve_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return out


def ffloat(value: str | None) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except ValueError:
        return None


def fmt(value: float | None, digits: int = 4) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def fmt_pm(mean: float | None, std: float | None, digits: int = 4) -> str:
    if mean is None:
        return "-"
    if std is None:
        return fmt(mean, digits)
    return f"{mean:.{digits}f} +/- {std:.{digits}f}"


def fmt_delta(value: float | None) -> str:
    return "-" if value is None else f"{value:+.4f}"


def final_rows_by_method() -> dict[str, dict[str, str]]:
    rows = [row for row in read_csv(FINAL_TABLE_CSV) if row.get("section") == "main_1280_completed_3seed"]
    return {row.get("method", ""): row for row in rows}


def summary_rows_by_ablation() -> dict[str, dict[str, str]]:
    return {row.get("ablation", ""): row for row in read_csv(SUMMARY_CSV) if row.get("ablation")}


def final_metric_row(method: str) -> dict[str, Any] | None:
    row = final_rows_by_method().get(method)
    if row is None:
        return None
    return {
        "AP": ffloat(row.get("AP")),
        "AP_std": ffloat(row.get("AP_std")),
        "AP50": ffloat(row.get("AP50")),
        "AP50_std": ffloat(row.get("AP50_std")),
        "P": ffloat(row.get("precision")),
        "R": ffloat(row.get("recall")),
        "F1": ffloat(row.get("F1")),
        "F1_std": None,
        "ParamsM": ffloat(row.get("params_m")),
        "GFLOPs": ffloat(row.get("gflops")),
        "seeds": row.get("seeds", ""),
        "seed_count": row.get("seed_count", ""),
        "source_note": row.get("note", ""),
    }


def ablation_metric_row(ablation_key: str) -> dict[str, Any] | None:
    row = summary_rows_by_ablation().get(ablation_key)
    if row is None:
        return None
    return {
        "AP": ffloat(row.get("best_AP_mean")),
        "AP_std": ffloat(row.get("best_AP_std")),
        "AP50": ffloat(row.get("best_AP50_mean")),
        "AP50_std": ffloat(row.get("best_AP50_std")),
        "P": ffloat(row.get("best_precision_mean")),
        "R": ffloat(row.get("best_recall_mean")),
        "F1": ffloat(row.get("best_F1_mean")),
        "F1_std": ffloat(row.get("best_F1_std")),
        "ParamsM": P2P4_PARAMS_M,
        "GFLOPs": P2P4_GFLOPS,
        "seeds": row.get("seeds", ""),
        "seed_count": row.get("seed_count", ""),
        "source_note": row.get("proposed_module", ""),
    }


def metric_for_item(item: dict[str, str]) -> dict[str, Any] | None:
    if item["source"] == "final":
        return final_metric_row(item["key"])
    return ablation_metric_row(item["key"])


def main_ablation_rows() -> list[dict[str, str]]:
    baseline = final_metric_row(BASELINE_NAME) or {}
    baseline_ap = baseline.get("AP")
    baseline_ap50 = baseline.get("AP50")
    baseline_f1 = baseline.get("F1")
    rows: list[dict[str, str]] = []
    for item in MAIN_ABLATION_ROWS:
        metric = metric_for_item(item) or {}
        ap = metric.get("AP")
        ap50 = metric.get("AP50")
        f1_value = metric.get("F1")
        rows.append(
            {
                "component": item["component"],
                "short": item["short"],
                "AP": fmt_pm(ap, metric.get("AP_std")),
                "AP_raw": "" if ap is None else f"{ap:.8f}",
                "AP50": fmt_pm(ap50, metric.get("AP50_std")),
                "AP50_raw": "" if ap50 is None else f"{ap50:.8f}",
                "F1": fmt_pm(f1_value, metric.get("F1_std")),
                "F1_raw": "" if f1_value is None else f"{f1_value:.8f}",
                "dAP_vs_YOLOv11l": fmt_delta(None if ap is None or baseline_ap is None else ap - baseline_ap),
                "dAP50_vs_YOLOv11l": fmt_delta(None if ap50 is None or baseline_ap50 is None else ap50 - baseline_ap50),
                "dF1_vs_YOLOv11l": fmt_delta(None if f1_value is None or baseline_f1 is None else f1_value - baseline_f1),
                "ParamsM": fmt(metric.get("ParamsM"), 2),
                "GFLOPs": fmt(metric.get("GFLOPs"), 1),
                "seeds": metric.get("seed_count") or metric.get("seeds", ""),
                "note": item["note"],
            }
        )
    return rows


def supplementary_ablation_rows() -> list[dict[str, str]]:
    baseline = final_metric_row(BASELINE_NAME) or {}
    baseline_ap = baseline.get("AP")
    baseline_ap50 = baseline.get("AP50")
    baseline_f1 = baseline.get("F1")
    rows: list[dict[str, str]] = []
    for key, label in SUPP_ABLATION_KEYS.items():
        metric = final_metric_row(OURS_NAME) if key == "p2p4_balanced_selfattn_tiny_frelu" else ablation_metric_row(key)
        if metric is None:
            continue
        ap = metric.get("AP")
        ap50 = metric.get("AP50")
        f1_value = metric.get("F1")
        seed_count = metric.get("seed_count", "")
        protocol = "3-seed" if seed_count == "3" else f"{seed_count}-seed exploratory"
        rows.append(
            {
                "component": label,
                "ablation": key,
                "protocol": protocol,
                "AP": fmt_pm(ap, metric.get("AP_std")),
                "AP_raw": "" if ap is None else f"{ap:.8f}",
                "AP50": fmt_pm(ap50, metric.get("AP50_std")),
                "AP50_raw": "" if ap50 is None else f"{ap50:.8f}",
                "F1": fmt_pm(f1_value, metric.get("F1_std")),
                "F1_raw": "" if f1_value is None else f"{f1_value:.8f}",
                "dAP_vs_YOLOv11l": fmt_delta(None if ap is None or baseline_ap is None else ap - baseline_ap),
                "dAP50_vs_YOLOv11l": fmt_delta(None if ap50 is None or baseline_ap50 is None else ap50 - baseline_ap50),
                "dF1_vs_YOLOv11l": fmt_delta(None if f1_value is None or baseline_f1 is None else f1_value - baseline_f1),
                "seeds": metric.get("seeds", ""),
                "note": "final" if key == "p2p4_balanced_selfattn_tiny_frelu" else "ablation",
            }
        )
    return rows


def latex_escape(value: str) -> str:
    return (
        value.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def write_main_latex(rows: list[dict[str, str]], out: Path) -> Path:
    path = resolve_path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{lcccccc}",
        "\\toprule",
        "Component & AP & AP50 & F1 & $\\Delta$AP & Params & Seeds \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{latex_escape(row['component'])} & {row['AP'].replace('+/-', '$\\pm$')} & "
            f"{row['AP50'].replace('+/-', '$\\pm$')} & {row['F1'].replace('+/-', '$\\pm$')} & "
            f"{row['dAP_vs_YOLOv11l']} & {row['ParamsM']}M & {row['seeds']} \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_supp_latex(rows: list[dict[str, str]], out: Path) -> Path:
    path = resolve_path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Ablation & Protocol & AP & AP50 & F1 & $\\Delta$AP \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{latex_escape(row['component'])} & {latex_escape(row['protocol'])} & "
            f"{row['AP'].replace('+/-', '$\\pm$')} & {row['AP50'].replace('+/-', '$\\pm$')} & "
            f"{row['F1'].replace('+/-', '$\\pm$')} & {row['dAP_vs_YOLOv11l']} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def draw_table_png(rows: list[dict[str, str]], out: Path) -> Path:
    plt = setup_matplotlib()
    from matplotlib.patches import Rectangle

    columns = [
        ("Component", 2.1),
        ("AP", 1.0),
        ("AP50", 1.0),
        ("F1", 1.0),
        ("dAP", 0.72),
        ("Params", 0.70),
        ("Seeds", 0.55),
        ("Note", 1.10),
    ]
    values = [
        [
            row["component"],
            row["AP"],
            row["AP50"],
            row["F1"],
            row["dAP_vs_YOLOv11l"],
            f"{row['ParamsM']}M" if row["ParamsM"] != "-" else "-",
            row["seeds"],
            row["note"],
        ]
        for row in rows
    ]
    fig = plt.figure(figsize=(13.8, 4.1), dpi=240)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.patch.set_facecolor("white")

    x0, y0, width, height = 0.025, 0.08, 0.95, 0.84
    header_h = 0.13
    row_h = (height - header_h) / len(values)
    total = sum(weight for _, weight in columns)
    xs = [x0]
    cur = x0
    for _, weight in columns:
        cur += width * weight / total
        xs.append(cur)

    ax.add_patch(Rectangle((x0, y0), width, height, facecolor="white", edgecolor="#CBD5E1", linewidth=0.8))
    ax.add_patch(Rectangle((x0, y0 + height - header_h), width, header_h, facecolor="#E2E8F0", edgecolor="none"))
    for idx, (label, _) in enumerate(columns):
        ax.text(xs[idx] + 0.006, y0 + height - 0.045, label, fontsize=8.0, fontweight="bold", color="#111827", va="top")
        ax.plot([xs[idx + 1], xs[idx + 1]], [y0, y0 + height], color="#E2E8F0", linewidth=0.5)

    for ridx, row_values in enumerate(values):
        y_top = y0 + height - header_h - ridx * row_h
        y_bot = y_top - row_h
        component = row_values[0]
        face = "#FEF3C7" if "SelfAttnFR" in component else "#F8FAFC" if ridx % 2 == 0 else "white"
        ax.add_patch(Rectangle((x0, y_bot), width, row_h, facecolor=face, edgecolor="none"))
        ax.plot([x0, x0 + width], [y_bot, y_bot], color="#E2E8F0", linewidth=0.5)
        for cidx, value in enumerate(row_values):
            color = "#111827"
            weight = "bold" if "SelfAttnFR" in component else "normal"
            if value.startswith("+"):
                color = "#047857"
                weight = "bold"
            elif value.startswith("-") and value != "-":
                color = "#B45309"
            ha = "right" if cidx in {1, 2, 3, 4, 5, 6} else "left"
            x_text = xs[cidx + 1] - 0.006 if ha == "right" else xs[cidx] + 0.006
            ax.text(x_text, y_bot + row_h * 0.55, value, fontsize=7.2, color=color, fontweight=weight, va="center", ha=ha)

    ax.text(
        x0,
        0.025,
        "VisDrone val, 1280 input. Deltas are relative to YOLOv11l. P2P4 rows use the selected P2P4-SelfAttnFR model profile for Params/GFLOPs.",
        fontsize=7.2,
        color="#64748B",
        va="bottom",
    )
    out_path = resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=240, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return out_path


def draw_delta_bar(rows: list[dict[str, str]], out: Path) -> Path:
    plt = setup_matplotlib()
    names = [row["short"] for row in rows]
    x_values = list(range(len(rows)))
    metrics = [
        ("dAP_vs_YOLOv11l", "dAP", "#2563EB"),
        ("dAP50_vs_YOLOv11l", "dAP50", "#059669"),
        ("dF1_vs_YOLOv11l", "dF1", "#D97706"),
    ]
    fig, ax = plt.subplots(figsize=(9.4, 4.8), dpi=240)
    width = 0.24
    all_values: list[float] = []
    for midx, (key, label, color) in enumerate(metrics):
        values = [ffloat(row[key]) or 0.0 for row in rows]
        all_values.extend(values)
        offsets = [x + (midx - 1) * width for x in x_values]
        ax.bar(offsets, values, width=width, label=label, color=color, alpha=0.88)
        for x, value in zip(offsets, values):
            if abs(value) < 0.00005:
                continue
            ax.text(
                x,
                value + (0.00018 if value >= 0 else -0.00022),
                f"{value:+.4f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=6.4,
                rotation=90,
            )
    ax.axhline(0, color="#111827", linewidth=0.8)
    ymin = min(all_values + [0.0])
    ymax = max(all_values + [0.0])
    ax.set_ylim(ymin - 0.0013, ymax + 0.0012)
    ax.set_xticks(x_values)
    ax.set_xticklabels(names, rotation=0)
    ax.set_ylabel("Delta vs YOLOv11l")
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(ncol=3, frameon=False, loc="upper left")
    out_path = resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=240, facecolor="white", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return out_path


def draw_metric_heatmap(rows: list[dict[str, str]], out: Path) -> Path:
    plt = setup_matplotlib()
    import numpy as np

    metrics = ["dAP_vs_YOLOv11l", "dAP50_vs_YOLOv11l", "dF1_vs_YOLOv11l"]
    labels = ["dAP", "dAP50", "dF1"]
    data = np.array([[ffloat(row[key]) or 0.0 for key in metrics] for row in rows], dtype=float)
    vmax = max(float(abs(data).max()), 0.001)
    fig_h = max(4.0, 0.48 * len(rows) + 1.1)
    fig, ax = plt.subplots(figsize=(7.5, fig_h), dpi=240)
    im = ax.imshow(data, cmap="RdYlGn", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([row["component"] for row in rows])
    for y_idx, row_values in enumerate(data):
        for x_idx, value in enumerate(row_values):
            ax.text(x_idx, y_idx, f"{value:+.4f}", ha="center", va="center", fontsize=7.2, color="#111827")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.032, pad=0.025)
    cbar.set_label("delta")
    out_path = resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=240, facecolor="white", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return out_path


def write_manifest(paths: list[Path], out: Path) -> Path:
    lines = [
        "# Final Ablation Paper Artifacts",
        "",
        "Use the main table/bar chart in the detector experiment section. Put the full ablation table/heatmap in supplementary material.",
        "",
        "Generated files:",
    ]
    lines.extend(f"- `{path}`" for path in paths)
    lines.extend(
        [
            "",
            "Recommended placement:",
            "- Main paper: `paper_fig08_final_ablation_main_table.png` or `final_ablation_main_table.tex`.",
            "- Main or supplementary: `paper_fig09_final_ablation_delta_bar.png`.",
            "- Supplementary: `paper_fig10_final_ablation_metric_heatmap.png` and `final_ablation_supplementary_table.tex`.",
            "",
        ]
    )
    out_path = resolve_path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--supp-dir", default=str(SUPP_DIR))
    parser.add_argument("--paper-table-dir", default=str(PAPER_TABLE_DIR))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    supp_dir = Path(args.supp_dir)
    paper_table_dir = Path(args.paper_table_dir)

    main_rows = main_ablation_rows()
    supp_rows = supplementary_ablation_rows()

    main_fields = [
        "component",
        "short",
        "AP",
        "AP_raw",
        "AP50",
        "AP50_raw",
        "F1",
        "F1_raw",
        "dAP_vs_YOLOv11l",
        "dAP50_vs_YOLOv11l",
        "dF1_vs_YOLOv11l",
        "ParamsM",
        "GFLOPs",
        "seeds",
        "note",
    ]
    supp_fields = [
        "component",
        "ablation",
        "protocol",
        "AP",
        "AP_raw",
        "AP50",
        "AP50_raw",
        "F1",
        "F1_raw",
        "dAP_vs_YOLOv11l",
        "dAP50_vs_YOLOv11l",
        "dF1_vs_YOLOv11l",
        "seeds",
        "note",
    ]

    written = [
        write_csv(out_dir / "final_ablation_main_table.csv", main_rows, main_fields),
        write_csv(supp_dir / "final_ablation_supplementary_table.csv", supp_rows, supp_fields),
        write_main_latex(main_rows, paper_table_dir / "final_ablation_main_table.tex"),
        write_supp_latex(supp_rows, paper_table_dir / "final_ablation_supplementary_table.tex"),
        draw_table_png(main_rows, out_dir / "paper_fig08_final_ablation_main_table.png"),
        draw_delta_bar(main_rows, out_dir / "paper_fig09_final_ablation_delta_bar.png"),
        draw_metric_heatmap(supp_rows, out_dir / "paper_fig10_final_ablation_metric_heatmap.png"),
    ]
    written.append(write_manifest(written, out_dir / "final_ablation_artifact_manifest.md"))

    for path in written:
        print(path)


if __name__ == "__main__":
    main()
