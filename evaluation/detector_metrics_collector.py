"""Collect detector baseline metrics into the detector comparison table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluation.detector_compare import DETECTOR_COLUMNS, empty_detector_table
from evaluation.stats import write_metrics_csv


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_metric_payload(payload: dict[str, Any]) -> dict[str, str | float]:
    """Normalize common detector metric aliases into paper-table columns."""

    return {
        "AP": payload.get("AP", payload.get("mAP50-95", "")),
        "AP50": payload.get("AP50", payload.get("mAP50", "")),
        "AP75": payload.get("AP75", payload.get("mAP75", "")),
        "APsmall": payload.get("APsmall", payload.get("APs", "")),
        "ROC-AUC": payload.get("ROC-AUC", payload.get("roc_auc", payload.get("AUROC", ""))),
        "FPS": payload.get("FPS", payload.get("fps", "")),
        "Params": payload.get("Params", payload.get("params", "")),
        "GFLOPs": payload.get("GFLOPs", payload.get("gflops", "")),
    }


def collect_detector_metrics(metrics_dir: str | Path, datasets: list[str] | None = None) -> list[dict[str, str | float]]:
    """Fill detector comparison rows from one JSON file per measured run."""

    metrics_dir = Path(metrics_dir)
    datasets = datasets or ["VisDrone2019-DET", "UAVDT"]
    rows = empty_detector_table(datasets)
    row_by_key = {(row["Method"], row["Dataset"]): row for row in rows}

    for json_path in sorted(metrics_dir.glob("*.json")):
        payload = _read_json(json_path)
        method = payload.get("Method") or payload.get("method") or payload.get("model")
        dataset = payload.get("Dataset") or payload.get("dataset")
        if (method, dataset) not in row_by_key:
            continue
        row_by_key[(method, dataset)].update(normalize_metric_payload(payload))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect detector metric JSON files into a paper CSV table.")
    parser.add_argument("--metrics-dir", default="outputs/detectors/metrics")
    parser.add_argument("--out", default="paper/tables/detector_frontend_comparison_filled.csv")
    args = parser.parse_args()
    rows = collect_detector_metrics(args.metrics_dir)
    write_metrics_csv(rows, args.out, fieldnames=DETECTOR_COLUMNS)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
