"""Build a compact MarineCity simulation dashboard PNG.

The dashboard separates three things that are easy to mix up during the Isaac
work:

1. The user's live Isaac GUI view.
2. The completed smoke-test capture artifacts.
3. The next paper-facing viewer160 recapture queue.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = REPO_ROOT / "outputs/reports/live"
OUT_PATH = LIVE_DIR / "marinecity_simulation_dashboard.png"
SYSTEM_DIR = LIVE_DIR / "marinecity_system_test_10plus"
PROMPT_PACK_MANIFEST = LIVE_DIR / "aerograph_prompt_pack/manifest.json"
STATUS_PATH = LIVE_DIR / "marinecity_3d_reasoner_status_2026-06-24.md"
VIEWER160_STATUS_CSV = REPO_ROOT / "outputs/experiments/marinecity_viewer160_pipeline_status.csv"
VIEWER160_STATUS_MD = REPO_ROOT / "outputs/experiments/marinecity_viewer160_pipeline_status.md"
VIEWER160_QUEUE_LOG = REPO_ROOT / "outputs/logs/marinecity_viewer160_pipeline/queue.log"
ISAAC_EXPORT_ROOT = Path("/home/oem/UAV/uav_marinecity/outputs/isaac_exports")
SESSION_OVERLAY_STATUS = Path("/home/oem/UAV/uav_marinecity/outputs/uavmarine_session_overlay_status_s0.json")

VIEWER160_SCENARIOS = [
    ("S0", "locked ROI", "uavmarine_s0_viewer160_session_recapture", "uavmarine_s0_viewer160_recapture"),
    ("S1", "adjacent overlap", "uavmarine_s1_viewer160_session_recapture", "uavmarine_s1_viewer160_recapture"),
    ("S2", "coastline multiview", "uavmarine_s2_viewer160_session_recapture", "uavmarine_s2_viewer160_recapture"),
]


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else ["DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_TITLE = font(42, True)
FONT_H = font(25, True)
FONT_BODY = font(20)
FONT_SMALL = font(16)
FONT_MONO = font(15)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def latest_queue_event(path: Path) -> str:
    if not path.exists():
        return "not started"
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        return "not started"
    return lines[-1][-120:]


def latest_status(rows: list[dict[str, str]], scenario: str, step: str) -> str:
    matches = [row for row in rows if row.get("scenario") == scenario and row.get("step") == step]
    if not matches:
        return "pending"
    return matches[-1].get("status", "unknown")


def unique_ok_count(rows: list[dict[str, str]], step: str) -> int:
    return len({row.get("scenario") for row in rows if row.get("step") == step and row.get("status") == "ok"})


def viewer160_result_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for short_name, label, session_stem, legacy_stem in VIEWER160_SCENARIOS:
        session_summary = REPO_ROOT / f"outputs/evidence/{session_stem}_detector_smoke_conf001/detector_smoke_summary.json"
        legacy_summary = REPO_ROOT / f"outputs/evidence/{legacy_stem}_detector_smoke_conf001/detector_smoke_summary.json"
        stem = session_stem if session_summary.exists() else legacy_stem
        detector = read_json(
            REPO_ROOT / f"outputs/evidence/{stem}_detector_smoke_conf001/detector_smoke_summary.json"
        )
        reasoner = read_json(REPO_ROOT / f"outputs/reasoning/{stem}_from_detector_conf001_mock/summary.json")
        preview_dir = REPO_ROOT / f"outputs/evidence/{stem}_detector_smoke_conf001/previews"
        preview = next(iter(sorted(preview_dir.glob("*_pred.png"))), None) if preview_dir.exists() else None
        rows.append(
            {
                "scenario": short_name,
                "label": label,
                "stem": stem,
                "token_count": int(detector.get("token_count", 0) or 0),
                "tokens_by_class": detector.get("tokens_by_class", {}) or {},
                "tokens_by_uav": detector.get("tokens_by_uav", {}) or {},
                "hypothesis_count": int(reasoner.get("hypothesis_count", 0) or 0),
                "reobserve_count": int(reasoner.get("reobserve_count", 0) or 0),
                "provider": reasoner.get("provider", "pending"),
                "preview": preview,
            }
        )
    return rows


def viewer160_capture_count() -> int:
    count = 0
    for _short_name, _label, session_stem, legacy_stem in VIEWER160_SCENARIOS:
        if (
            (ISAAC_EXPORT_ROOT / session_stem / "real_cesium_capture_summary.json").exists()
            or (ISAAC_EXPORT_ROOT / legacy_stem / "real_cesium_capture_summary.json").exists()
        ):
            count += 1
    return count


def result_count(root: Path, pattern: str) -> int:
    if not root.exists():
        return 0
    return len(list(root.glob(pattern)))


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGB", size, "#f8fafc")
    draw = ImageDraw.Draw(image)
    if not path.exists():
        draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=2)
        draw.text((18, size[1] // 2 - 10), f"missing: {path.name}", fill="#b91c1c", font=FONT_SMALL)
        return image
    src = Image.open(path).convert("RGB")
    src.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - src.width) // 2
    y = (size[1] - src.height) // 2
    image.paste(src, (x, y))
    return image


def preview_strip(paths: list[Path | None], size: tuple[int, int], labels: list[str]) -> Image.Image:
    image = Image.new("RGB", size, "#f8fafc")
    draw = ImageDraw.Draw(image)
    pad = 14
    tile_w = (size[0] - pad * (len(paths) + 1)) // max(1, len(paths))
    tile_h = size[1] - 54
    for idx, path in enumerate(paths):
        x0 = pad + idx * (tile_w + pad)
        y0 = 12
        draw.rounded_rectangle([x0, y0, x0 + tile_w, y0 + tile_h], radius=8, fill="#ffffff", outline="#cbd5e1", width=2)
        if path and path.exists():
            thumb = Image.open(path).convert("RGB")
            thumb.thumbnail((tile_w - 12, tile_h - 12), Image.Resampling.LANCZOS)
            image.paste(thumb, (x0 + (tile_w - thumb.width) // 2, y0 + (tile_h - thumb.height) // 2))
        else:
            draw.text((x0 + 14, y0 + tile_h // 2 - 10), "missing preview", fill="#b91c1c", font=FONT_SMALL)
        draw.text((x0 + 8, y0 + tile_h + 10), labels[idx], fill="#0f172a", font=FONT_SMALL)
    return image


def wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_chars: int,
    line_h: int,
    fill: str = "#0f172a",
    font_obj: ImageFont.ImageFont = FONT_BODY,
) -> int:
    import textwrap

    for paragraph in text.splitlines():
        lines = textwrap.wrap(paragraph, width=max_chars) or [""]
        for line in lines:
            draw.text((x, y), line, fill=fill, font=font_obj)
            y += line_h
    return y


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, accent: str) -> tuple[int, int]:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=12, fill="#ffffff", outline="#cbd5e1", width=2)
    draw.rectangle([x0, y0, x1, y0 + 46], fill=accent)
    draw.text((x0 + 18, y0 + 9), title, fill="white", font=FONT_H)
    return x0 + 18, y0 + 66


def status_badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: str) -> None:
    x, y = xy
    w = max(150, len(text) * 11 + 28)
    draw.rounded_rectangle([x, y, x + w, y + 34], radius=15, fill=fill)
    draw.text((x + 14, y + 6), text, fill="white", font=FONT_SMALL)


def main() -> None:
    manifest = read_json(SYSTEM_DIR / "manifest.json")
    prompt_pack = read_json(PROMPT_PACK_MANIFEST)
    session_overlay = read_json(SESSION_OVERLAY_STATUS)
    scenario_rows = read_csv(SYSTEM_DIR / "paper_system_scenario_table.csv")
    token_rows = read_csv(SYSTEM_DIR / "system_test_token_results.csv")
    viewer_rows = read_csv(VIEWER160_STATUS_CSV)
    detector_results_root = REPO_ROOT / "outputs/detectors"
    viewer_reasoner_ok = unique_ok_count(viewer_rows, "reasoner")
    viewer_detector_ok = unique_ok_count(viewer_rows, "detector")
    viewer_capture_ok = viewer160_capture_count()
    viewer_results = viewer160_result_rows()
    viewer_total_tokens = sum(int(row["token_count"]) for row in viewer_results)
    viewer_total_hypotheses = sum(int(row["hypothesis_count"]) for row in viewer_results)
    viewer_total_reobserve = sum(int(row["reobserve_count"]) for row in viewer_results)
    viewer_classes = sorted(
        {
            cls
            for row in viewer_results
            for cls, count in (row.get("tokens_by_class") or {}).items()
            if int(count or 0) > 0
        }
    )
    viewer_started = VIEWER160_QUEUE_LOG.exists()
    viewer_badge = "paper recapture: running" if viewer_started and viewer_reasoner_ok < 3 else "paper recapture: done" if viewer_reasoner_ok >= 3 else "paper recapture: pending"
    viewer_badge_color = "#f97316" if viewer_started and viewer_reasoner_ok < 3 else "#16a34a" if viewer_reasoner_ok >= 3 else "#7c3aed"
    camera_profile = str(session_overlay.get("camera_profile", "manual_user_camera"))
    camera_set = bool(session_overlay.get("camera_set", False))
    camera_badge = "GUI: viewer160" if camera_set else "GUI: manual"
    camera_badge_color = "#16a34a" if camera_set else "#2563eb"

    related_counts = {
        "required related-work reimpl": result_count(
            detector_results_root / "required_related_work_reimplementations", "*/ultralytics/results.csv"
        ),
        "YOLO11s-UAV repro": result_count(
            detector_results_root / "related_work_module_reproductions", "*/ultralytics/results.csv"
        ),
        "TinyPerson 640": result_count(detector_results_root / "tinyperson_640", "*/ultralytics/results.csv"),
        "CSFPR/MFFSOD consistency": result_count(detector_results_root / "related_work_consistency", "*/*/results.csv"),
    }

    canvas = Image.new("RGB", (2200, 1480), "#eef2f7")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 2200, 96], fill="#0f172a")
    draw.text((36, 22), "MarineCity Isaac/Cesium Simulation Dashboard", fill="white", font=FONT_TITLE)
    draw.text((36, 66), f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST", fill="#cbd5e1", font=FONT_SMALL)
    status_badge(draw, (1710, 28), camera_badge, camera_badge_color)
    status_badge(draw, (1900, 28), viewer_badge, viewer_badge_color)

    x, y = card(draw, (36, 130, 690, 500), "What You See in Isaac", "#2563eb")
    overlay_status = session_overlay.get("status", "not verified")
    root_layer = Path(str(session_overlay.get("root_layer", "unknown"))).name
    actor_layer = Path(str(session_overlay.get("actor_layer", "unknown"))).name
    prim_status = session_overlay.get("prim_status", {}) or {}
    google_ok = prim_status.get("/Google_Photorealistic_3D_Tiles", {}).get("valid", False)
    terrain_ok = prim_status.get("/Cesium_World_Terrain", {}).get("valid", False)
    fake_city = session_overlay.get("substitute_city_geometry_created", "unknown")
    georef = session_overlay.get("georeference_readback", {}) or {}
    georef_height = georef.get("cesium:georeferenceOrigin:height", "unknown")
    active_camera = Path(str(session_overlay.get("active_camera_path", "unknown"))).name
    if camera_set:
        live_text = (
            "Current visible Isaac GUI is the real-time view you can inspect manually. "
            "It has been reset to the encoded viewer160 runtime camera so the MarineCity "
            "ROI should stay visible instead of drifting into a dark tile or shadowed view."
        )
    else:
        live_text = (
            "Current visible Isaac GUI is the real-time view you can inspect manually. "
            "You reported the viewport altitude around 160 m. The automation will not "
            "blindly replace this view; it should recapture from a matching viewer160 profile."
        )
    y = wrapped(
        draw,
        live_text,
        x,
        y,
        48,
        29,
    )
    draw.text((x, y + 18), "Viewer camera altitude: 160 m", fill="#0f172a", font=FONT_H)
    draw.text((x, y + 58), f"Camera profile: {camera_profile}; active: {active_camera}", fill="#334155", font=FONT_SMALL)
    draw.text((x, y + 88), f"Live overlay: {overlay_status}", fill="#0f172a", font=FONT_SMALL)
    draw.text((x, y + 114), f"Root: {root_layer}; actor: {actor_layer}", fill="#334155", font=FONT_SMALL)
    draw.text((x, y + 140), f"Google tiles={google_ok}, terrain={terrain_ok}, georef h={georef_height}, fake city={fake_city}", fill="#b45309", font=FONT_SMALL)

    x, y = card(draw, (730, 130, 1420, 500), "Viewer160 Real-Cesium Queue", "#0f766e")
    smoke_summary = (
        f"Scenarios complete: {viewer_reasoner_ok}/3\n"
        f"Real Cesium captures: {viewer_capture_ok}/3\n"
        f"P2P4-SelfAttnFR detector runs: {viewer_detector_ok}/3\n"
        f"EvidenceTokens: {viewer_total_tokens}\n"
        f"3D hypotheses / re-observe actions: {viewer_total_hypotheses} / {viewer_total_reobserve}\n"
        f"Detected classes in this smoke pass: {', '.join(viewer_classes) if viewer_classes else 'none'}"
    )
    wrapped(draw, smoke_summary, x, y, 50, 31)
    draw.text((x, 438), "Integration works; paper-quality visuals still need a cleaner recapture.", fill="#b45309", font=FONT_SMALL)

    x, y = card(draw, (1460, 130, 2164, 500), "Next Paper-Facing Queue", "#7c3aed")
    next_steps = [
        f"1. Recapture S0/S1/S2 with viewer160 ({viewer_capture_ok}/3 done)",
        f"2. Run P2P4-SelfAttnFR detector ({viewer_detector_ok}/3 done)",
        f"3. Build 3D evidence + reasoner outputs ({viewer_reasoner_ok}/3 done)",
        "4. Improve object placement/scale for stronger car/person detections",
        f"5. Run non-mock AeroGraph LLM ({prompt_pack.get('total_prompts', 0)} prompts ready)",
    ]
    for step in next_steps:
        draw.text((x, y), step, fill="#0f172a", font=FONT_BODY)
        y += 35

    x, y = card(draw, (36, 540, 690, 900), "2D Experiment Situation", "#1d4ed8")
    for label, count in related_counts.items():
        draw.text((x, y), f"{label}: {count} result files", fill="#0f172a", font=FONT_BODY)
        y += 35
    queue_paths = [
        ("required related-work", REPO_ROOT / "outputs/logs/required_related_work_models/queue.log"),
        ("related module repro", REPO_ROOT / "outputs/logs/related_work_module_reproductions/queue.log"),
        ("TinyPerson 640", REPO_ROOT / "outputs/logs/tinyperson_640/queue.log"),
    ]
    y += 14
    for label, path in queue_paths:
        event = latest_queue_event(path)
        if len(event) > 72:
            event = event[:69] + "..."
        y = wrapped(draw, f"{label}: {event}", x, y, 58, 20, fill="#334155", font_obj=FONT_SMALL)
        y += 4

    x, y = card(draw, (730, 540, 1420, 900), "Current Viewer160 Results", "#16a34a")
    for row in viewer_results:
        classes = ", ".join(f"{k}:{v}" for k, v in (row.get("tokens_by_class") or {}).items()) or "none"
        line = (
            f"{row['scenario']} {row['label']}: tokens {row['token_count']}, "
            f"3D hyp {row['hypothesis_count']}, reobs {row['reobserve_count']}, classes {classes}"
        )
        y = wrapped(draw, line, x, y, 68, 22, fill="#0f172a", font_obj=FONT_SMALL)
        y += 4
    y += 8
    wrapped(
        draw,
        "These rows are valid as real-Cesium system integration smoke-test records. They should not be presented as final 3D/reasoner quantitative results until the non-mock LLM/VLM study is complete.",
        x,
        y,
        54,
        28,
        fill="#334155",
    )

    x, y = card(draw, (1460, 540, 2164, 900), "Live Viewing Reality", "#dc2626")
    wrapped(
        draw,
        "You can watch the current Isaac GUI in real time. Codex-side scripts normally launch or drive a separate capture process, so they do not automatically inherit the exact manual viewport unless we encode it as a profile or save it into a camera prim.",
        x,
        y,
        54,
        29,
    )
    wrapped(
        draw,
        "Current move: viewer160 runtime camera is active. Next, recapture clean S0/S1/S2 views and keep the GUI stage unsaved.",
        x,
        790,
        50,
        27,
    )
    previews = preview_strip(
        [row.get("preview") for row in viewer_results],
        (680, 350),
        [f"{row['scenario']} detector preview" for row in viewer_results],
    )
    canvas.paste(previews, (36, 960))
    draw.text((36, 925), "Latest Viewer160 Detector Previews", fill="#0f172a", font=FONT_H)

    tokens = fit_image(SYSTEM_DIR / "contact_sheet_3_scenarios.png", (680, 350))
    canvas.paste(tokens, (760, 960))
    draw.text((760, 925), "Current Real-Cesium System Sheet", fill="#0f172a", font=FONT_H)

    x, y = card(draw, (1484, 960, 2164, 1344), "Concrete Commands", "#0f172a")
    commands = [
        "bash scripts/ubuntu/start_accv_continuous_queue.sh",
        "COM3D_KEEP_USER_CAMERA=0 SESSION=uav-marinecity-s0-viewer160-gui bash scripts/ubuntu/start_uavmarine_overlay_gui.sh s0",
        "tmux attach -t live-training-scoreboard",
        "python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png",
        "python scripts/build_aerograph_prompt_pack.py",
        "capture_realcities_multiuav.py --camera-profile viewer160 --stage /workspace/uav_marinecity/uavmarine_multiuav_overlay_s0_locked_roi.usda",
        "run_marinecity_3d_reasoner_smoke.py --provider openai|command",
    ]
    for cmd in commands:
        y = wrapped(draw, cmd, x, y, 66, 20, fill="#334155", font_obj=FONT_SMALL)
        y += 7

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_PATH)
    print(OUT_PATH)


if __name__ == "__main__":
    main()
