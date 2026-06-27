"""Collect Fig. 1/Fig. 3 simulation evidence assets for figure revision."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUT_DIR = Path("outputs/reports/live/fig1_fig3_handoff")


@dataclass(frozen=True)
class Asset:
    label: str
    source: Path
    target: str
    figure: str
    note: str


ASSETS = [
    Asset(
        "Real-Cesium capture contact sheet",
        Path("outputs/reports/live/marinecity_real_capture_benchmark_contact_sheet.png"),
        "fig1_map_multiuav_preview.png",
        "Fig. 1",
        "Use as the real MarineCity multi-UAV observation/map panel. Shows 3 scenarios x 3 UAV captures at 140-160 m.",
    ),
    Asset(
        "Three-scenario system panel",
        Path("outputs/reports/live/marinecity_system_test_10plus/contact_sheet_3_scenarios.png"),
        "fig1_fig3_three_scenario_system_panel.png",
        "Fig. 1/Fig. 3",
        "Compact system-level visual summary for locked ROI, adjacent overlap, and coastline multi-view scenarios.",
    ),
    Asset(
        "UAV 1 RGB view",
        Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_001_uav_01_rgb.png"),
        "fig1_uav01_rgb.png",
        "Fig. 1",
        "Raw UAV view for the multi-UAV observations column.",
    ),
    Asset(
        "UAV 2 RGB view",
        Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_002_uav_02_rgb.png"),
        "fig1_uav02_rgb.png",
        "Fig. 1",
        "Raw UAV view for the multi-UAV observations column.",
    ),
    Asset(
        "UAV 3 RGB view",
        Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports/uavmarine_s2_viewer160_session_recapture/real_cesium_capture/frame_003_uav_03_rgb.png"),
        "fig1_uav03_rgb.png",
        "Fig. 1",
        "Raw UAV view for the multi-UAV observations column.",
    ),
    Asset(
        "UAV 1 Isaac bbox preview",
        Path("outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_001_uav_01_bbox_preview.png"),
        "fig1_uav01_isaac_bbox.png",
        "Fig. 1",
        "Ground-truth-like Isaac object layout/bbox preview.",
    ),
    Asset(
        "UAV 2 Isaac bbox preview",
        Path("outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_002_uav_02_bbox_preview.png"),
        "fig1_uav02_isaac_bbox.png",
        "Fig. 1",
        "Ground-truth-like Isaac object layout/bbox preview.",
    ),
    Asset(
        "UAV 3 Isaac bbox preview",
        Path("outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct/frame_003_uav_03_bbox_preview.png"),
        "fig1_uav03_isaac_bbox.png",
        "Fig. 1",
        "Ground-truth-like Isaac object layout/bbox preview.",
    ),
    Asset(
        "YOLO detection preview UAV 1",
        Path("outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/previews/frame_001_uav_01_rgb_pred.png"),
        "fig3_uav01_yolo_detection.png",
        "Fig. 3",
        "P2P4-SelfAttnFR output from one simulated UAV view.",
    ),
    Asset(
        "YOLO detection preview UAV 2",
        Path("outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/previews/frame_002_uav_02_rgb_pred.png"),
        "fig3_uav02_yolo_detection.png",
        "Fig. 3",
        "P2P4-SelfAttnFR output from one simulated UAV view.",
    ),
    Asset(
        "YOLO detection preview UAV 3",
        Path("outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/previews/frame_003_uav_03_rgb_pred.png"),
        "fig3_uav03_yolo_detection.png",
        "Fig. 3",
        "P2P4-SelfAttnFR output from one simulated UAV view.",
    ),
    Asset(
        "Evidence tokens JSONL",
        Path("outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/evidence_tokens.jsonl"),
        "fig3_evidence_tokens.jsonl",
        "Fig. 3",
        "Structured detector output to drive the 3D evidence graph/reasoner panel.",
    ),
    Asset(
        "Detector smoke summary",
        Path("outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/detector_smoke_summary.json"),
        "fig3_detector_smoke_summary.json",
        "Fig. 3",
        "Summary for current detector-on-simulation smoke test.",
    ),
    Asset(
        "Current real-Cesium detector preview sheet",
        Path("paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png"),
        "fig3_real_cesium_detector_preview_contact_sheet.png",
        "Fig. 3",
        "Current real-Cesium SAFR-YOLO detector-preview sheet from the 3-scenario smoke run.",
    ),
    Asset(
        "Current cross-view evidence graph",
        Path("outputs/reports/live/marinecity_crossview_evidence_graph.png"),
        "fig3_crossview_evidence_graph_smoke.png",
        "Fig. 3",
        "Current real-Cesium cross-view EvidenceToken graph with support/conflict/missing edges.",
    ),
    Asset(
        "Depth point-cloud 3D smoke",
        Path("paper/figures/results/marinecity_system/marinecity_depth_pointcloud_smoke_topdown.png"),
        "fig3_depth_pointcloud_smoke_topdown.png",
        "Fig. 3",
        "Depth-backed 3D geometry smoke preview. Use as handoff context, not as neural 3D completion evidence.",
    ),
    Asset(
        "Scenario S0 panel",
        Path("paper/figures/results/marinecity_system/s0_scenario_panel.png"),
        "fig3_s0_locked_roi_panel.png",
        "Fig. 3",
        "Locked MarineCity ROI scenario panel.",
    ),
    Asset(
        "Scenario S1 panel",
        Path("paper/figures/results/marinecity_system/s1_scenario_panel.png"),
        "fig3_s1_adjacent_overlap_panel.png",
        "Fig. 3",
        "Adjacent/overlap ambiguity scenario panel.",
    ),
    Asset(
        "Scenario S2 panel",
        Path("paper/figures/results/marinecity_system/s2_scenario_panel.png"),
        "fig3_s2_coastline_multiview_panel.png",
        "Fig. 3",
        "Coastline multi-view scenario panel.",
    ),
    Asset(
        "Capture quality ranking sheet",
        Path("paper/figures/results/marinecity_system/marinecity_capture_quality_top8.png"),
        "fig1_fig3_capture_quality_top8.png",
        "Fig. 1/Fig. 3",
        "Visual QA sheet for selecting clean real-Cesium views and avoiding black/void regions.",
    ),
    Asset(
        "Crop candidate sheet",
        Path("paper/figures/results/marinecity_system/marinecity_real_capture_crop_top12.png"),
        "fig1_fig3_crop_candidates_top12.png",
        "Fig. 1/Fig. 3",
        "Crop-only framing candidates for artist guidance; do not use as a synthetic replacement.",
    ),
    Asset(
        "Capture plan",
        Path("outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/capture_plan.json"),
        "fig1_fig3_capture_plan.json",
        "Fig. 1/Fig. 3",
        "UAV altitude, pose, weather, and camera metadata.",
    ),
    Asset(
        "Replicator capture summary",
        Path("outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct_capture_summary.json"),
        "fig1_fig3_replicator_capture_summary.json",
        "Fig. 1/Fig. 3",
        "Isaac output summary: UAV count, object count, bbox counts, and stage origin.",
    ),
    Asset(
        "Isaac stage opened marker",
        Path("outputs/logs/gpu1_isaac51_streaming/marinecity_stage_opened.json"),
        "fig1_fig3_isaac_stage_opened.json",
        "Fig. 1/Fig. 3",
        "Proof that the MarineCity stage opened in the GPU1 Isaac streaming run.",
    ),
]


PLACEHOLDERS = [
    ("fig3_final_neural3d_completion_render.png", "Final neural 3D completion or novel-view rendering after NeRF/Instant-NGP/3DGS-style evaluation."),
    ("fig3_final_nonmock_aerograph_decision_panel.png", "Final non-mock AeroGraph Reasoner output panel: belief, uncertainty, action, verifier result."),
]


def _copy_asset(asset: Asset, out_dir: Path) -> dict[str, str]:
    target = out_dir / asset.target
    row = {
        "label": asset.label,
        "figure": asset.figure,
        "source": str(asset.source),
        "target": str(target),
        "status": "missing",
        "note": asset.note,
    }
    if asset.source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset.source, target)
        row["status"] = "copied"
    return row


def _write_manifest(rows: list[dict[str, str]], out_dir: Path) -> Path:
    lines = [
        "# Fig. 1/Fig. 3 Simulation Handoff Package",
        "",
        "Purpose: collect the real Isaac/MarineCity, multi-UAV detector, 3D evidence, and reasoner assets that will replace placeholder panels in Main Fig. 1 and Main Fig. 3.",
        "",
        "Stable figures: Fig. 2, SelfAttnFR, TinyFReLU, and overlap-aware NMS are treated as architecture/module figures and do not need revision unless the final detector changes.",
        "",
        "## Current Revision Decision",
        "",
        "- Fig. 1 should be revised with the current real-Cesium MarineCity 3-UAV captures and should no longer rely on generic/synthetic city panels.",
        "- Fig. 3 should be revised now for detector previews and cross-view EvidenceToken graph, but the neural 3D completion panel and non-mock AeroGraph output panel must stay visually marked as pending until those gates finish.",
        "- Use the current smoke-test assets as visual/evidence-flow material, not as final neural 3D reconstruction or external LLM validation.",
        "",
        "## Copied Assets",
        "",
        "| Status | Figure | File | Source | Use |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        target_name = Path(row["target"]).name
        lines.append(
            f"| {row['status']} | {row['figure']} | `{target_name}` | `{row['source']}` | {row['note']} |"
        )

    lines.extend(
        [
            "",
            "## Final Missing Assets",
            "",
            "| File | Needed After Final Simulation/Reasoner Experiments |",
            "|---|---|",
        ]
    )
    for filename, note in PLACEHOLDERS:
        placeholder = out_dir / filename
        if _needs_placeholder_png(placeholder):
            _write_placeholder_png(placeholder, note)
        lines.append(f"| `{filename}` | {note} |")

    lines.extend(
        [
            "",
            "## Figure Update Guidance",
            "",
            "- Fig. 1 should use `fig1_map_multiuav_preview.png`, the three `fig1_uav*_rgb.png` views, and the three `fig1_uav*_isaac_bbox.png` previews while keeping the high-level CoM3D-ACE pipeline layout.",
            "- Fig. 3 should use `fig3_real_cesium_detector_preview_contact_sheet.png`, `fig3_crossview_evidence_graph_smoke.png`, and `fig3_depth_pointcloud_smoke_topdown.png` for the current evidence-flow story.",
            "- Fig. 3's final neural 3D completion and non-mock AeroGraph panels should be replaced later by actual runner/provider outputs.",
            "- Keep diagrams compact. Detailed equations and module internals stay in Fig. 2 and supplementary figures.",
            "- Do not present the current smoke-test detector output as the final 3D/reasoner result until the full simulation experiment is completed.",
            "",
        ]
    )
    manifest = out_dir / "README.md"
    manifest.write_text("\n".join(lines), encoding="utf-8")
    return manifest


def _needs_placeholder_png(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        return path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n"
    except OSError:
        return True


def _write_placeholder_png(path: Path, note: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    font = ImageFont.truetype(str(font_path), 28) if font_path.exists() else ImageFont.load_default()
    small_font = ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
    image = Image.new("RGB", (1280, 720), "#FEE2E2")
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 1256, 696), outline="#DC2626", width=6)
    draw.text((64, 64), "PENDING FINAL SIMULATION ARTIFACT", fill="#991B1B", font=font)
    words = note.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if draw.textlength(candidate, font=small_font) > 1080 and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    y = 150
    for line in lines[:8]:
        draw.text((64, y), line, fill="#7F1D1D", font=small_font)
        y += 34
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [_copy_asset(asset, out_dir) for asset in ASSETS]
    manifest = _write_manifest(rows, out_dir)

    summary = {
        "out_dir": str(out_dir),
        "manifest": str(manifest),
        "copied": sum(row["status"] == "copied" for row in rows),
        "missing": sum(row["status"] != "copied" for row in rows),
        "placeholder_count": len(PLACEHOLDERS),
    }
    (out_dir / "handoff_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
