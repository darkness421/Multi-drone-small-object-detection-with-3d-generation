"""Import verified MarineCity neural-3D metric rows from external runners.

This script is intentionally strict: placeholder rows, missing quality metrics,
and unknown methods are rejected by default. It lets upstream NeRF/Instant-NGP/
3DGS runs be converted into the repository's normalized result JSON files and
comparison CSV without inventing paper-facing numbers.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.generative3d_compare import COLUMNS, canonical_method, collect_results, write_csv  # noqa: E402
from generative3d.registry import specs_by_key  # noqa: E402

DEFAULT_RESULTS_DIR = ROOT / "outputs/experiments/3d_generation"
DEFAULT_COMPARISON = ROOT / "outputs/experiments/3d_generation_comparison.csv"
DEFAULT_SCENE = "marinecity_real_capture"
BLOCKED_STATUSES = {"", "pending", "placeholder", "missing", "dry_run", "mock"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def numeric(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first(payload: dict[str, Any], *keys: str) -> Any:
    metrics = payload.get("metrics", {})
    for key in keys:
        if payload.get(key) not in (None, ""):
            return payload.get(key)
        if isinstance(metrics, dict) and metrics.get(key) not in (None, ""):
            return metrics.get(key)
    return ""


def normalize_payload(payload: dict[str, Any], source: Path, default_scene: str) -> dict[str, Any]:
    method = canonical_method(str(payload.get("method") or payload.get("model") or payload.get("display_name") or ""))
    return {
        "method": method,
        "scene": payload.get("scene") or default_scene,
        "status": str(payload.get("status") or "complete").lower(),
        "PSNR": first(payload, "PSNR", "psnr"),
        "SSIM": first(payload, "SSIM", "ssim"),
        "LPIPS": first(payload, "LPIPS", "lpips"),
        "FPS": first(payload, "FPS", "fps"),
        "train_time_min": first(payload, "train_time_min", "training_time_min", "runtime_min", "time_min"),
        "VRAM_GB": first(payload, "VRAM_GB", "vram_gb", "peak_vram_gb"),
        "disk_GB": first(payload, "disk_GB", "disk_gb"),
        "checkpoint": payload.get("checkpoint") or payload.get("checkpoint_path") or "",
        "render_dir": payload.get("render_dir") or payload.get("renders") or "",
        "source_result": str(source),
        "notes": payload.get("notes") or payload.get("note") or "",
    }


def payloads_from_path(path: Path, default_scene: str) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        payload = read_json(path)
        if isinstance(payload.get("rows"), list):
            return [normalize_payload(dict(row), path, default_scene) for row in payload["rows"]]
        if isinstance(payload.get("results"), list):
            return [normalize_payload(dict(row), path, default_scene) for row in payload["results"]]
        return [normalize_payload(payload, path, default_scene)]
    if path.suffix.lower() == ".csv":
        return [normalize_payload(row, path, default_scene) for row in read_csv(path)]
    raise SystemExit(f"Unsupported input format: {path}")


def validate(row: dict[str, Any], required_metrics: list[str], allow_unknown: bool) -> list[str]:
    errors: list[str] = []
    specs = specs_by_key()
    method = str(row.get("method") or "")
    if not method:
        errors.append("missing method")
    if method not in specs and not allow_unknown:
        errors.append(f"unknown method `{method}`; expected one of {sorted(specs)}")
    status = str(row.get("status") or "").lower()
    if status in BLOCKED_STATUSES:
        errors.append(f"blocked status `{status}`")
    for metric in required_metrics:
        if numeric(row.get(metric)) is None:
            errors.append(f"missing numeric {metric}")
    return errors


def write_result_json(row: dict[str, Any], results_dir: Path, overwrite: bool) -> Path:
    method = str(row["method"])
    scene = str(row.get("scene") or DEFAULT_SCENE)
    out = results_dir / f"{method}_{scene}_result.json"
    if out.exists() and not overwrite:
        raise SystemExit(f"Refusing to overwrite existing result JSON: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="External runner JSON/CSV metric files.")
    parser.add_argument("--results-dir", default=str(DEFAULT_RESULTS_DIR))
    parser.add_argument("--comparison-csv", default=str(DEFAULT_COMPARISON))
    parser.add_argument("--scene", default=DEFAULT_SCENE)
    parser.add_argument("--required-metrics", default="PSNR,SSIM,LPIPS")
    parser.add_argument("--allow-unknown-method", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    required_metrics = [item.strip() for item in args.required_metrics.split(",") if item.strip()]
    results_dir = Path(args.results_dir)
    comparison_csv = Path(args.comparison_csv)
    imported: list[str] = []
    rejected: list[dict[str, Any]] = []

    for value in args.inputs:
        path = Path(value)
        rows = payloads_from_path(path, args.scene)
        for row in rows:
            errors = validate(row, required_metrics, args.allow_unknown_method)
            if errors:
                rejected.append({"source": str(path), "method": row.get("method"), "errors": errors})
                continue
            imported.append(str(write_result_json(row, results_dir, args.overwrite)))

    if rejected:
        print(json.dumps({"imported": imported, "rejected": rejected}, indent=2, ensure_ascii=False))
        raise SystemExit(2)

    rows = collect_results(results_dir)
    write_csv(comparison_csv, rows)
    print(
        json.dumps(
            {
                "imported": imported,
                "comparison_csv": str(comparison_csv),
                "comparison_rows": len(rows),
                "columns": COLUMNS,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
