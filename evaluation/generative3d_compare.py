"""Collect and compare Marine City 3D generative reconstruction results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from generative3d.registry import specs_by_key
from runtime.config import resolve_path


COLUMNS = [
    "method",
    "display_name",
    "scene",
    "status",
    "PSNR",
    "SSIM",
    "LPIPS",
    "FPS",
    "train_time_min",
    "VRAM_GB",
    "disk_GB",
    "advantage",
    "limitation",
    "result_path",
]

METHOD_ALIASES = {
    "3dgs": "gaussian_splatting",
    "3d_gaussian_splatting": "gaussian_splatting",
    "gaussian": "gaussian_splatting",
    "gaussian-splatting": "gaussian_splatting",
    "instant-ngp": "instant_ngp",
    "instantngp": "instant_ngp",
    "mip-nerf-360": "mip_nerf_360",
    "mipnerf360": "mip_nerf_360",
    "nerfacto": "nerf",
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    metrics = payload.get("metrics", {})
    if isinstance(metrics, dict):
        for key in keys:
            value = metrics.get(key)
            if value is not None:
                return value
    return ""


def canonical_method(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_")
    return METHOD_ALIASES.get(normalized, normalized)


def display_name_for(method: str, payload: dict[str, Any], spec: Any) -> str:
    explicit = str(payload.get("display_name") or "").strip()
    if explicit:
        return explicit
    status_notes = f"{payload.get('status', '')} {payload.get('notes', '')}".lower()
    if method == "nerf" and "nerfacto" in status_notes:
        return "Nerfacto (torch smoke)"
    return spec.display_name if spec else method


def normalize_result(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    method = canonical_method(str(payload.get("method") or payload.get("model") or path.stem.split("_")[0]))
    spec = specs_by_key().get(method)
    strengths = spec.expected_strengths if spec else []
    weaknesses = spec.expected_weaknesses if spec else []
    return {
        "method": method,
        "display_name": display_name_for(method, payload, spec),
        "scene": payload.get("scene", ""),
        "status": payload.get("status", ""),
        "PSNR": first(payload, "PSNR", "psnr"),
        "SSIM": first(payload, "SSIM", "ssim"),
        "LPIPS": first(payload, "LPIPS", "lpips"),
        "FPS": first(payload, "FPS", "fps"),
        "train_time_min": first(payload, "train_time_min", "training_time_min"),
        "VRAM_GB": first(payload, "VRAM_GB", "vram_gb"),
        "disk_GB": first(payload, "disk_GB", "disk_gb"),
        "advantage": "; ".join(strengths),
        "limitation": "; ".join(weaknesses),
        "result_path": str(path),
    }


def collect_results(results_dir: str | Path) -> list[dict[str, Any]]:
    root = resolve_path(results_dir)
    return [normalize_result(path) for path in sorted(root.glob("*_result.json"))]


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    out = resolve_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect 3D generative model comparison results.")
    parser.add_argument("--results-dir", default="outputs/experiments/3d_generation")
    parser.add_argument("--out", default="outputs/experiments/3d_generation_comparison.csv")
    args = parser.parse_args()
    rows = collect_results(args.results_dir)
    write_csv(args.out, rows)
    print(f"Wrote {resolve_path(args.out)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
