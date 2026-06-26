"""Export verified MarineCity captures into a neural-3D dataset package.

The exporter consumes ``outputs/experiments/marinecity_real_capture_benchmark.json``
and writes a NeRF/Instant-NGP/Nerfstudio-style ``transforms.json`` package with
copied RGB images, optional depth arrays, and split manifests. It does not train
or fabricate a 3D model; it prepares the real-Cesium capture source for upstream
NeRF/3DGS runners.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = REPO_ROOT / "outputs/experiments/marinecity_real_capture_benchmark.json"
DEFAULT_OUT = REPO_ROOT / "outputs/experiments/3d_generation/marinecity_real_capture_neural3d"
LIVE_DIR = REPO_ROOT / "outputs/reports/live"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(vec: list[float], fallback: list[float]) -> list[float]:
    length = math.sqrt(sum(value * value for value in vec))
    if length < 1e-9:
        return list(fallback)
    return [value / length for value in vec]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def look_at_c2w(eye: list[float], target: list[float]) -> list[list[float]]:
    """Return an approximate camera-to-world matrix for NeRF-style metadata."""

    forward = normalize([target[i] - eye[i] for i in range(3)], [0.0, 0.0, -1.0])
    world_up = [0.0, 0.0, 1.0]
    right = normalize(cross(forward, world_up), [1.0, 0.0, 0.0])
    up = normalize(cross(right, forward), [0.0, 1.0, 0.0])
    # NeRF/Blender convention stores camera x=right, y=up, z=backward.
    backward = [-value for value in forward]
    return [
        [right[0], up[0], backward[0], eye[0]],
        [right[1], up[1], backward[1], eye[1]],
        [right[2], up[2], backward[2], eye[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def focal_from_hfov(width: int, hfov_deg: float) -> float:
    return 0.5 * width / math.tan(math.radians(hfov_deg) / 2.0)


def rel_for_json(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def split_name(frame: dict[str, Any]) -> str:
    # Keep UAV-03 as held-out cross-view validation/test evidence; train on the
    # two lower-altitude views from each scenario.
    return "test" if str(frame.get("uav_id")) == "uav_03" else "train"


def copy_file(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def make_frame_payload(
    frame: dict[str, Any],
    *,
    out_root: Path,
    images_dir: Path,
    depths_dir: Path,
) -> dict[str, Any]:
    scenario_id = str(frame.get("scenario_id", "unknown_scenario"))
    frame_id = str(frame.get("frame_id", Path(str(frame.get("rgb_path", "frame"))).stem))
    uav_id = str(frame.get("uav_id", "uav_unknown"))
    stem = f"{scenario_id}_{frame_id}_{uav_id}".replace("/", "_")
    rgb_src = Path(str(frame.get("rgb_path", "")))
    depth_src = Path(str(frame.get("depth_path", "")))
    image_dst = images_dir / f"{stem}.png"
    depth_dst = depths_dir / f"{stem}.npy"
    image_ok = copy_file(rgb_src, image_dst)
    depth_ok = copy_file(depth_src, depth_dst)
    eye = [float(v) for v in frame.get("camera_position", [])]
    target = [float(v) for v in frame.get("look_at_target", [])]
    transform_matrix = look_at_c2w(eye, target) if len(eye) == 3 and len(target) == 3 else []
    payload = {
        "file_path": rel_for_json(image_dst, out_root),
        "depth_file_path": rel_for_json(depth_dst, out_root) if depth_ok else "",
        "transform_matrix": transform_matrix,
        "scenario_id": scenario_id,
        "frame_id": frame_id,
        "uav_id": uav_id,
        "camera_prim": frame.get("camera_prim", ""),
        "camera_position": frame.get("camera_position", []),
        "look_at_target": frame.get("look_at_target", []),
        "altitude_m": frame.get("altitude_m"),
        "rgb_black_ratio": frame.get("rgb_black_ratio"),
        "depth_finite_ratio": frame.get("depth_finite_ratio"),
        "depth_median_m": frame.get("depth_median_m"),
        "split": split_name(frame),
        "source_rgb_path": str(rgb_src),
        "source_depth_path": str(depth_src),
        "copied_rgb": image_ok,
        "copied_depth": depth_ok,
    }
    return payload


def transforms_payload(
    frames: list[dict[str, Any]],
    *,
    width: int,
    height: int,
    hfov_deg: float,
    note: str,
) -> dict[str, Any]:
    fl_x = focal_from_hfov(width, hfov_deg)
    return {
        "camera_model": "OPENCV",
        "w": width,
        "h": height,
        "fl_x": fl_x,
        "fl_y": fl_x,
        "cx": width / 2.0,
        "cy": height / 2.0,
        "camera_angle_x": math.radians(hfov_deg),
        "aabb_scale": 16,
        "frames": frames,
        "com3d_note": note,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def export_dataset(args: argparse.Namespace) -> dict[str, Any]:
    benchmark_path = Path(args.benchmark)
    benchmark = read_json(benchmark_path)
    frames = benchmark.get("frames", [])
    if not frames:
        raise SystemExit(f"No frames found in benchmark: {benchmark_path}")
    out_root = Path(args.out)
    images_dir = out_root / "images"
    depths_dir = out_root / "depths"
    frame_payloads = [
        make_frame_payload(frame, out_root=out_root, images_dir=images_dir, depths_dir=depths_dir)
        for frame in frames
    ]
    image_sizes = [frame.get("image_size", []) for frame in frames if frame.get("image_size")]
    width = int(image_sizes[0][0]) if image_sizes else int(args.width)
    height = int(image_sizes[0][1]) if image_sizes else int(args.height)
    note = (
        "Generated from verified real-Cesium MarineCity RGB/depth/pose captures. "
        "Camera transforms are metadata-derived look-at matrices for upstream 3D runner handoff; "
        "this package is not itself a completed neural reconstruction result."
    )
    all_payload = transforms_payload(frame_payloads, width=width, height=height, hfov_deg=args.hfov_deg, note=note)
    train_frames = [frame for frame in frame_payloads if frame["split"] == "train"]
    test_frames = [frame for frame in frame_payloads if frame["split"] == "test"]
    write_json(out_root / "transforms.json", all_payload)
    write_json(
        out_root / "transforms_train.json",
        transforms_payload(train_frames, width=width, height=height, hfov_deg=args.hfov_deg, note=note),
    )
    write_json(
        out_root / "transforms_val.json",
        transforms_payload(test_frames, width=width, height=height, hfov_deg=args.hfov_deg, note=note),
    )
    write_json(
        out_root / "transforms_test.json",
        transforms_payload(test_frames, width=width, height=height, hfov_deg=args.hfov_deg, note=note),
    )
    summary = benchmark.get("summary", {}) or {}
    copied_rgb = sum(1 for frame in frame_payloads if frame["copied_rgb"])
    copied_depth = sum(1 for frame in frame_payloads if frame["copied_depth"])
    manifest = {
        "status": "marinecity_neural3d_dataset_export_ready",
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "benchmark": str(benchmark_path),
        "out_dir": str(out_root),
        "transforms": str(out_root / "transforms.json"),
        "transforms_train": str(out_root / "transforms_train.json"),
        "transforms_val": str(out_root / "transforms_val.json"),
        "transforms_test": str(out_root / "transforms_test.json"),
        "frame_count": len(frame_payloads),
        "train_frame_count": len(train_frames),
        "heldout_frame_count": len(test_frames),
        "copied_rgb_count": copied_rgb,
        "copied_depth_count": copied_depth,
        "scenario_count": summary.get("scenario_count"),
        "uav_count": summary.get("uav_count"),
        "altitude_range_m": summary.get("altitude_range_m"),
        "mean_rgb_black_ratio": summary.get("mean_rgb_black_ratio"),
        "mean_depth_finite_ratio": summary.get("mean_depth_finite_ratio"),
        "hfov_deg": args.hfov_deg,
        "image_size": [width, height],
        "split_rule": "train=uav_01/uav_02 views for each scenario; heldout val/test=uav_03 views",
        "claiming_rule": (
            "This package is a neural-3D input handoff. It upgrades source readiness, "
            "but it is not a NeRF/3DGS metric result."
        ),
        "runner_commands": [
            f"ns-train nerfacto --data {out_root}",
            f"python -m generative3d.external_runner --method instant_ngp --scene marinecity_real_capture --data {out_root}",
            f"python -m generative3d.external_runner --method gaussian_splatting --scene marinecity_real_capture --data {out_root}",
        ],
    }
    write_json(out_root / "dataset_manifest.json", manifest)
    return manifest


def write_live_report(manifest: dict[str, Any], path: Path) -> None:
    lines = [
        "# MarineCity Neural-3D Dataset Export",
        "",
        f"Updated: `{manifest['updated_at_kst']}`",
        f"Status: `{manifest['status']}`",
        "",
        "## Dataset",
        "",
        f"- Output directory: `{manifest['out_dir']}`",
        f"- Transforms: `{manifest['transforms']}`",
        f"- Frames/train/heldout: `{manifest['frame_count']}` / `{manifest['train_frame_count']}` / `{manifest['heldout_frame_count']}`",
        f"- Copied RGB/depth: `{manifest['copied_rgb_count']}` / `{manifest['copied_depth_count']}`",
        f"- Scenarios/UAVs: `{manifest['scenario_count']}` / `{manifest['uav_count']}`",
        f"- UAV altitude range: `{manifest['altitude_range_m']}` m",
        f"- Image size/HFOV: `{manifest['image_size']}` / `{manifest['hfov_deg']}` deg",
        f"- Split rule: {manifest['split_rule']}",
        "",
        "## Runner Handoff",
        "",
    ]
    for command in manifest["runner_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", f"Claiming rule: {manifest['claiming_rule']}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--hfov-deg", type=float, default=55.0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--live-md", default=str(LIVE_DIR / "marinecity_neural3d_dataset_export.md"))
    parser.add_argument("--live-json", default=str(LIVE_DIR / "marinecity_neural3d_dataset_export.json"))
    args = parser.parse_args()
    manifest = export_dataset(args)
    write_live_report(manifest, Path(args.live_md))
    write_json(Path(args.live_json), manifest)
    print(json.dumps({"manifest": manifest["out_dir"] + "/dataset_manifest.json", "status": manifest["status"]}, indent=2))


if __name__ == "__main__":
    main()
