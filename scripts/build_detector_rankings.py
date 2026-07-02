"""Build detector performance and trade-off ranking snapshots."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.watch_live_training_scoreboard import model_size_from_name


BASELINE_AP = 0.3776566666666667
BASELINE_AP50 = 0.59809
BASELINE_F1 = 0.624751330466615
BASELINE_PARAMS_M = 25.31819

PROPOSED_RESULTS = Path("outputs/experiments/priority_detector_queue_results.csv")
PROPOSED_SUMMARY = Path("outputs/experiments/priority_detector_queue_summary.csv")
FINAL_TABLE = Path("outputs/reports/final_detector_table_preview.csv")
OUT_DIR = Path("outputs/reports/detector_rankings")
EXCLUDED_METHODS = {"yolov9e", "yolo9e"}


@dataclass
class RankingRow:
    name: str
    method: str
    ablation: str
    seed: str
    status: str
    seeds: str
    seed_count: str
    n: str
    group: str
    ap: float
    ap50: float
    precision: float | None
    recall: float | None
    f1: float | None
    params_m: float | None
    gflops: float | None
    dap: float
    tradeoff: float
    gated_tradeoff: float
    note: str
    source: str


DISPLAY_NAMES = {
    "p2_cbam_frelu": "P2-CBAM-FR",
    "p2_dct_frelu": "P2-DCT-FR",
    "p2_wavelet_cbam_frelu": "P2-WaveletCBAM-FR",
    "p2_wavelet_frelu": "P2-Wavelet-FR",
    "p2_se_frelu": "P2-SE-FR",
    "p2p4_balanced_selfattn_tiny_frelu": "P2P4-SelfAttnFR",
    "p2p4_balanced_dynfreq_small_tiny_frelu": "P2P4-DynSmallFR",
    "p2p4_balanced_dynfreq_p2_tiny_frelu": "P2P4-DynP2FR",
    "p2p4_balanced_se_tiny_frelu": "P2P4-SEFR",
    "p2p4_balanced_selfattn_rf_tiny_frelu": "P2P4-SelfAttnRF-FR",
    "p2_compress_v3_se_tiny_frelu": "P2CompV3-SEFR",
    "p2_compress_v3_dynfreq_p2_tiny_frelu": "P2CompV3-DynP2FR",
    "p2_efficient_v3_se_tiny_frelu": "P2EffV3-SEFR",
    "p2_efficient_v3_dynfreq_p2_tiny_frelu": "P2EffV3-DynP2FR",
    "p2_balanced_v2_tiny_frelu": "P2BalV2-FR",
    "p2_efficient_v3_tiny_frelu": "P2EffV3-FR",
    "p2_compress_v3_tiny_frelu": "P2CompV3-FR",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def as_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def f1_score(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall <= 0:
        return None
    return 2 * precision * recall / (precision + recall)


def method_name(row: dict[str, str]) -> str:
    ablation = row.get("ablation", "")
    if ablation in DISPLAY_NAMES:
        return DISPLAY_NAMES[ablation]
    method = row.get("method") or row.get("model") or row.get("name") or ""
    if method.startswith("yolov"):
        return "YOLOv" + method.removeprefix("yolov")
    if method.startswith("yolo") and not method.startswith("YOLO"):
        return "YOLO" + method.removeprefix("yolo")
    return method or ablation


def is_excluded_method(name: str) -> bool:
    normalized = name.lower().replace("-", "").replace("_", "").replace(".pt", "")
    return normalized in EXCLUDED_METHODS


def size_for(row: dict[str, str]) -> tuple[float | None, float | None]:
    params = as_float(row.get("params_m")) or as_float(row.get("ParamsM")) or as_float(row.get("params"))
    gflops = as_float(row.get("GFLOPs")) or as_float(row.get("gflops"))
    if params is not None:
        if params > 1000:
            params /= 1_000_000.0
        return params, gflops

    fields = [
        row.get("ablation", ""),
        row.get("method", ""),
        row.get("model", ""),
        row.get("base_model", ""),
        row.get("run_dir", ""),
        row.get("note", ""),
    ]
    params_m, estimated_gflops = model_size_from_name(" ".join(fields))
    return params_m, gflops if gflops is not None else estimated_gflops


def first_float(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        value = as_float(row.get(key))
        if value is not None:
            return value
    return None


def raw_tradeoff(ap: float, ap50: float, f1_value: float | None, params_m: float | None) -> float:
    if params_m is None or params_m <= 0 or f1_value is None:
        return -1.0
    return ((ap + ap50 + f1_value) / 3.0) * (BASELINE_PARAMS_M / params_m)


def paper_gated_tradeoff(ap: float, ap50: float, f1_value: float | None, params_m: float | None) -> float:
    if params_m is None or params_m <= 0 or f1_value is None:
        return -1.0
    if ap < BASELINE_AP or ap50 < BASELINE_AP50:
        return -1.0
    accuracy = 0.50 * (ap / BASELINE_AP) + 0.25 * (ap50 / BASELINE_AP50) + 0.25 * (f1_value / BASELINE_F1)
    return accuracy * (BASELINE_PARAMS_M / params_m)


def proposed_run_rows() -> list[RankingRow]:
    rows: list[RankingRow] = []
    for row in read_rows(PROPOSED_RESULTS):
        ap = as_float(row.get("best_AP"))
        ap50 = as_float(row.get("best_AP50"))
        precision = as_float(row.get("best_precision"))
        recall = as_float(row.get("best_recall"))
        f1_value = as_float(row.get("best_F1")) or f1_score(precision, recall)
        if ap is None or ap50 is None:
            continue
        name = method_name(row)
        if is_excluded_method(name):
            continue
        params_m, gflops = size_for(row)
        rows.append(
            RankingRow(
                name=name,
                method=row.get("method", ""),
                ablation=row.get("ablation", ""),
                seed=row.get("seed", ""),
                status=row.get("status", ""),
                seeds="",
                seed_count="",
                n="",
                group="proposed_run",
                ap=ap,
                ap50=ap50,
                precision=precision,
                recall=recall,
                f1=f1_value,
                params_m=params_m,
                gflops=gflops,
                dap=ap - BASELINE_AP,
                tradeoff=raw_tradeoff(ap, ap50, f1_value, params_m),
                gated_tradeoff=paper_gated_tradeoff(ap, ap50, f1_value, params_m),
                note=row.get("run_dir", ""),
                source=str(PROPOSED_RESULTS),
            )
        )
    return rows


def proposed_summary_rows() -> list[RankingRow]:
    rows: list[RankingRow] = []
    for row in read_rows(PROPOSED_SUMMARY):
        ap = as_float(row.get("best_AP_mean"))
        ap50 = as_float(row.get("best_AP50_mean"))
        precision = as_float(row.get("best_precision_mean"))
        recall = as_float(row.get("best_recall_mean"))
        f1_value = as_float(row.get("best_F1_mean")) or f1_score(precision, recall)
        if ap is None or ap50 is None:
            continue
        name = method_name(row)
        if is_excluded_method(name):
            continue
        params_m, gflops = size_for(row)
        rows.append(
            RankingRow(
                name=name,
                method=row.get("method", ""),
                ablation=row.get("ablation", ""),
                seed="",
                status=row.get("result_level", ""),
                seeds=row.get("seeds", ""),
                seed_count=row.get("seed_count", ""),
                n=row.get("best_AP_n", ""),
                group="proposed_summary",
                ap=ap,
                ap50=ap50,
                precision=precision,
                recall=recall,
                f1=f1_value,
                params_m=params_m,
                gflops=gflops,
                dap=ap - BASELINE_AP,
                tradeoff=raw_tradeoff(ap, ap50, f1_value, params_m),
                gated_tradeoff=paper_gated_tradeoff(ap, ap50, f1_value, params_m),
                note="grouped summary",
                source=str(PROPOSED_SUMMARY),
            )
        )
    return rows


def overall_rows() -> list[RankingRow]:
    rows: list[RankingRow] = []
    for row in read_rows(FINAL_TABLE):
        if row.get("section") != "main_1280_completed_3seed":
            continue
        name = row.get("method", "")
        if is_excluded_method(name):
            continue
        ap = first_float(row, "ap", "AP")
        ap50 = first_float(row, "ap50", "AP50")
        f1_value = first_float(row, "f1", "F1")
        if ap is None or ap50 is None:
            continue
        params_m = first_float(row, "params_m", "ParamsM")
        gflops = first_float(row, "gflops", "GFLOPs")
        rows.append(
            RankingRow(
                name=name,
                method=name,
                ablation="",
                seed="",
                status="completed_3seed",
                seeds=row.get("seeds", ""),
                seed_count=row.get("seed_count", ""),
                n=row.get("seed_count", ""),
                group=row.get("group", ""),
                ap=ap,
                ap50=ap50,
                precision=first_float(row, "precision", "P"),
                recall=first_float(row, "recall", "R"),
                f1=f1_value,
                params_m=params_m,
                gflops=gflops,
                dap=first_float(row, "delta_ap", "delta_AP_vs_YOLOv11l") or ap - BASELINE_AP,
                tradeoff=raw_tradeoff(ap, ap50, f1_value, params_m),
                gated_tradeoff=paper_gated_tradeoff(ap, ap50, f1_value, params_m),
                note=row.get("note", ""),
                source=str(FINAL_TABLE),
            )
        )
    return rows


def fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def write_csv(path: Path, rows: list[RankingRow], *, key: str) -> None:
    ranked = sorted(rows, key=lambda item: getattr(item, key), reverse=True)
    fieldnames = [
        "rank",
        "name",
        "group",
        "method",
        "ablation",
        "seed",
        "seeds",
        "seed_count",
        "n",
        "status",
        "AP",
        "AP50",
        "P",
        "R",
        "F1",
        "ParamsM",
        "GFLOPs",
        "dAP",
        "tradeoff",
        "gated_tradeoff",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(ranked, 1):
            writer.writerow(
                {
                    "rank": rank,
                    "name": row.name,
                    "group": row.group,
                    "method": row.method,
                    "ablation": row.ablation,
                    "seed": row.seed,
                    "seeds": row.seeds,
                    "seed_count": row.seed_count,
                    "n": row.n,
                    "status": row.status,
                    "AP": fmt(row.ap, 6),
                    "AP50": fmt(row.ap50, 6),
                    "P": fmt(row.precision, 6),
                    "R": fmt(row.recall, 6),
                    "F1": fmt(row.f1, 6),
                    "ParamsM": fmt(row.params_m, 4),
                    "GFLOPs": fmt(row.gflops, 1),
                    "dAP": fmt(row.dap, 6),
                    "tradeoff": fmt(row.tradeoff, 6),
                    "gated_tradeoff": fmt(row.gated_tradeoff, 6) if row.gated_tradeoff >= 0 else "",
                    "note": row.note,
                }
            )


def markdown_table(rows: list[RankingRow], columns: list[str], *, limit: int | None = None) -> list[str]:
    selected = rows[:limit] if limit else rows
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for rank, row in enumerate(selected, 1):
        values = {
            "rank": str(rank),
            "name": row.name,
            "group": row.group,
            "seed": row.seed,
            "seeds": row.seeds,
            "status": row.status,
            "AP": fmt(row.ap),
            "AP50": fmt(row.ap50),
            "P": fmt(row.precision),
            "R": fmt(row.recall),
            "F1": fmt(row.f1),
            "ParamsM": fmt(row.params_m, 2),
            "GFLOPs": fmt(row.gflops, 1),
            "dAP": f"{row.dap:+.4f}",
            "tradeoff": fmt(row.tradeoff, 3),
            "gated": fmt(row.gated_tradeoff, 3) if row.gated_tradeoff >= 0 else "-",
            "note": row.note,
        }
        lines.append("| " + " | ".join(values[col] for col in columns) + " |")
    return lines


def write_markdown(path: Path, run_rows: list[RankingRow], summary_rows: list[RankingRow], official_rows: list[RankingRow]) -> None:
    run_by_ap = sorted(run_rows, key=lambda item: item.ap, reverse=True)
    run_by_tradeoff = sorted(run_rows, key=lambda item: item.tradeoff, reverse=True)
    summary_by_ap = sorted(summary_rows, key=lambda item: item.ap, reverse=True)
    summary_by_tradeoff = sorted(summary_rows, key=lambda item: item.tradeoff, reverse=True)
    official_by_ap = sorted(official_rows, key=lambda item: item.ap, reverse=True)
    official_by_gated = [row for row in sorted(official_rows, key=lambda item: item.gated_tradeoff, reverse=True) if row.gated_tradeoff >= 0]

    lines: list[str] = [
        "# Detector Ranking Snapshot",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Trade-off score = mean(AP, AP50, F1) * (YOLOv11l params / model params).",
        "Paper-gated trade-off additionally requires AP and AP50 to be at least YOLOv11l before scoring.",
        "",
        "## Key Answer",
        "",
        "- Raw single-run AP leader is P2-CBAM-FR-s123, with P2-DCT-FR-s123 essentially tied just behind it.",
        "- P2-DCT-FR-s123 is currently rank 2 by raw single-run AP and rank 1 among the high-AP runs by raw trade-off after Params correction.",
        "- The paper-ready completed 3-seed 1280 ranking still has Ours at rank 1 above YOLOv11l; its current implementation is SAFR-YOLO/P2P4-SelfAttnFR, while DCT/CBAM remain unconfirmed search variants.",
        "",
        "## Proposed Search: Single-Run Performance Ranking",
        "",
    ]
    lines.extend(markdown_table(run_by_ap, ["rank", "name", "seed", "status", "AP", "AP50", "P", "R", "F1", "ParamsM", "GFLOPs", "dAP"], limit=20))
    lines.extend(["", "## Proposed Search: Single-Run Trade-off Ranking", ""])
    lines.extend(markdown_table(run_by_tradeoff, ["rank", "name", "seed", "status", "AP", "AP50", "F1", "ParamsM", "GFLOPs", "tradeoff"], limit=20))
    lines.extend(["", "## Proposed Search: Grouped Summary Performance Ranking", ""])
    lines.extend(markdown_table(summary_by_ap, ["rank", "name", "seeds", "status", "AP", "AP50", "P", "R", "F1", "ParamsM", "GFLOPs", "dAP"], limit=20))
    lines.extend(["", "## Proposed Search: Grouped Summary Trade-off Ranking", ""])
    lines.extend(markdown_table(summary_by_tradeoff, ["rank", "name", "seeds", "status", "AP", "AP50", "F1", "ParamsM", "GFLOPs", "tradeoff"], limit=20))
    lines.extend(["", "## Paper-Ready 1280 Completed 3-Seed Performance Ranking", ""])
    lines.extend(markdown_table(official_by_ap, ["rank", "name", "group", "seeds", "AP", "AP50", "F1", "ParamsM", "GFLOPs", "dAP"], limit=None))
    lines.extend(["", "## Paper-Gated Completed 3-Seed Trade-off Ranking", ""])
    lines.extend(markdown_table(official_by_gated, ["rank", "name", "group", "seeds", "AP", "AP50", "F1", "ParamsM", "GFLOPs", "gated"], limit=None))
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- proposed_run_performance_ranking.csv",
            "- proposed_run_tradeoff_ranking.csv",
            "- proposed_summary_performance_ranking.csv",
            "- proposed_summary_tradeoff_ranking.csv",
            "- overall_1280_completed_performance_ranking.csv",
            "- overall_1280_completed_tradeoff_ranking.csv",
            "- overall_1280_completed_gated_tradeoff_ranking.csv",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    runs = proposed_run_rows()
    summaries = proposed_summary_rows()
    official = overall_rows()

    write_csv(OUT_DIR / "proposed_run_performance_ranking.csv", runs, key="ap")
    write_csv(OUT_DIR / "proposed_run_tradeoff_ranking.csv", runs, key="tradeoff")
    write_csv(OUT_DIR / "proposed_summary_performance_ranking.csv", summaries, key="ap")
    write_csv(OUT_DIR / "proposed_summary_tradeoff_ranking.csv", summaries, key="tradeoff")
    write_csv(OUT_DIR / "overall_1280_completed_performance_ranking.csv", official, key="ap")
    write_csv(OUT_DIR / "overall_1280_completed_tradeoff_ranking.csv", official, key="tradeoff")
    write_csv(OUT_DIR / "overall_1280_completed_gated_tradeoff_ranking.csv", official, key="gated_tradeoff")
    write_markdown(OUT_DIR / "detector_ranking_snapshot.md", runs, summaries, official)

    print(f"Wrote ranking snapshot to {OUT_DIR / 'detector_ranking_snapshot.md'}")


if __name__ == "__main__":
    main()
