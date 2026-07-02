"""Collect related-work detector eval logs into CSV/Markdown tables."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


CSFPR_LOGS = {
    "640": "csfpr_rtdetr_visdrone_eval_img640.log",
    "1280": "csfpr_rtdetr_visdrone_eval_img1280.log",
}
LEAF_LOGS = {
    ("LEAF-YOLO-N", "640"): "leaf_yolo_n_visdrone_eval_img640.log",
    ("LEAF-YOLO-S", "640"): "leaf_yolo_s_visdrone_eval_img640.log",
    ("LEAF-YOLO-N", "1280"): "leaf_yolo_n_visdrone_eval_img1280.log",
    ("LEAF-YOLO-S", "1280"): "leaf_yolo_s_visdrone_eval_img1280.log",
}


def parse_float(value: str) -> float:
    return float(value.strip())


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def extract_json_object(text: str) -> dict | None:
    method_index = text.find('"method"')
    if method_index == -1:
        return None
    start = text.rfind("{", 0, method_index)
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : index + 1])
                except json.JSONDecodeError:
                    return None
    return None


def pycoco_metric(text: str, iou_token: str, area_token: str = "all") -> float | None:
    for line in text.splitlines():
        if "Average Precision" not in line:
            continue
        if iou_token not in line or f"area={area_token:>6}" not in line:
            continue
        match = re.search(r"=\s*([0-9.]+)\s*$", line)
        if match:
            return parse_float(match.group(1))
    return None


def collect_csfpr(log_dir: Path, filename: str, expected_imgsz: str) -> dict[str, str] | None:
    path = log_dir / filename
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    payload = extract_json_object(text)
    if not payload:
        return None
    metrics = payload.get("results_dict") or {}
    summary = re.search(r"summary: .*?,\s*([0-9.]+) parameters,.*?,\s*([0-9.]+) GFLOPs", text)
    precision = float(metrics.get("metrics/precision(B)", 0.0))
    recall = float(metrics.get("metrics/recall(B)", 0.0))
    ap50 = float(metrics.get("metrics/mAP50(B)", 0.0))
    ap = float(metrics.get("metrics/mAP50-95(B)", 0.0))
    speed = re.search(r"Speed: .*?([0-9.]+)ms inference", text)
    imgsz = str(payload.get("imgsz") or expected_imgsz)
    if imgsz == "1280":
        note = "Staged CSFPR checkpoint evaluated at 1280; keep separate from trained 3-seed rows because this is an external eval-only checkpoint."
    else:
        note = "Staged CSFPR checkpoint evaluated at 640; compare separately from our strict 1280 trained runs."
    return {
        "method": "CSFPR-RTDETR",
        "dataset": "VisDrone2019-DET val",
        "imgsz": imgsz,
        "precision": fmt(precision),
        "recall": fmt(recall),
        "f1": fmt(f1(precision, recall)),
        "ap50": fmt(ap50),
        "ap": fmt(ap),
        "params_m": fmt(float(summary.group(1)) / 1_000_000 if summary else None),
        "gflops": fmt(float(summary.group(2)) if summary else None),
        "speed_ms": fmt(float(speed.group(1)) if speed else None),
        "source_log": str(path),
        "fairness_note": note,
    }


def collect_leaf(log_dir: Path, method: str, imgsz: str, filename: str) -> dict[str, str] | None:
    path = log_dir / filename
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    summary = re.search(r"Model Summary: .*?,\s*([0-9.]+) parameters,.*?,\s*([0-9.]+) GFLOPS", text)
    all_line = re.search(
        r"\n\s*all\s+548\s+38759\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)",
        text,
    )
    speed = re.search(r"Speed:\s*([0-9.]+)/([0-9.]+)/([0-9.]+) ms inference/NMS/total", text)
    coco_ap = pycoco_metric(text, "IoU=0.50:0.95")
    coco_ap50 = pycoco_metric(text, "IoU=0.50      ")
    precision = recall = ap50 = ap = None
    if all_line:
        precision = parse_float(all_line.group(1))
        recall = parse_float(all_line.group(2))
        ap50 = parse_float(all_line.group(3))
        ap = parse_float(all_line.group(4))
    if coco_ap is not None:
        ap = coco_ap
    if coco_ap50 is not None:
        ap50 = coco_ap50
    if imgsz == "1280":
        note = "Staged LEAF eval at 1280; external eval-only checkpoint, not our 3-seed training protocol."
    else:
        note = "Staged LEAF eval at 640; compare separately from our strict 1280 trained runs."
    return {
        "method": method,
        "dataset": "VisDrone2019-DET val",
        "imgsz": imgsz,
        "precision": fmt(precision),
        "recall": fmt(recall),
        "f1": fmt(f1(precision, recall)),
        "ap50": fmt(ap50),
        "ap": fmt(ap),
        "params_m": fmt(float(summary.group(1)) / 1_000_000 if summary else None),
        "gflops": fmt(float(summary.group(2)) if summary else None),
        "speed_ms": fmt(float(speed.group(1)) if speed else None),
        "source_log": str(path),
        "fairness_note": note,
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "method",
        "dataset",
        "imgsz",
        "precision",
        "recall",
        "f1",
        "ap50",
        "ap",
        "params_m",
        "gflops",
        "speed_ms",
        "source_log",
        "fairness_note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Related-Work Detector Results",
        "",
        "These rows are same-dataset comparison evaluations from staged external models.",
        "They are eval-only rows from external checkpoints. Keep them separate from our strict `imgsz=1280`, 3-seed trained main table unless a full matched training protocol is completed.",
        "",
        "| Method | Dataset | Img | P | R | F1 | AP50 | AP | ParamsM | GFLOPs | ms/img | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["method"],
                    row["dataset"],
                    row["imgsz"],
                    row["precision"],
                    row["recall"],
                    row["f1"],
                    row["ap50"],
                    row["ap"],
                    row["params_m"],
                    row["gflops"],
                    row["speed_ms"],
                    row["fairness_note"],
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default="outputs/logs/related_work_detectors")
    parser.add_argument("--out-csv", default="outputs/experiments/related_work_detector_results.csv")
    parser.add_argument("--out-md", default="outputs/reports/server_with_proposed/related_work_detector_results.md")
    parser.add_argument(
        "--include-internal-leaf",
        action="store_true",
        help="Include legacy LEAF-YOLO eval logs for lab review. By default these are excluded because LEAF-YOLO is not cited in the paper.",
    )
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    rows: list[dict[str, str]] = []
    for imgsz, filename in CSFPR_LOGS.items():
        csfpr = collect_csfpr(log_dir, filename, imgsz)
        if csfpr:
            rows.append(csfpr)
    if args.include_internal_leaf:
        for (method, imgsz), filename in LEAF_LOGS.items():
            row = collect_leaf(log_dir, method, imgsz, filename)
            if row:
                rows.append(row)
    rows.sort(key=lambda item: float(item["ap"] or 0), reverse=True)
    write_csv(Path(args.out_csv), rows)
    write_md(Path(args.out_md), rows)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")


if __name__ == "__main__":
    main()
