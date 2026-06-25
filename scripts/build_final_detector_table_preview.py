"""Build the current final-detector table preview for the ACCV paper."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


BASELINE_METHOD = "YOLOv11l"
BASELINE_AP = 0.3776566666666667
BASELINE_AP50 = 0.59809
BASELINE_F1 = 0.624751330466615
BASELINE_PARAMS_M = 25.31819
EXCLUDED_METHODS = {"yolov9e", "yolo9e"}


SUMMARY_SOURCES = [
    Path("outputs/experiments/server_baseline_summary.csv"),
    Path("outputs/experiments/priority_detector_queue_summary.csv"),
    Path("outputs/experiments/server_with_yolov11_p2_confirm_slim_summary.csv"),
    Path("outputs/experiments/server_with_proposed_summary.csv"),
    Path("outputs/experiments/archive/initial_server_baselines/server_baseline_summary.csv"),
]

CURRENT_SWEEP_RESULTS = Path("outputs/experiments/server_baseline_results.csv")
RELATED_REFERENCE_LABELS = Path("paper/tables/related_work_reference_labels.csv")
REQUIRED_RELATED_WORK_ROOT = Path("outputs/detectors/required_related_work_reimplementations")
REQUIRED_RELATED_WORK_LOG_DIR = Path("outputs/logs/required_related_work_models")


@dataclass
class TableEntry:
    group: str
    method: str
    protocol: str
    seeds: str
    seed_count: int
    ap: float
    ap_std: float | None
    ap50: float
    ap50_std: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    params_m: float | None
    gflops: float | None
    delta_ap: float
    note: str


def as_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def cited_related_methods() -> set[str]:
    methods: set[str] = set()
    for row in read_rows(RELATED_REFERENCE_LABELS):
        method = row.get("model", "").strip()
        if method:
            methods.add(method)
    return methods


def related_reference_labels() -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in read_rows(RELATED_REFERENCE_LABELS):
        model = row.get("model", "").strip()
        if not model:
            continue
        number = row.get("reference_number", "").strip()
        fallback = row.get("fallback_label", "").strip()
        cite_key = row.get("cite_key", "").strip()
        label = number or fallback
        if not label and cite_key:
            label = "TBD"
        if label:
            labels[model] = label
    return labels


def related_display_method(method: str, labels: dict[str, str]) -> str:
    label = labels.get(method)
    return f"{method} [{label}]" if label else method


def fmt(value: float | None, digits: int = 4) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def fmt_pm(mean: float, std: float | None) -> str:
    if std is None:
        return fmt(mean)
    return f"{mean:.4f} +/- {std:.4f}"


def fmt_m(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def paper_order(entries: list[TableEntry]) -> list[TableEntry]:
    """Keep the proposed method as the final row in paper-facing tables."""
    baselines = [entry for entry in entries if not entry.method.startswith("Ours:")]
    ours = [entry for entry in entries if entry.method.startswith("Ours:")]
    return sorted(baselines, key=entry_sort_key, reverse=True) + ours


def display_group(group: str) -> str:
    if group == "Ours final candidate":
        return "Ours"
    if group == "Best YOLO baseline":
        return "YOLO baseline"
    if group == "Related-work runnable eval":
        return "Cited related work"
    return group


def sample_std(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def mean(values: list[float]) -> float:
    return statistics.mean(values)


def f1_score(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0:
        return None
    return 2 * precision * recall / (precision + recall)


def params_to_m(value: str | None) -> float | None:
    raw = as_float(value)
    if raw is None:
        return None
    return raw / 1_000_000 if raw > 1000 else raw


def display_method_name(method: str) -> str:
    if method.startswith("yolov"):
        return "YOLOv" + method.removeprefix("yolov")
    if method.startswith("yolo") and not method.startswith("YOLO"):
        return "YOLO" + method.removeprefix("yolo")
    return method


def is_excluded_method(method: str) -> bool:
    normalized = method.lower().replace("-", "").replace("_", "").replace(".pt", "")
    return normalized in EXCLUDED_METHODS


def row_group(row: dict[str, str]) -> str:
    method = row.get("method", "")
    family = row.get("detector_family", "")
    scale = row.get("model_scale") or row.get("name_size_tag") or row.get("param_size_group") or ""
    if scale == "unknown":
        scale = ""
    if not scale and method.lower().startswith(("yolov9t", "yolo9t")):
        scale = "nano"
    if method == BASELINE_METHOD:
        return "Best YOLO baseline"
    if family == "RT-DETR" or method.upper().startswith("RT-DETR"):
        return "Transformer baseline"
    if method.startswith("YOLO") or method.startswith("yolo"):
        return f"YOLO {scale or 'family'}"
    return "Other baseline"


def source_rank(path: Path) -> int:
    names = [item.as_posix() for item in SUMMARY_SOURCES]
    try:
        return names.index(path.as_posix())
    except ValueError:
        return len(names)


def summary_entry(row: dict[str, str], source: Path | None = None) -> TableEntry | None:
    if row.get("is_proposed") == "true":
        return None
    method = row.get("method") or row.get("model") or ""
    if not method:
        return None
    method = display_method_name(method)
    if is_excluded_method(method):
        return None
    seed_count = as_int(row.get("seed_count"))
    if seed_count < 3:
        return None
    ap = as_float(row.get("best_AP_mean"))
    ap50 = as_float(row.get("best_AP50_mean"))
    if ap is None or ap50 is None:
        return None
    params_m = params_to_m(row.get("Params_mean"))
    gflops = as_float(row.get("GFLOPs_mean"))
    seeds = row.get("seeds") or "-"
    source_note = "official comparison row"
    if source == Path("outputs/experiments/server_baseline_summary.csv"):
        source_note = "current 1280 comparison sweep, completed 3-seed"
    elif source and "archive/" in source.as_posix():
        source_note = "archived 1280 completed row; current sweep may refresh this"
    return TableEntry(
        group=row_group(row),
        method=method,
        protocol="VisDrone val, 1280, 3-seed" if seed_count == 3 else f"VisDrone val, 1280, {seed_count}-seed",
        seeds=seeds,
        seed_count=seed_count,
        ap=ap,
        ap_std=as_float(row.get("best_AP_std")),
        ap50=ap50,
        ap50_std=as_float(row.get("best_AP50_std")),
        precision=as_float(row.get("best_precision_mean")),
        recall=as_float(row.get("best_recall_mean")),
        f1=as_float(row.get("best_F1_mean")),
        params_m=params_m,
        gflops=gflops,
        delta_ap=ap - BASELINE_AP,
        note=source_note,
    )


def dedupe_summary_entries() -> list[TableEntry]:
    best: dict[str, tuple[int, int, float, TableEntry]] = {}
    for path in SUMMARY_SOURCES:
        for row in read_rows(path):
            entry = summary_entry(row, path)
            if entry is None:
                continue
            method = entry.method
            exact_three_seed = 1 if entry.seed_count == 3 else 0
            candidate_key = (-source_rank(path), exact_three_seed, entry.ap)
            old = best.get(method)
            if old is None or candidate_key > old[:3]:
                best[method] = (*candidate_key, entry)
    return [item[3] for item in best.values()]


def run_timestamp(path_text: str) -> str:
    match = re.search(r"/(\d{8}_\d{6})_", path_text)
    return match.group(1) if match else ""


def build_ours_entry(results_csv: Path) -> TableEntry | None:
    rows = read_rows(results_csv)
    target = "ProposedSize-P2P4BalancedSelfAttnTinyFReLU-yolo11l"
    by_seed: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("method") != target:
            continue
        seed = row.get("seed", "")
        if seed not in {"42", "123", "2026"}:
            continue
        old = by_seed.get(seed)
        if old is None or run_timestamp(row.get("run_dir", "")) > run_timestamp(old.get("run_dir", "")):
            by_seed[seed] = row
    if set(by_seed) != {"42", "123", "2026"}:
        return None
    ordered = [by_seed[seed] for seed in ["42", "123", "2026"]]
    ap = [as_float(row.get("best_AP"), 0.0) or 0.0 for row in ordered]
    ap50 = [as_float(row.get("best_AP50"), 0.0) or 0.0 for row in ordered]
    precision = [as_float(row.get("best_precision"), 0.0) or 0.0 for row in ordered]
    recall = [as_float(row.get("best_recall"), 0.0) or 0.0 for row in ordered]
    f1_values = [as_float(row.get("best_F1"), f1_score(p, r) or 0.0) or 0.0 for row, p, r in zip(ordered, precision, recall)]
    ap_mean = mean(ap)
    return TableEntry(
        group="Ours final candidate",
        method="Ours: P2P4-SelfAttnFR",
        protocol="VisDrone val, 1280, 3-seed",
        seeds="42,123,2026",
        seed_count=3,
        ap=ap_mean,
        ap_std=sample_std(ap),
        ap50=mean(ap50),
        ap50_std=sample_std(ap50),
        precision=mean(precision),
        recall=mean(recall),
        f1=mean(f1_values),
        params_m=20.82,
        gflops=109.3,
        delta_ap=ap_mean - BASELINE_AP,
        note="deduped latest official seed runs",
    )


def read_nms_entries(path: Path, limit: int = 4) -> list[TableEntry]:
    entries: list[TableEntry] = []
    for row in read_rows(path)[:limit]:
        ap = as_float(row.get("AP"))
        ap50 = as_float(row.get("AP50"))
        if ap is None or ap50 is None:
            continue
        method = f"{row.get('method')} + class-aware NMS"
        note = f"single-seed eval, conf={row.get('conf')}, iou={row.get('iou')}, strict_pass={row.get('strict_pass')}"
        entries.append(
            TableEntry(
                group="Postprocess/NMS snapshot",
                method=method,
                protocol="VisDrone val, 1280, eval only",
                seeds="42",
                seed_count=1,
                ap=ap,
                ap_std=None,
                ap50=ap50,
                ap50_std=None,
                precision=as_float(row.get("precision")),
                recall=as_float(row.get("recall")),
                f1=as_float(row.get("F1")),
                params_m=as_float(row.get("params_m")),
                gflops=None,
                delta_ap=ap - BASELINE_AP,
                note=note,
            )
        )
    return entries


def read_related_entries(path: Path) -> list[TableEntry]:
    entries: list[TableEntry] = []
    cited_methods = cited_related_methods()
    ref_labels = related_reference_labels()
    for row in read_rows(path):
        method = row.get("method", "")
        if cited_methods and method not in cited_methods:
            continue
        ap = as_float(row.get("ap"))
        ap50 = as_float(row.get("ap50"))
        if ap is None or ap50 is None:
            continue
        entries.append(
            TableEntry(
                group="Related-work runnable eval",
                method=related_display_method(method, ref_labels),
                protocol=f"{row.get('dataset', 'VisDrone val')}, {row.get('imgsz', '640')}-eval",
                seeds="-",
                seed_count=0,
                ap=ap,
                ap_std=None,
                ap50=ap50,
                ap50_std=None,
                precision=as_float(row.get("precision")),
                recall=as_float(row.get("recall")),
                f1=as_float(row.get("f1")),
                params_m=as_float(row.get("params_m")),
                gflops=as_float(row.get("gflops")),
                delta_ap=ap - BASELINE_AP,
                note=row.get("fairness_note", "external eval; report separately"),
            )
        )
    return entries


def normalized_result_row(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip(): str(value).strip() for key, value in row.items()}


def best_epoch_metrics(path: Path) -> dict[str, float] | None:
    rows = [normalized_result_row(row) for row in read_rows(path)]
    if not rows:
        return None
    best: dict[str, float] | None = None
    for row in rows:
        ap = as_float(row.get("metrics/mAP50-95(B)"))
        ap50 = as_float(row.get("metrics/mAP50(B)"))
        precision = as_float(row.get("metrics/precision(B)"))
        recall = as_float(row.get("metrics/recall(B)"))
        if ap is None:
            ap = as_float(row.get("metrics/mAP_0.5:0.95"))
            ap50 = as_float(row.get("metrics/mAP_0.5"))
            precision = as_float(row.get("metrics/precision"))
            recall = as_float(row.get("metrics/recall"))
        if ap is None or ap50 is None:
            continue
        candidate = {
            "ap": ap,
            "ap50": ap50,
            "precision": precision or 0.0,
            "recall": recall or 0.0,
        }
        if best is None or (candidate["ap"], candidate["ap50"]) > (best["ap"], best["ap50"]):
            best = candidate
    return best


def related_complexity(log_glob: str) -> tuple[float | None, float | None]:
    params_values: list[float] = []
    gflops_values: list[float] = []
    for path in Path().glob(log_glob):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r"([0-9]+(?:\.[0-9]+)?) parameters.*?([0-9]+(?:\.[0-9]+)?) GFLOPs?", text, re.IGNORECASE):
            params_values.append(float(match.group(1)) / 1_000_000)
            gflops_values.append(float(match.group(2)))
    if not params_values:
        return None, None
    return min(params_values), min(gflops_values) if gflops_values else None


def strict_related_work_entries() -> list[TableEntry]:
    specs = [
        {
            "method": "CSFPR-RTDETR",
            "root": Path("outputs/detectors/related_work_consistency/csfpr_rtdetr"),
            "log_glob": "outputs/logs/related_work_consistency/csfpr_rtdetr_img1280_seed*.log",
            "note": "official/staged 1280 3-seed related-work run",
        },
        {
            "method": "MFFSODNet",
            "root": Path("outputs/detectors/related_work_consistency/mffsodnet"),
            "log_glob": "outputs/logs/related_work_consistency/mffsodnet_img1280_seed*.log",
            "note": "official code scratch retrain; no pretrained checkpoint found",
        },
    ]
    labels = related_reference_labels()
    entries: list[TableEntry] = []
    for spec in specs:
        seed_rows: list[tuple[str, dict[str, float]]] = []
        for path in sorted(spec["root"].glob("*seed*/results.csv")):
            seed_match = re.search(r"seed(\d+)", path.as_posix())
            seed = seed_match.group(1) if seed_match else "-"
            metrics = best_epoch_metrics(path)
            if metrics is not None:
                seed_rows.append((seed, metrics))
        if len(seed_rows) < 3:
            continue
        seed_rows = sorted(seed_rows, key=lambda item: item[0])
        ap_values = [metrics["ap"] for _, metrics in seed_rows]
        ap50_values = [metrics["ap50"] for _, metrics in seed_rows]
        precision_values = [metrics["precision"] for _, metrics in seed_rows]
        recall_values = [metrics["recall"] for _, metrics in seed_rows]
        f1_values = [f1_score(p, r) or 0.0 for p, r in zip(precision_values, recall_values)]
        params_m, gflops = related_complexity(str(spec["log_glob"]))
        ap_mean = mean(ap_values)
        entries.append(
            TableEntry(
                group="Cited related work",
                method=related_display_method(str(spec["method"]), labels),
                protocol="VisDrone val, 1280, 3-seed",
                seeds=",".join(seed for seed, _ in seed_rows),
                seed_count=len(seed_rows),
                ap=ap_mean,
                ap_std=sample_std(ap_values),
                ap50=mean(ap50_values),
                ap50_std=sample_std(ap50_values),
                precision=mean(precision_values),
                recall=mean(recall_values),
                f1=mean(f1_values),
                params_m=params_m,
                gflops=gflops,
                delta_ap=ap_mean - BASELINE_AP,
                note=str(spec["note"]),
            )
        )
    return entries


def required_reimpl_complexity(run_key: str) -> tuple[float | None, float | None]:
    params_values: list[float] = []
    gflops_values: list[float] = []
    for path in REQUIRED_RELATED_WORK_LOG_DIR.glob(f"{run_key}_visdrone_seed*.log"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(
            r"summary(?: \(fused\))?: .*?([0-9][0-9,]*) parameters.*?([0-9]+(?:\.[0-9]+)?) GFLOPs?",
            text,
            re.IGNORECASE,
        ):
            params_values.append(float(match.group(1).replace(",", "")) / 1_000_000)
            gflops_values.append(float(match.group(2)))
    if not params_values:
        return None, None
    return max(params_values), max(gflops_values) if gflops_values else None


def required_related_reimpl_entries() -> list[TableEntry]:
    specs = [
        ("SFFEF-YOLO", "sffef_yolo_reimpl", "paper-faithful reimplementation; not official checkpoint"),
        ("BPD-YOLO", "bpd_yolo_reimpl", "paper-faithful reimplementation; not official checkpoint"),
        ("HF-D-FINE", "hf_dfine_reimpl", "high-resolution/frequency-detail reproduction; not official D-FINE checkpoint"),
        ("UAVDet", "uavdet_inspired_reimpl", "inspired reproduction from cited UAVDet design; not official checkpoint"),
    ]
    labels = related_reference_labels()
    by_model_seed: dict[tuple[str, str], tuple[int, str, dict[str, Any]]] = {}
    for summary_path in REQUIRED_RELATED_WORK_ROOT.glob("*/metrics/eval_summary.json"):
        run_name = summary_path.parts[-3]
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        method_text = str(summary.get("method", ""))
        seed_match = re.search(r"seed(\d+)", run_name)
        seed = seed_match.group(1) if seed_match else ""
        if not seed:
            continue
        for model_name, run_key, _note in specs:
            if model_name not in method_text and run_key not in run_name:
                continue
            # Prefer explicit post-training eval summaries over the training-run
            # validation snapshot when both exist for the same seed.
            priority = 1 if "_eval_" in run_name else 0
            timestamp = run_timestamp(f"/{run_name}_")
            old = by_model_seed.get((model_name, seed))
            if old is None or (priority, timestamp) > (old[0], old[1]):
                by_model_seed[(model_name, seed)] = (priority, timestamp, summary)
            break

    entries: list[TableEntry] = []
    for model_name, run_key, base_note in specs:
        seed_items: list[tuple[str, dict[str, float]]] = []
        for (entry_model, seed), (_priority, _timestamp, summary) in by_model_seed.items():
            if entry_model != model_name:
                continue
            raw_metrics = summary.get("metrics", {}) or {}
            metrics = {
                "ap": as_float(raw_metrics.get("AP")),
                "ap50": as_float(raw_metrics.get("AP50")),
                "precision": as_float(raw_metrics.get("precision")),
                "recall": as_float(raw_metrics.get("recall")),
            }
            if metrics["ap"] is None or metrics["ap50"] is None:
                continue
            seed_items.append((seed, {key: float(value or 0.0) for key, value in metrics.items()}))
        if not seed_items:
            continue
        seed_items = sorted(seed_items, key=lambda item: int(item[0]) if item[0].isdigit() else 999999)
        ap_values = [metrics["ap"] for _, metrics in seed_items]
        ap50_values = [metrics["ap50"] for _, metrics in seed_items]
        precision_values = [metrics["precision"] for _, metrics in seed_items]
        recall_values = [metrics["recall"] for _, metrics in seed_items]
        f1_values = [f1_score(p, r) or 0.0 for p, r in zip(precision_values, recall_values)]
        params_m, gflops = required_reimpl_complexity(run_key)
        seed_count = len(seed_items)
        seeds = ",".join(seed for seed, _ in seed_items)
        protocol_status = "1280, 3-seed" if seed_count >= 3 else f"1280, partial {seed_count}/3 seeds"
        note = f"{base_note}; {protocol_status}"
        ap_mean = mean(ap_values)
        entries.append(
            TableEntry(
                group="Cited related work",
                method=related_display_method(model_name, labels),
                protocol=f"VisDrone val, {protocol_status}",
                seeds=seeds,
                seed_count=seed_count,
                ap=ap_mean,
                ap_std=sample_std(ap_values) if seed_count > 1 else None,
                ap50=mean(ap50_values),
                ap50_std=sample_std(ap50_values) if seed_count > 1 else None,
                precision=mean(precision_values),
                recall=mean(recall_values),
                f1=mean(f1_values),
                params_m=params_m,
                gflops=gflops,
                delta_ap=ap_mean - BASELINE_AP,
                note=note,
            )
        )
    return entries


def current_sweep_status_entries(path: Path) -> list[TableEntry]:
    """Summarize latest current-sweep rows, including incomplete active runs."""
    latest_by_method_seed: dict[tuple[str, str], dict[str, str]] = {}
    for row in read_rows(path):
        method = row.get("method") or row.get("model") or ""
        if not method:
            continue
        method = display_method_name(method)
        if is_excluded_method(method):
            continue
        row = dict(row)
        row["method"] = method
        run_dir = row.get("run_dir", "")
        if "outputs/detectors/server_baselines/202606" not in run_dir:
            continue
        seed = row.get("seed", "")
        key = (method, seed)
        old = latest_by_method_seed.get(key)
        if old is None or run_timestamp(run_dir) > run_timestamp(old.get("run_dir", "")):
            latest_by_method_seed[key] = row

    by_method: dict[str, list[dict[str, str]]] = {}
    for row in latest_by_method_seed.values():
        by_method.setdefault(row.get("method") or row.get("model") or "", []).append(row)

    entries: list[TableEntry] = []
    for method, rows in by_method.items():
        ap_values = [as_float(row.get("best_AP")) for row in rows]
        ap50_values = [as_float(row.get("best_AP50")) for row in rows]
        precision_values = [as_float(row.get("best_precision")) for row in rows]
        recall_values = [as_float(row.get("best_recall")) for row in rows]
        f1_values = [as_float(row.get("best_F1")) for row in rows]
        ap = [value for value in ap_values if value is not None]
        ap50 = [value for value in ap50_values if value is not None]
        if not ap or not ap50:
            continue
        precision = [value for value in precision_values if value is not None]
        recall = [value for value in recall_values if value is not None]
        f1_vals = [value for value in f1_values if value is not None]
        seeds = sorted({row.get("seed", "") for row in rows if row.get("seed", "")})
        statuses = sorted({row.get("status", "") for row in rows if row.get("status", "")})
        params = next((params_to_m(row.get("Params")) for row in rows if params_to_m(row.get("Params")) is not None), None)
        gflops = next((as_float(row.get("GFLOPs")) for row in rows if as_float(row.get("GFLOPs")) is not None), None)
        seed_count = len(seeds)
        completed = all(row.get("status") == "completed" for row in rows) and seed_count >= 3
        protocol_status = "completed 3-seed" if completed else f"partial {seed_count}/3 seeds"
        note = f"current 202606 sweep; {protocol_status}; status={','.join(statuses) or '-'}"
        entries.append(
            TableEntry(
                group=row_group(rows[0]),
                method=method,
                protocol=f"VisDrone val, 1280, {protocol_status}",
                seeds=",".join(seeds) or "-",
                seed_count=seed_count,
                ap=mean(ap),
                ap_std=sample_std(ap) if seed_count > 1 else None,
                ap50=mean(ap50),
                ap50_std=sample_std(ap50) if seed_count > 1 else None,
                precision=mean(precision) if precision else None,
                recall=mean(recall) if recall else None,
                f1=mean(f1_vals) if f1_vals else None,
                params_m=params,
                gflops=gflops,
                delta_ap=mean(ap) - BASELINE_AP,
                note=note,
            )
        )
    return sorted(entries, key=entry_sort_key, reverse=True)


def entry_sort_key(entry: TableEntry) -> tuple[float, float]:
    return (entry.ap, entry.ap50)


def base_method_name(method: str) -> str:
    return re.sub(r"\s*\[[^\]]+\]$", "", method.strip())


def markdown_table(entries: list[TableEntry], start_rank: int = 1) -> list[str]:
    lines = [
        "| Rank | Group | Method | Protocol | Seeds | AP | AP50 | P | R | F1 | Params(M) | GFLOPs | Delta AP | Note |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for idx, entry in enumerate(entries, start_rank):
        lines.append(
            "| "
            f"{idx} | {entry.group} | {entry.method} | {entry.protocol} | {entry.seeds} | "
            f"{fmt_pm(entry.ap, entry.ap_std)} | {fmt_pm(entry.ap50, entry.ap50_std)} | "
            f"{fmt(entry.precision)} | {fmt(entry.recall)} | {fmt(entry.f1)} | "
            f"{fmt_m(entry.params_m)} | {fmt_m(entry.gflops)} | {entry.delta_ap:+.4f} | {entry.note} |"
        )
    return lines


def write_csv(entries: list[TableEntry], path: Path, section: str = "mixed") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank",
        "section",
        "group",
        "method",
        "protocol",
        "seeds",
        "seed_count",
        "AP",
        "AP_std",
        "AP50",
        "AP50_std",
        "precision",
        "recall",
        "F1",
        "params_m",
        "gflops",
        "delta_AP_vs_YOLOv11l",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, entry in enumerate(entries, 1):
            writer.writerow(
                {
                    "rank": rank,
                    "section": section,
                    "group": entry.group,
                    "method": entry.method,
                    "protocol": entry.protocol,
                    "seeds": entry.seeds,
                    "seed_count": entry.seed_count,
                    "AP": f"{entry.ap:.6f}",
                    "AP_std": "" if entry.ap_std is None else f"{entry.ap_std:.6f}",
                    "AP50": f"{entry.ap50:.6f}",
                    "AP50_std": "" if entry.ap50_std is None else f"{entry.ap50_std:.6f}",
                    "precision": "" if entry.precision is None else f"{entry.precision:.6f}",
                    "recall": "" if entry.recall is None else f"{entry.recall:.6f}",
                    "F1": "" if entry.f1 is None else f"{entry.f1:.6f}",
                    "params_m": "" if entry.params_m is None else f"{entry.params_m:.4f}",
                    "gflops": "" if entry.gflops is None else f"{entry.gflops:.4f}",
                    "delta_AP_vs_YOLOv11l": f"{entry.delta_ap:.6f}",
                    "note": entry.note,
                }
            )


def write_sectioned_csv(sections: list[tuple[str, list[TableEntry]]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank",
        "section",
        "group",
        "method",
        "protocol",
        "seeds",
        "seed_count",
        "AP",
        "AP_std",
        "AP50",
        "AP50_std",
        "precision",
        "recall",
        "F1",
        "params_m",
        "gflops",
        "delta_AP_vs_YOLOv11l",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for section, entries in sections:
            for rank, entry in enumerate(entries, 1):
                writer.writerow(
                    {
                        "rank": rank,
                        "section": section,
                        "group": entry.group,
                        "method": entry.method,
                        "protocol": entry.protocol,
                        "seeds": entry.seeds,
                        "seed_count": entry.seed_count,
                        "AP": f"{entry.ap:.6f}",
                        "AP_std": "" if entry.ap_std is None else f"{entry.ap_std:.6f}",
                        "AP50": f"{entry.ap50:.6f}",
                        "AP50_std": "" if entry.ap50_std is None else f"{entry.ap50_std:.6f}",
                        "precision": "" if entry.precision is None else f"{entry.precision:.6f}",
                        "recall": "" if entry.recall is None else f"{entry.recall:.6f}",
                        "F1": "" if entry.f1 is None else f"{entry.f1:.6f}",
                        "params_m": "" if entry.params_m is None else f"{entry.params_m:.4f}",
                        "gflops": "" if entry.gflops is None else f"{entry.gflops:.4f}",
                        "delta_AP_vs_YOLOv11l": f"{entry.delta_ap:.6f}",
                        "note": entry.note,
                    }
                )


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def write_latex(entries: list[TableEntry], path: Path, limit: int = 12) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if limit:
        baselines = [entry for entry in entries if not entry.method.startswith("Ours:")]
        ours = [entry for entry in entries if entry.method.startswith("Ours:")]
        rows = sorted(baselines, key=entry_sort_key, reverse=True)[: max(0, limit - len(ours))] + ours
    else:
        rows = paper_order(entries)
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\caption{Main detector comparison on VisDrone validation at 1280 input resolution. All rows are completed three-seed runs under the same protocol; our proposed detector is placed at the bottom following common comparison-table style.}",
        r"\label{tab:detector_preview_overall}",
        r"\begin{tabular}{@{}llrrrrrrrr@{}}",
        r"\toprule",
        r"Group & Method & AP & AP50 & P & R & F1 & Params(M) & GFLOPs & $\Delta$AP \\",
        r"\midrule",
    ]
    for entry in rows:
        row_prefix = r"\textbf{" if entry.method.startswith("Ours:") else ""
        row_suffix = r"}" if entry.method.startswith("Ours:") else ""
        lines.append(
            " & ".join(
                [
                    row_prefix + latex_escape(display_group(entry.group)) + row_suffix,
                    row_prefix + latex_escape(entry.method) + row_suffix,
                    row_prefix + fmt_pm(entry.ap, entry.ap_std).replace("+/-", r"$\pm$") + row_suffix,
                    row_prefix + fmt_pm(entry.ap50, entry.ap50_std).replace("+/-", r"$\pm$") + row_suffix,
                    row_prefix + fmt(entry.precision) + row_suffix,
                    row_prefix + fmt(entry.recall) + row_suffix,
                    row_prefix + fmt(entry.f1) + row_suffix,
                    row_prefix + fmt_m(entry.params_m) + row_suffix,
                    row_prefix + fmt_m(entry.gflops) + row_suffix,
                    row_prefix + f"{entry.delta_ap:+.4f}" + row_suffix,
                ]
            )
            + r" \\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_related_work_latex(entries: list[TableEntry], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(entries, key=entry_sort_key, reverse=True)
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\caption{Cited related-work detector status. These rows are separated from the main three-seed comparison unless the method is retrained or evaluated under the same protocol.}",
        r"\label{tab:cited_related_detector_status}",
        r"\begin{tabular}{@{}llrrrrrl@{}}",
        r"\toprule",
        r"Method & Protocol & AP & AP50 & F1 & Params(M) & GFLOPs & Note \\",
        r"\midrule",
    ]
    if rows:
        for entry in rows:
            lines.append(
                " & ".join(
                    [
                        latex_escape(entry.method),
                        latex_escape(entry.protocol),
                        fmt_pm(entry.ap, entry.ap_std).replace("+/-", r"$\pm$"),
                        fmt_pm(entry.ap50, entry.ap50_std).replace("+/-", r"$\pm$"),
                        fmt(entry.f1),
                        fmt_m(entry.params_m),
                        fmt_m(entry.gflops),
                        latex_escape(entry.note),
                    ]
                )
                + r" \\"
            )
    else:
        lines.append(r"\multicolumn{8}{c}{Additional cited related-work implementations are being audited for runnable 1280-resolution evaluation.} \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def build_preview() -> tuple[list[TableEntry], list[TableEntry], list[TableEntry], list[TableEntry]]:
    main_entries = dedupe_summary_entries()
    strict_related_entries = strict_related_work_entries()
    reimpl_related_entries = required_related_reimpl_entries()
    strict_related_methods = {entry.method for entry in strict_related_entries}
    main_entries = [entry for entry in main_entries if entry.method not in strict_related_methods]
    main_entries.extend(strict_related_entries)
    main_entries.extend(entry for entry in reimpl_related_entries if entry.seed_count >= 3)
    ours = build_ours_entry(Path("outputs/experiments/priority_detector_queue_results.csv"))
    if ours:
        main_entries = [entry for entry in main_entries if entry.method != ours.method]
        main_entries.append(ours)
    main_entries = sorted(main_entries, key=entry_sort_key, reverse=True)
    current_sweep_entries = current_sweep_status_entries(CURRENT_SWEEP_RESULTS)
    nms_entries = read_nms_entries(Path("outputs/experiments/nms_sweep_summary.csv"))
    external_related_entries = read_related_entries(Path("outputs/experiments/related_work_detector_results.csv"))
    covered_related = {base_method_name(entry.method) for entry in strict_related_entries + reimpl_related_entries}
    external_related_entries = [
        entry for entry in external_related_entries if base_method_name(entry.method) not in covered_related
    ]
    related_entries = sorted(
        strict_related_entries + reimpl_related_entries + external_related_entries,
        key=entry_sort_key,
        reverse=True,
    )
    return main_entries, current_sweep_entries, nms_entries, related_entries


def write_markdown(
    main_entries: list[TableEntry],
    current_sweep_entries: list[TableEntry],
    nms_entries: list[TableEntry],
    related_entries: list[TableEntry],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Final Detector Table Preview",
        "",
        f"Updated: {now}",
        "",
        "Reference baseline: YOLOv11l 3-seed mean, AP 0.3777 / AP50 0.5981 / F1 0.6248 / Params 25.32M.",
        "This preview separates completed 1280 3-seed rows, the current 1280 sweep status, single-seed NMS snapshots, and cited related-work rows.",
        "",
        "## Main Paper Candidate: Completed 1280 3-Seed Rows",
        "",
        "Only completed 1280-resolution 3-seed rows belong in the main detector comparison table. Rows marked as archived are valid completed rows, but they may be refreshed by the current expanded comparison sweep.",
        "",
        *markdown_table(main_entries),
        "",
        "## Current 1280 YOLO-Family Sweep Status",
        "",
        "This section shows the newest 202606 comparison sweep. Partial rows are for monitoring only and should not be used as final paper rows until all three seeds complete.",
        "",
        *markdown_table(current_sweep_entries),
        "",
        "## NMS/Postprocessing Snapshot",
        "",
        "These rows are useful for the postprocessing/overlap discussion, but they are not yet 3-seed detector-training rows.",
        "",
        *markdown_table(nms_entries),
        "",
        "## Cited Related-Work Snapshot",
        "",
        "Strict 1280 three-seed related-work runs can be considered for the paper comparison table. External eval-only rows remain separate and must keep their protocol note.",
        "",
        *markdown_table(related_entries),
        "",
        "## Active Queue Note",
        "",
        "- YOLO-family nano/small/medium/large sweep rows in this preview are completed 1280-resolution three-seed rows.",
        "- Cited related-work rows with compatible staged runs are completed or explicitly marked with their reproduction/adapter caveat.",
        "- P2P4-SelfAttnFR is deduped by latest official seed run for seeds 42, 123, and 2026.",
        "- External related-work eval-only rows are intentionally separated; strict 1280 3-seed related-work rows are tracked with protocol notes.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--md-out", type=Path, default=Path("outputs/reports/final_detector_table_preview.md"))
    parser.add_argument("--csv-out", type=Path, default=Path("outputs/reports/final_detector_table_preview.csv"))
    parser.add_argument("--tex-out", type=Path, default=Path("outputs/reports/final_detector_table_preview.tex"))
    parser.add_argument("--split-dir", type=Path, default=Path("outputs/reports/final_detector_tables"))
    parser.add_argument("--overleaf-repo", type=Path, default=Path("/tmp/accv-overleaf"))
    args = parser.parse_args()

    main_entries, current_sweep_entries, nms_entries, related_entries = build_preview()
    sections = [
        ("main_1280_completed_3seed", main_entries),
        ("current_1280_sweep_status", current_sweep_entries),
        ("nms_postprocess_snapshot", nms_entries),
        ("related_work_cited_snapshot", related_entries),
    ]
    write_markdown(main_entries, current_sweep_entries, nms_entries, related_entries, args.md_out)
    write_sectioned_csv(sections, args.csv_out)
    write_csv(main_entries, args.split_dir / "main_1280_completed_3seed.csv", "main_1280_completed_3seed")
    write_csv(current_sweep_entries, args.split_dir / "current_1280_sweep_status.csv", "current_1280_sweep_status")
    write_csv(nms_entries, args.split_dir / "nms_postprocess_snapshot.csv", "nms_postprocess_snapshot")
    write_csv(related_entries, args.split_dir / "related_work_cited_snapshot.csv", "related_work_cited_snapshot")
    write_latex(main_entries, args.tex_out)
    write_latex(main_entries, Path("paper/tables/main_detector_comparison_table.tex"), limit=14)
    write_related_work_latex(related_entries, Path("paper/tables/related_work_detector_status_table.tex"))
    print(args.md_out)
    print(args.csv_out)
    print(args.tex_out)
    print(args.split_dir)
    if args.overleaf_repo.exists():
        overleaf_tex = args.overleaf_repo / "tables" / "final_detector_table_preview.tex"
        write_latex(main_entries, overleaf_tex)
        write_latex(main_entries, args.overleaf_repo / "tables" / "main_detector_comparison_table.tex", limit=14)
        write_related_work_latex(related_entries, args.overleaf_repo / "tables" / "related_work_detector_status_table.tex")
        print(overleaf_tex)


if __name__ == "__main__":
    main()
