"""Build a real-Cesium MarineCity capture benchmark manifest.

This script intentionally ignores the older dry-run placeholder RGB/depth files
under outputs/experiments/images|depth.  It scans Isaac/Cesium exports that
contain real PNG RGB captures and distance-to-camera depth arrays, writes a
small paper-facing manifest, and produces a visual QA contact sheet.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


DEFAULT_EXPORT_ROOT = Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports")
DEFAULT_SCENARIOS = [
    "uavmarine_s0_viewer160_session_recapture",
    "uavmarine_s1_viewer160_session_recapture",
    "uavmarine_s2_viewer160_session_recapture",
]


@dataclass(slots=True)
class CaptureFrame:
    scenario_id: str
    frame_id: str
    uav_id: str
    rgb_path: str
    depth_path: str
    depth_preview_path: str
    camera_prim: str
    camera_position: list[float]
    look_at_target: list[float]
    altitude_m: float | None
    image_size: list[int]
    rgb_black_ratio: float
    depth_finite_ratio: float
    depth_min_m: float | None
    depth_median_m: float | None
    depth_max_m: float | None


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def image_black_ratio(path: Path) -> tuple[list[int], float]:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        arr = np.asarray(rgb, dtype=np.uint8)
    gray = arr.mean(axis=2)
    return [int(rgb.width), int(rgb.height)], float((gray < 10).mean())


def depth_stats(path: Path) -> tuple[float, float | None, float | None, float | None]:
    arr = np.load(path)
    finite = np.isfinite(arr)
    finite_ratio = float(finite.mean())
    if not finite.any():
        return finite_ratio, None, None, None
    vals = arr[finite].astype(np.float64)
    return finite_ratio, float(vals.min()), float(np.median(vals)), float(vals.max())


def scenario_sort_key(path: Path) -> tuple[int, str]:
    name = path.name
    if "_s0_" in name:
        return (0, name)
    if "_s1_" in name:
        return (1, name)
    if "_s2_" in name:
        return (2, name)
    return (99, name)


def resolve_scenarios(export_root: Path, requested: list[str]) -> list[Path]:
    if requested:
        return [export_root / item for item in requested]
    found = [export_root / item for item in DEFAULT_SCENARIOS]
    if all((path / "real_cesium_capture_summary.json").exists() for path in found):
        return found
    return sorted(
        [path for path in export_root.glob("uavmarine_s*_viewer160*_recapture*") if (path / "real_cesium_capture_summary.json").exists()],
        key=scenario_sort_key,
    )[:3]


def build_frames(scenario_dirs: list[Path]) -> tuple[list[CaptureFrame], list[dict[str, Any]]]:
    frames: list[CaptureFrame] = []
    scenarios: list[dict[str, Any]] = []
    for scenario_dir in scenario_dirs:
        summary_path = scenario_dir / "real_cesium_capture_summary.json"
        if not summary_path.exists():
            continue
        summary = read_json(summary_path)
        capture_dir = scenario_dir / "real_cesium_capture"
        scenario_id = scenario_dir.name
        frame_rows = summary.get("frames", [])
        scenarios.append(
            {
                "scenario_id": scenario_id,
                "summary_path": str(summary_path),
                "stage_path": summary.get("stage_path") or summary.get("root_layer") or summary.get("base_stage"),
                "root_layer": summary.get("root_layer"),
                "georeference_readback": summary.get("georeference_readback", {}),
                "camera_profile": summary.get("camera_profile", {}),
                "object_marker_count": summary.get("object_marker_count"),
                "uav_marker_count": summary.get("uav_marker_count"),
                "real_cesium_google_tiles": bool(summary.get("prim_status", {}).get("/Google_Photorealistic_3D_Tiles", {}).get("valid")),
                "real_cesium_terrain": bool(summary.get("prim_status", {}).get("/Cesium_World_Terrain", {}).get("valid")),
            }
        )
        for idx, row in enumerate(frame_rows, start=1):
            rgb_rel = row.get("rgb_path") or f"real_cesium_capture/frame_{idx:03d}_{row.get('uav_id','uav')}_rgb.png"
            depth_rel = row.get("depth_npy_path") or f"real_cesium_capture/frame_{idx:03d}_{row.get('uav_id','uav')}_depth.npy"
            depth_preview_rel = row.get("depth_preview_path") or ""
            rgb_path = scenario_dir / str(rgb_rel)
            depth_path = scenario_dir / str(depth_rel)
            depth_preview_path = scenario_dir / str(depth_preview_rel) if depth_preview_rel else Path("")
            if not rgb_path.exists() or not depth_path.exists():
                continue
            size, black_ratio = image_black_ratio(rgb_path)
            finite_ratio, depth_min, depth_median, depth_max = depth_stats(depth_path)
            camera_position = [float(x) for x in row.get("camera_position", [])]
            frames.append(
                CaptureFrame(
                    scenario_id=scenario_id,
                    frame_id=Path(str(rgb_rel)).stem.replace("_rgb", ""),
                    uav_id=str(row.get("uav_id", "")),
                    rgb_path=str(rgb_path),
                    depth_path=str(depth_path),
                    depth_preview_path=str(depth_preview_path) if depth_preview_path else "",
                    camera_prim=str(row.get("camera_prim", "")),
                    camera_position=camera_position,
                    look_at_target=[float(x) for x in row.get("look_at_target", [])],
                    altitude_m=finite_float(camera_position[2] if len(camera_position) >= 3 else row.get("altitude_m")),
                    image_size=size,
                    rgb_black_ratio=black_ratio,
                    depth_finite_ratio=finite_ratio,
                    depth_min_m=depth_min,
                    depth_median_m=depth_median,
                    depth_max_m=depth_max,
                )
            )
    return frames, scenarios


def write_csv(path: Path, frames: list[CaptureFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(frames[0]).keys()) if frames else ["scenario_id"])
        writer.writeheader()
        for frame in frames:
            writer.writerow(asdict(frame))


def make_contact_sheet(path: Path, frames: list[CaptureFrame]) -> None:
    if not frames:
        return
    thumb_w, thumb_h = 360, 203
    label_h = 58
    cols = 3
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, frame in enumerate(frames):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h)
        with Image.open(frame.rgb_path) as image:
            thumb = image.convert("RGB")
            thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        label = (
            f"{frame.scenario_id} / {frame.uav_id}\n"
            f"alt={frame.altitude_m:.0f}m black={frame.rgb_black_ratio:.3f} "
            f"depthFinite={frame.depth_finite_ratio:.3f}"
        )
        draw.rectangle([x, y + thumb_h, x + thumb_w, y + thumb_h + label_h], fill=(248, 248, 248))
        draw.text((x + 6, y + thumb_h + 6), label, fill=(20, 20, 20))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def write_markdown(path: Path, payload: dict[str, Any], csv_path: Path, contact_sheet: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# MarineCity Real-Cesium Capture Benchmark",
        "",
        f"Updated: `{summary['updated']}`",
        "",
        "## Summary",
        "",
        f"- Scenario count: `{summary['scenario_count']}`",
        f"- Frame count: `{summary['frame_count']}`",
        f"- UAV count: `{summary['uav_count']}`",
        f"- Altitude range: `{summary['altitude_range_m']}` m",
        f"- Mean RGB black ratio: `{summary['mean_rgb_black_ratio']:.4f}`",
        f"- Mean depth finite ratio: `{summary['mean_depth_finite_ratio']:.4f}`",
        f"- Real Cesium terrain valid in all scenarios: `{summary['terrain_all_valid']}`",
        f"- Google Photorealistic 3D Tiles valid in all scenarios: `{summary['google_tiles_all_valid']}`",
        "",
        "## Files",
        "",
        f"- Manifest: `{payload['manifest_path']}`",
        f"- CSV: `{csv_path}`",
        f"- Contact sheet: `{contact_sheet}`",
        "",
        "## Claiming Rule",
        "",
        "This benchmark is valid as a real-Cesium RGB/depth/pose capture source for",
        "MarineCity system smoke tests and depth-backed evidence-graph checks. It is",
        "not a completed NeRF/Instant-NGP/Mip-NeRF/3DGS training result yet; those",
        "methods still require connecting an external upstream runner.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build real-Cesium MarineCity capture benchmark manifest.")
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT))
    parser.add_argument("--scenario", action="append", default=[], help="Scenario directory name under export root.")
    parser.add_argument("--out", default="outputs/experiments/marinecity_real_capture_benchmark.json")
    parser.add_argument("--csv-out", default="outputs/experiments/marinecity_real_capture_benchmark.csv")
    parser.add_argument("--md-out", default="outputs/reports/live/marinecity_real_capture_benchmark.md")
    parser.add_argument("--contact-sheet", default="outputs/reports/live/marinecity_real_capture_benchmark_contact_sheet.png")
    args = parser.parse_args()

    export_root = Path(args.export_root)
    scenario_dirs = resolve_scenarios(export_root, args.scenario)
    frames, scenarios = build_frames(scenario_dirs)
    altitudes = [frame.altitude_m for frame in frames if frame.altitude_m is not None]
    summary = {
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_export_root": str(export_root),
        "scenario_count": len(scenarios),
        "frame_count": len(frames),
        "uav_count": len({frame.uav_id for frame in frames if frame.uav_id}),
        "altitude_range_m": [min(altitudes), max(altitudes)] if altitudes else [],
        "mean_rgb_black_ratio": float(np.mean([frame.rgb_black_ratio for frame in frames])) if frames else 0.0,
        "mean_depth_finite_ratio": float(np.mean([frame.depth_finite_ratio for frame in frames])) if frames else 0.0,
        "terrain_all_valid": all(item.get("real_cesium_terrain") for item in scenarios) if scenarios else False,
        "google_tiles_all_valid": all(item.get("real_cesium_google_tiles") for item in scenarios) if scenarios else False,
        "external_neural_3d_runner_status": "pending_upstream_runner_connection",
    }
    out = Path(args.out)
    payload = {
        "summary": summary,
        "scenarios": scenarios,
        "frames": [asdict(frame) for frame in frames],
        "manifest_path": str(out),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    csv_out = Path(args.csv_out)
    write_csv(csv_out, frames)
    contact_sheet = Path(args.contact_sheet)
    make_contact_sheet(contact_sheet, frames)
    write_markdown(Path(args.md_out), payload, csv_out, contact_sheet)
    print(json.dumps({"manifest": str(out), "csv": str(csv_out), "markdown": args.md_out, "contact_sheet": str(contact_sheet), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
