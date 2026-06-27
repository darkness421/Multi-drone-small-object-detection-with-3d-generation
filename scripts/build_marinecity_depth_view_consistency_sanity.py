"""Depth-backed cross-view consistency sanity for MarineCity captures.

This is not a NeRF/3DGS benchmark. It projects the real-Cesium RGB/depth/pose
captures from train UAV views into the held-out UAV view and measures only the
pixels that receive a projected color. The artifact is useful for checking that
the 3D handoff is geometrically plausible while the neural runner gate remains
pending.
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
DEFAULT_OUT = REPO_ROOT / "outputs/experiments/3d_generation/marinecity_depth_view_consistency_sanity"
LIVE_DIR = REPO_ROOT / "outputs/reports/live"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dataset(dataset_manifest: Path) -> tuple[Path, dict[str, Any]]:
    manifest = read_json(dataset_manifest)
    transforms_path = Path(str(manifest["transforms"]))
    return transforms_path.parent, read_json(transforms_path)


def frame_key(frame: dict[str, Any]) -> tuple[str, str]:
    return str(frame.get("scenario_id", "")), str(frame.get("uav_id", ""))


def normalize(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.maximum(np.linalg.norm(vectors, axis=-1, keepdims=True), 1e-9)


def load_frame_arrays(dataset_root: Path, frame: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    image = np.asarray(Image.open(dataset_root / frame["file_path"]).convert("RGB"), dtype=np.uint8)
    depth = np.load(dataset_root / frame["depth_file_path"]).astype(np.float32)
    return image, depth


def source_points(
    dataset_root: Path,
    frame: dict[str, Any],
    *,
    fl_x: float,
    fl_y: float,
    cx: float,
    cy: float,
    stride: int,
    max_depth_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    image, depth = load_frame_arrays(dataset_root, frame)
    height, width = depth.shape[:2]
    ys = np.arange(0, height, stride)
    xs = np.arange(0, width, stride)
    grid_x, grid_y = np.meshgrid(xs, ys)
    sampled_depth = depth[grid_y, grid_x]
    valid = np.isfinite(sampled_depth) & (sampled_depth > 0.1) & (sampled_depth < max_depth_m)
    if not np.any(valid):
        return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 3), dtype=np.uint8)

    x = (grid_x[valid].astype(np.float32) - cx) / fl_x
    y = -(grid_y[valid].astype(np.float32) - cy) / fl_y
    camera_dirs = normalize(np.stack([x, y, -np.ones_like(x)], axis=1))
    c2w = np.asarray(frame["transform_matrix"], dtype=np.float32)
    rotation = c2w[:3, :3]
    eye = c2w[:3, 3]
    world_dirs = normalize(camera_dirs @ rotation.T)
    points = eye[None, :] + world_dirs * sampled_depth[valid, None]
    colors = image[grid_y[valid], grid_x[valid]]
    return points.astype(np.float32), colors.astype(np.uint8)


def splat_to_target(
    points: np.ndarray,
    colors: np.ndarray,
    target: dict[str, Any],
    *,
    width: int,
    height: int,
    fl_x: float,
    fl_y: float,
    cx: float,
    cy: float,
) -> tuple[np.ndarray, np.ndarray]:
    rendered = np.zeros((height, width, 3), dtype=np.uint8)
    mask = np.zeros((height, width), dtype=bool)
    zbuf = np.full((height, width), np.inf, dtype=np.float32)
    if len(points) == 0:
        return rendered, mask

    c2w = np.asarray(target["transform_matrix"], dtype=np.float32)
    w2c = np.linalg.inv(c2w)
    points_h = np.concatenate([points, np.ones((len(points), 1), dtype=np.float32)], axis=1)
    cam = (points_h @ w2c.T)[:, :3]
    depth = -cam[:, 2]
    valid = depth > 0.1
    if not np.any(valid):
        return rendered, mask

    cam = cam[valid]
    depth = depth[valid]
    colors = colors[valid]
    u = np.rint(fl_x * (cam[:, 0] / depth) + cx).astype(np.int32)
    v = np.rint(cy - fl_y * (cam[:, 1] / depth)).astype(np.int32)
    inside = (u >= 0) & (u < width) & (v >= 0) & (v < height)
    u, v, depth, colors = u[inside], v[inside], depth[inside], colors[inside]

    order = np.argsort(depth)[::-1]
    for idx in order:
        x = int(u[idx])
        y = int(v[idx])
        z = float(depth[idx])
        if z < zbuf[y, x]:
            zbuf[y, x] = z
            rendered[y, x] = colors[idx]
            mask[y, x] = True
    return rendered, mask


def psnr(pred: np.ndarray, target: np.ndarray) -> float:
    mse = float(np.mean((pred.astype(np.float32) - target.astype(np.float32)) ** 2))
    if mse <= 1e-12:
        return 99.0
    return 20.0 * math.log10(255.0 / math.sqrt(mse))


def ssim_luma(pred: np.ndarray, target: np.ndarray) -> float:
    weights = np.asarray([0.299, 0.587, 0.114], dtype=np.float32)
    x = pred.astype(np.float32) @ weights
    y = target.astype(np.float32) @ weights
    mux = float(np.mean(x))
    muy = float(np.mean(y))
    varx = float(np.var(x))
    vary = float(np.var(y))
    cov = float(np.mean((x - mux) * (y - muy)))
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    return ((2 * mux * muy + c1) * (2 * cov + c2)) / ((mux * mux + muy * muy + c1) * (varx + vary + c2))


def masked_metrics(rendered: np.ndarray, target_rgb: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    if not np.any(mask):
        return {
            "filled_pixel_count": 0,
            "fill_ratio": 0.0,
            "PSNR": None,
            "SSIM_luma": None,
            "MAE": None,
        }
    pred = rendered[mask]
    tgt = target_rgb[mask]
    return {
        "filled_pixel_count": int(mask.sum()),
        "fill_ratio": float(mask.mean()),
        "PSNR": float(psnr(pred, tgt)),
        "SSIM_luma": float(ssim_luma(pred, tgt)),
        "MAE": float(np.mean(np.abs(pred.astype(np.float32) - tgt.astype(np.float32)))),
    }


def save_triplet(path: Path, target_rgb: np.ndarray, rendered: np.ndarray, mask: np.ndarray, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    error = np.zeros_like(target_rgb)
    diff = np.abs(rendered.astype(np.int16) - target_rgb.astype(np.int16)).astype(np.uint8)
    error[mask] = diff[mask]
    masked_render = rendered.copy()
    masked_render[~mask] = np.asarray([245, 245, 245], dtype=np.uint8)
    tiles = [
        Image.fromarray(target_rgb).resize((426, 240)),
        Image.fromarray(masked_render).resize((426, 240)),
        Image.fromarray(error).resize((426, 240)),
    ]
    canvas = Image.new("RGB", (1280, 330), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
        small = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    labels = ["held-out UAV view", "depth-splat reconstruction", "masked absolute error"]
    for i, tile in enumerate(tiles):
        x = i * 426
        canvas.paste(tile, (x, 42))
        draw.text((x + 12, 12), labels[i], fill=(17, 24, 39), font=font)
    summary = (
        f"{row['scenario_id']} -> {row['target_uav']} | sources={','.join(row['source_uavs'])} | "
        f"fill={row['fill_ratio']:.3f} PSNR={row['PSNR']:.2f} SSIM={row['SSIM_luma']:.3f}"
    )
    draw.text((12, 292), summary, fill=(55, 65, 81), font=small)
    canvas.save(path)


def save_contact_sheet(path: Path, triplets: list[Path]) -> None:
    images = [Image.open(item).convert("RGB") for item in triplets if item.exists()]
    if not images:
        return
    width = max(image.width for image in images)
    height = sum(image.height for image in images)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for image in images:
        canvas.paste(image, (0, y))
        y += image.height
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def build(args: argparse.Namespace) -> dict[str, Any]:
    dataset_root, transforms = load_dataset(Path(args.dataset_manifest))
    frames = transforms["frames"]
    by_key = {frame_key(frame): frame for frame in frames}
    width = int(transforms["w"])
    height = int(transforms["h"])
    rows: list[dict[str, Any]] = []
    triplets: list[Path] = []
    out_dir = Path(args.out_dir)
    scenarios = sorted({str(frame.get("scenario_id")) for frame in frames})
    for scenario_id in scenarios:
        target = by_key.get((scenario_id, args.target_uav))
        sources = [by_key[(scenario_id, uav)] for uav in args.source_uavs.split(",") if (scenario_id, uav) in by_key]
        if target is None or not sources:
            continue
        point_sets: list[np.ndarray] = []
        color_sets: list[np.ndarray] = []
        for source in sources:
            points, colors = source_points(
                dataset_root,
                source,
                fl_x=float(transforms["fl_x"]),
                fl_y=float(transforms["fl_y"]),
                cx=float(transforms["cx"]),
                cy=float(transforms["cy"]),
                stride=args.stride,
                max_depth_m=args.max_depth_m,
            )
            point_sets.append(points)
            color_sets.append(colors)
        points = np.concatenate(point_sets, axis=0) if point_sets else np.zeros((0, 3), dtype=np.float32)
        colors = np.concatenate(color_sets, axis=0) if color_sets else np.zeros((0, 3), dtype=np.uint8)
        rendered, mask = splat_to_target(
            points,
            colors,
            target,
            width=width,
            height=height,
            fl_x=float(transforms["fl_x"]),
            fl_y=float(transforms["fl_y"]),
            cx=float(transforms["cx"]),
            cy=float(transforms["cy"]),
        )
        target_rgb, _ = load_frame_arrays(dataset_root, target)
        row = {
            "scenario_id": scenario_id,
            "target_uav": args.target_uav,
            "source_uavs": [source.get("uav_id") for source in sources],
            "source_point_count": int(len(points)),
            **masked_metrics(rendered, target_rgb, mask),
        }
        rows.append(row)
        triplet_path = out_dir / f"{scenario_id}_{args.target_uav}_depth_splat_triplet.png"
        save_triplet(triplet_path, target_rgb, rendered, mask, row)
        triplets.append(triplet_path)

    psnr_values = [float(row["PSNR"]) for row in rows if row.get("PSNR") is not None]
    ssim_values = [float(row["SSIM_luma"]) for row in rows if row.get("SSIM_luma") is not None]
    fill_values = [float(row["fill_ratio"]) for row in rows]
    contact_sheet = out_dir / "marinecity_depth_view_consistency_contact_sheet.png"
    save_contact_sheet(contact_sheet, triplets)
    live_contact_sheet = Path(args.live_png)
    live_contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(contact_sheet, live_contact_sheet)
    manifest = {
        "status": "marinecity_depth_view_consistency_sanity_ready" if rows else "marinecity_depth_view_consistency_sanity_empty",
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "dataset_manifest": str(args.dataset_manifest),
        "out_dir": str(out_dir),
        "contact_sheet": str(contact_sheet),
        "live_contact_sheet": str(live_contact_sheet),
        "target_uav": args.target_uav,
        "source_uavs": args.source_uavs.split(","),
        "stride": args.stride,
        "max_depth_m": args.max_depth_m,
        "scenario_count": len(rows),
        "mean_psnr": float(np.mean(psnr_values)) if psnr_values else None,
        "mean_ssim_luma": float(np.mean(ssim_values)) if ssim_values else None,
        "mean_fill_ratio": float(np.mean(fill_values)) if fill_values else 0.0,
        "rows": rows,
        "claiming_rule": (
            "This is a depth-backed cross-view sanity check from real RGB/depth/pose captures. "
            "It is not a neural 3D reconstruction benchmark and must not be reported as NeRF/3DGS performance."
        ),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    write_live(manifest, Path(args.live_json), Path(args.live_md))
    return manifest


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}"


def write_live(manifest: dict[str, Any], live_json: Path, live_md: Path) -> None:
    live_json.parent.mkdir(parents=True, exist_ok=True)
    live_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# MarineCity Depth View-Consistency Sanity",
        "",
        f"Updated: `{manifest['updated_at_kst']}`",
        f"Status: `{manifest['status']}`",
        "",
        f"- Dataset: `{manifest['dataset_manifest']}`",
        f"- Contact sheet: `{manifest['contact_sheet']}`",
        f"- Source UAVs -> target UAV: `{manifest['source_uavs']}` -> `{manifest['target_uav']}`",
        f"- Mean fill ratio: `{fmt(manifest['mean_fill_ratio'])}`",
        f"- Mean PSNR on filled pixels: `{fmt(manifest['mean_psnr'], 2)}`",
        f"- Mean luma SSIM on filled pixels: `{fmt(manifest['mean_ssim_luma'])}`",
        "",
        "| Scenario | Sources | Target | Fill | PSNR | SSIM-luma | MAE |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in manifest["rows"]:
        lines.append(
            f"| {row['scenario_id']} | {','.join(row['source_uavs'])} | {row['target_uav']} | "
            f"{fmt(row['fill_ratio'])} | {fmt(row['PSNR'], 2)} | {fmt(row['SSIM_luma'])} | {fmt(row['MAE'], 2)} |"
        )
    lines.extend(["", f"Claiming rule: {manifest['claiming_rule']}", ""])
    live_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-manifest", default=str(DEFAULT_DATASET))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--live-json", default=str(LIVE_DIR / "marinecity_depth_view_consistency_sanity.json"))
    parser.add_argument("--live-md", default=str(LIVE_DIR / "marinecity_depth_view_consistency_sanity.md"))
    parser.add_argument("--live-png", default=str(LIVE_DIR / "marinecity_depth_view_consistency_sanity.png"))
    parser.add_argument("--source-uavs", default="uav_01,uav_02")
    parser.add_argument("--target-uav", default="uav_03")
    parser.add_argument("--stride", type=int, default=2)
    parser.add_argument("--max-depth-m", type=float, default=600.0)
    args = parser.parse_args()
    print(json.dumps(build(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
