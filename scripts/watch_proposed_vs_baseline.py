"""Live proposed-detector metrics against the best baseline gate."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall <= 0 else 2.0 * precision * recall / (precision + recall)


def fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def fmt_params(value: float | None) -> str:
    if value is None or value <= 0:
        return "-"
    return f"{value / 1_000_000:.2f}M"


def best_baseline(summary_csv: Path, method: str) -> dict[str, Any]:
    rows = read_rows(summary_csv)
    matches = [row for row in rows if row.get("method") == method]
    if not matches:
        rows.sort(key=lambda row: as_float(row.get("best_AP_mean")), reverse=True)
        matches = rows[:1]
    if not matches:
        return {
            "method": method,
            "AP": 0.3776566666666667,
            "AP50": 0.59809,
            "F1": 0.624751330466615,
            "Params": 25318190.0,
            "GFLOPs": 87.3,
        }
    row = matches[0]
    return {
        "method": row.get("method") or method,
        "AP": as_float(row.get("best_AP_mean")),
        "AP50": as_float(row.get("best_AP50_mean")),
        "F1": as_float(row.get("best_F1_mean")),
        "Params": as_float(row.get("Params_mean")),
        "GFLOPs": as_float(row.get("GFLOPs_mean")),
    }


def parse_size_from_logs(run_name: str, log_roots: list[Path]) -> tuple[float | None, float | None]:
    patterns = [
        re.compile(r"summary:.*?([\d,]+) parameters.*?([\d.]+) GFLOPs"),
        re.compile(r"summary:.*?([\d,]+) gradients,\s*([\d.]+) GFLOPs"),
    ]
    candidates: list[Path] = []
    stripped_run_name = re.sub(r"^\d{8}_\d{6}_", "", run_name)
    for root in log_roots:
        candidates.extend(root.glob(f"{run_name}.log"))
        candidates.extend(root.glob(f"{stripped_run_name}.log"))
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                params, gflops = matches[-1]
                return float(params.replace(",", "")), float(gflops)
    return None, None


def run_label(run_dir: Path) -> str:
    label = re.sub(r"^\d{8}_\d{6}_", "", run_dir.name)
    label = re.sub(r"_visdrone_yolov11_p2_(next|confirm)_seed", "_seed", label)
    label = label.replace("proposed_", "")
    return label


def metric_row(
    run_dir: Path,
    baseline: dict[str, Any],
    log_roots: list[Path],
    target_rel_improvement: float,
    overpass_rel_improvement: float,
    same_params_tolerance: float,
) -> dict[str, str]:
    results_csv = run_dir / "ultralytics" / "results.csv"
    rows = read_rows(results_csv)
    name = run_label(run_dir)
    params, gflops = parse_size_from_logs(run_dir.name, log_roots)
    if not rows:
        target_ap = baseline["AP"] * (1.0 + target_rel_improvement)
        return {
            "run": name,
            "status": "waiting",
            "ep": "-",
            "AP": "-",
            "AP50": "-",
            "F1": "-",
            "bestAP": "-",
            "targetAP": fmt(target_ap),
            "dAP": "-",
            "dTarget": "-",
            "dAP50": "-",
            "dF1": "-",
            "Params": fmt_params(params),
            "dParams": "-",
            "GFLOPs": fmt(gflops, 1) if gflops else "-",
            "gate": "waiting",
        }

    latest = rows[-1]
    best = max(rows, key=lambda row: as_float(row.get("metrics/mAP50-95(B)")))
    p_latest = as_float(latest.get("metrics/precision(B)"))
    r_latest = as_float(latest.get("metrics/recall(B)"))
    p_best = as_float(best.get("metrics/precision(B)"))
    r_best = as_float(best.get("metrics/recall(B)"))
    latest_ap = as_float(latest.get("metrics/mAP50-95(B)"))
    latest_ap50 = as_float(latest.get("metrics/mAP50(B)"))
    latest_f1 = f1(p_latest, r_latest)
    best_ap = as_float(best.get("metrics/mAP50-95(B)"))
    best_ap50 = as_float(best.get("metrics/mAP50(B)"))
    best_f1 = f1(p_best, r_best)
    target_ap = baseline["AP"] * (1.0 + target_rel_improvement)
    target_ap50 = baseline["AP50"] * (1.0 + target_rel_improvement)
    overpass_ap = baseline["AP"] * (1.0 + overpass_rel_improvement)
    overpass_ap50 = baseline["AP50"] * (1.0 + overpass_rel_improvement)
    params_delta = None if not params or not baseline["Params"] else (params - baseline["Params"]) / baseline["Params"]
    accuracy_pass = best_ap >= target_ap and best_ap50 >= target_ap50
    accuracy_overpass = best_ap >= overpass_ap and best_ap50 >= overpass_ap50
    if accuracy_pass and params_delta is not None and params_delta < -same_params_tolerance:
        gate = "BEST-less-param"
    elif accuracy_pass and params_delta is not None and params_delta <= same_params_tolerance:
        gate = "PASS-same-param"
    elif accuracy_pass:
        gate = "PASS-more-param"
    elif accuracy_overpass and params_delta is not None and params_delta > same_params_tolerance:
        gate = "PASS-over-param"
    elif params_delta is not None and params_delta <= same_params_tolerance:
        gate = "acc-below"
    else:
        gate = "below"
    return {
        "run": name,
        "status": "completed" if (run_dir / "metrics" / "train_summary.json").exists() else "active",
        "ep": str(int(as_float(latest.get("epoch")))),
        "AP": fmt(latest_ap),
        "AP50": fmt(latest_ap50),
        "F1": fmt(latest_f1),
        "bestAP": fmt(best_ap),
        "targetAP": fmt(target_ap),
        "dAP": fmt(best_ap - baseline["AP"]),
        "dTarget": fmt(best_ap - target_ap),
        "dAP50": fmt(best_ap50 - baseline["AP50"]),
        "dF1": fmt(best_f1 - baseline["F1"]),
        "Params": fmt_params(params),
        "dParams": "-" if params_delta is None else f"{params_delta * 100:+.1f}%",
        "GFLOPs": fmt(gflops, 1) if gflops else "-",
        "gate": gate,
    }


def print_table(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No proposed results.csv found yet. Waiting for first validation epoch.")
        return
    columns = list(rows[0])
    widths = {col: max(len(col), *(len(row[col]) for row in rows)) for col in columns}
    print("  " + "  ".join(col.ljust(widths[col]) for col in columns))
    print("  " + "  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  " + "  ".join(row[col].ljust(widths[col]) for col in columns))


def print_status_sections(rows: list[dict[str, str]]) -> None:
    active_rows = [row for row in rows if row.get("status") != "completed"]
    completed_rows = [row for row in rows if row.get("status") == "completed"]

    print("Active / Waiting Proposed Runs")
    if active_rows:
        print_table([{key: value for key, value in row.items() if key != "status"} for row in active_rows])
    else:
        print("  no active or waiting rows")

    print("")
    print("Completed Proposed Runs")
    if completed_rows:
        print_table([{key: value for key, value in row.items() if key != "status"} for row in completed_rows])
    else:
        print("  no completed rows yet")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-dir",
        default="outputs/detectors/server_yolov11_p2_next_step,outputs/detectors/server_yolov11_p2_confirm",
        help="Comma-separated detector project directories to monitor.",
    )
    parser.add_argument("--summary-csv", default="outputs/experiments/server_with_proposed/server_with_proposed_summary.csv")
    parser.add_argument("--baseline-method", default="YOLOv11l")
    parser.add_argument("--target-rel-improvement", type=float, default=0.015)
    parser.add_argument("--overpass-rel-improvement", type=float, default=0.001)
    parser.add_argument("--same-params-tolerance", type=float, default=0.01)
    args = parser.parse_args()

    project = Path(args.project_dir)
    baseline = best_baseline(Path(args.summary_csv), args.baseline_method)
    print(
        f"Best baseline gate: {baseline['method']}  "
        f"AP={baseline['AP']:.4f}  AP50={baseline['AP50']:.4f}  "
        f"F1={baseline['F1']:.4f}  Params={fmt_params(baseline['Params'])}  "
        f"GFLOPs={baseline['GFLOPs']:.1f}"
    )
    print(
        "Target tiers: AP/AP50 must be at least "
        f"{args.target_rel_improvement * 100:.1f}% above baseline "
        f"(AP>={baseline['AP'] * (1 + args.target_rel_improvement):.4f}, "
        f"AP50>={baseline['AP50'] * (1 + args.target_rel_improvement):.4f}). "
        f"Then rank by Params: BEST less params, PASS same params within "
        f"{args.same_params_tolerance * 100:.1f}%, PASS increased params. "
        f"PASS-over-param means increased params but AP/AP50 at least "
        f"{args.overpass_rel_improvement * 100:.1f}% above baseline."
    )
    print("")

    log_roots = [
        Path("outputs/logs/gpu0_yolov11_p2_weekend"),
        Path("outputs/logs/gpu1_yolov11_p2_weekend"),
        Path("outputs/logs/server_yolov11_p2_confirm"),
        Path("outputs/logs/server_baselines"),
    ]
    projects = [Path(item.strip()) for item in args.project_dir.split(",") if item.strip()]
    run_dirs = []
    for project in projects:
        run_dirs.extend([path for path in project.glob("*") if path.is_dir() and (path / "ultralytics").exists()])
    run_dirs = sorted(run_dirs, key=lambda path: path.stat().st_mtime, reverse=True)
    rows = []
    seen: set[str] = set()
    for path in run_dirs:
        key = run_label(path)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            metric_row(
                path,
                baseline,
                log_roots,
                args.target_rel_improvement,
                args.overpass_rel_improvement,
                args.same_params_tolerance,
            )
        )
        if len(rows) >= 8:
            break
    print_status_sections(rows)


if __name__ == "__main__":
    main()
