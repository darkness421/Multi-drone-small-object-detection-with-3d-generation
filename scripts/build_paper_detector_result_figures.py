"""Export paper-ready detector result tables and charts as PNG files."""

from __future__ import annotations

import argparse
import csv
import os
import textwrap
from pathlib import Path
from typing import Iterable

os.environ.setdefault("MPLBACKEND", "Agg")


FINAL_TABLE = Path("outputs/reports/final_detector_table_preview.csv")
GATED_RANKING = Path("outputs/reports/detector_rankings/overall_1280_completed_gated_tradeoff_ranking.csv")
PROPOSED_RUN_RANKING = Path("outputs/reports/detector_rankings/proposed_run_performance_ranking.csv")
PROPOSED_SUMMARY_RANKING = Path("outputs/reports/detector_rankings/proposed_summary_performance_ranking.csv")
PROPOSED_RUN_TRADEOFF = Path("outputs/reports/detector_rankings/proposed_run_tradeoff_ranking.csv")
PROPOSED_SUMMARY_TRADEOFF = Path("outputs/reports/detector_rankings/proposed_summary_tradeoff_ranking.csv")
RELATED_QUEUE = Path("outputs/experiments/related_work_1280_consistency_queue.csv")
RELATED_REFERENCE_LABELS = Path("paper/tables/related_work_reference_labels.csv")
RELATED_EXPERIMENT_PLAN = Path("paper/tables/related_work_detector_experiment_plan.csv")
PVALUES = Path("outputs/experiments/final_detector_pvalues.csv")
OUT_DIR = Path("outputs/reports/live")
INTERNAL_OUT_DIR = Path("outputs/reports/internal/proposed_search")

BASELINE_AP = 0.3776566666666667
BASELINE_AP50 = 0.59809
BASELINE_PARAMS = 25.3182
EXCLUDED_METHODS = {"yolov9e", "yolo9e"}
EXTRA_DETECTOR_ARTIFACTS = [
    "paper_fig08_final_ablation_main_table.png",
    "paper_fig09_final_ablation_delta_bar.png",
    "paper_fig10_final_ablation_metric_heatmap.png",
    "paper_fig11_final_detector_feature_activation_heatmap.png",
]

PAPER_MAIN_METHODS = [
    "Ours",
    "BPD-YOLO [7]",
    "SFFEF-YOLO [4]",
    "YOLOv11l",
    "YOLOv12l",
    "YOLOv8l",
    "YOLOv9c",
    "YOLOv9m",
    "RT-DETR-L",
    "CSFPR-RTDETR [11]",
    "MFFSODNet [2]",
]

PAPER_BAR_METHODS = [
    "Ours",
    "YOLOv11l",
    "YOLOv12l",
    "YOLOv8l",
    "YOLOv9c",
    "YOLOv26l",
    "YOLOv10l",
    "YOLOv5lu",
    "RT-DETR-L",
]

SCATTER_LABEL_METHODS = {
    "Ours",
    "YOLOv11l",
    "YOLOv12l",
    "YOLOv8l",
    "YOLOv9c",
    "YOLOv9m",
    "YOLOv9s",
    "YOLOv9t",
    "RT-DETR-L",
}

FINAL_ABLATION_PLAN = [
    {
        "component": "YOLOv11l baseline",
        "key": "YOLOv11l",
        "source": "final",
        "protocol": "1280, 3 seeds",
        "status": "Complete",
        "placement": "Main reference",
    },
    {
        "component": "P2/P3/P4 high-resolution heads",
        "key": "p2p4_balanced_head_only",
        "source": "proposed",
        "protocol": "1280, 3 seeds",
        "status": "Complete",
        "placement": "Ablation",
    },
    {
        "component": "P2/P3/P4 + TinyFReLU",
        "key": "p2p4_balanced_tiny_frelu",
        "source": "proposed",
        "protocol": "1280, 3 seeds",
        "status": "Complete",
        "placement": "Ablation",
    },
    {
        "component": "P2/P3/P4 + SelfAttn",
        "key": "p2p4_balanced_selfattn_only",
        "source": "proposed",
        "protocol": "1280, 3 seeds",
        "status": "Complete",
        "placement": "Ablation",
    },
    {
        "component": "Ours",
        "key": "Ours",
        "source": "final",
        "protocol": "1280, 3 seeds",
        "status": "Complete",
        "placement": "Main result",
    },
    {
        "component": "Overlap-aware NMS",
        "key": "nms_sweep",
        "source": "pending",
        "protocol": "Final checkpoint eval",
        "status": "Pending",
        "placement": "Supplementary",
    },
]

COLORS = {
    "ink": "#111827",
    "muted": "#64748B",
    "grid": "#CBD5E1",
    "header": "#E2E8F0",
    "row": "#F8FAFC",
    "row_alt": "#FFFFFF",
    "ours": "#FEF3C7",
    "ours_edge": "#F59E0B",
    "green": "#047857",
    "red": "#B91C1C",
    "blue": "#2563EB",
    "orange": "#B45309",
    "gray": "#94A3B8",
}


def setup_matplotlib():
    os.environ.setdefault("MPLCONFIGDIR", str(Path(".cache/matplotlib").resolve()))
    os.environ.setdefault("XDG_CACHE_HOME", str(Path(".cache").resolve()))
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": COLORS["grid"],
            "axes.labelcolor": COLORS["ink"],
            "xtick.color": COLORS["muted"],
            "ytick.color": COLORS["muted"],
        }
    )
    return plt, Rectangle


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def is_excluded_method(name: str) -> bool:
    normalized = name.lower().replace("-", "").replace("_", "").replace(".pt", "")
    return normalized in EXCLUDED_METHODS


def as_float(value: str | None) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except ValueError:
        return None


def fmt(value: str | float | None, digits: int = 4, blank: str = "-") -> str:
    if isinstance(value, str):
        parsed = as_float(value)
        if parsed is None:
            return blank if value == "" else value
        value = parsed
    if value is None:
        return blank
    return f"{value:.{digits}f}"


def fmt_signed(value: str | float | None, digits: int = 4) -> str:
    parsed = as_float(value) if isinstance(value, str) else value
    if parsed is None:
        return "-"
    return f"{parsed:+.{digits}f}"


def short_method(name: str) -> str:
    if name in {"Ours", "Ours: P2P4-SelfAttnFR"}:
        return "Ours"
    return name.replace("Ours: ", "Ours ").replace("P2P4-SelfAttnFR", "P2P4-SelfAttnFR")


def is_ours_method(name: str) -> bool:
    return name in {"Ours", "Ours: P2P4-SelfAttnFR"}


def display_group(group: str) -> str:
    if group == "Ours final candidate":
        return "Ours"
    if group == "Best YOLO baseline":
        return "YOLO baseline"
    return group.replace(" baseline", "")


def paper_order(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    baselines = [row for row in rows if not is_ours_method(row.get("method", ""))]
    ours = [row for row in rows if is_ours_method(row.get("method", ""))]
    return sorted(baselines, key=lambda row: as_float(row.get("AP")) or -1, reverse=True) + ours


def related_reference_labels() -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in read_csv(RELATED_REFERENCE_LABELS):
        model = row.get("model", "")
        if not model:
            continue
        number = row.get("reference_number", "").strip()
        cite_key = row.get("cite_key", "").strip()
        label = number or row.get("fallback_label", "").strip()
        if not label:
            label = "TBD" if cite_key else ""
        labels[model] = label
    return labels


def related_candidate_label(name: str, labels: dict[str, str]) -> str:
    base = name
    if name.startswith("LEAF-YOLO-"):
        base = "LEAF-YOLO"
    label = labels.get(name) or labels.get(base)
    return f"{name} [{label}]" if label else name


def wrap(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return "\n".join(textwrap.wrap(value, width=width, break_long_words=False, max_lines=2, placeholder="..."))


def main_rows() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_csv(FINAL_TABLE)
        if row.get("section") == "main_1280_completed_3seed" and not is_excluded_method(row.get("method", ""))
    ]
    return sorted(rows, key=lambda row: as_float(row.get("AP")) or -1, reverse=True)


def rows_by_method(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("method", ""): row for row in rows}


def paper_method_rows(methods: list[str]) -> list[dict[str, str]]:
    by_name = rows_by_method(main_rows())
    rows = []
    for name in methods:
        if name in by_name:
            rows.append(by_name[name])
        elif name == "Ours" and "Ours: P2P4-SelfAttnFR" in by_name:
            rows.append(by_name["Ours: P2P4-SelfAttnFR"])
    return paper_order(rows)


def final_metric_row(method: str) -> dict[str, str] | None:
    by_name = rows_by_method(main_rows())
    if method == "Ours":
        return by_name.get("Ours") or by_name.get("Ours: P2P4-SelfAttnFR")
    return by_name.get(method)


def proposed_metric_rows_by_ablation() -> dict[str, dict[str, str]]:
    rows = read_csv(PROPOSED_SUMMARY_RANKING) or read_csv(PROPOSED_RUN_RANKING)
    best: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get("ablation") or row.get("name") or row.get("method")
        if not key:
            continue
        old = best.get(key)
        if old is None or (as_float(row.get("AP")) or -1) > (as_float(old.get("AP")) or -1):
            best[key] = row
    return best


def related_external_rows() -> list[dict[str, str]]:
    rows = [row for row in read_csv(FINAL_TABLE) if row.get("section") == "related_work_external_eval_snapshot"]
    return sorted(rows, key=lambda row: as_float(row.get("AP")) or -1, reverse=True)


def pvalue_note() -> str:
    rows = {row.get("metric", ""): row for row in read_csv(PVALUES)}
    ap = as_float(rows.get("AP", {}).get("paired_t_pvalue"))
    ap50 = as_float(rows.get("AP50", {}).get("paired_t_pvalue"))
    parts = []
    if ap is not None:
        parts.append(f"AP paired t-test p={ap:.4f}")
    if ap50 is not None:
        parts.append(f"AP50 paired t-test p={ap50:.4f}")
    return "; ".join(parts)


def group_color(group: str) -> str:
    group_l = group.lower()
    if "ours" in group_l:
        return COLORS["ours"]
    if "best yolo" in group_l:
        return "#E0F2FE"
    if "large" in group_l:
        return "#EEF2FF"
    if "medium" in group_l:
        return "#ECFDF5"
    if "small" in group_l:
        return "#FFF7ED"
    if "nano" in group_l:
        return "#F1F5F9"
    if "transformer" in group_l:
        return "#FDF2F8"
    return COLORS["row"]


def draw_table(
    out: Path,
    title: str,
    subtitle: str,
    columns: list[tuple[str, float]],
    rows: list[dict[str, str]],
    row_to_values,
    *,
    figsize: tuple[float, float],
    footer: str = "",
    row_face=None,
) -> None:
    plt, Rectangle = setup_matplotlib()
    fig = plt.figure(figsize=figsize, dpi=220)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.patch.set_facecolor("#F8FAFC")

    table_x = 0.035
    table_y = 0.075 if footer else 0.045
    table_w = 0.93
    table_h = 0.885 if footer else 0.905
    nrows = max(1, len(rows))
    header_h = 0.050
    row_h = (table_h - header_h) / nrows

    ax.add_patch(Rectangle((table_x, table_y), table_w, table_h, facecolor="white", edgecolor=COLORS["grid"], linewidth=1.0))
    ax.add_patch(Rectangle((table_x, table_y + table_h - header_h), table_w, header_h, facecolor=COLORS["header"], edgecolor="none"))

    total_weight = sum(width for _, width in columns)
    x_positions = [table_x]
    cursor = table_x
    for _, width in columns:
        cursor += table_w * (width / total_weight)
        x_positions.append(cursor)

    for idx, (label, _) in enumerate(columns):
        x0, x1 = x_positions[idx], x_positions[idx + 1]
        ax.text(x0 + 0.006, table_y + table_h - 0.018, label, fontsize=7.8, fontweight="bold", color=COLORS["ink"], va="top")
        ax.plot([x1, x1], [table_y, table_y + table_h], color="#E2E8F0", linewidth=0.6)

    for ridx, row in enumerate(rows):
        y1 = table_y + table_h - header_h - ridx * row_h
        y0 = y1 - row_h
        face = row_face(row, ridx) if row_face else (COLORS["row"] if ridx % 2 == 0 else COLORS["row_alt"])
        ax.add_patch(Rectangle((table_x, y0), table_w, row_h, facecolor=face, edgecolor="none"))
        ax.plot([table_x, table_x + table_w], [y0, y0], color="#E2E8F0", linewidth=0.55)
        values = row_to_values(row)
        for cidx, value in enumerate(values):
            x0, x1 = x_positions[cidx], x_positions[cidx + 1]
            cell_w = x1 - x0
            is_number = cidx > 1 and value.replace(".", "", 1).replace("+", "", 1).replace("-", "", 1).isdigit()
            color = COLORS["ink"]
            weight = "bold" if ("Ours" in values[0] or values[0] == "Complete") else "normal"
            if value.startswith("+"):
                color = COLORS["green"]
                weight = "bold"
            if value.startswith("-") and value != "-":
                color = COLORS["red"]
            ax.text(
                x1 - 0.006 if is_number else x0 + 0.006,
                y0 + row_h * 0.55,
                value,
                fontsize=max(5.4, min(7.5, 115 * row_h)),
                color=color,
                fontweight=weight,
                va="center",
                ha="right" if is_number else "left",
                linespacing=0.95,
            )

    if footer:
        ax.text(0.04, 0.052, footer, fontsize=8.2, color=COLORS["muted"], va="bottom")

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)


def export_main_detector_table(out_dir: Path) -> Path:
    rows = paper_method_rows(PAPER_MAIN_METHODS)
    columns = [
        ("Method", 1.60),
        ("Type", 1.05),
        ("AP", 0.55),
        ("AP50", 0.55),
        ("P", 0.50),
        ("R", 0.50),
        ("F1", 0.50),
        ("Params", 0.62),
        ("GFLOPs", 0.58),
        ("Seeds", 0.82),
        ("Status", 0.90),
    ]

    def values(row: dict[str, str]) -> list[str]:
        return [
            short_method(row.get("method", "")),
            display_group(row.get("group", "")),
            fmt(row.get("AP")),
            fmt(row.get("AP50")),
            fmt(row.get("precision")),
            fmt(row.get("recall")),
            fmt(row.get("F1")),
            fmt(row.get("params_m"), 2),
            fmt(row.get("gflops"), 1),
            row.get("seeds", ""),
            "Complete",
        ]

    out = out_dir / "paper_fig01_main_detector_table.png"
    draw_table(
        out,
        "Main Detector Comparison",
        "VisDrone val, 1280 input, 3 seeds. Rows are paper-ready; related-work external eval-only rows are excluded.",
        columns,
        rows,
        values,
        figsize=(16, 8.0),
        footer=pvalue_note(),
        row_face=lambda row, _: group_color(row.get("group", "")),
    )
    return out


def export_yolo_scale_table(out_dir: Path) -> Path:
    rows = [row for row in main_rows() if "YOLO" in row.get("group", "") or row.get("method", "").startswith("YOLO")]
    out = out_dir / "paper_fig02_yolo_family_scale_table.png"

    plt, Rectangle = setup_matplotlib()
    fig = plt.figure(figsize=(15.5, 8.8), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.patch.set_facecolor("#F8FAFC")

    families = ["YOLOv5", "YOLOv8", "YOLOv9", "YOLOv10", "YOLOv11", "YOLOv12", "YOLOv26"]
    scales = ["large", "medium", "small", "nano"]

    def method_family(method: str) -> str:
        for family in families:
            if method.startswith(family):
                return family
        return method

    def method_scale(row: dict[str, str]) -> str:
        group = row.get("group", "")
        if "large" in group or row.get("method") == "YOLOv11l":
            return "large"
        if "medium" in group:
            return "medium"
        if "small" in group:
            return "small"
        if "nano" in group:
            return "nano"
        method = row.get("method", "").lower()
        if method.endswith(("l", "lu")):
            return "large"
        if method == "yolov9c":
            return "large"
        if method.endswith(("m", "mu")):
            return "medium"
        if method.endswith(("s", "su")):
            return "small"
        if method.endswith(("n", "nu", "t")):
            return "nano"
        return ""

    cells: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        family = method_family(row.get("method", ""))
        scale = method_scale(row)
        if family in families and scale in scales:
            current = cells.get((scale, family))
            if current is None or (as_float(row.get("AP")) or -1) > (as_float(current.get("AP")) or -1):
                cells[(scale, family)] = row

    ap_values = [as_float(row.get("AP")) or 0 for row in cells.values()]
    lo = min(ap_values) if ap_values else 0.0
    hi = max(ap_values) if ap_values else 1.0
    span = max(hi - lo, 1e-6)

    table_x, table_y = 0.055, 0.090
    table_w, table_h = 0.890, 0.825
    label_w = 0.090
    header_h = 0.075
    cell_w = (table_w - label_w) / len(families)
    cell_h = (table_h - header_h) / len(scales)

    ax.add_patch(Rectangle((table_x, table_y), table_w, table_h, facecolor="white", edgecolor=COLORS["grid"], linewidth=1.2))
    ax.add_patch(Rectangle((table_x, table_y + table_h - header_h), table_w, header_h, facecolor="#DBEAFE", edgecolor="none"))
    ax.add_patch(Rectangle((table_x, table_y), label_w, table_h, facecolor="#E2E8F0", edgecolor="none"))

    for cidx, family in enumerate(families):
        x0 = table_x + label_w + cidx * cell_w
        ax.text(x0 + cell_w / 2, table_y + table_h - header_h / 2, family, fontsize=11, fontweight="bold", ha="center", va="center", color=COLORS["ink"])
        ax.plot([x0, x0], [table_y, table_y + table_h], color="#CBD5E1", linewidth=0.8)
    ax.plot([table_x + table_w, table_x + table_w], [table_y, table_y + table_h], color="#CBD5E1", linewidth=0.8)

    scale_faces = {
        "large": "#EEF2FF",
        "medium": "#ECFDF5",
        "small": "#FFF7ED",
        "nano": "#F1F5F9",
    }
    for ridx, scale in enumerate(scales):
        y0 = table_y + table_h - header_h - (ridx + 1) * cell_h
        ax.text(table_x + label_w * 0.5, y0 + cell_h / 2, scale.upper(), fontsize=10.5, fontweight="bold", ha="center", va="center", color=COLORS["ink"])
        ax.plot([table_x, table_x + table_w], [y0, y0], color="#CBD5E1", linewidth=0.8)
        for cidx, family in enumerate(families):
            x0 = table_x + label_w + cidx * cell_w
            row = cells.get((scale, family))
            if not row:
                ax.add_patch(Rectangle((x0, y0), cell_w, cell_h, facecolor="#F8FAFC", edgecolor="#E2E8F0", linewidth=0.6))
                continue
            ap = as_float(row.get("AP")) or 0
            intensity = (ap - lo) / span
            base = scale_faces[scale]
            alpha = 0.35 + 0.55 * intensity
            ax.add_patch(Rectangle((x0, y0), cell_w, cell_h, facecolor=base, edgecolor="#E2E8F0", linewidth=0.6))
            ax.add_patch(Rectangle((x0 + 0.004, y0 + 0.006), cell_w - 0.008, cell_h - 0.012, facecolor="#2563EB", alpha=alpha, edgecolor="none"))
            text_color = "white" if intensity > 0.48 else COLORS["ink"]
            method = row.get("method", "").replace("YOLO", "")
            ax.text(x0 + 0.012, y0 + cell_h * 0.73, method, fontsize=10.5, fontweight="bold", color=text_color, va="center")
            ax.text(x0 + 0.012, y0 + cell_h * 0.50, f"AP {fmt(ap)}", fontsize=10.0, fontweight="bold", color=text_color, va="center")
            ax.text(
                x0 + 0.012,
                y0 + cell_h * 0.30,
                f"AP50 {fmt(row.get('AP50'))}  |  {fmt(row.get('params_m'), 1)}M",
                fontsize=8.8,
                color=text_color,
                va="center",
            )

    ax.text(
        0.055,
        0.035,
        f"YOLO scale overview: {len(cells)} selected 1280/3-seed rows; blank = not selected.",
        fontsize=10.5,
        color=COLORS["muted"],
        va="bottom",
    )
    ax.text(
        0.945,
        0.035,
        "Supplementary overview; main uses the compact top comparison table.",
        fontsize=10.5,
        color=COLORS["muted"],
        ha="right",
        va="bottom",
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out


def export_related_status_table(out_dir: Path) -> Path:
    rows = [row for row in read_csv(FINAL_TABLE) if row.get("section") == "related_work_cited_snapshot"]
    if not rows:
        rows = related_external_rows()
    rows = sorted(rows, key=lambda row: as_float(row.get("AP")) or -1, reverse=True)
    ours = final_metric_row("Ours")
    ours_ap = as_float(ours.get("AP")) if ours else None
    columns = [
        ("Method", 1.20),
        ("Protocol", 1.55),
        ("AP", 0.45),
        ("AP50", 0.45),
        ("F1", 0.45),
        ("Params", 0.50),
        ("GFLOPs", 0.50),
        ("Seeds", 0.62),
        ("dAP vs Ours", 0.58),
        ("Status", 1.40),
    ]

    def values(row: dict[str, str]) -> list[str]:
        ap = as_float(row.get("AP"))
        dap = (ap - ours_ap) if ap is not None and ours_ap is not None else None
        note = row.get("note", "")
        protocol = row.get("protocol", "")
        if "partial" in protocol:
            status = "Partial; not final"
        elif "not official" in note:
            status = "Reimpl 3-seed"
        elif "scratch" in note:
            status = "Scratch 3-seed"
        elif "official/staged" in note:
            status = "Official 3-seed"
        else:
            status = "Measured"
        return [
            row.get("method", ""),
            wrap(row.get("protocol", ""), 28),
            fmt(row.get("AP")),
            fmt(row.get("AP50")),
            fmt(row.get("F1")),
            fmt(row.get("params_m"), 2),
            fmt(row.get("gflops"), 1),
            row.get("seeds", "-"),
            fmt_signed(dap),
            wrap(status, 24),
        ]

    out = out_dir / "paper_fig03_related_work_status_table.png"
    draw_table(
        out,
        "Related-Work Detector Results",
        "Measured cited models from Sec. 2.1. Reimplementation rows are explicitly marked and separated from official checkpoints.",
        columns,
        rows,
        values,
        figsize=(15.5, max(4.8, 1.0 + 0.58 * max(1, len(rows)))),
        row_face=lambda row, idx: "#FEF3C7" if "partial" in row.get("protocol", "") else (COLORS["row"] if idx % 2 == 0 else COLORS["row_alt"]),
    )
    return out


def export_ap_ap50_bars(out_dir: Path) -> Path:
    plt, _ = setup_matplotlib()
    rows = paper_method_rows(PAPER_BAR_METHODS)
    labels = [short_method(row["method"]) for row in rows]
    ap = [as_float(row.get("AP")) or 0 for row in rows]
    ap50 = [as_float(row.get("AP50")) or 0 for row in rows]
    y = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(11.8, 7.4), dpi=220)
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#FFFFFF")
    fig.subplots_adjust(left=0.25, right=0.97, top=0.97, bottom=0.11)
    width = 0.36
    ap_bars = ax.barh([i + width / 2 for i in y], ap, width, label="AP", color="#2563EB")
    ap50_bars = ax.barh([i - width / 2 for i in y], ap50, width, label="AP50", color="#10B981")
    ax.axvline(BASELINE_AP, color="#2563EB", linestyle="--", linewidth=1.0, alpha=0.55)
    ax.axvline(BASELINE_AP50, color="#10B981", linestyle="--", linewidth=1.0, alpha=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.0)
    ax.invert_yaxis()
    ax.set_xlim(0.30, 0.63)
    ax.set_xlabel("Score")
    ax.grid(axis="x", color="#E2E8F0", linewidth=0.8)
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower right")
    for bars in (ap_bars, ap50_bars):
        for bar in bars:
            value = bar.get_width()
            ax.text(value + 0.003, bar.get_y() + bar.get_height() / 2, f"{value:.4f}", va="center", ha="left", fontsize=7.8, color=COLORS["ink"])
    out = out_dir / "paper_fig04_ap_ap50_bar_chart.png"
    fig.savefig(out, dpi=220, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return out


def export_scatter(out_dir: Path) -> Path:
    plt, _ = setup_matplotlib()
    rows = main_rows()
    fig, ax = plt.subplots(figsize=(11.2, 7.6), dpi=220)
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#FFFFFF")
    fig.subplots_adjust(left=0.10, right=0.97, top=0.97, bottom=0.10)

    palette = {
        "Ours final candidate": "#F59E0B",
        "Best YOLO baseline": "#2563EB",
        "YOLO large": "#7C3AED",
        "YOLO medium": "#059669",
        "YOLO small": "#EA580C",
        "YOLO nano": "#64748B",
        "Transformer baseline": "#DB2777",
    }
    for group in sorted({row.get("group", "") for row in rows}):
        group_rows = [row for row in rows if row.get("group", "") == group]
        x = [as_float(row.get("params_m")) or 0 for row in group_rows]
        y = [as_float(row.get("AP")) or 0 for row in group_rows]
        sizes = [max(32, (as_float(row.get("gflops")) or 20) * 1.3) for row in group_rows]
        ax.scatter(x, y, s=sizes, color=palette.get(group, COLORS["gray"]), alpha=0.82, edgecolor="white", linewidth=0.8, label=group)

    for row in rows:
        method = row.get("method", "")
        if method in SCATTER_LABEL_METHODS:
            offset = {
                "Ours": (6, 10),
                "YOLOv11l": (8, 12),
                "YOLOv12l": (30, 2),
                "YOLOv8l": (8, 5),
                "YOLOv9c": (8, -14),
                "YOLOv9m": (8, 12),
                "YOLOv9s": (8, 12),
                "YOLOv9t": (8, 10),
                "RT-DETR-L": (-72, 14),
            }.get(method, (6, 6))
            ax.annotate(
                short_method(method).replace("Ours ", "Ours\n"),
                (as_float(row.get("params_m")) or 0, as_float(row.get("AP")) or 0),
                textcoords="offset points",
                xytext=offset,
                fontsize=8.0,
                color=COLORS["ink"],
            )
    ax.axhline(BASELINE_AP, color="#2563EB", linestyle="--", linewidth=1.0, alpha=0.65)
    ax.axvline(BASELINE_PARAMS, color="#94A3B8", linestyle="--", linewidth=1.0, alpha=0.75)
    ax.set_xlabel("Parameters (M)")
    ax.set_ylabel("AP")
    ax.set_xlim(0, max((as_float(row.get("params_m")) or 0 for row in rows), default=45) + 5)
    ax.set_ylim(0.27, 0.392)
    ax.grid(color="#E2E8F0", linewidth=0.8)
    ax.legend(frameon=False, fontsize=7.1, loc="lower right", ncol=1)
    out = out_dir / "paper_fig05_ap_params_scatter.png"
    fig.savefig(out, dpi=220, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return out


def export_gated_tradeoff(out_dir: Path) -> Path:
    plt, _ = setup_matplotlib()
    rows = [row for row in read_csv(GATED_RANKING) if row.get("gated_tradeoff")]
    labels = [short_method(row.get("name", "")) for row in rows]
    values = [as_float(row.get("gated_tradeoff")) or 0 for row in rows]
    colors = [COLORS["orange"] if "Ours" in row.get("name", "") else COLORS["blue"] for row in rows]

    fig, ax = plt.subplots(figsize=(9.8, 3.8), dpi=220)
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#FFFFFF")
    fig.subplots_adjust(left=0.27, right=0.96, top=0.94, bottom=0.20)
    y = list(range(len(rows)))
    bars = ax.barh(y, values, color=colors, height=0.46)
    ax.axvline(1.0, color=COLORS["muted"], linestyle="--", linewidth=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Gated trade-off score")
    ax.set_xlim(0, max(values + [1.0]) * 1.20)
    ax.grid(axis="x", color="#E2E8F0", linewidth=0.8)
    ax.grid(axis="y", visible=False)
    for bar, value in zip(bars, values, strict=False):
        ax.text(value + 0.025, bar.get_y() + bar.get_height() / 2, f"{value:.3f}", ha="left", va="center", fontsize=10, fontweight="bold", color=COLORS["ink"])
    out = out_dir / "paper_fig06_gated_tradeoff_bar.png"
    fig.savefig(out, dpi=220, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return out


def export_status_overview(out_dir: Path) -> Path:
    rows = [
        {
            "block": "Final detector comparison",
            "protocol": "VisDrone val, 1280, 3-seed",
            "status": "Complete",
            "placement": "Main",
            "next": "Use Ours as the final trade-off detector; describe SAFR-YOLO/P2P4-SelfAttnFR in the method.",
        },
        {
            "block": "YOLO-family scale coverage",
            "protocol": "VisDrone val, 1280, 3-seed",
            "status": "Complete",
            "placement": "Main backup or Suppl.",
            "next": "Use full nano/small/medium/large coverage as supplementary reviewer evidence.",
        },
        {
            "block": "Sec. 2.1 related-work models",
            "protocol": "Only cited models; 1280 where runnable",
            "status": "6 cited rows complete",
            "placement": "Suppl. / status note",
            "next": "Main uses compact status table; supplementary keeps coverage notes for non-runnable citations.",
        },
        {
            "block": "NMS / postprocess sweep",
            "protocol": "1280 eval only, single seed",
            "status": "Not main-ready",
            "placement": "Suppl.",
            "next": "Use as analysis unless confirmed with final detector and 3 seeds.",
        },
        {
            "block": "Raw AP architecture search",
            "protocol": "1280, mostly single seed",
            "status": "Screening only",
            "placement": "Optional Suppl.",
            "next": "Do not put in main because larger high-AP variants distract from size claim.",
        },
        {
            "block": "Heatmap / input-size / categories",
            "protocol": "Final checkpoints",
            "status": "Feature heatmap complete",
            "placement": "Suppl.",
            "next": "Use feature-activation wording; do not claim class-logit Grad-CAM attribution.",
        },
        {
            "block": "TinyPerson corrected check",
            "protocol": "TinyPerson original-window, 1280, Ours vs YOLOv9m",
            "status": "Complete diagnostic",
            "placement": "Suppl. limitation",
            "next": "Do not mix legacy 640 rows into the paper comparison; report corrected 1280 only if we discuss domain transfer.",
        },
        {
            "block": "3D benchmark and reasoner",
            "protocol": "NVIDIA Isaac / 3D / LLM",
            "status": "Pending",
            "placement": "Main system + Suppl.",
            "next": "Start after 2D detector table is locked.",
        },
    ]
    columns = [
        ("Experiment Block", 1.55),
        ("Protocol", 1.45),
        ("Status", 0.95),
        ("Placement", 1.05),
        ("Next / Missing", 2.25),
    ]

    def values(row: dict[str, str]) -> list[str]:
        return [
            wrap(row["block"], 26),
            wrap(row["protocol"], 26),
            row["status"],
            row["placement"],
            wrap(row["next"], 44),
        ]

    def face(row: dict[str, str], idx: int) -> str:
        status = row["status"].lower()
        if "complete" in status:
            return "#ECFDF5"
        if "pending" in status or "not main" in status:
            return "#FFF7ED"
        if "screening" in status:
            return "#F1F5F9"
        return COLORS["row"] if idx % 2 == 0 else COLORS["row_alt"]

    out = out_dir / "paper_fig07_experiment_status_overview.png"
    draw_table(
        out,
        "Experiment Result Readiness Overview",
        "Completed results are paper-ready; pending rows should remain blank/marked until the matching protocol is finished.",
        columns,
        rows,
        values,
        figsize=(15.5, 8.2),
        row_face=face,
    )
    return out


def export_ablation_status_table(out_dir: Path) -> Path:
    proposed_by_key = proposed_metric_rows_by_ablation()
    rows: list[dict[str, str]] = []
    for item in FINAL_ABLATION_PLAN:
        metric: dict[str, str] | None = None
        if item["source"] == "final":
            metric = final_metric_row(item["key"])
        elif item["source"] == "proposed":
            metric = proposed_by_key.get(item["key"])

        row = dict(item)
        if metric:
            row.update(
                {
                    "AP": metric.get("AP", ""),
                    "AP50": metric.get("AP50", ""),
                    "F1": metric.get("F1", ""),
                    "Params": metric.get("params_m") or metric.get("ParamsM") or "",
                    "GFLOPs": metric.get("gflops") or metric.get("GFLOPs") or "",
                    "seeds": metric.get("seeds") or metric.get("seed_count") or metric.get("n") or "",
                }
            )
        else:
            row.update({"AP": "", "AP50": "", "F1": "", "Params": "", "GFLOPs": "", "seeds": ""})
        rows.append(row)

    columns = [
        ("Ablation Row", 1.65),
        ("Protocol", 1.10),
        ("AP", 0.45),
        ("AP50", 0.45),
        ("F1", 0.45),
        ("Params", 0.55),
        ("GFLOPs", 0.55),
        ("Seeds", 0.55),
        ("Status", 0.75),
        ("Placement", 0.95),
    ]

    def values(row: dict[str, str]) -> list[str]:
        return [
            wrap(row["component"], 30),
            wrap(row["protocol"], 22),
            fmt(row.get("AP"), blank=""),
            fmt(row.get("AP50"), blank=""),
            fmt(row.get("F1"), blank=""),
            fmt(row.get("Params"), 2, blank=""),
            fmt(row.get("GFLOPs"), 1, blank=""),
            row.get("seeds", ""),
            row["status"],
            row["placement"],
        ]

    def face(row: dict[str, str], idx: int) -> str:
        status = row["status"].lower()
        if "complete" in status:
            return "#ECFDF5" if "ours" not in row["component"].lower() else COLORS["ours"]
        if "running" in status:
            return "#FEF3C7"
        if "queued" in status or "pending" in status or "partial" in status:
            return "#FFF7ED"
        return COLORS["row"] if idx % 2 == 0 else COLORS["row_alt"]

    out = out_dir / "paper_fig08_final_ablation_status_table.png"
    draw_table(
        out,
        "Final Detector Ablation Status",
        "Paper-facing ablation rows only; exploratory search variants are exported separately under outputs/reports/internal.",
        columns,
        rows,
        values,
        figsize=(16.2, 6.0),
        row_face=face,
    )
    return out


def export_internal_proposed_search(out_dir: Path = INTERNAL_OUT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    run_rows = read_csv(PROPOSED_RUN_RANKING)[:20]
    tradeoff_rows = read_csv(PROPOSED_RUN_TRADEOFF)[:20]
    summary_rows = read_csv(PROPOSED_SUMMARY_RANKING)

    table_columns = [
        ("Candidate", 1.45),
        ("Ablation", 1.35),
        ("Seed(s)", 0.55),
        ("Status", 0.65),
        ("AP", 0.45),
        ("AP50", 0.45),
        ("P", 0.42),
        ("R", 0.42),
        ("F1", 0.42),
        ("Params", 0.55),
        ("GFLOPs", 0.55),
        ("dAP", 0.50),
    ]

    def values(row: dict[str, str]) -> list[str]:
        return [
            wrap(row.get("name", ""), 24),
            wrap(row.get("ablation", ""), 28),
            row.get("seed") or row.get("seeds") or row.get("n", ""),
            row.get("status", ""),
            fmt(row.get("AP")),
            fmt(row.get("AP50")),
            fmt(row.get("P")),
            fmt(row.get("R")),
            fmt(row.get("F1")),
            fmt(row.get("ParamsM"), 2),
            fmt(row.get("GFLOPs"), 1),
            fmt_signed(row.get("dAP")),
        ]

    def face(row: dict[str, str], idx: int) -> str:
        name = row.get("name", "")
        if name == "P2P4-SelfAttnFR":
            return COLORS["ours"]
        if row.get("status") != "completed":
            return "#FFF7ED"
        return COLORS["row"] if idx % 2 == 0 else COLORS["row_alt"]

    top_perf = out_dir / "internal_proposed_search_top20_performance.png"
    draw_table(
        top_perf,
        "Internal Proposed Search",
        "For lab review only. Do not insert this broad architecture-search table into the paper.",
        table_columns,
        run_rows,
        values,
        figsize=(17.2, 11.2),
        row_face=face,
    )
    files.append(top_perf)

    top_trade = out_dir / "internal_proposed_search_top20_tradeoff.png"
    draw_table(
        top_trade,
        "Internal Proposed Search Trade-off",
        "For lab review only. Paper-facing trade-off uses only the final 3-seed detector table.",
        table_columns,
        tradeoff_rows,
        values,
        figsize=(17.2, 11.2),
        row_face=face,
    )
    files.append(top_trade)

    if summary_rows:
        plt, _ = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(10.6, 6.8), dpi=220)
        fig.patch.set_facecolor("#F8FAFC")
        ax.set_facecolor("#FFFFFF")
        fig.subplots_adjust(left=0.10, right=0.96, top=0.96, bottom=0.11)
        for row in summary_rows:
            ap = as_float(row.get("AP"))
            params = as_float(row.get("ParamsM"))
            if ap is None or params is None:
                continue
            color = COLORS["orange"] if row.get("name") == "P2P4-SelfAttnFR" else "#64748B"
            size = 72 if row.get("name") == "P2P4-SelfAttnFR" else 46
            ax.scatter(params, ap, s=size, color=color, edgecolor="white", linewidth=0.8, alpha=0.90)
            if row.get("name") == "P2P4-SelfAttnFR" or row.get("rank") in {"1", "2", "3"}:
                ax.annotate(row.get("name", ""), (params, ap), textcoords="offset points", xytext=(6, 6), fontsize=8.0, color=COLORS["ink"])
        ax.axhline(BASELINE_AP, color="#2563EB", linestyle="--", linewidth=1.0, alpha=0.65)
        ax.axvline(BASELINE_PARAMS, color="#94A3B8", linestyle="--", linewidth=1.0, alpha=0.75)
        ax.set_xlabel("Parameters (M)")
        ax.set_ylabel("AP")
        ax.grid(color="#E2E8F0", linewidth=0.8)
        scatter = out_dir / "internal_proposed_search_ap_params_scatter.png"
        fig.savefig(scatter, dpi=220, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.12)
        plt.close(fig)
        files.append(scatter)

    manifest = out_dir / "README.md"
    manifest.write_text(
        "\n".join(
            [
                "# Internal Proposed Detector Search",
                "",
                "These figures are for lab-side model selection only.",
                "They intentionally include single-seed and partially confirmed proposed variants such as P2-CBAM-FR, P2-DCT-FR, wavelet, DCT, SE, and DynFreq trials.",
                "",
                "Do not insert these broad search figures into the ACCV paper. Paper-facing figures should use only:",
                "- final `Ours` rows",
                "- YOLO-family comparisons",
                "- final detector ablation rows",
                "- related-work comparison rows",
                "",
                "Generated files:",
                *[f"- `{path.name}`" for path in files],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    files.append(manifest)
    return files


def export_manifest(out_dir: Path, files: Iterable[Path]) -> Path:
    manifest = out_dir / "paper_detector_figures_manifest.md"
    lines = [
        "# Paper Detector Figure PNG Manifest",
        "",
        "Generated files for LaTeX/Overleaf insertion. The PNGs intentionally omit large embedded titles because the paper captions carry the figure titles.",
        "Rows with only 640-pixel evaluation are excluded from paper-facing 1280-pixel figures. Blank cells in the YOLO-family scale overview are unselected family-scale combinations, not unfinished paper claims. YOLOv9c is included as the YOLOv9 large-anchor row; YOLOv9e is excluded from the paper-facing comparison because it is outside the target size regime.",
        "Paper-facing detector figures are restricted to final Ours, YOLO-family baselines, final ablations, and related-work comparison/status rows. Broad proposed-search candidates are exported separately under `outputs/reports/internal/proposed_search/` for lab review only.",
        "",
    ]
    for path in files:
        lines.append(f"- `{path.name}`")
    lines.extend(
        [
            "",
            "Main-paper recommended:",
            "- `paper_fig01_main_detector_table.png`",
            "- `paper_fig04_ap_ap50_bar_chart.png`",
            "- `paper_fig05_ap_params_scatter.png`",
            "- `paper_fig06_gated_tradeoff_bar.png`",
            "- `paper_fig08_final_ablation_main_table.png`",
            "- `paper_fig08_final_ablation_status_table.png`",
            "",
            "Supplementary or appendix recommended:",
            "- `paper_fig02_yolo_family_scale_table.png`",
            "- `paper_fig03_related_work_status_table.png`",
            "- `paper_fig07_experiment_status_overview.png`",
            "- `paper_fig09_final_ablation_delta_bar.png`",
            "- `paper_fig10_final_ablation_metric_heatmap.png`",
            "- `paper_fig11_final_detector_feature_activation_heatmap.png`",
            "",
            "Internal-only diagnostics:",
            "- Auxiliary cross-dataset stress-test artifacts are intentionally excluded from this paper-facing figure manifest.",
        ]
    )
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build paper-ready detector result PNGs.")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [
        export_main_detector_table(out_dir),
        export_yolo_scale_table(out_dir),
        export_related_status_table(out_dir),
        export_ap_ap50_bars(out_dir),
        export_scatter(out_dir),
        export_gated_tradeoff(out_dir),
        export_status_overview(out_dir),
        export_ablation_status_table(out_dir),
    ]
    existing_names = {path.name for path in files}
    for name in EXTRA_DETECTOR_ARTIFACTS:
        path = out_dir / name
        if path.exists() and name not in existing_names:
            files.append(path)
            existing_names.add(name)
    internal_files = export_internal_proposed_search()
    manifest = export_manifest(out_dir, files)
    for path in [*files, manifest, *internal_files]:
        print(path)


if __name__ == "__main__":
    main()
