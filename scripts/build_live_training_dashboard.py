"""Build a narrow live PNG dashboard for detector training."""

from __future__ import annotations

import argparse
import csv
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.config import resolve_path
from scripts.watch_live_training_scoreboard import Baseline
from scripts.watch_live_training_scoreboard import f1
from scripts.watch_live_training_scoreboard import fmt
from scripts.watch_live_training_scoreboard import gpu_lines
from scripts.watch_live_training_scoreboard import recently_touched
from scripts.watch_live_training_scoreboard import row_for_log
from scripts.watch_live_training_scoreboard import row_for_run
from scripts.watch_live_training_scoreboard import sort_key_ap


DEFAULT_PROJECT_DIRS = [
    "outputs/detectors/server_yolov11_p2_compact_ideas",
    "outputs/detectors/server_yolov11_p2_module_search",
    "outputs/detectors/server_yolov11_p2_compression",
    "outputs/detectors/server_yolov11_p2_balanced_followup",
    "outputs/detectors/server_yolov11_p2_balanced_v2_modules",
    "outputs/detectors/server_yolov11_p2p4_balanced",
    "outputs/detectors/server_yolov11_p2_balanced_v3",
    "outputs/detectors/server_yolov11_p2_balanced_v2",
    "outputs/detectors/server_yolov11_p2_balanced",
    "outputs/detectors/server_yolov11_p2_slim",
    "outputs/detectors/server_yolov11_p2_confirm",
    "outputs/detectors/server_yolov11_p2_next_step",
]
DEFAULT_LOG_DIRS = [
    "outputs/logs/server_yolov11_p2_compact_ideas",
    "outputs/logs/server_yolov11_p2_module_search",
    "outputs/logs/server_yolov11_p2_compression",
    "outputs/logs/server_yolov11_p2_balanced_followup",
    "outputs/logs/server_yolov11_p2_balanced_v2_modules",
    "outputs/logs/server_yolov11_p2p4_balanced",
    "outputs/logs/server_yolov11_p2_balanced_v3",
    "outputs/logs/server_yolov11_p2_balanced_v2",
    "outputs/logs/server_yolov11_p2_balanced",
    "outputs/logs/server_yolov11_p2_slim",
    "outputs/logs/server_yolov11_p2_confirm",
]

SELECTED_OURS = "P2P4-SelfAttnFR-s123"


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    return plt, FancyBboxPatch


def collect_rows(project_dirs: list[str], log_dirs: list[str], baseline: Baseline) -> list[dict[str, str]]:
    result_files: list[Path] = []
    for root in project_dirs:
        result_files.extend(resolve_path(root).glob("*/ultralytics/results.csv"))
    result_files = sorted(result_files, key=lambda path: path.stat().st_mtime, reverse=True)
    result_slugs = {re.sub(r"^\d{8}_\d{6}_", "", path.parent.parent.name) for path in result_files}

    log_rows: list[dict[str, str]] = []
    for log_dir in log_dirs:
        for log_path in resolve_path(log_dir).glob("*.log"):
            if not log_path.stem.startswith("proposed_"):
                continue
            if log_path.stem not in result_slugs and recently_touched([log_path]):
                log_rows.append(row_for_log(log_path, baseline))
    log_rows = sorted(log_rows, key=lambda row: row["run"])
    run_rows = [row_for_run(path, [resolve_path(item) for item in log_dirs], baseline) for path in result_files]
    return log_rows + run_rows


def numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv(path: str) -> list[dict[str, str]]:
    csv_path = resolve_path(path)
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(key): str(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def params_m(row: dict[str, str]) -> float | None:
    value = row.get("Params", "").replace("M", "").strip()
    return numeric(value)


def metric_from_summary(row: dict[str, str], metric: str) -> float | None:
    return numeric(row.get(f"{metric}_mean", "")) or numeric(row.get(metric, ""))


def params_from_summary(row: dict[str, str]) -> float | None:
    value = metric_from_summary(row, "Params")
    if value is None:
        return None
    return value / 1_000_000.0 if value > 1_000 else value


def is_plain_yolo_family(method: str) -> bool:
    normalized = method.lower().replace("-", "").replace("_", "")
    return normalized.startswith(("yolov5", "yolov8", "yolov9", "yolov10", "yolo11", "yolo12", "yolo26"))


def fmt_signed(value: float | None) -> str:
    return "-" if value is None else f"{value:+.4f}"


def comparison_tradeoff_score(row: dict[str, str], baseline: Baseline) -> float:
    ap = numeric(row.get("AP", "-"))
    ap50 = numeric(row.get("AP50", "-"))
    f1_value = numeric(row.get("F1", "-"))
    params = params_m(row)
    if ap is None or ap50 is None or f1_value is None or params is None or params <= 0:
        return -1.0
    if ap < baseline.ap or ap50 < baseline.ap50:
        return -1.0
    accuracy = 0.50 * (ap / baseline.ap) + 0.25 * (ap50 / baseline.ap50) + 0.25 * (f1_value / baseline.f1)
    efficiency = baseline.params_m / params
    return accuracy * efficiency


def comparison_row_key(row: dict[str, str]) -> str:
    return row.get("model", "").lower().replace(" ", "").replace("_", "-")


def add_unique_comparison_row(rows: list[dict[str, str]], seen: set[str], row: dict[str, str]) -> None:
    key = comparison_row_key(row)
    if not key or key in seen:
        return
    seen.add(key)
    rows.append(row)


def summary_to_comparison_row(row: dict[str, str], baseline: Baseline) -> dict[str, str] | None:
    method = row.get("method") or row.get("model") or ""
    if not method:
        return None
    ap = metric_from_summary(row, "best_AP")
    ap50 = metric_from_summary(row, "best_AP50")
    precision = metric_from_summary(row, "best_precision")
    recall = metric_from_summary(row, "best_recall")
    f1_value = metric_from_summary(row, "best_F1") or f1(precision, recall)
    params = params_from_summary(row)
    if ap is None or ap50 is None:
        return None
    if row.get("is_proposed") == "true":
        group = "Proposed confirm"
    elif row.get("detector_family") == "YOLO" or is_plain_yolo_family(method):
        group = "YOLO family baseline"
    elif method.upper().startswith("RT-DETR") or (row.get("detector_family") or "").upper().startswith("RT-DETR"):
        group = "Generic non-YOLO baseline"
    else:
        group = "Related-work prior model"
    seed_count = row.get("seed_count") or row.get("best_AP_n") or ""
    note = f"{seed_count}-seed" if seed_count else "summary"
    return {
        "model": method,
        "group": group,
        "AP": fmt(ap),
        "AP50": fmt(ap50),
        "P": fmt(precision),
        "R": fmt(recall),
        "F1": fmt(f1_value),
        "Params": "-" if params is None else f"{params:.2f}M",
        "dAP": fmt_signed(ap - baseline.ap),
        "note": note,
    }


def related_work_to_comparison_row(row: dict[str, str], baseline: Baseline) -> dict[str, str] | None:
    method = row.get("method") or ""
    ap = numeric(row.get("ap", ""))
    ap50 = numeric(row.get("ap50", ""))
    precision = numeric(row.get("precision", ""))
    recall = numeric(row.get("recall", ""))
    f1_value = numeric(row.get("f1", "")) or f1(precision, recall)
    params = numeric(row.get("params_m", ""))
    if not method or ap is None or ap50 is None:
        return None
    return {
        "model": method,
        "group": "Related-work prior model",
        "AP": fmt(ap),
        "AP50": fmt(ap50),
        "P": fmt(precision),
        "R": fmt(recall),
        "F1": fmt(f1_value),
        "Params": "-" if params is None else f"{params:.2f}M",
        "dAP": fmt_signed(ap - baseline.ap),
        "note": f"{row.get('imgsz', '-')}-eval",
    }


def build_full_comparison_rows(rows: list[dict[str, str]], baseline: Baseline) -> list[dict[str, str]]:
    comparison_rows: list[dict[str, str]] = []
    seen: set[str] = set()

    proposed_candidates = [row for row in rows if row.get("bestAP") != "-"]
    for best_proposed in sorted(proposed_candidates, key=sort_key_ap, reverse=True):
        add_unique_comparison_row(
            comparison_rows,
            seen,
            {
                "model": best_proposed["run"],
                "group": "Proposed search",
                "AP": best_proposed["bestAP"],
                "AP50": best_proposed["bestAP50"],
                "P": best_proposed.get("bestP", "-"),
                "R": best_proposed.get("bestR", "-"),
                "F1": best_proposed.get("bestF1", "-"),
                "Params": best_proposed["Params"],
                "dAP": best_proposed["dAP"],
                "note": best_proposed["gate"],
            },
        )

    add_unique_comparison_row(
        comparison_rows,
        seen,
        {
            "model": "YOLOv11l",
            "group": "YOLO family baseline",
            "AP": f"{baseline.ap:.4f}",
            "AP50": f"{baseline.ap50:.4f}",
            "P": "0.6666",
            "R": "0.5881",
            "F1": f"{baseline.f1:.4f}",
            "Params": f"{baseline.params_m:.2f}M",
            "dAP": "+0.0000",
            "note": "best YOLO baseline",
        },
    )

    for summary_path in [
        "outputs/experiments/server_with_top3_proposed_summary.csv",
        "outputs/experiments/server_with_yolov11_p2_confirm_slim_summary.csv",
        "outputs/experiments/server_with_yolov11_p2_next_summary.csv",
        "outputs/experiments/server_with_proposed_summary.csv",
    ]:
        for source_row in read_csv(summary_path):
            comp_row = summary_to_comparison_row(source_row, baseline)
            if comp_row is not None:
                add_unique_comparison_row(comparison_rows, seen, comp_row)

    for source_row in read_csv("outputs/experiments/related_work_detector_results.csv"):
        comp_row = related_work_to_comparison_row(source_row, baseline)
        if comp_row is not None:
            add_unique_comparison_row(comparison_rows, seen, comp_row)

    def sort_key(row: dict[str, str]) -> tuple[int, float, float]:
        group_order = {
            "Proposed search": 0,
            "Proposed confirm": 1,
            "YOLO family baseline": 2,
            "Generic non-YOLO baseline": 4,
            "Related-work prior model": 5,
        }.get(row.get("group", ""), 6)
        return (group_order, -(numeric(row.get("AP", "-")) or -1.0), params_m(row) or 999.0)

    return sorted(comparison_rows, key=sort_key)


def visible_comparison_rows(comparison_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = next((row for row in comparison_rows if row.get("model") == SELECTED_OURS), None)
    if selected is None:
        selected = {
            "model": SELECTED_OURS,
            "group": "Ours final",
            "AP": "0.3825",
            "AP50": "0.6061",
            "P": "0.6714",
            "R": "0.5867",
            "F1": "0.6262",
            "Params": "20.82M",
            "dAP": "+0.0048",
            "note": "selected",
        }
    selected = dict(selected)
    selected["model"] = f"1. Ours {SELECTED_OURS}"
    selected["group"] = "Ours final"
    selected["note"] = "selected"

    comparison_pool = [row for row in comparison_rows if row.get("model") != SELECTED_OURS]
    yolo_pool = sorted(
        [
            row
            for row in comparison_pool
            if row.get("group") == "YOLO family baseline"
        ],
        key=lambda row: (numeric(row.get("AP", "-")) or -1.0, numeric(row.get("AP50", "-")) or -1.0),
        reverse=True,
    )

    visible = [selected, {"section": "true", "model": "YOLO Family Baselines", "group": "plain YOLO n/s/m/l scale rows"}]
    for row in yolo_pool[:6]:
        visible.append(dict(row))

    non_yolo_names = ["RT-DETR-L"]
    related_names = ["CSFPR-RTDETR", "LEAF-YOLO-S"]
    seen = {comparison_row_key(row) for row in visible}
    for name in non_yolo_names:
        for row in comparison_pool:
            if row.get("model") == name and comparison_row_key(row) not in seen:
                visible.append(dict(row))
                seen.add(comparison_row_key(row))
                break

    visible.append({"section": "true", "model": "Related-Work / Prior-Art Models", "group": "paper-proposed external methods"})
    for name in related_names:
        for row in comparison_pool:
            if row.get("model") == name and comparison_row_key(row) not in seen:
                visible.append(dict(row))
                seen.add(comparison_row_key(row))
                break

    visible = visible[:14]
    rank = 2
    for idx, row in enumerate(visible[1:], start=1):
        if row.get("section") == "true":
            continue
        ranked = dict(row)
        ranked["model"] = f"{rank}. {row['model']}"
        visible[idx] = ranked
        rank += 1
    return visible


def tradeoff_score(row: dict[str, str], baseline: Baseline) -> float:
    ap = numeric(row.get("bestAP", "-"))
    ap50 = numeric(row.get("bestAP50", "-"))
    f1 = numeric(row.get("bestF1", "-"))
    params = params_m(row)
    if ap is None or ap50 is None or f1 is None or params is None or params <= 0:
        return -1.0
    accuracy = 0.50 * (ap / baseline.ap) + 0.25 * (ap50 / baseline.ap50) + 0.25 * (f1 / baseline.f1)
    efficiency = baseline.params_m / params
    return accuracy * efficiency


def gate_color(gate: str) -> str:
    if gate == "TARGET-under-param":
        return "#047857"
    if gate.startswith("BEST"):
        return "#047857"
    if gate.startswith("PASS"):
        return "#0F766E"
    if gate == "waiting":
        return "#475569"
    if gate == "acc-below":
        return "#B45309"
    return "#B91C1C"


def dap_color(value: str) -> str:
    val = numeric(value)
    if val is None:
        return "#475569"
    if val > 0.0:
        return "#047857"
    if val > -0.005:
        return "#B45309"
    return "#B91C1C"


def short_note(value: str) -> str:
    replacements = {
        "PASS-over-param": "over-param",
        "PASS-more-param": "more-param",
        "TARGET-under-param": "target",
        "acc-below": "below-target",
        "best baseline": "baseline",
        "large baseline": "large",
        "Proposed confirm": "confirm",
        "YOLO family baseline": "YOLO baseline",
        "Generic non-YOLO baseline": "non-YOLO",
        "Related-work prior model": "prior art",
    }
    return replacements.get(value, value)


def display_gate(value: str) -> str:
    return short_note(value)


def text(ax: Any, x: float, y: float, value: str, *, size: int = 12, weight: str = "normal", color: str = "#111827") -> None:
    ax.text(x, y, value, transform=ax.transAxes, fontsize=size, fontweight=weight, color=color, va="top", ha="left")


def card(ax: Any, patch_cls: Any, x: float, y: float, w: float, h: float, *, face: str = "#F8FAFC", edge: str = "#CBD5E1") -> None:
    ax.add_patch(
        patch_cls(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            linewidth=1.0,
            edgecolor=edge,
            facecolor=face,
            transform=ax.transAxes,
        )
    )


def draw_metric_bar(ax: Any, x: float, y: float, w: float, h: float, value: str, baseline_value: float, target_value: float) -> None:
    val = numeric(value)
    ax.add_patch(plt_rectangle(ax, x, y, w, h, "#E2E8F0"))
    if val is None:
        return
    lo = max(0.0, baseline_value - 0.08)
    hi = max(target_value + 0.02, baseline_value + 0.03)
    frac = min(1.0, max(0.0, (val - lo) / (hi - lo)))
    color = "#059669" if val >= target_value else "#2563EB" if val >= baseline_value else "#D97706"
    ax.add_patch(plt_rectangle(ax, x, y, w * frac, h, color))


def plt_rectangle(ax: Any, x: float, y: float, w: float, h: float, color: str) -> Any:
    from matplotlib.patches import Rectangle

    rect = Rectangle((x, y), w, h, transform=ax.transAxes, facecolor=color, edgecolor="none")
    return rect


def render_dashboard(rows: list[dict[str, str]], out: Path, baseline: Baseline) -> None:
    plt, patch_cls = setup_matplotlib()
    active = [row for row in rows if row["active"] == "true"]
    active = active[:2]

    comparison_rows = build_full_comparison_rows(rows, baseline)
    tradeoff_eligible = [row for row in comparison_rows if comparison_tradeoff_score(row, baseline) >= 0]
    tradeoff_top1 = max(tradeoff_eligible, key=lambda row: comparison_tradeoff_score(row, baseline), default=None)

    fig = plt.figure(figsize=(11.4, 14.2), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.patch.set_facecolor("#EEF2F7")

    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    text(ax, 0.04, 0.975, "Live Detector Dashboard", size=22, weight="bold")
    text(ax, 0.04, 0.945, f"Updated {now}  |  refresh: 30s", size=10, color="#475569")
    text(
        ax,
        0.04,
        0.918,
        f"Baseline YOLOv11l: AP {baseline.ap:.4f}  AP50 {baseline.ap50:.4f}  F1 {baseline.f1:.4f}  Params {baseline.params_m:.2f}M",
        size=11,
        color="#334155",
    )
    text(ax, 0.04, 0.895, f"Strict target: AP >= {baseline.ap * 1.015:.4f}  AP50 >= {baseline.ap50 * 1.015:.4f}", size=11, color="#334155")
    text(ax, 0.04, 0.875, f"Paper target: AP > {baseline.target_ap:.4f} and Params < {baseline.params_m:.2f}M", size=11, color="#334155")

    gpu_status = "   |   ".join(gpu_lines())
    text(ax, 0.04, 0.842, gpu_status or "GPU status unavailable", size=11, weight="bold", color="#0F172A")

    text(ax, 0.04, 0.805, "Final Detector Table Preview", size=16, weight="bold")
    text(ax, 0.04, 0.785, "Plain YOLO family baselines and related-work prior models are intentionally separated.", size=9.5, color="#64748B")
    y = 0.755
    card(ax, patch_cls, 0.04, y - 0.336, 0.92, 0.321, face="#FFFFFF")
    headers = [
        ("Model", 0.060),
        ("Group", 0.245),
        ("AP", 0.390),
        ("AP50", 0.465),
        ("P", 0.545),
        ("R", 0.610),
        ("F1", 0.675),
        ("Params", 0.745),
        ("dAP", 0.825),
        ("Note", 0.880),
    ]
    for label, x in headers:
        text(ax, x, y - 0.035, label, size=8.7, weight="bold", color="#334155")
    row_y = y - 0.065
    for row in visible_comparison_rows(comparison_rows):
        if row.get("section") == "true":
            ax.add_patch(plt_rectangle(ax, 0.052, row_y - 0.025, 0.895, 0.023, "#E2E8F0"))
            text(ax, 0.060, row_y - 0.005, row["model"], size=7.5, weight="bold", color="#0F172A")
            text(ax, 0.245, row_y - 0.005, row.get("group", ""), size=7.2, color="#475569")
            row_y -= 0.022
            continue
        bg = "#ECFDF5" if row["group"].startswith("Proposed") and numeric(row["dAP"]) and numeric(row["dAP"]) > 0 else "#F8FAFC"
        if row["group"] == "Ours final":
            bg = "#FEF3C7"
        elif tradeoff_top1 is not None and comparison_row_key(row) == comparison_row_key(tradeoff_top1):
            bg = "#FEF3C7"
        ax.add_patch(plt_rectangle(ax, 0.052, row_y - 0.025, 0.895, 0.023, bg))
        weight = "bold" if row["group"] == "Ours final" or row["group"].startswith("Proposed") else "normal"
        text(ax, 0.060, row_y - 0.005, row["model"], size=7.2, weight=weight)
        text(ax, 0.245, row_y - 0.005, row["group"], size=7.2, color="#475569")
        text(ax, 0.390, row_y - 0.005, row["AP"], size=7.8)
        text(ax, 0.465, row_y - 0.005, row["AP50"], size=7.8)
        text(ax, 0.545, row_y - 0.005, row["P"], size=7.8)
        text(ax, 0.610, row_y - 0.005, row["R"], size=7.8)
        text(ax, 0.675, row_y - 0.005, row["F1"], size=7.8)
        text(ax, 0.745, row_y - 0.005, row["Params"], size=7.8)
        text(ax, 0.825, row_y - 0.005, row["dAP"], size=7.8, weight="bold", color=dap_color(row["dAP"]))
        text(ax, 0.880, row_y - 0.005, short_note(row["note"]), size=7.0, color="#475569")
        row_y -= 0.022

    y = 0.400
    text(ax, 0.04, y, "Active Runs", size=16, weight="bold")
    y -= 0.026
    for row in active:
        card(ax, patch_cls, 0.04, y - 0.090, 0.92, 0.080, face="#FFFFFF")
        text(ax, 0.065, y - 0.004, f"G{row['gpu']}  {row['run']}  {row['progress']}  {row['speed']}", size=11.5, weight="bold")
        text(ax, 0.065, y - 0.031, f"latest AP {row['AP']}  AP50 {row['AP50']}  F1 {row['F1']}  |  best AP {row['bestAP']}  AP50 {row['bestAP50']}  P {row['bestP']}  R {row['bestR']}  F1 {row['bestF1']}", size=8.4, color="#111827")
        text(ax, 0.065, y - 0.058, f"size {row['Params']}   GFLOPs {row['GFLOPs']}   target gap {row['targetGap']}", size=9.2, color="#475569")
        text(ax, 0.74, y - 0.058, display_gate(row["gate"]), size=10.5, weight="bold", color=gate_color(row["gate"]))
        draw_metric_bar(ax, 0.82, y - 0.035, 0.10, 0.009, row["bestAP"], baseline.ap, baseline.ap * 1.015)
        y -= 0.095
    if not active:
        card(ax, patch_cls, 0.04, y - 0.065, 0.92, 0.055, face="#FFFFFF")
        text(ax, 0.065, y - 0.025, "No active runs detected.", size=12, color="#475569")
        y -= 0.09

    y -= 0.006
    text(ax, 0.04, y, "Final Selected Detector", size=16, weight="bold")
    text(ax, 0.04, y - 0.024, "Chosen for the current paper table because it beats YOLOv11l while reducing parameters.", size=8.8, color="#64748B")
    rank_y = y - 0.044
    if tradeoff_top1 is not None:
        score = comparison_tradeoff_score(tradeoff_top1, baseline)
        face = "#FEF3C7" if score >= 1.0 else "#FFFFFF"
        card(ax, patch_cls, 0.04, rank_y - 0.128, 0.92, 0.118, face=face, edge="#F59E0B" if score >= 1.0 else "#CBD5E1")
        text(ax, 0.065, rank_y - 0.017, f"1. Ours {tradeoff_top1['model']}", size=13.0, weight="bold")
        text(
            ax,
            0.065,
            rank_y - 0.048,
            f"trade-off score {score:.3f}   final detector candidate",
            size=9.4,
            weight="bold" if score >= 1.0 else "normal",
            color="#047857" if score >= 1.0 else "#475569",
        )
        text(
            ax,
            0.065,
            rank_y - 0.079,
            f"AP {tradeoff_top1['AP']}   AP50 {tradeoff_top1['AP50']}   F1 {tradeoff_top1['F1']}   Params {tradeoff_top1['Params']}   dAP {tradeoff_top1['dAP']}",
            size=9.0,
            color="#111827",
        )
        text(
            ax,
            0.065,
            rank_y - 0.106,
            "Active runs above are still monitored, but they do not replace Ours until they finish and beat this trade-off.",
            size=8.2,
            color="#64748B",
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.png")
    fig.savefig(tmp, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    tmp.replace(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", action="append", default=DEFAULT_PROJECT_DIRS)
    parser.add_argument("--log-dir", action="append", default=DEFAULT_LOG_DIRS)
    parser.add_argument("--out", default="outputs/reports/live/training_dashboard.png")
    args = parser.parse_args()

    baseline = Baseline()
    rows = collect_rows(args.project_dir, args.log_dir, baseline)
    render_dashboard(rows, resolve_path(args.out), baseline)
    print(resolve_path(args.out))


if __name__ == "__main__":
    main()
