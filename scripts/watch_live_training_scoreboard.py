"""Compact live scoreboard for detector training runs."""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
PROGRESS_RE = re.compile(
    r"(?P<epoch>\d+)/(?P<epochs>\d+)\s+"
    r"(?P<gpu_mem>[\d.]+)G\s+"
    r"(?P<box>[\d.]+)\s+"
    r"(?P<cls>[\d.]+)\s+"
    r"(?P<dfl>[\d.]+)\s+"
    r"(?P<instances>\d+)\s+"
    r"(?P<size>\d+):\s+"
    r"(?P<pct>\d+)%.*?"
    r"(?P<step>\d+)/(?P<steps>\d+)\s+"
    r"(?:\[[^\]]*,\s*)?"
    r"(?P<speed>[\d.]+)(?P<speed_unit>it/s|s/it)"
)
LEAF_PROGRESS_RE = re.compile(
    r"(?P<epoch>\d+)/(?P<epochs>\d+)\s+"
    r"(?P<gpu_mem>[\d.]+)G\s+"
    r"(?P<box>[\d.]+)\s+"
    r"(?P<obj>[\d.]+)\s+"
    r"(?P<cls>[\d.]+)\s+"
    r"(?P<total>[\d.]+)\s+"
    r"(?P<labels>\d+)\s+"
    r"(?P<size>\d+):\s+"
    r"(?P<pct>\d+)%.*?"
    r"(?P<step>\d+)/(?P<steps>\d+).*?"
    r"(?:\[[^\]]*,\s*)?"
    r"(?P<speed>[\d.]+)(?P<speed_unit>it/s|s/it)"
)
MODEL_SUMMARY_RE = re.compile(
    r"Model Summary:.*?(?P<params>[\d,]+)\s+parameters.*?(?P<gflops>[\d.]+)\s+GFLOPs",
    re.IGNORECASE,
)


@dataclass
class Baseline:
    ap: float = 0.3776566666666667
    ap50: float = 0.59809
    f1: float = 0.624751330466615
    params_m: float = 25.32
    gflops: float = 87.3
    target_ap: float = 0.3835
    leading_ap: float = 0.382163
    leading_ap50: float = 0.605173
    leading_f1: float = 0.627275
    leading_params_m: float = 20.82
    candidate_ap_margin: float = 0.0010
    candidate_param_budget_m: float = 22.00
    high_capacity_ref_ap: float = 0.3893
    high_capacity_ref_ap50: float = 0.6150
    high_capacity_ref_params_m: float = 58.15


def leading_improvement_target_ap(baseline: Baseline) -> float:
    return baseline.leading_ap + baseline.candidate_ap_margin


def candidate_target_ap(baseline: Baseline) -> float:
    return baseline.target_ap


def candidate_target_ap50(baseline: Baseline) -> float:
    return baseline.ap50 * 1.015


def candidate_target_gap(best_ap: float | None, baseline: Baseline) -> float | None:
    if best_ap is None:
        return None
    return best_ap - candidate_target_ap(baseline)


def clean(text: str) -> str:
    return ANSI_RE.sub("", text.replace("\r", "\n"))


def tail_text(path: Path, max_bytes: int = 2_000_000) -> str:
    if not path.exists():
        return ""
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size > max_bytes:
            handle.seek(size - max_bytes)
        return handle.read().decode("utf-8", errors="replace")


def head_text(path: Path, max_bytes: int = 200_000) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as handle:
        return handle.read(max_bytes).decode("utf-8", errors="replace")


def ffloat(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def metric_value(row: dict[str, str] | None, *keys: str) -> float | None:
    if row is None:
        return None
    for key in keys:
        value = ffloat(row.get(key))
        if value is not None:
            return value
    return None


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0:
        return None
    return 2.0 * precision * recall / (precision + recall)


def fmt(value: float | None, digits: int = 4) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def parse_millions(value: str) -> float | None:
    cleaned = value.replace("M", "").strip()
    return ffloat(cleaned)


def latest_progress(log_path: Path) -> dict[str, str]:
    text = clean(tail_text(log_path))
    matches = list(PROGRESS_RE.finditer(text))
    if matches:
        return matches[-1].groupdict()
    leaf_matches = list(LEAF_PROGRESS_RE.finditer(text))
    if not leaf_matches:
        return {}
    progress = leaf_matches[-1].groupdict()
    return {
        "epoch": progress["epoch"],
        "epochs": progress["epochs"],
        "gpu_mem": progress["gpu_mem"],
        "box": progress["box"],
        "cls": progress["cls"],
        "dfl": progress["total"],
        "instances": progress["labels"],
        "size": progress["size"],
        "pct": progress["pct"],
        "step": progress["step"],
        "steps": progress["steps"],
        "speed": progress["speed"],
        "speed_unit": progress["speed_unit"],
    }


def read_results(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({str(key).strip(): str(value).strip() for key, value in row.items()})
        return rows


def best_and_latest_metrics(results_csv: Path) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    rows = read_results(results_csv)
    if not rows:
        return None, None
    latest = rows[-1]
    best = max(
        rows,
        key=lambda row: metric_value(row, "metrics/mAP50-95(B)", "metrics/mAP_0.5:0.95") or -1.0,
    )
    return latest, best


def leaf_results_path_for_log(log_path: Path) -> Path | None:
    if not log_path.stem.startswith("leaf_yolo_"):
        return None
    return Path("outputs/detectors/related_work_consistency/leaf_yolo") / log_path.stem / "results.txt"


def read_leaf_results(results_txt: Path | None) -> list[dict[str, str]]:
    if results_txt is None or not results_txt.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in results_txt.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 15 or "/" not in parts[0]:
            continue
        rows.append(
            {
                "epoch": parts[0].split("/", maxsplit=1)[0],
                "epochs": parts[0].split("/", maxsplit=1)[1],
                "gpu_mem": parts[1],
                "box": parts[2],
                "obj": parts[3],
                "cls": parts[4],
                "total": parts[5],
                "labels": parts[6],
                "img_size": parts[7],
                "precision": parts[8],
                "recall": parts[9],
                "ap50": parts[10],
                "ap": parts[11],
                "val_box": parts[12],
                "val_obj": parts[13],
                "val_cls": parts[14],
            }
        )
    return rows


def latest_best_leaf_metrics(log_path: Path) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    rows = read_leaf_results(leaf_results_path_for_log(log_path))
    if not rows:
        return None, None
    latest = rows[-1]
    best = max(rows, key=lambda row: ffloat(row.get("ap"), -1.0) or -1.0)
    return latest, best


def results_run_slug(path: Path) -> str:
    if path.parent.name == "ultralytics":
        return path.parent.parent.name
    return path.parent.name


def run_name_from_path(path: Path) -> str:
    name = results_run_slug(path)
    name = re.sub(r"^\d{8}_\d{6}_", "", name)
    name = name.replace("proposed_", "")
    name = re.sub(r"_visdrone_yolov11_p2_(next|confirm)_seed", "_s", name)
    return name


def seed_from_name(name: str) -> str:
    match = re.search(r"(?:seed|_s)(\d+)", name)
    return match.group(1) if match else "-"


def gpu_for_seed(seed: str) -> str:
    return {"123": "0", "2026": "1", "42": "-"}.get(seed, "-")


def gpu_fallback_for_run(name: str, seed: str) -> str:
    if "leaf_yolo" in name:
        return "1"
    if "mffsod" in name:
        return "-"
    if "csfpr" in name or "rtdetr" in name:
        return "-"
    if "p2_balanced" in name:
        return {"42": "0", "123": "1"}.get(seed, "-")
    return gpu_for_seed(seed)


def gpu_from_log(log_path: Path | None, fallback: str) -> str:
    if log_path is None:
        return fallback
    text = clean(head_text(log_path))
    stem_match = re.search(r"_gpu(\d+)", log_path.stem)
    if stem_match:
        return stem_match.group(1)
    for pattern in [r"Target GPU:\s*(\d+)", r"\bdevice=(\d+)\b", r"CUDA:(\d+)", r"CUDA device(\d+)"]:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return fallback


def recently_touched(paths: list[Path | None], max_age_seconds: int = 300) -> bool:
    now = time.time()
    for path in paths:
        if path is not None and path.exists() and now - path.stat().st_mtime <= max_age_seconds:
            return True
    return False


def log_is_terminal(log_path: Path | None) -> bool:
    if log_path is None:
        return False
    text = clean(tail_text(log_path, max_bytes=2_000_000))
    terminal_markers = (
        "TRAIN_FAILED",
        "TRAIN_OK",
        "Balanced P2 job finished",
        "P2 compression job finished",
        "job finished",
    )
    return any(marker in text for marker in terminal_markers)


def gate(best_ap: float | None, best_ap50: float | None, baseline: Baseline, params_m: float) -> str:
    if best_ap is None or best_ap50 is None:
        return "waiting"
    under_budget = params_m <= baseline.candidate_param_budget_m
    if under_budget and best_ap >= candidate_target_ap(baseline) and best_ap50 >= candidate_target_ap50(baseline):
        return "TARGET-pass"
    if under_budget and best_ap >= leading_improvement_target_ap(baseline) and best_ap50 >= baseline.leading_ap50:
        return "CANDIDATE-improve"
    if under_budget and best_ap >= baseline.leading_ap and best_ap50 >= baseline.leading_ap50:
        return "CANDIDATE-watch"
    if under_budget and best_ap >= baseline.ap and best_ap50 >= baseline.ap50:
        return "BASELINE-pass-budget"
    if not under_budget and best_ap >= baseline.high_capacity_ref_ap:
        return "high-cap-ref"
    if not under_budget and best_ap >= baseline.leading_ap:
        return "large-ref"
    if under_budget:
        return "below-candidate"
    return "over-budget"


def apply_static_targets(rows: list[dict[str, str]], baseline: Baseline) -> None:
    """Keep live gates tied to the paper-facing YOLOv11l/size-budget target."""
    for row in rows:
        best_ap = ffloat(row.get("bestAP"))
        best_ap50 = ffloat(row.get("bestAP50"))
        params = parse_millions(row.get("Params", ""))
        if row.get("active") == "true" and best_ap is None:
            row["targetGap"] = "-"
            row["gate"] = "running"
            continue
        row["targetGap"] = fmt(candidate_target_gap(best_ap, baseline))
        row["gate"] = gate(best_ap, best_ap50, baseline, params or 0.0)


def gpu_lines() -> list[str]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
    except Exception:
        return []
    lines = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 6:
            used_gb = ffloat(parts[2], 0.0) / 1024.0
            total_gb = ffloat(parts[3], 0.0) / 1024.0
            lines.append(f"G{parts[0]} {parts[1]}% {used_gb:.1f}/{total_gb:.1f}G {parts[5]}C")
    return lines


def attach_session_for_label(label: str) -> str | None:
    if "uavdet" in label.lower():
        return "uavdet-inspired-after-required-gpu0"
    session_by_label = {
        "P2P4-SEFR-s123": "compact-gpu0-p2p4-se",
        "P2P4-SelfAttn-s42": "final-ablation-p2p4-balanced-selfattn-only-s42",
        "P2P4-SelfAttn-s123": "final-ablation-p2p4-balanced-selfattn-only-s123",
        "P2P4-SelfAttn-s2026": "final-ablation-p2p4-balanced-selfattn-only-s2026",
        "P2P4-SelfAttnFR-s123": "compact-gpu1-p2p4-selfattn",
        "P2P4-DynP2FR-s123": "compact-gpu0-p2p4-dynp2",
        "P2P4-DynSmFR-s123": "compact-gpu1-p2p4-dynsmall",
        "LEAF-YOLO-N-s42": "related-work-consistency-1280",
        "LEAF-YOLO-N-s123": "related-work-consistency-1280",
        "LEAF-YOLO-N-s2026": "related-work-consistency-1280",
        "LEAF-YOLO-S-s42": "related-work-consistency-1280",
        "LEAF-YOLO-S-s123": "related-work-consistency-1280",
        "LEAF-YOLO-S-s2026": "related-work-consistency-1280",
        "CSFPR-RTDETR-s42": "related-work-consistency-1280",
        "CSFPR-RTDETR-s123": "related-work-consistency-1280",
        "CSFPR-RTDETR-s2026": "related-work-consistency-1280",
        "MFFSODNet-s42": "related-work-gpu0-mffsod-s42",
        "MFFSODNet-s123": "related-work-gpu0-mffsod-s123",
        "MFFSODNet-s2026": "related-work-gpu0-mffsod-s2026",
    }
    return session_by_label.get(label)


def short_run_label(name: str) -> str:
    seed = seed_from_name(name)
    suffix = f"-s{seed}" if seed != "-" else ""
    yolo_match = re.match(r"(yolov?[\w.]+|yolo\d+\w?)_visdrone", name)
    if yolo_match:
        return f"{yolo_match.group(1)}{suffix}"
    if "leaf_yolo_n" in name:
        return f"LEAF-YOLO-N{suffix}"
    if "leaf_yolo_s" in name:
        return f"LEAF-YOLO-S{suffix}"
    if "csfpr_rtdetr" in name:
        return f"CSFPR-RTDETR{suffix}"
    if "mffsodnet" in name or "mffsod" in name:
        return f"MFFSODNet{suffix}"
    if "p2_dynfreq_cbam_frelu" in name:
        return f"P2-DynFreqCBAM-FR{suffix}"
    if "p2_dynfreq_frelu" in name:
        return f"P2-DynFreq-FR{suffix}"
    if "p2_wavelet_cbam_frelu" in name:
        return f"P2-WCBAM-FR{suffix}"
    if "p2_wavelet_frelu" in name:
        return f"P2-WaveFR{suffix}"
    if "p2_dct_frelu" in name:
        return f"P2-DCT-FR{suffix}"
    if "p2_deform_frelu" in name:
        return f"P2-DeformFR{suffix}"
    if "p2_cbam_frelu" in name:
        return f"P2-CBAM-FR{suffix}"
    if "p2_se_frelu" in name:
        return f"P2-SE-FR{suffix}"
    if "p2_balanced_wavelet" in name:
        return f"P2Bal-WaveFR{suffix}"
    if "p2_efficient_v3_dynfreq_p2" in name:
        return f"P2EffV3-DynP2FR{suffix}"
    if "p2_efficient_v3_se" in name:
        return f"P2EffV3-SEFR{suffix}"
    if "p2_efficient_v3" in name:
        return f"P2EffV3-FR{suffix}"
    if "p2_compress_v3_dynfreq_p2" in name:
        return f"P2CompV3-DynP2FR{suffix}"
    if "p2_compress_v3_se" in name:
        return f"P2CompV3-SEFR{suffix}"
    if "p2_compress_v3" in name:
        return f"P2CompV3-FR{suffix}"
    if "p2_balanced_v2_wavelet_selfattn" in name:
        return f"P2BalV2-WAttnFR{suffix}"
    if "p2_balanced_v2_selfattn" in name:
        return f"P2BalV2-AttnFR{suffix}"
    if "p2_balanced_v2_cbam" in name:
        return f"P2BalV2-CBAMFR{suffix}"
    if "p2_balanced_v2_wavelet" in name:
        return f"P2BalV2-WaveFR{suffix}"
    if "p2_balanced_v2" in name:
        return f"P2BalV2-FR{suffix}"
    if "p2_balanced_v3_dynfreq_p2" in name:
        return f"P2BalV3-DynP2FR{suffix}"
    if "p2_balanced_v3_dynfreq_small" in name:
        return f"P2BalV3-DynSmFR{suffix}"
    if "p2_balanced_v3" in name:
        return f"P2BalV3-FR{suffix}"
    if "p2p4_balanced_selfattn_rf" in name:
        return f"P2P4-SelfAttnRF-FR{suffix}"
    if "p2p4_balanced_selfattn_tiny_frelu" in name:
        return f"P2P4-SelfAttnFR{suffix}"
    if "p2p4_balanced_selfattn_only" in name:
        return f"P2P4-SelfAttn{suffix}"
    if "p2p4_balanced_tiny_frelu" in name:
        return f"P2P4-TinyFR{suffix}"
    if "p2p4_balanced_head_only" in name:
        return f"P2P4-Head{suffix}"
    if "p2p4_balanced_selfattn" in name:
        return f"P2P4-SelfAttnFR{suffix}"
    if "p2p4_balanced_se" in name:
        return f"P2P4-SEFR{suffix}"
    if "p2p4_balanced_dynfreq_p2" in name:
        return f"P2P4-DynP2FR{suffix}"
    if "p2p4_balanced_dynfreq_small" in name:
        return f"P2P4-DynSmFR{suffix}"
    if "p2p4_balanced" in name:
        return f"P2P4-FR{suffix}"
    if "p2_balanced" in name:
        return f"P2Bal-FR{suffix}"
    if "p2_slim_wavelet" in name:
        return f"P2Slim-WaveFR{suffix}"
    if "p2_slim" in name:
        return f"P2Slim-FR{suffix}"
    if "p2_full_light" in name:
        return f"P2Full-WCBAM{suffix}"
    if "p2_tiny_frelu" in name:
        return f"P2-FR{suffix}"
    if "cbam_tiny_frelu" in name:
        return f"CBAM-FR{suffix}"
    if "tiny_frelu_neck" in name:
        return f"FR-only{suffix}"
    return (name[:18] + "...") if len(name) > 21 else name


def sort_key_ap(row: dict[str, str]) -> float:
    return ffloat(row.get("bestAP"), -1.0) or -1.0


def model_size_from_name(name: str) -> tuple[float, float]:
    name = name.lower()
    if "leaf_yolo_n" in name:
        return 1.20, 5.8
    if "leaf_yolo_s" in name:
        return 4.28, 18.6
    if "csfpr_rtdetr" in name:
        return 14.09, 57.0
    if "mffsodnet" in name or "mffsod" in name:
        return 4.55, 55.8
    if "p2_dynfreq_cbam_frelu" in name:
        return 26.24, 116.2
    if "p2_dynfreq_frelu" in name:
        return 26.10, 115.8
    if "p2_deform_frelu" in name:
        return 27.20, 117.0
    if "p2_cbam_frelu" in name or "p2_wavelet_cbam_frelu" in name:
        return 26.22, 113.4
    if "p2_se_frelu" in name:
        return 26.14, 113.1
    if "p2_wavelet_frelu" in name or "p2_dct_frelu" in name:
        return 26.08, 112.9
    if "p2_compress_v3" in name:
        return 24.08, 110.0
    if "p2_efficient_v3" in name:
        return 23.15, 103.2
    if "p2_balanced_v2" in name:
        if "wavelet_selfattn" in name or "selfattn" in name:
            return 24.73, 112.4
        if "cbam" in name:
            return 24.50, 111.2
        return 24.41, 110.1
    if "p2_balanced_v3" in name:
        if "dynfreq_p2" in name:
            return 25.29, 116.0
        if "dynfreq_small" in name:
            return 25.30, 118.1
        return 25.28, 113.8
    if "p2p4_balanced" in name:
        if "selfattn_rf" in name:
            return 20.88, 110.2
        if "dynfreq_p2" in name:
            return 20.83, 109.4
        if "dynfreq_small" in name:
            return 20.84, 109.5
        return 20.82, 109.3
    if "p2_balanced" in name:
        return 24.10, 104.0
    if "p2_slim" in name:
        return 22.72, 95.7
    yolo_sizes = {
        "yolov5nu": (2.65, 7.7),
        "yolov5su": (9.13, 24.1),
        "yolov8n": (3.01, 8.2),
        "yolov8s": (11.14, 28.7),
        "yolov8l": (43.64, 165.4),
        "yolov9t": (2.00, 7.7),
        "yolov9s": (7.29, 27.4),
        "yolov9c": (25.54, 112.9),
        "yolov10n": (2.71, 8.4),
        "yolov10s": (8.07, 24.8),
        "yolov10m": (16.50, 64.0),
        "yolov10l": (25.78, 127.3),
        "yolo11n": (2.59, 6.5),
        "yolo11s": (9.43, 21.6),
        "yolo11l": (25.32, 87.3),
        "yolo12n": (2.57, 6.5),
        "yolo12s": (9.26, 21.5),
        "yolo12m": (20.15, 67.8),
        "yolo12l": (26.40, 89.4),
        "yolo26n": (2.51, 5.8),
        "yolo26s": (9.96, 22.5),
        "yolo26l": (26.19, 93.2),
    }
    for key, value in yolo_sizes.items():
        if key in name:
            return value
    return 26.08, 112.9


def model_size_from_log(log_path: Path | None, fallback: tuple[float, float]) -> tuple[float, float]:
    if log_path is None:
        return fallback
    text = clean(head_text(log_path, max_bytes=400_000))
    matches = list(MODEL_SUMMARY_RE.finditer(text))
    if not matches:
        return fallback
    match = matches[-1]
    params = int(match.group("params").replace(",", "")) / 1_000_000.0
    gflops = ffloat(match.group("gflops"), fallback[1]) or fallback[1]
    return params, gflops


def row_for_run(results_csv: Path, log_dirs: list[Path], baseline: Baseline) -> dict[str, str]:
    name = run_name_from_path(results_csv)
    run_slug = re.sub(r"^\d{8}_\d{6}_", "", results_run_slug(results_csv))
    seed = seed_from_name(name)
    log_candidates: list[Path] = []
    for log_dir in log_dirs:
        log_candidates.extend(log_dir.glob(f"{run_slug}.log"))
        log_candidates.extend(log_dir.glob(f"{run_slug}_gpu*.log"))
    log_candidates = sorted(log_candidates, key=lambda path: path.stat().st_mtime, reverse=True)
    log_path = log_candidates[0] if log_candidates else None
    progress = latest_progress(log_path) if log_path else {}
    latest, best = best_and_latest_metrics(results_csv)
    params_m, gflops = model_size_from_log(log_path, model_size_from_name(name))

    latest_ap = metric_value(latest, "metrics/mAP50-95(B)", "metrics/mAP_0.5:0.95")
    latest_ap50 = metric_value(latest, "metrics/mAP50(B)", "metrics/mAP_0.5")
    latest_p = metric_value(latest, "metrics/precision(B)", "metrics/precision")
    latest_r = metric_value(latest, "metrics/recall(B)", "metrics/recall")
    best_ap = metric_value(best, "metrics/mAP50-95(B)", "metrics/mAP_0.5:0.95")
    best_ap50 = metric_value(best, "metrics/mAP50(B)", "metrics/mAP_0.5")
    best_p = metric_value(best, "metrics/precision(B)", "metrics/precision")
    best_r = metric_value(best, "metrics/recall(B)", "metrics/recall")
    latest_epoch = latest.get("epoch", "-") if latest else "-"
    progress_text = "-"
    if progress:
        progress_text = f"E{progress['epoch']}/{progress['epochs']} {progress['pct']}% {progress['step']}/{progress['steps']}"
    elif latest:
        progress_text = f"E{latest_epoch}/100 val"

    target_gap = candidate_target_gap(best_ap, baseline)
    return {
        "run": short_run_label(name),
        "gpu": gpu_from_log(log_path, gpu_fallback_for_run(name, seed)),
        "active": "true" if recently_touched([log_path]) and not log_is_terminal(log_path) else "false",
        "progress": progress_text,
        "speed": (progress.get("speed", "-") + progress.get("speed_unit", "")) if progress else "-",
        "box": progress.get("box", latest.get("train/box_loss", "-") if latest else "-"),
        "cls": progress.get("cls", latest.get("train/cls_loss", "-") if latest else "-"),
        "dfl": progress.get("dfl", latest.get("train/dfl_loss", "-") if latest else "-"),
        "AP": fmt(latest_ap),
        "AP50": fmt(latest_ap50),
        "F1": fmt(f1(latest_p, latest_r)),
        "bestAP": fmt(best_ap),
        "bestAP50": fmt(best_ap50),
        "bestP": fmt(best_p),
        "bestR": fmt(best_r),
        "bestF1": fmt(f1(best_p, best_r)),
        "dAP": fmt(None if best_ap is None else best_ap - baseline.ap),
        "targetGap": fmt(target_gap),
        "Params": f"{params_m:.2f}M",
        "GFLOPs": f"{gflops:.1f}",
        "gate": gate(best_ap, best_ap50, baseline, params_m),
    }


def row_for_log(log_path: Path, baseline: Baseline) -> dict[str, str]:
    name = log_path.stem
    name = name.replace("proposed_", "")
    seed = seed_from_name(name)
    progress = latest_progress(log_path)
    latest_leaf, best_leaf = latest_best_leaf_metrics(log_path)
    params_m, gflops = model_size_from_log(log_path, model_size_from_name(name))
    progress_text = "-"
    if progress:
        progress_text = f"E{progress['epoch']}/{progress['epochs']} {progress['pct']}% {progress['step']}/{progress['steps']}"
    elif latest_leaf:
        progress_text = f"E{latest_leaf.get('epoch', '-')}/{latest_leaf.get('epochs', '-') } val"

    latest_ap = ffloat(latest_leaf.get("ap") if latest_leaf else None)
    latest_ap50 = ffloat(latest_leaf.get("ap50") if latest_leaf else None)
    latest_p = ffloat(latest_leaf.get("precision") if latest_leaf else None)
    latest_r = ffloat(latest_leaf.get("recall") if latest_leaf else None)
    best_ap = ffloat(best_leaf.get("ap") if best_leaf else None)
    best_ap50 = ffloat(best_leaf.get("ap50") if best_leaf else None)
    best_p = ffloat(best_leaf.get("precision") if best_leaf else None)
    best_r = ffloat(best_leaf.get("recall") if best_leaf else None)
    target_gap = candidate_target_gap(best_ap, baseline)
    gate_value = "running" if progress or recently_touched([log_path]) else "waiting"
    if best_ap is not None or best_ap50 is not None:
        gate_value = gate(best_ap, best_ap50, baseline, params_m)

    return {
        "run": short_run_label(name),
        "gpu": gpu_from_log(log_path, gpu_fallback_for_run(name, seed)),
        "active": "true" if recently_touched([log_path]) and not log_is_terminal(log_path) else "false",
        "progress": progress_text,
        "speed": (progress.get("speed", "-") + progress.get("speed_unit", "")) if progress else "-",
        "box": progress.get("box", latest_leaf.get("box", "-") if latest_leaf else "-"),
        "cls": progress.get("cls", latest_leaf.get("cls", "-") if latest_leaf else "-"),
        "dfl": progress.get("dfl", latest_leaf.get("total", "-") if latest_leaf else "-"),
        "AP": fmt(latest_ap),
        "AP50": fmt(latest_ap50),
        "F1": fmt(f1(latest_p, latest_r)),
        "bestAP": fmt(best_ap),
        "bestAP50": fmt(best_ap50),
        "bestP": fmt(best_p),
        "bestR": fmt(best_r),
        "bestF1": fmt(f1(best_p, best_r)),
        "dAP": fmt(None if best_ap is None else best_ap - baseline.ap),
        "targetGap": fmt(target_gap),
        "Params": f"{params_m:.2f}M",
        "GFLOPs": f"{gflops:.1f}",
        "gate": gate_value,
    }


def related_work_rows_from_csv(baseline: Baseline) -> list[dict[str, str]]:
    rows = read_results(Path("outputs/experiments/related_work_detector_results.csv"))
    out: list[dict[str, str]] = []
    for row in rows:
        ap = ffloat(row.get("ap"))
        ap50 = ffloat(row.get("ap50"))
        if ap is None or ap50 is None:
            continue
        precision = ffloat(row.get("precision"))
        recall = ffloat(row.get("recall"))
        out.append(
            {
                "model": row.get("method", "related-work"),
                "group": "Related work eval",
                "AP": fmt(ap),
                "AP50": fmt(ap50),
                "P": fmt(precision),
                "R": fmt(recall),
                "F1": row.get("f1") or fmt(f1(precision, recall)),
                "Params": f"{ffloat(row.get('params_m'), 0.0):.2f}M",
                "dAP": fmt(ap - baseline.ap),
                "note": f"{row.get('imgsz', '-')}-eval-only",
            }
        )
    return sorted(out, key=lambda item: (ffloat(item.get("AP"), -1.0) or -1.0, ffloat(item.get("AP50"), -1.0) or -1.0), reverse=True)


def paper_facing_rows_from_preview(baseline: Baseline, limit: int = 10) -> list[dict[str, str]]:
    rows = read_results(Path("outputs/reports/final_detector_table_preview.csv"))
    out: list[dict[str, str]] = []
    for row in rows:
        if row.get("section") != "main_1280_completed_3seed":
            continue
        ap = ffloat(row.get("AP"))
        ap50 = ffloat(row.get("AP50"))
        if ap is None or ap50 is None:
            continue
        precision = ffloat(row.get("precision"))
        recall = ffloat(row.get("recall"))
        params_m = ffloat(row.get("params_m"))
        delta_ap = ffloat(row.get("delta_AP_vs_YOLOv11l"))
        note = row.get("note", "")
        seeds = row.get("seeds", "")
        if seeds:
            note = f"{seeds}; {note}" if note else seeds
        out.append(
            {
                "model": row.get("method", "model"),
                "group": row.get("group", "-"),
                "AP": fmt(ap),
                "AP50": fmt(ap50),
                "P": fmt(precision),
                "R": fmt(recall),
                "F1": fmt(ffloat(row.get("F1")) or f1(precision, recall)),
                "Params": "-" if params_m is None else f"{params_m:.2f}M",
                "dAP": fmt(delta_ap if delta_ap is not None else ap - baseline.ap),
                "note": note or row.get("protocol", "-"),
            }
        )
    return out[:limit]


def comparison_reference_rows(rows: list[dict[str, str]], baseline: Baseline) -> list[dict[str, str]]:
    paper_rows = paper_facing_rows_from_preview(baseline)
    if paper_rows:
        return paper_rows

    comparison_rows: list[dict[str, str]] = []
    comparison_rows.extend(
        [
            {
                "model": "Ours",
                "group": "Ours final",
                "AP": "0.3822",
                "AP50": "0.6052",
                "P": "0.6732",
                "R": "0.5872",
                "F1": "0.6273",
                "Params": "20.82M",
                "dAP": fmt(0.3822 - baseline.ap),
                "note": "official 3-seed; SAFR-YOLO/P2P4-SelfAttnFR implementation",
            },
            {
                "model": "YOLOv11l",
                "group": "Best baseline",
                "AP": f"{baseline.ap:.4f}",
                "AP50": f"{baseline.ap50:.4f}",
                "P": "0.6666",
                "R": "0.5881",
                "F1": f"{baseline.f1:.4f}",
                "Params": f"{baseline.params_m:.2f}M",
                "dAP": "+0.0000",
                "note": "baseline",
            },
            {
                "model": "YOLOv12l",
                "group": "Large comparator",
                "AP": "0.3771",
                "AP50": "0.5958",
                "P": "0.6698",
                "R": "0.5805",
                "F1": fmt(f1(0.6698, 0.5805)),
                "Params": "26.40M",
                "dAP": fmt(0.3771 - baseline.ap),
                "note": "large",
            },
            {
                "model": "YOLOv8l",
                "group": "Large comparator",
                "AP": "0.3765",
                "AP50": "0.5963",
                "P": "0.6695",
                "R": "0.5770",
                "F1": fmt(f1(0.6695, 0.5770)),
                "Params": "43.64M",
                "dAP": fmt(0.3765 - baseline.ap),
                "note": "large",
            },
        ]
    )
    comparison_rows.extend(related_work_rows_from_csv(baseline)[:3])
    return comparison_rows[:10]


def print_comparison_snapshot(rows: list[dict[str, str]], baseline: Baseline) -> None:
    comp_rows = comparison_reference_rows(rows, baseline)
    columns = ["model", "group", "AP", "AP50", "P", "R", "F1", "Params", "dAP", "note"]
    widths = {col: max(len(col), *(len(row.get(col, "")) for row in comp_rows)) for col in columns}
    print("PAPER-FACING COMPARISON SNAPSHOT")
    print("  ".join(col.ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for row in comp_rows:
        print("  ".join(row.get(col, "").ljust(widths[col]) for col in columns))
    print("")


def print_table(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No result files found yet.")
        return
    columns = ["run", "gpu", "progress", "speed", "box", "cls", "dfl", "AP", "AP50", "F1", "bestP", "bestR", "bestF1", "bestAP", "bestAP50", "dAP", "targetGap", "Params", "GFLOPs", "gate"]
    widths = {col: max(len(col), *(len(row.get(col, "")) for row in rows)) for col in columns}
    print("  ".join(col.ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(row.get(col, "").ljust(widths[col]) for col in columns))


def print_compact(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No result files found yet.")
        return
    active = [row for row in rows if row["active"] == "true"]
    reference = sorted([row for row in rows if row not in active], key=sort_key_ap, reverse=True)

    print("ACTIVE")
    for row in active:
        print(f"G{row['gpu']} {row['run']}  {row['progress']}  {row['speed']}")
        print(f"  loss box/cls/dfl: {row['box']} / {row['cls']} / {row['dfl']}")
        print(f"  latest AP {row['AP']}  AP50 {row['AP50']}  F1 {row['F1']}")
        print(f"  best AP {row['bestAP']}  AP50 {row['bestAP50']}  P {row['bestP']}  R {row['bestR']}  F1 {row['bestF1']}")
        print(f"  target gap {row['targetGap']}")
        print(f"  size {row['Params']}  {row['GFLOPs']}G  {row['gate']}")
    if not active:
        print("  no active runs")

    print("")
    print("RECENT INTERNAL RUNS")
    print("  search/ablation only; paper-facing comparison is above")
    for index, row in enumerate(reference[:3], start=1):
        print(f"{index}. {row['run']}  AP {row['bestAP']}  AP50 {row['bestAP50']}")
        print(f"   P {row['bestP']}  R {row['bestR']}  F1 {row['bestF1']}")
        print(f"   dAP {row['dAP']}  target gap {row['targetGap']}  {row['Params']}")
        print(f"   {row['gate']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", action="append", default=[
        "outputs/detectors/server_baselines",
        "outputs/detectors/server_fresh_baselines/large_20260524_140922",
        "outputs/detectors/server_yolov11_p2_compact_ideas",
        "outputs/detectors/server_yolov11_p2_module_search",
        "outputs/detectors/server_yolov11_p2_compression",
        "outputs/detectors/server_yolov11_p2_balanced_followup",
        "outputs/detectors/server_yolov11_p2p4_balanced",
        "outputs/detectors/server_yolov11_p2_balanced_v3",
        "outputs/detectors/server_yolov11_p2_balanced_v2",
        "outputs/detectors/server_yolov11_p2_balanced",
        "outputs/detectors/server_yolov11_p2_slim",
        "outputs/detectors/server_yolov11_p2_confirm",
        "outputs/detectors/server_yolov11_p2_next_step",
        "outputs/detectors/related_work_consistency",
        "outputs/detectors/required_related_work_reimplementations",
    ])
    parser.add_argument("--log-dir", action="append", default=[
        "outputs/logs/server_baselines",
        "outputs/logs/server_yolov11_p2_compact_ideas",
        "outputs/logs/server_yolov11_p2_module_search",
        "outputs/logs/server_yolov11_p2_compression",
        "outputs/logs/server_yolov11_p2_balanced_followup",
        "outputs/logs/server_yolov11_p2p4_balanced",
        "outputs/logs/server_yolov11_p2_balanced_v3",
        "outputs/logs/server_yolov11_p2_balanced_v2",
        "outputs/logs/server_yolov11_p2_balanced",
        "outputs/logs/server_yolov11_p2_slim",
        "outputs/logs/server_yolov11_p2_confirm",
        "outputs/logs/related_work_consistency",
        "outputs/logs/required_related_work_models",
    ])
    parser.add_argument("--refresh", type=int, default=5)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    baseline = Baseline()
    while True:
        os.system("clear")
        print(datetime.now().astimezone().isoformat(timespec="seconds"))
        print(
            f"Baseline YOLOv11l: AP={baseline.ap:.4f} AP50={baseline.ap50:.4f} "
            f"F1={baseline.f1:.4f} Params={baseline.params_m:.2f}M GFLOPs={baseline.gflops:.1f}"
        )
        print(
            f"Detector target: AP>={candidate_target_ap(baseline):.4f} "
            f"AP50>={candidate_target_ap50(baseline):.4f}; preferred Params<={baseline.candidate_param_budget_m:.2f}M"
        )
        print(
            "Baseline dAP is vs YOLOv11l; the fair YOLO-family comparison stops at YOLOv9c."
        )
        gpu_status = gpu_lines()
        if gpu_status:
            print(" | ".join(gpu_status))
        print("")

        result_files: list[Path] = []
        for root in args.project_dir:
            root_path = Path(root)
            for pattern in ["*/ultralytics/results.csv", "*/*/results.csv", "*/results.csv"]:
                result_files.extend(root_path.glob(pattern))
        result_files = list(dict.fromkeys(result_files))
        result_files = sorted(result_files, key=lambda path: path.stat().st_mtime, reverse=True)
        result_slugs = {re.sub(r"^\d{8}_\d{6}_", "", results_run_slug(path)) for path in result_files}
        log_rows: list[dict[str, str]] = []
        for log_dir in args.log_dir:
            for log_path in Path(log_dir).glob("*.log"):
                if log_path.name == "queue.log":
                    continue
                has_result_row = any(log_path.stem == slug or log_path.stem.startswith(f"{slug}_") for slug in result_slugs)
                if not has_result_row and recently_touched([log_path]):
                    log_rows.append(row_for_log(log_path, baseline))
        log_rows = sorted(log_rows, key=lambda row: row["run"])
        rows = log_rows + [row_for_run(path, [Path(item) for item in args.log_dir], baseline) for path in result_files]
        rows = [row for row in rows if not row.get("run", "").lower().startswith("yolov9e")]
        apply_static_targets(rows, baseline)
        rows = rows[:8]
        print_comparison_snapshot(rows, baseline)
        width = shutil.get_terminal_size((100, 24)).columns
        if width < 132:
            print_compact(rows)
        else:
            print_table(rows)
        print("")
        active_rows = [row for row in rows if row["active"] == "true"]
        print("Attach active runs:")
        for row in active_rows:
            session = attach_session_for_label(row["run"])
            if session:
                print(f"  {row['run']}: tmux attach -t {session}")
            else:
                print(f"  {row['run']}: session lookup not configured")
        print("  tmux attach -t live-training-scoreboard")
        print("Detach: Ctrl-b then d")
        if args.once:
            break
        try:
            import time

            time.sleep(args.refresh)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
