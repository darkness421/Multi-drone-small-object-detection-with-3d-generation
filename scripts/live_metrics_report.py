"""Readable live metric tables for server detector experiments."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


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


def fmt_millions(value: Any) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "-"
    return f"{parsed / 1_000_000:.2f}M"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0:
        return None
    return 2.0 * precision * recall / (precision + recall)


def strip_timestamp(name: str) -> str:
    return re.sub(r"^\d{8}_\d{6}_", "", name)


def infer_model_from_run(run_name: str) -> str:
    clean = strip_timestamp(run_name)
    match = re.match(r"(?P<model>.+?)_(?:visdrone|uavdt|marinecity|dataset)_seed\d+", clean)
    if not match:
        return "-"
    model = match.group("model")
    return f"{model}.pt" if not model.endswith(".pt") else model


def infer_seed_from_run(run_name: str) -> str:
    match = re.search(r"seed(\d+)", run_name)
    return match.group(1) if match else "-"


def compact_id(model: Any, seed: Any, run_name: str) -> str:
    model_text = str(model or infer_model_from_run(run_name)).removesuffix(".pt")
    seed_text = str(seed if seed is not None else infer_seed_from_run(run_name))
    return f"{model_text}-s{seed_text}"


def live_rows(project_dir: str | Path, limit: int = 12) -> list[dict[str, str]]:
    root = resolve_path(project_dir)
    csv_paths = sorted(root.glob("*/ultralytics/results.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    rows: list[dict[str, str]] = []
    for path in csv_paths[:limit]:
        result_rows = read_csv(path)
        if not result_rows:
            continue
        run_dir = path.parents[1]
        summary = read_json(run_dir / "metrics" / "train_summary.json")
        eval_summary = read_json(run_dir / "metrics" / "eval_summary.json")
        last = result_rows[-1]
        best = max(result_rows, key=lambda row: as_float(row.get("metrics/mAP50-95(B)")) or -1.0)
        precision = as_float(last.get("metrics/precision(B)"))
        recall = as_float(last.get("metrics/recall(B)"))
        metrics = eval_summary.get("metrics") or {}
        latency = as_float(metrics.get("latency_ms") or eval_summary.get("latency_ms"))
        fps = as_float(metrics.get("FPS") or eval_summary.get("FPS"))
        model = summary.get("requested_model") or summary.get("model") or infer_model_from_run(run_dir.name)
        seed = summary.get("seed") if summary.get("seed") is not None else infer_seed_from_run(run_dir.name)
        rows.append(
            {
                "ID": compact_id(model, seed, run_dir.name),
                "Ep": fmt(last.get("epoch"), 0),
                "P": fmt(precision),
                "R": fmt(recall),
                "F1": fmt(f1(precision, recall)),
                "m50": fmt(last.get("metrics/mAP50(B)")),
                "Acc": fmt(last.get("metrics/mAP50-95(B)")),
                "Best": fmt(best.get("metrics/mAP50-95(B)")),
                "FPS": fmt(fps, 2),
                "ms": fmt(latency, 2),
            }
        )
    return rows


def summary_rows(summary_csv: str | Path, limit: int = 20) -> list[dict[str, str]]:
    rows = read_csv(resolve_path(summary_csv))
    rows = [row for row in rows if row.get("dataset", "") in {"", "VisDrone2019-DET"}]
    rows.sort(key=lambda row: as_float(row.get("best_AP_mean")) or -1.0, reverse=True)
    out: list[dict[str, str]] = []
    for row in rows[:limit]:
        out.append(
            {
                "Method": row.get("method") or row.get("model") or "-",
                "Size": row.get("param_size_group") or row.get("model_scale") or "-",
                "N": row.get("seed_count") or "-",
                "Level": row.get("analysis_level") or "-",
                "P": fmt(row.get("best_precision_mean")),
                "R": fmt(row.get("best_recall_mean")),
                "F1": fmt(row.get("best_F1_mean")),
                "mAP50": fmt(row.get("best_AP50_mean")),
                "Acc": fmt(row.get("best_AP_mean")),
                "FPS": fmt(row.get("FPS_mean"), 2),
                "Params": fmt_millions(row.get("Params_mean")),
                "GFLOPs": fmt(row.get("GFLOPs_mean"), 1),
            }
        )
    return out


def render_text_table(title: str, rows: list[dict[str, str]]) -> str:
    if not rows:
        return f"{title}\n  no rows yet"
    columns = list(rows[0])
    widths = {col: max(len(col), *(len(str(row.get(col, ""))) for row in rows)) for col in columns}
    lines = [title, "  " + "  ".join(col.ljust(widths[col]) for col in columns)]
    lines.append("  " + "  ".join("-" * widths[col] for col in columns))
    for row in rows:
        lines.append("  " + "  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))
    return "\n".join(lines)


def render_html_table(title: str, rows: list[dict[str, str]]) -> str:
    if not rows:
        return f"<h3>{html.escape(title)}</h3><p class=\"muted\">No rows yet.</p>"
    columns = list(rows[0])
    head = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(str(row.get(col, '')))}</td>" for col in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<h3>{html.escape(title)}</h3><table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def build_text_report(
    project_dir: str | Path = "outputs/detectors/server_baselines",
    summary_csv: str | Path = "outputs/experiments/live/server_baseline_summary.csv",
) -> str:
    sections = [
        "Detector note: Acc = mAP50-95 proxy. Use it with mAP50, P, R, F1, FPS, Params, and GFLOPs.",
        render_text_table("Live Running / Recent Runs", live_rows(project_dir)),
        render_text_table("Completed Seed Summary", summary_rows(summary_csv)),
    ]
    return "\n\n".join(sections)


def build_html_report(
    project_dir: str | Path = "outputs/detectors/server_baselines",
    summary_csv: str | Path = "outputs/experiments/live/server_baseline_summary.csv",
) -> str:
    note = (
        "<p class=\"note\">Detector accuracy proxy: <strong>Acc = mAP50-95</strong>. "
        "Use it together with mAP50, P(precision), R(recall), F1, FPS, Params, and GFLOPs.</p>"
    )
    return note + render_html_table("Live Running / Recent Runs", live_rows(project_dir)) + render_html_table(
        "Completed Seed Summary", summary_rows(summary_csv)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Print readable live detector metric tables.")
    parser.add_argument("--project-dir", default="outputs/detectors/server_baselines")
    parser.add_argument("--summary-csv", default="outputs/experiments/live/server_baseline_summary.csv")
    parser.add_argument("--html", action="store_true")
    args = parser.parse_args()
    if args.html:
        print(build_html_report(args.project_dir, args.summary_csv))
    else:
        print(build_text_report(args.project_dir, args.summary_csv))


if __name__ == "__main__":
    main()
