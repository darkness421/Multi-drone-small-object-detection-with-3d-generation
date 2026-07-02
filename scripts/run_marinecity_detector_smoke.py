"""Run the selected 2D detector on MarineCity multi-UAV Isaac captures."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from detectors.wrappers import UltralyticsWrapper
from evidence import EvidenceToken, save_tokens_jsonl


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def view_metadata(capture_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(view["uav_id"]): view for view in capture_plan.get("views", [])}


def draw_preview(image_path: Path, tokens: list[EvidenceToken], out_path: Path) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    palette = ["#22C55E", "#2563EB", "#F97316", "#DC2626", "#7C3AED", "#0891B2"]
    for idx, token in enumerate(tokens):
        x, y, w, h = token.bbox_2d
        color = palette[idx % len(palette)]
        draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
        label = str(token.metadata.get("class_name", token.class_id))
        text = f"{label} {token.confidence:.2f}"
        draw.rectangle([x, max(0, y - 18), x + max(80, len(text) * 8), y], fill=color)
        draw.text((x + 3, max(0, y - 17)), text, fill="white", font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate EvidenceTokens from Isaac MarineCity UAV RGB captures.")
    parser.add_argument("--summary", default="outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct_capture_summary.json")
    parser.add_argument("--capture-plan", default="outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/capture_plan.json")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--out-dir", default="outputs/evidence/marinecity_detector_smoke")
    parser.add_argument("--device", default="1")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    summary_path = Path(args.summary)
    capture_plan_path = Path(args.capture_plan)
    out_dir = Path(args.out_dir)
    summary = load_json(summary_path)
    capture_plan = load_json(capture_plan_path)
    metadata_by_uav = view_metadata(capture_plan)
    capture_root = summary_path.parent

    wrapper = UltralyticsWrapper(
        args.weights,
        predict_kwargs={"device": args.device, "imgsz": args.imgsz, "conf": args.conf},
    )

    all_tokens: list[EvidenceToken] = []
    by_uav: dict[str, int] = {}
    by_class: Counter[str] = Counter()
    preview_dir = out_dir / "previews"
    crop_dir = out_dir / "crops"

    for frame in summary.get("frames", []):
        uav_id = str(frame.get("uav_id", "uav_unknown"))
        image_path = capture_root / str(frame["rgb_path"])
        view = metadata_by_uav.get(uav_id, {})
        metadata = {
            "image_id": image_path.stem,
            "uav_id": uav_id,
            "timestamp": view.get("timestamp", 0.0),
            "camera_intrinsic": view.get("camera_intrinsic", []),
            "camera_extrinsic": view.get("camera_extrinsic", []),
            "uav_pose": list(view.get("uav_pose", {}).values()) if isinstance(view.get("uav_pose"), dict) else view.get("uav_pose", []),
            "depth_path": str(capture_root / str(frame.get("depth_npy_path", ""))) if frame.get("depth_npy_path") else None,
            "camera_pose_path": str(capture_root / str(view.get("pose_path", ""))) if view.get("pose_path") else None,
        }
        tokens = wrapper.predict(image_path, metadata, crop_dir=crop_dir / uav_id)
        all_tokens.extend(tokens)
        by_uav[uav_id] = len(tokens)
        for token in tokens:
            by_class[str(token.metadata.get("class_name", token.class_id))] += 1
        draw_preview(image_path, tokens, preview_dir / f"{image_path.stem}_pred.png")

    out_jsonl = out_dir / "evidence_tokens.jsonl"
    save_tokens_jsonl(all_tokens, out_jsonl)
    smoke_summary = {
        "status": "detector_smoke_complete",
        "weights": str(Path(args.weights).resolve()),
        "summary": str(summary_path.resolve()),
        "capture_plan": str(capture_plan_path.resolve()),
        "out_jsonl": str(out_jsonl.resolve()),
        "preview_dir": str(preview_dir.resolve()),
        "device": args.device,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "uav_count": len(by_uav),
        "token_count": len(all_tokens),
        "tokens_by_uav": by_uav,
        "tokens_by_class": dict(by_class),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "detector_smoke_summary.json").write_text(json.dumps(smoke_summary, indent=2), encoding="utf-8")
    print(json.dumps(smoke_summary, indent=2))


if __name__ == "__main__":
    main()
