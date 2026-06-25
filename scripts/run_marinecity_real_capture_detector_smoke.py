"""Run the selected detector on verified real-Cesium MarineCity captures.

This runner consumes ``outputs/experiments/marinecity_real_capture_benchmark.json``
directly. It does not open, modify, or save the Isaac/Cesium USD stage; it only
uses already exported RGB/depth/pose evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from detectors.wrappers import UltralyticsWrapper
from evidence import EvidenceToken, save_tokens_jsonl


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _class_name(token: EvidenceToken) -> str:
    return str(token.metadata.get("class_name", token.class_id if token.class_id is not None else "unknown"))


def _draw_preview(image_path: Path, tokens: list[EvidenceToken], out_path: Path) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    palette = ["#22C55E", "#2563EB", "#F97316", "#DC2626", "#7C3AED", "#0891B2", "#EAB308"]
    for idx, token in enumerate(tokens):
        x, y, w, h = token.bbox_2d
        color = palette[idx % len(palette)]
        x2 = x + w
        y2 = y + h
        draw.rectangle([x, y, x2, y2], outline=color, width=2)
        text = f"{_class_name(token)} {token.confidence:.2f}"
        tw = max(80, len(text) * 8)
        draw.rectangle([x, max(0, y - 18), x + tw, y], fill=color)
        draw.text((x + 3, max(0, y - 17)), text, fill="white", font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def _contact_sheet(
    paths: list[Path],
    out_path: Path,
    *,
    labels: list[str] | None = None,
    cols: int = 3,
    thumb_width: int = 520,
) -> None:
    if not paths:
        return
    thumbs: list[Image.Image] = []
    for path in paths:
        img = Image.open(path).convert("RGB")
        ratio = thumb_width / img.width
        thumb = img.resize((thumb_width, int(img.height * ratio)))
        thumbs.append(thumb)
    rows = (len(thumbs) + cols - 1) // cols
    pad = 18
    label_h = 26
    cell_h = max(img.height for img in thumbs) + label_h
    sheet = Image.new("RGB", (cols * thumb_width + (cols + 1) * pad, rows * cell_h + (rows + 1) * pad), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    labels = labels or [path.stem for path in paths]
    for idx, (path, img) in enumerate(zip(paths, thumbs)):
        row, col = divmod(idx, cols)
        x = pad + col * (thumb_width + pad)
        y = pad + row * (cell_h + pad)
        draw.text((x, y), labels[idx], fill="#111827", font=font)
        sheet.paste(img, (x, y + label_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def run(args: argparse.Namespace) -> dict[str, Any]:
    benchmark = _read_json(args.benchmark)
    frames = benchmark.get("frames", [])
    if args.scenario:
        frames = [frame for frame in frames if str(frame.get("scenario_id")) == args.scenario]
    if args.limit:
        frames = frames[: args.limit]

    out_dir = Path(args.out_dir)
    preview_dir = out_dir / "previews"
    crop_dir = out_dir / "crops"
    out_dir.mkdir(parents=True, exist_ok=True)

    wrapper = UltralyticsWrapper(
        args.weights,
        predict_kwargs={"device": args.device, "imgsz": args.imgsz, "conf": args.conf},
    )

    all_tokens: list[EvidenceToken] = []
    tokens_by_scenario_payload: defaultdict[str, list[EvidenceToken]] = defaultdict(list)
    preview_paths: list[Path] = []
    preview_labels: list[str] = []
    by_scenario: defaultdict[str, int] = defaultdict(int)
    by_uav: defaultdict[str, int] = defaultdict(int)
    by_class: Counter[str] = Counter()
    frame_rows: list[dict[str, Any]] = []

    for frame in frames:
        image_path = Path(str(frame["rgb_path"]))
        scenario_id = str(frame.get("scenario_id", "unknown_scenario"))
        uav_id = str(frame.get("uav_id", "uav_unknown"))
        metadata = {
            "image_id": str(frame.get("frame_id", image_path.stem)),
            "uav_id": uav_id,
            "timestamp": float(frame.get("timestamp", 0.0) or 0.0),
            "uav_pose": frame.get("camera_position", []),
            "depth_path": str(frame.get("depth_path", "")) or None,
            "camera_pose_path": str(frame.get("camera_prim", "")) or None,
            "num_classes": args.num_classes,
        }
        tokens = wrapper.predict(image_path, metadata, crop_dir=crop_dir / scenario_id / uav_id)
        for idx, token in enumerate(tokens):
            token.depth_value = frame.get("depth_median_m")
            token.object_id = f"{scenario_id}:{uav_id}:{_class_name(token)}:{idx:03d}"
            token.metadata.update(
                {
                    "scenario_id": scenario_id,
                    "frame_id": frame.get("frame_id", image_path.stem),
                    "camera_prim": frame.get("camera_prim"),
                    "camera_position": frame.get("camera_position", []),
                    "look_at_target": frame.get("look_at_target", []),
                    "altitude_m": frame.get("altitude_m"),
                    "rgb_black_ratio": frame.get("rgb_black_ratio"),
                    "depth_finite_ratio": frame.get("depth_finite_ratio"),
                    "source": "real_cesium_marinecity_capture",
                }
            )
            by_class[_class_name(token)] += 1
            tokens_by_scenario_payload[scenario_id].append(token)
        all_tokens.extend(tokens)
        by_scenario[scenario_id] += len(tokens)
        by_uav[uav_id] += len(tokens)
        preview_path = preview_dir / scenario_id / f"{image_path.stem}_pred.png"
        _draw_preview(image_path, tokens, preview_path)
        preview_paths.append(preview_path)
        scenario_short = scenario_id.replace("uavmarine_", "").replace("_viewer160_session_recapture", "")
        preview_labels.append(f"{scenario_short} | {uav_id} | {frame.get('frame_id', image_path.stem)}")
        frame_rows.append(
            {
                "scenario_id": scenario_id,
                "frame_id": frame.get("frame_id", image_path.stem),
                "uav_id": uav_id,
                "rgb_path": str(image_path),
                "altitude_m": frame.get("altitude_m"),
                "token_count": len(tokens),
                "rgb_black_ratio": frame.get("rgb_black_ratio"),
                "depth_finite_ratio": frame.get("depth_finite_ratio"),
            }
        )

    out_jsonl = out_dir / "evidence_tokens.jsonl"
    save_tokens_jsonl(all_tokens, out_jsonl)
    scenario_jsonl_paths: dict[str, str] = {}
    for scenario_id, scenario_tokens in sorted(tokens_by_scenario_payload.items()):
        scenario_path = out_dir / f"evidence_tokens_{scenario_id}.jsonl"
        save_tokens_jsonl(scenario_tokens, scenario_path)
        scenario_jsonl_paths[scenario_id] = str(scenario_path.resolve())

    with (out_dir / "frame_token_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "frame_id",
                "uav_id",
                "rgb_path",
                "altitude_m",
                "token_count",
                "rgb_black_ratio",
                "depth_finite_ratio",
            ],
        )
        writer.writeheader()
        writer.writerows(frame_rows)

    contact_path = out_dir / "marinecity_detector_preview_contact_sheet.png"
    _contact_sheet(preview_paths, contact_path, labels=preview_labels)

    summary = {
        "status": "marinecity_real_capture_detector_smoke_complete",
        "benchmark": str(Path(args.benchmark).resolve()),
        "weights": str(Path(args.weights).resolve()),
        "out_jsonl": str(out_jsonl.resolve()),
        "scenario_jsonl": scenario_jsonl_paths,
        "preview_contact_sheet": str(contact_path.resolve()),
        "device": args.device,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "frame_count": len(frames),
        "token_count": len(all_tokens),
        "tokens_by_scenario": dict(sorted(by_scenario.items())),
        "tokens_by_uav": dict(sorted(by_uav.items())),
        "tokens_by_class": dict(by_class.most_common()),
    }
    (out_dir / "detector_smoke_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "detector_smoke_summary.md").write_text(
        "\n".join(
            [
                "# MarineCity Real-Cesium Detector Smoke",
                "",
                f"- Status: `{summary['status']}`",
                f"- Frames: `{summary['frame_count']}`",
                f"- Tokens: `{summary['token_count']}`",
                f"- Weights: `{summary['weights']}`",
                f"- Contact sheet: `{summary['preview_contact_sheet']}`",
                f"- Tokens by scenario: `{summary['tokens_by_scenario']}`",
                f"- Tokens by UAV: `{summary['tokens_by_uav']}`",
                f"- Tokens by class: `{summary['tokens_by_class']}`",
                "",
                "This is a system smoke test on verified real Cesium MarineCity captures, not a labeled benchmark score.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run detector on verified real-Cesium MarineCity captures.")
    parser.add_argument("--benchmark", default="outputs/experiments/marinecity_real_capture_benchmark.json")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--out-dir", default="outputs/evidence/marinecity_real_capture_detector_smoke")
    parser.add_argument("--device", default="0")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--conf", type=float, default=0.15)
    parser.add_argument("--num-classes", type=int, default=10)
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
