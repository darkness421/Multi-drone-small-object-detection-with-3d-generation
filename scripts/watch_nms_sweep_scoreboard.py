"""Compact live scoreboard for detector NMS sweep runs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


BASELINE_AP = 0.3776567
BASELINE_AP50 = 0.59809
BASELINE_PRECISION = 0.6665667
BASELINE_RECALL = 0.5880633
BASELINE_F1 = 0.6247513
BASELINE_PARAMS_M = 25.31819
BASELINE_GFLOPS = 87.3
TARGET_AP = BASELINE_AP * 1.015
TARGET_AP50 = BASELINE_AP50 * 1.015

PARAMS_M = {
    "P2BalV2-FR-s42": 24.41,
    "P2Bal-FR-s42": 24.10,
    "P2-FR-s123": 26.08,
    "YOLOv11l-s42": 25.32,
}


def signed(value: float, digits: int = 4) -> str:
    return f"{value:+.{digits}f}"


def signed_m(value: float | None) -> str:
    if value is None:
        return "?"
    return f"{value:+.2f}M"


def short_method(method: str) -> str:
    return method.replace("+nms_sweep", "")


def parse_ablation(ablation: str) -> tuple[str, str, str]:
    conf = "?"
    iou = "?"
    nms = "?"
    for part in ablation.split(","):
        if part.startswith("conf="):
            conf = part.split("=", 1)[1]
        elif part.startswith("iou="):
            iou = part.split("=", 1)[1]
        elif part:
            nms = part
    return conf, iou, nms


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect_rows(roots: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in roots:
        for summary_path in root.glob("*/metrics/eval_summary.json"):
            payload = read_json(summary_path)
            if not payload:
                continue
            metrics = payload.get("metrics", {})
            method = short_method(str(payload.get("method") or summary_path.parent.parent.name))
            conf, iou, nms = parse_ablation(str(payload.get("ablation") or ""))
            precision = float(metrics.get("precision") or 0.0)
            recall = float(metrics.get("recall") or 0.0)
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            ap = float(metrics.get("AP") or 0.0)
            ap50 = float(metrics.get("AP50") or 0.0)
            rows.append(
                {
                    "method": method,
                    "conf": conf,
                    "iou": iou,
                    "nms": nms,
                    "ap": ap,
                    "ap50": ap50,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "params": PARAMS_M.get(method),
                    "pass": ap >= TARGET_AP and ap50 >= TARGET_AP50,
                    "path": str(summary_path),
                }
            )
    return sorted(rows, key=lambda row: (row["ap"], row["ap50"], row["f1"]), reverse=True)


def latest_run_from_log(path: Path) -> str:
    if not path.exists():
        return "no log"
    run_line = ""
    finished = False
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-250:]:
            if line.startswith("[NMS sweep] finished"):
                finished = True
            if line.startswith("[run] "):
                run_line = line
    except OSError:
        return "unreadable"
    if finished:
        return "finished"
    if not run_line:
        return "starting"
    return re.sub(r"^\[run\]\s+\S+\s+", "", run_line)


def print_scoreboard(rows: list[dict[str, Any]], limit: int) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    print(now)
    print(f"Target: AP>={TARGET_AP:.4f} AP50>={TARGET_AP50:.4f}  Baseline mean: AP={BASELINE_AP:.4f} AP50={BASELINE_AP50:.4f}")
    print()
    print("STRONG BASELINE")
    print(
        "  YOLOv11l mean   "
        f"AP {BASELINE_AP:.4f}  AP50 {BASELINE_AP50:.4f}  "
        f"P {BASELINE_PRECISION:.4f}  R {BASELINE_RECALL:.4f}  F1 {BASELINE_F1:.4f}  "
        f"{BASELINE_PARAMS_M:.2f}M  {BASELINE_GFLOPS:.1f}G"
    )
    best_yolo11l = next((row for row in rows if row["method"].startswith("YOLOv11l")), None)
    ref = {
        "name": "YOLOv11l NMS" if best_yolo11l else "YOLOv11l mean",
        "ap": best_yolo11l["ap"] if best_yolo11l else BASELINE_AP,
        "ap50": best_yolo11l["ap50"] if best_yolo11l else BASELINE_AP50,
        "precision": best_yolo11l["precision"] if best_yolo11l else BASELINE_PRECISION,
        "recall": best_yolo11l["recall"] if best_yolo11l else BASELINE_RECALL,
        "f1": best_yolo11l["f1"] if best_yolo11l else BASELINE_F1,
        "params": best_yolo11l["params"] if best_yolo11l else BASELINE_PARAMS_M,
    }
    if best_yolo11l:
        params = f"{best_yolo11l['params']:.2f}M" if best_yolo11l["params"] is not None else "?"
        print(
            "  YOLOv11l NMS    "
            f"AP {best_yolo11l['ap']:.4f}  AP50 {best_yolo11l['ap50']:.4f}  "
            f"P {best_yolo11l['precision']:.4f}  R {best_yolo11l['recall']:.4f}  "
            f"F1 {best_yolo11l['f1']:.4f}  {params}"
        )
        print(f"                  conf={best_yolo11l['conf']} iou={best_yolo11l['iou']} nms={best_yolo11l['nms']}")
    print()
    print("ACTIVE")
    print(f"  GPU0 efficient: {latest_run_from_log(Path('outputs/logs/nms_sweep/efficient_gpu0.log'))}")
    print(f"  GPU1 accuracy : {latest_run_from_log(Path('outputs/logs/nms_sweep/accuracy_gpu1.log'))}")
    print()
    print(f"TOP NMS RESULTS  delta ref: {ref['name']}")
    if not rows:
        print("  waiting for first completed eval...")
        return
    for idx, row in enumerate(rows[:limit], 1):
        mark = "PASS" if row["pass"] else "wait"
        params = f"{row['params']:.2f}M" if row["params"] is not None else "?"
        dparams = None if row["params"] is None or ref["params"] is None else row["params"] - ref["params"]
        print(
            f"{idx}. {row['method']:<14} AP {row['ap']:.4f}  AP50 {row['ap50']:.4f}  "
            f"P {row['precision']:.4f}  R {row['recall']:.4f}  F1 {row['f1']:.4f}  "
            f"{params}  {mark}"
        )
        print(
            f"   dAP {signed(row['ap'] - ref['ap'])}  dAP50 {signed(row['ap50'] - ref['ap50'])}  "
            f"dP {signed(row['precision'] - ref['precision'])}  dR {signed(row['recall'] - ref['recall'])}  "
            f"dF1 {signed(row['f1'] - ref['f1'])}  dParam {signed_m(dparams)}"
        )
        print(f"   conf={row['conf']} iou={row['iou']} nms={row['nms']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument(
        "--roots",
        nargs="+",
        type=Path,
        default=[Path("outputs/detectors/nms_sweep_efficient"), Path("outputs/detectors/nms_sweep_accuracy")],
    )
    args = parser.parse_args()
    print_scoreboard(collect_rows(args.roots), args.limit)


if __name__ == "__main__":
    main()
