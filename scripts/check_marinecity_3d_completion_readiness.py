"""Check whether MarineCity neural 3D completion/reconstruction results exist."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = REPO_ROOT / "outputs/reports/live"
BENCHMARK = REPO_ROOT / "outputs/experiments/marinecity_real_capture_benchmark.json"
COMPARISON = REPO_ROOT / "outputs/experiments/3d_generation_comparison.csv"
RESULT_DIR = REPO_ROOT / "outputs/experiments/3d_generation"
DATASET_EXPORT = RESULT_DIR / "marinecity_real_capture_neural3d/dataset_manifest.json"
POINTCLOUD_SMOKE = RESULT_DIR / "marinecity_depth_pointcloud_smoke/manifest.json"
DEPTH_VIEW_CONSISTENCY = RESULT_DIR / "marinecity_depth_view_consistency_sanity/manifest.json"
RUNNER_PREFLIGHT = LIVE_DIR / "marinecity_3d_runner_preflight.json"
EXPECTED_METHODS = ["nerf", "instant_ngp", "mip_nerf_360", "gaussian_splatting"]
REQUIRED_QUALITY_METRICS = ["PSNR", "SSIM", "LPIPS"]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def numeric_present(row: dict[str, str], key: str) -> bool:
    value = (row.get(key, "") or "").strip()
    if not value:
        return False
    try:
        float(value)
    except ValueError:
        return False
    return True


def result_jsons() -> list[Path]:
    if not RESULT_DIR.exists():
        return []
    return sorted(RESULT_DIR.rglob("*result*.json"))


def build_report() -> dict[str, Any]:
    benchmark = read_json(BENCHMARK)
    dataset_export = read_json(DATASET_EXPORT)
    pointcloud_smoke = read_json(POINTCLOUD_SMOKE)
    view_consistency = read_json(DEPTH_VIEW_CONSISTENCY)
    runner_preflight = read_json(RUNNER_PREFLIGHT)
    summary = benchmark.get("summary", {}) or {}
    rows = read_csv(COMPARISON)
    metric_rows = [
        row
        for row in rows
        if all(numeric_present(row, metric) for metric in REQUIRED_QUALITY_METRICS)
        and (row.get("status", "") or "").lower() not in {"pending", "placeholder", "missing"}
    ]
    json_paths = result_jsons()
    methods_ready = sorted(set((row.get("method") or "").strip() for row in metric_rows if (row.get("method") or "").strip()))
    missing_methods = [method for method in EXPECTED_METHODS if method not in methods_ready]
    source_ready = bool(summary.get("terrain_all_valid")) and bool(summary.get("google_tiles_all_valid")) and int(summary.get("frame_count", 0) or 0) >= 9
    dataset_ready = dataset_export.get("status") == "marinecity_neural3d_dataset_export_ready"
    pointcloud_ready = pointcloud_smoke.get("status") == "marinecity_depth_pointcloud_smoke_ready"
    if source_ready and len(metric_rows) >= 2:
        status = "marinecity_3d_completion_ready"
    elif source_ready and dataset_ready:
        status = "marinecity_3d_input_dataset_ready_metrics_pending"
    else:
        status = "marinecity_3d_completion_pending_upstream_runner"
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "source_capture_ready": source_ready,
        "neural3d_dataset_ready": dataset_ready,
        "depth_pointcloud_smoke_ready": pointcloud_ready,
        "runner_preflight_status": runner_preflight.get("status", "missing"),
        "neural_runner_available": runner_preflight.get("neural_runner_available"),
        "geometry_smoke_available": runner_preflight.get("geometry_smoke_available"),
        "runner_preflight_report": str(RUNNER_PREFLIGHT.with_suffix(".md").relative_to(REPO_ROOT)),
        "depth_pointcloud_smoke_manifest": str(POINTCLOUD_SMOKE.relative_to(REPO_ROOT)),
        "depth_pointcloud_point_count": pointcloud_smoke.get("point_count"),
        "depth_pointcloud_preview": pointcloud_smoke.get("preview"),
        "depth_view_consistency_sanity_ready": view_consistency.get("status") == "marinecity_depth_view_consistency_sanity_ready",
        "depth_view_consistency_manifest": str(DEPTH_VIEW_CONSISTENCY.relative_to(REPO_ROOT)),
        "depth_view_consistency_contact_sheet": view_consistency.get("live_contact_sheet") or view_consistency.get("contact_sheet"),
        "depth_view_consistency_mean_psnr": view_consistency.get("mean_psnr"),
        "depth_view_consistency_mean_ssim_luma": view_consistency.get("mean_ssim_luma"),
        "depth_view_consistency_mean_fill_ratio": view_consistency.get("mean_fill_ratio"),
        "neural3d_dataset_manifest": str(DATASET_EXPORT.relative_to(REPO_ROOT)),
        "neural3d_dataset_frame_count": dataset_export.get("frame_count"),
        "neural3d_dataset_train_frame_count": dataset_export.get("train_frame_count"),
        "neural3d_dataset_heldout_frame_count": dataset_export.get("heldout_frame_count"),
        "neural3d_dataset_transforms": dataset_export.get("transforms"),
        "capture_summary": {
            "scenario_count": summary.get("scenario_count"),
            "frame_count": summary.get("frame_count"),
            "uav_count": summary.get("uav_count"),
            "altitude_range_m": summary.get("altitude_range_m"),
            "terrain_all_valid": summary.get("terrain_all_valid"),
            "google_tiles_all_valid": summary.get("google_tiles_all_valid"),
            "mean_rgb_black_ratio": summary.get("mean_rgb_black_ratio"),
            "mean_depth_finite_ratio": summary.get("mean_depth_finite_ratio"),
        },
        "comparison_csv": str(COMPARISON.relative_to(REPO_ROOT)),
        "comparison_row_count": len(rows),
        "metric_result_row_count": len(metric_rows),
        "result_json_count": len(json_paths),
        "result_jsons": [str(path.relative_to(REPO_ROOT)) for path in json_paths[:20]],
        "methods_ready": methods_ready,
        "missing_expected_methods": missing_methods,
        "claiming_rule": (
            "The real-Cesium RGB/depth/pose capture source, neural-3D transforms package, and depth point-cloud smoke are ready for the 3D handoff. "
            "Neural 3D completion/reconstruction remains pending until non-placeholder metric rows are collected."
        ),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# MarineCity 3D Completion Readiness",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        "",
        "## Capture Source",
        "",
    ]
    for key, value in report["capture_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
        "## Neural 3D Results",
        "",
        f"- Input dataset ready: `{report['neural3d_dataset_ready']}`",
        f"- Runner preflight: `{report['runner_preflight_status']}`",
        f"- Neural runner available: `{report['neural_runner_available']}`",
        f"- Geometry smoke available: `{report['geometry_smoke_available']}`",
        f"- Runner preflight report: `{report['runner_preflight_report']}`",
        f"- Depth point-cloud smoke ready: `{report['depth_pointcloud_smoke_ready']}`",
        f"- Depth point-cloud points: `{report['depth_pointcloud_point_count']}`",
        f"- Depth point-cloud preview: `{report['depth_pointcloud_preview']}`",
        f"- Depth view-consistency sanity ready: `{report['depth_view_consistency_sanity_ready']}`",
        f"- Depth view-consistency manifest: `{report['depth_view_consistency_manifest']}`",
        f"- Depth view-consistency contact sheet: `{report['depth_view_consistency_contact_sheet']}`",
        f"- Depth view-consistency mean PSNR/SSIM/fill: `{report['depth_view_consistency_mean_psnr']}` / `{report['depth_view_consistency_mean_ssim_luma']}` / `{report['depth_view_consistency_mean_fill_ratio']}`",
        f"- Input dataset manifest: `{report['neural3d_dataset_manifest']}`",
        f"- Dataset frames train/heldout: `{report['neural3d_dataset_frame_count']}` / `{report['neural3d_dataset_train_frame_count']}` / `{report['neural3d_dataset_heldout_frame_count']}`",
        f"- Transforms: `{report['neural3d_dataset_transforms']}`",
        f"- Comparison CSV: `{report['comparison_csv']}`",
            f"- Comparison rows: `{report['comparison_row_count']}`",
            f"- Metric result rows: `{report['metric_result_row_count']}`",
            f"- Result JSON count: `{report['result_json_count']}`",
            f"- Methods ready: `{report['methods_ready']}`",
            f"- Missing expected methods: `{report['missing_expected_methods']}`",
            "",
            f"Claiming rule: {report['claiming_rule']}",
            "",
            "Next action: run the 3D generation/completion runner on the verified MarineCity captures and collect PSNR/SSIM/LPIPS/FPS/runtime rows before upgrading this from pending to a paper benchmark claim.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    json_path = LIVE_DIR / "marinecity_3d_completion_readiness.json"
    md_path = LIVE_DIR / "marinecity_3d_completion_readiness.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(md_path, report)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
