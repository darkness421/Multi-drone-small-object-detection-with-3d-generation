"""Build a depth-fused point-cloud smoke artifact from MarineCity captures.

This is not a neural reconstruction benchmark. It uses the verified
real-Cesium RGB/depth/pose captures and the exported ``transforms.json`` to
produce a small colored PLY and a top-down preview for sanity checking the 3D
handoff before NeRF/3DGS runners are installed.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = REPO_ROOT / "outputs/experiments/3d_generation/marinecity_real_capture_neural3d/dataset_manifest.json"
DEFAULT_OUT = REPO_ROOT / "outputs/experiments/3d_generation/marinecity_depth_pointcloud_smoke"
LIVE_DIR = REPO_ROOT / "outputs/reports/live"
DEFAULT_PAPER_PREVIEW = REPO_ROOT / "paper/figures/results/marinecity_system/marinecity_depth_pointcloud_smoke_topdown.png"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(vec: np.ndarray) -> np.ndarray:
    length = np.linalg.norm(vec, axis=-1, keepdims=True)
    return vec / np.maximum(length, 1e-9)


def load_frames(dataset_manifest: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    transforms_path = Path(str(dataset_manifest["transforms"]))
    transforms = read_json(transforms_path)
    return transforms_path.parent, transforms


def frame_points(
    frame: dict[str, Any],
    *,
    dataset_root: Path,
    fl_x: float,
    fl_y: float,
    cx: float,
    cy: float,
    stride: int,
    max_depth_m: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    image_path = dataset_root / frame["file_path"]
    depth_path = dataset_root / frame["depth_file_path"]
    image = Image.open(image_path).convert("RGB")
    rgb = np.asarray(image)
    depth = np.load(depth_path)
    height, width = depth.shape[:2]
    ys = np.arange(0, height, stride)
    xs = np.arange(0, width, stride)
    grid_x, grid_y = np.meshgrid(xs, ys)
    sampled_depth = depth[grid_y, grid_x].astype(np.float32)
    valid = np.isfinite(sampled_depth) & (sampled_depth > 0.1) & (sampled_depth < max_depth_m)
    if not np.any(valid):
        return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 3), dtype=np.uint8), {
            "frame_id": frame.get("frame_id"),
            "uav_id": frame.get("uav_id"),
            "sampled_points": 0,
            "valid_points": 0,
        }
    x = (grid_x[valid].astype(np.float32) - cx) / fl_x
    y = -(grid_y[valid].astype(np.float32) - cy) / fl_y
    camera_dirs = normalize(np.stack([x, y, -np.ones_like(x)], axis=1))
    c2w = np.asarray(frame["transform_matrix"], dtype=np.float32)
    rotation = c2w[:3, :3]
    eye = c2w[:3, 3]
    world_dirs = normalize(camera_dirs @ rotation.T)
    points = eye[None, :] + world_dirs * sampled_depth[valid, None]
    colors = rgb[grid_y[valid], grid_x[valid]].astype(np.uint8)
    return points.astype(np.float32), colors, {
        "frame_id": frame.get("frame_id"),
        "scenario_id": frame.get("scenario_id"),
        "uav_id": frame.get("uav_id"),
        "split": frame.get("split"),
        "sampled_points": int(sampled_depth.size),
        "valid_points": int(points.shape[0]),
        "depth_median_m": frame.get("depth_median_m"),
        "altitude_m": frame.get("altitude_m"),
    }


def write_ply(path: Path, points: np.ndarray, colors: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "\n".join(
        [
            "ply",
            "format ascii 1.0",
            f"element vertex {len(points)}",
            "property float x",
            "property float y",
            "property float z",
            "property uchar red",
            "property uchar green",
            "property uchar blue",
            "end_header",
        ]
    )
    with path.open("w", encoding="utf-8") as handle:
        handle.write(header + "\n")
        for point, color in zip(points, colors):
            handle.write(
                f"{point[0]:.5f} {point[1]:.5f} {point[2]:.5f} {int(color[0])} {int(color[1])} {int(color[2])}\n"
            )


def write_preview(path: Path, points: np.ndarray, colors: np.ndarray, *, title: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1400, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image, "RGBA")
    if len(points) == 0:
        draw.text((30, 30), "No valid points", fill=(0, 0, 0, 255))
        image.save(path)
        return {"bounds_xyz": [], "preview_path": str(path)}
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    span = np.maximum(maxs - mins, 1e-6)
    margin = 70
    scale = min((width - 2 * margin) / span[0], (height - 2 * margin) / span[1])
    xs = margin + (points[:, 0] - mins[0]) * scale
    ys = height - margin - (points[:, 1] - mins[1]) * scale
    order = np.argsort(points[:, 2])
    for idx in order:
        color = tuple(int(v) for v in colors[idx])
        x = float(xs[idx])
        y = float(ys[idx])
        draw.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(*color, 160))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
        small = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    draw.text((24, 18), title, fill=(17, 24, 39, 255), font=font)
    draw.text(
        (24, 48),
        f"points={len(points)} | x=[{mins[0]:.1f},{maxs[0]:.1f}] y=[{mins[1]:.1f},{maxs[1]:.1f}] z=[{mins[2]:.1f},{maxs[2]:.1f}]",
        fill=(55, 65, 81, 255),
        font=small,
    )
    image.save(path)
    return {
        "bounds_xyz": [[float(mins[i]), float(maxs[i])] for i in range(3)],
        "preview_path": str(path),
    }


def shutil_copy_preview(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build(args: argparse.Namespace) -> dict[str, Any]:
    dataset_manifest = read_json(Path(args.dataset_manifest))
    dataset_root, transforms = load_frames(dataset_manifest)
    out_dir = Path(args.out_dir)
    frames = transforms.get("frames", [])
    all_points: list[np.ndarray] = []
    all_colors: list[np.ndarray] = []
    frame_rows: list[dict[str, Any]] = []
    for frame in frames:
        points, colors, row = frame_points(
            frame,
            dataset_root=dataset_root,
            fl_x=float(transforms["fl_x"]),
            fl_y=float(transforms["fl_y"]),
            cx=float(transforms["cx"]),
            cy=float(transforms["cy"]),
            stride=args.stride,
            max_depth_m=args.max_depth_m,
        )
        if args.max_points_per_frame and len(points) > args.max_points_per_frame:
            sample_idx = np.linspace(0, len(points) - 1, args.max_points_per_frame).astype(np.int64)
            points = points[sample_idx]
            colors = colors[sample_idx]
            row["valid_points_after_cap"] = int(len(points))
        all_points.append(points)
        all_colors.append(colors)
        frame_rows.append(row)
    merged_points = np.concatenate(all_points, axis=0) if all_points else np.zeros((0, 3), dtype=np.float32)
    merged_colors = np.concatenate(all_colors, axis=0) if all_colors else np.zeros((0, 3), dtype=np.uint8)
    ply_path = out_dir / "marinecity_depth_pointcloud_smoke.ply"
    preview_path = out_dir / "marinecity_depth_pointcloud_smoke_topdown.png"
    paper_preview_path = Path(args.paper_preview)
    write_ply(ply_path, merged_points, merged_colors)
    preview = write_preview(preview_path, merged_points, merged_colors, title="MarineCity Depth-Fused Point-Cloud Smoke")
    paper_preview_path.parent.mkdir(parents=True, exist_ok=True)
    shutil_copy_preview(preview_path, paper_preview_path)
    manifest = {
        "status": "marinecity_depth_pointcloud_smoke_ready",
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "dataset_manifest": str(Path(args.dataset_manifest)),
        "dataset_status": dataset_manifest.get("status"),
        "out_dir": str(out_dir),
        "ply": str(ply_path),
        "preview": str(preview_path),
        "paper_preview": str(paper_preview_path),
        "frame_count": len(frames),
        "point_count": int(len(merged_points)),
        "stride": args.stride,
        "max_depth_m": args.max_depth_m,
        "max_points_per_frame": args.max_points_per_frame,
        "bounds_xyz": preview.get("bounds_xyz", []),
        "frame_rows": frame_rows,
        "claiming_rule": (
            "This is a depth-fused geometry smoke artifact from real-Cesium RGB/depth/pose captures. "
            "It is not a neural NeRF/3DGS reconstruction benchmark."
        ),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    write_live(manifest, Path(args.live_md), Path(args.live_json))
    return manifest


def write_live(manifest: dict[str, Any], live_md: Path, live_json: Path) -> None:
    live_json.parent.mkdir(parents=True, exist_ok=True)
    live_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# MarineCity Depth Point-Cloud Smoke",
        "",
        f"Updated: `{manifest['updated_at_kst']}`",
        f"Status: `{manifest['status']}`",
        "",
        f"- Dataset status: `{manifest['dataset_status']}`",
        f"- Frames: `{manifest['frame_count']}`",
        f"- Points: `{manifest['point_count']}`",
        f"- PLY: `{manifest['ply']}`",
        f"- Preview: `{manifest['preview']}`",
        f"- Paper preview: `{manifest['paper_preview']}`",
        f"- Bounds XYZ: `{manifest['bounds_xyz']}`",
        f"- Sampling stride: `{manifest['stride']}`; max depth `{manifest['max_depth_m']}` m",
        "",
        "## Frame Counts",
        "",
        "| Scenario | UAV | Split | Valid points | Altitude |",
        "|---|---|---|---:|---:|",
    ]
    for row in manifest["frame_rows"]:
        lines.append(
            f"| {row.get('scenario_id')} | {row.get('uav_id')} | {row.get('split')} | "
            f"{row.get('valid_points_after_cap', row.get('valid_points', 0))} | {row.get('altitude_m')} |"
        )
    lines.extend(["", f"Claiming rule: {manifest['claiming_rule']}", ""])
    live_md.parent.mkdir(parents=True, exist_ok=True)
    live_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-manifest", default=str(DEFAULT_DATASET))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--stride", type=int, default=32)
    parser.add_argument("--max-depth-m", type=float, default=500.0)
    parser.add_argument("--max-points-per-frame", type=int, default=1200)
    parser.add_argument("--live-md", default=str(LIVE_DIR / "marinecity_depth_pointcloud_smoke.md"))
    parser.add_argument("--live-json", default=str(LIVE_DIR / "marinecity_depth_pointcloud_smoke.json"))
    parser.add_argument("--paper-preview", default=str(DEFAULT_PAPER_PREVIEW))
    args = parser.parse_args()
    manifest = build(args)
    print(json.dumps({"manifest": str(Path(args.out_dir) / "manifest.json"), "status": manifest["status"], "points": manifest["point_count"]}, indent=2))


if __name__ == "__main__":
    main()
