"""Generate a visible smoke sample for EvidenceToken preview workflow.

This does not train a model and does not require raw datasets. It creates small
SVG UAV-view scenes, matching EvidenceToken JSONL, and an HTML preview so the
visual inspection workflow can be checked end to end.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence import EvidenceToken, save_tokens_jsonl
from evidence.uncertainty import uncertainty_score
from evidence.visualization import render_preview_from_jsonl


@dataclass(slots=True)
class SmokeSampleOutput:
    out_dir: Path
    image_dir: Path
    tokens_jsonl: Path
    preview_html: Path
    summary_csv: Path


def _svg_rect(x: float, y: float, w: float, h: float, fill: str, label: str) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" stroke="#0f172a" stroke-width="2"/>',
            f'<text x="{x + 4}" y="{max(14, y - 6)}" font-size="12" fill="#e2e8f0">{label}</text>',
        ]
    )


def _write_svg_scene(path: Path, title: str, objects: list[dict[str, object]], *, width: int = 640, height: int = 480) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    object_markup = []
    for obj in objects:
        x, y, w, h = obj["bbox"]
        object_markup.append(_svg_rect(float(x), float(y), float(w), float(h), str(obj["color"]), str(obj["label"])))
    path.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                '<rect width="100%" height="100%" fill="#111827"/>',
                '<rect x="0" y="300" width="640" height="180" fill="#1e293b"/>',
                '<rect x="30" y="70" width="120" height="220" fill="#334155"/>',
                '<rect x="190" y="40" width="90" height="250" fill="#475569"/>',
                '<rect x="430" y="80" width="140" height="210" fill="#334155"/>',
                '<path d="M0 360 C120 330 220 390 340 350 C450 315 520 340 640 315 L640 480 L0 480 Z" fill="#0369a1" opacity="0.7"/>',
                f'<text x="22" y="32" font-size="20" font-weight="700" fill="#f8fafc">{title}</text>',
                *object_markup,
                "</svg>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _make_token(
    *,
    token_id: str,
    image_id: str,
    uav_id: str,
    image_path: Path,
    bbox: list[float],
    logits: list[float],
    confidence: float,
    class_id: int,
    class_name: str,
    center_3d: list[float],
    visibility_score: float,
) -> EvidenceToken:
    return EvidenceToken(
        token_id=token_id,
        image_id=image_id,
        uav_id=uav_id,
        timestamp=0.0,
        bbox_2d=bbox,
        class_logits=logits,
        confidence=confidence,
        uncertainty=uncertainty_score(logits),
        crop_feature=[round(v, 3) for v in logits],
        resolution_level="smoke",
        uav_pose=[0.0, 0.0, 80.0],
        depth_value=80.0,
        class_id=class_id,
        metadata={
            "image_path": str(image_path.resolve()),
            "class_name": class_name,
            "center_3d": center_3d,
            "visibility_score": visibility_score,
        },
    )


def create_visible_smoke_sample(out_dir: str | Path = "outputs/smoke/visible_sample") -> SmokeSampleOutput:
    """Create SVG images, EvidenceToken JSONL, and preview HTML."""

    out_dir = Path(out_dir)
    image_dir = out_dir / "images"
    preview_dir = out_dir / "preview"
    tokens_jsonl = out_dir / "tokens.jsonl"

    scenes = {
        "scene001_uav01_t000": [
            {"bbox": [100.0, 120.0, 54.0, 28.0], "color": "#22c55e", "label": "van"},
            {"bbox": [420.0, 300.0, 24.0, 18.0], "color": "#f97316", "label": "tiny_boat"},
        ],
        "scene001_uav02_t000": [
            {"bbox": [132.0, 122.0, 48.0, 26.0], "color": "#22c55e", "label": "van"},
            {"bbox": [438.0, 286.0, 34.0, 22.0], "color": "#f97316", "label": "tiny_boat"},
        ],
        "scene001_uav03_t000": [
            {"bbox": [390.0, 270.0, 18.0, 13.0], "color": "#f97316", "label": "ambiguous"},
        ],
    }

    image_paths: dict[str, Path] = {}
    for image_id, objects in scenes.items():
        image_path = image_dir / f"{image_id}.svg"
        _write_svg_scene(image_path, image_id, objects)
        image_paths[image_id] = image_path

    tokens = [
        _make_token(
            token_id="scene001_uav01_obj001",
            image_id="scene001_uav01_t000",
            uav_id="uav_01",
            image_path=image_paths["scene001_uav01_t000"],
            bbox=[100.0, 120.0, 54.0, 28.0],
            logits=[2.7, 1.0, 0.2],
            confidence=0.78,
            class_id=1,
            class_name="van",
            center_3d=[0.0, 0.0, 0.0],
            visibility_score=0.75,
        ),
        _make_token(
            token_id="scene001_uav02_obj001",
            image_id="scene001_uav02_t000",
            uav_id="uav_02",
            image_path=image_paths["scene001_uav02_t000"],
            bbox=[132.0, 122.0, 48.0, 26.0],
            logits=[2.5, 1.2, 0.2],
            confidence=0.74,
            class_id=1,
            class_name="van",
            center_3d=[0.2, 0.0, 0.1],
            visibility_score=0.68,
        ),
        _make_token(
            token_id="scene001_uav03_obj002",
            image_id="scene001_uav03_t000",
            uav_id="uav_03",
            image_path=image_paths["scene001_uav03_t000"],
            bbox=[390.0, 270.0, 18.0, 13.0],
            logits=[1.1, 1.0, 1.0],
            confidence=0.39,
            class_id=2,
            class_name="ambiguous_small_object",
            center_3d=[18.0, 4.0, 0.0],
            visibility_score=0.30,
        ),
    ]

    save_tokens_jsonl(tokens, tokens_jsonl)
    preview = render_preview_from_jsonl(tokens_jsonl, preview_dir)
    manifest = {
        "out_dir": str(out_dir),
        "image_dir": str(image_dir),
        "tokens_jsonl": str(tokens_jsonl),
        "preview_html": str(preview.index_html),
        "summary_csv": str(preview.summary_csv),
        "token_count": preview.token_count,
        "image_count": preview.image_count,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return SmokeSampleOutput(
        out_dir=out_dir,
        image_dir=image_dir,
        tokens_jsonl=tokens_jsonl,
        preview_html=preview.index_html,
        summary_csv=preview.summary_csv,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a visible CoM3D-ACE smoke sample.")
    parser.add_argument("--out-dir", default="outputs/smoke/visible_sample")
    args = parser.parse_args()

    result = create_visible_smoke_sample(args.out_dir)
    print(json.dumps({key: str(value) for key, value in asdict(result).items()}, indent=2))


if __name__ == "__main__":
    main()
