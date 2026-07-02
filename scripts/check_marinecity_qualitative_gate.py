"""Gate MarineCity real-Cesium qualitative figures for paper promotion.

This check deliberately separates three evidence levels:

1. Real-Cesium system smoke evidence.
2. Crop-only supplementary/framing candidates.
3. Full-frame main-paper qualitative figures.

Crop candidates can be useful, but they should not silently satisfy the
full-frame main-paper figure gate.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def to_float(row: dict[str, str], key: str, default: float = 1.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def build_gate(args: argparse.Namespace) -> dict[str, Any]:
    capture_rows = read_csv(REPO_ROOT / args.capture_csv)
    crop_rows = read_csv(REPO_ROOT / args.crop_csv)
    system_manifest = read_json(REPO_ROOT / args.system_manifest)
    session_overlay = read_json(Path(args.session_overlay_status))

    best_capture = capture_rows[0] if capture_rows else {}
    best_crop = crop_rows[0] if crop_rows else {}
    prim_status = session_overlay.get("prim_status", {}) or {}

    best_full_black = to_float(best_capture, "best_black_ratio")
    mean_top3_black = to_float(best_capture, "mean_top3_black_ratio")
    best_crop_black = to_float(best_crop, "black_ratio")
    best_crop_area = to_float(best_crop, "area_ratio", 0.0)

    real_cesium_ok = bool(
        prim_status.get("/Google_Photorealistic_3D_Tiles", {}).get("valid")
        and prim_status.get("/Cesium_World_Terrain", {}).get("valid")
        and session_overlay.get("substitute_city_geometry_created") is False
    )
    smoke_ok = (
        system_manifest.get("status") == "marinecity_system_test_artifacts_complete"
        and int(system_manifest.get("scenario_count", 0) or 0) >= 3
        and int(system_manifest.get("token_level_test_count", 0) or 0) >= args.min_token_tests
    )
    crop_supp_ready = bool(best_crop) and best_crop_black <= args.crop_black_max and best_crop_area >= args.crop_area_min
    full_main_ready = bool(best_capture) and best_full_black <= args.full_black_max and mean_top3_black <= args.mean_top3_black_max

    if real_cesium_ok and smoke_ok and full_main_ready:
        status = "marinecity_qualitative_gate_main_ready"
    elif real_cesium_ok and smoke_ok and crop_supp_ready:
        status = "marinecity_qualitative_gate_smoke_and_supp_ready_main_recapture_pending"
    elif real_cesium_ok and smoke_ok:
        status = "marinecity_qualitative_gate_smoke_ready_visual_recapture_pending"
    else:
        status = "marinecity_qualitative_gate_needs_attention"

    checks = {
        "real_cesium_ok": real_cesium_ok,
        "system_smoke_ok": smoke_ok,
        "crop_supplementary_ready": crop_supp_ready,
        "full_frame_main_ready": full_main_ready,
        "google_tiles_valid": bool(prim_status.get("/Google_Photorealistic_3D_Tiles", {}).get("valid")),
        "terrain_valid": bool(prim_status.get("/Cesium_World_Terrain", {}).get("valid")),
        "fake_or_substitute_city_created": session_overlay.get("substitute_city_geometry_created"),
    }
    thresholds = {
        "full_black_max": args.full_black_max,
        "mean_top3_black_max": args.mean_top3_black_max,
        "crop_black_max": args.crop_black_max,
        "crop_area_min": args.crop_area_min,
        "min_token_tests": args.min_token_tests,
    }
    if full_main_ready:
        next_actions = [
            "Use the current full-frame real-Cesium MarineCity capture as the main-paper qualitative candidate.",
            "Keep the live real-Cesium MarineCity GUI at the user-verified 160 m review view.",
            "Use the reviewed AeroGraph candidate table with a caveat; reserve final reasoning claims for external-provider replication.",
            "Regenerate paper tables and figure manifests after any external-provider/local-model replication pass.",
        ]
    else:
        next_actions = [
            "Keep the live real-Cesium MarineCity GUI at the user-verified 160 m review view.",
            "Recapture S0/S1/S2 full-frame RGB views until best full black/void ratio <= threshold.",
            "Use crop candidates only as supplementary/framing evidence unless the caption explicitly says crop-only.",
            "Regenerate capture quality, crop candidates, qualitative selection, and this gate after recapture.",
        ]

    report = {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "checks": checks,
        "thresholds": thresholds,
        "best_full_capture": {
            "capture_name": best_capture.get("capture_name"),
            "best_image": best_capture.get("best_image"),
            "best_black_ratio": best_full_black if best_capture else None,
            "mean_top3_black_ratio": mean_top3_black if best_capture else None,
            "camera_profile": best_capture.get("camera_profile"),
        },
        "best_crop_candidate": {
            "capture_name": best_crop.get("capture_name"),
            "source": best_crop.get("source"),
            "crop_path": best_crop.get("crop_path"),
            "black_ratio": best_crop_black if best_crop else None,
            "area_ratio": best_crop_area if best_crop else None,
            "score": to_float(best_crop, "score", 0.0) if best_crop else None,
        },
        "system_manifest": {
            "path": args.system_manifest,
            "status": system_manifest.get("status"),
            "scenario_count": system_manifest.get("scenario_count"),
            "token_level_test_count": system_manifest.get("token_level_test_count"),
        },
        "claiming_rule": (
            "Main paper full-frame qualitative figure may be promoted."
            if full_main_ready
            else "Keep current MarineCity visual evidence as smoke/protocol or supplementary framing evidence; recapture a cleaner full-frame real-Cesium view before main-paper qualitative promotion."
        ),
        "next_actions": next_actions,
    }
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    checks = report["checks"]
    thresholds = report["thresholds"]
    full = report["best_full_capture"]
    crop = report["best_crop_candidate"]
    system = report["system_manifest"]
    lines = [
        "# MarineCity Qualitative Gate",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        "",
        "## Gate Checks",
        "",
        "| Check | Value |",
        "| --- | --- |",
    ]
    for key, value in checks.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Thresholds",
            "",
            "| Metric | Threshold |",
            "| --- | ---: |",
        ]
    )
    for key, value in thresholds.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Current Best Full-Frame Candidate",
            "",
            f"- Capture: `{full.get('capture_name')}`",
            f"- Image: `{full.get('best_image')}`",
            f"- Best black/void ratio: `{full.get('best_black_ratio')}`",
            f"- Mean top-3 black/void ratio: `{full.get('mean_top3_black_ratio')}`",
            f"- Camera profile: `{full.get('camera_profile')}`",
            "",
            "## Current Best Crop Candidate",
            "",
            f"- Capture: `{crop.get('capture_name')}`",
            f"- Source: `{crop.get('source')}`",
            f"- Crop path: `{crop.get('crop_path')}`",
            f"- Black/void ratio: `{crop.get('black_ratio')}`",
            f"- Area ratio: `{crop.get('area_ratio')}`",
            f"- Score: `{crop.get('score')}`",
            "",
            "## System Smoke Evidence",
            "",
            f"- Manifest: `{system.get('path')}`",
            f"- Status: `{system.get('status')}`",
            f"- Scenarios: `{system.get('scenario_count')}`",
            f"- Token-level tests: `{system.get('token_level_test_count')}`",
            "",
            "## Claiming Rule",
            "",
            report["claiming_rule"],
            "",
            "## Next Actions",
            "",
        ]
    )
    for item in report["next_actions"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-csv", default="paper/figures/results/marinecity_system/marinecity_capture_quality_rank.csv")
    parser.add_argument("--crop-csv", default="paper/figures/results/marinecity_system/marinecity_real_capture_crop_candidates.csv")
    parser.add_argument("--system-manifest", default="outputs/reports/live/marinecity_system_test_10plus/manifest.json")
    parser.add_argument("--session-overlay-status", default="/home/oem/UAV/uav_marinecity/outputs/uavmarine_session_overlay_status_s0.json")
    parser.add_argument("--out-json", default="outputs/reports/live/marinecity_qualitative_gate.json")
    parser.add_argument("--out-md", default="outputs/reports/live/marinecity_qualitative_gate.md")
    parser.add_argument(
        "--paper-md",
        default="",
        help="Optional extra Markdown copy. Leave empty so paper/ stays publication-asset clean.",
    )
    parser.add_argument("--full-black-max", type=float, default=0.10)
    parser.add_argument("--mean-top3-black-max", type=float, default=0.15)
    parser.add_argument("--crop-black-max", type=float, default=0.02)
    parser.add_argument("--crop-area-min", type=float, default=0.35)
    parser.add_argument("--min-token-tests", type=int, default=10)
    args = parser.parse_args()

    report = build_gate(args)
    out_json = REPO_ROOT / args.out_json
    out_md = REPO_ROOT / args.out_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(out_md, report)
    payload = {"json": rel(out_json), "markdown": rel(out_md), "status": report["status"]}
    if args.paper_md:
        paper_md = REPO_ROOT / args.paper_md
        write_markdown(paper_md, report)
        payload["paper_markdown"] = rel(paper_md)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
