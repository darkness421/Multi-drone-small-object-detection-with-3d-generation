"""Build the MarineCity clean full-frame recapture runbook.

The current real-Cesium MarineCity system smoke evidence is valid, but the
full-frame qualitative gate can fail when a capture contains too much black
tile/void area. This script turns the gate output into a concrete recapture
plan with exact queue commands and post-run checks.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = REPO_ROOT / "outputs/reports/live"
DOCS_DIR = REPO_ROOT / "docs"
GATE_PATH = LIVE_DIR / "marinecity_qualitative_gate.json"
PIPELINE_STATUS = REPO_ROOT / "outputs/experiments/marinecity_viewer160_pipeline_status.md"
OUT_JSON = LIVE_DIR / "marinecity_clean_recapture_plan.json"
OUT_MD = LIVE_DIR / "marinecity_clean_recapture_plan.md"
DOC_COPY = DOCS_DIR / "marinecity_clean_recapture_plan.md"

SCENARIOS = [
    {
        "id": "S0",
        "reasoner_scenario": "s0_locked_roi",
        "overlay": "uavmarine_multiuav_actor_overlay_s0_locked_roi.usda",
        "out_name": "uavmarine_s0_viewer160_session_recapture",
        "role": "locked MarineCity ROI smoke/full-frame candidate",
    },
    {
        "id": "S1",
        "reasoner_scenario": "s1_adjacent_overlap",
        "overlay": "uavmarine_multiuav_actor_overlay_s1_adjacent_overlap.usda",
        "out_name": "uavmarine_s1_viewer160_session_recapture",
        "role": "adjacent-overlap ambiguity candidate",
    },
    {
        "id": "S2",
        "reasoner_scenario": "s2_coastline_multiview",
        "overlay": "uavmarine_multiuav_actor_overlay_s2_coastline_multiview.usda",
        "out_name": "uavmarine_s2_viewer160_session_recapture",
        "role": "coastline multi-view candidate",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def command_lines() -> dict[str, str]:
    start_gui = (
        "COM3D_KEEP_USER_CAMERA=1 COM3D_VIEWER_PROFILE=viewer160 "
        "COM3D_GEOREF_HEIGHT=160.0 "
        "SESSION=uav-marinecity-s0-viewer160-gui "
        "bash scripts/ubuntu/start_uavmarine_overlay_gui.sh s0"
    )
    recapture_queue = (
        "FORCE_RECAPTURE=1 FORCE_DETECTOR=1 FORCE_REASONER=1 "
        "CAPTURE_USE_ACTOR_SESSION=1 CAPTURE_HEADLESS=1 "
        "CAPTURE_CAMERA_PROFILE=viewer160-clean "
        "CAPTURE_OPEN_WARMUP=900 CAPTURE_RENDER_WARMUP=240 "
        "CAPTURE_WIDTH=1280 CAPTURE_HEIGHT=720 "
        "DETECTOR_DEVICE=cpu DETECTOR_IMGSZ=1280 DETECTOR_CONF=0.01 "
        "REASONER_PROVIDER=mock "
        "bash scripts/ubuntu/start_marinecity_viewer160_pipeline_queue.sh"
    )
    qa_refresh = "\n".join(
        [
            "python scripts/select_marinecity_capture_quality.py",
            "python scripts/build_marinecity_real_capture_crop_candidates.py",
            "python scripts/build_marinecity_qualitative_selection.py",
            "python scripts/check_marinecity_qualitative_gate.py",
            "python scripts/build_marinecity_simulation_dashboard.py",
            "PYTHONPATH=. python scripts/build_live_training_dashboard.py --out outputs/reports/live/training_dashboard.png",
            "python scripts/check_paper_artifact_readiness.py",
            "python scripts/build_accv_status_snapshot.py",
        ]
    )
    monitor = "\n".join(
        [
            "tmux attach -t marinecity-viewer160-pipeline",
            "tail -f outputs/logs/marinecity_viewer160_pipeline/queue.log",
        ]
    )
    return {
        "start_gui": start_gui,
        "recapture_queue": recapture_queue,
        "qa_refresh": qa_refresh,
        "monitor": monitor,
    }


def build_plan() -> dict[str, Any]:
    gate = read_json(GATE_PATH)
    thresholds = gate.get("thresholds", {}) or {}
    checks = gate.get("checks", {}) or {}
    best_full = gate.get("best_full_capture", {}) or {}
    best_crop = gate.get("best_crop_candidate", {}) or {}
    system_manifest = gate.get("system_manifest", {}) or {}
    commands = command_lines()
    full_black = best_full.get("best_black_ratio")
    mean_top3 = best_full.get("mean_top3_black_ratio")
    full_black_max = thresholds.get("full_black_max", 0.1)
    mean_top3_max = thresholds.get("mean_top3_black_max", 0.15)
    try:
        needed_best_improvement = max(0.0, float(full_black) - float(full_black_max))
    except (TypeError, ValueError):
        needed_best_improvement = None
    try:
        needed_top3_improvement = max(0.0, float(mean_top3) - float(mean_top3_max))
    except (TypeError, ValueError):
        needed_top3_improvement = None
    full_main_ready = bool(checks.get("full_frame_main_ready"))

    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": "main_full_frame_ready" if full_main_ready else "main_full_frame_recapture_plan_ready",
        "source_gate": rel(GATE_PATH),
        "source_gate_status": gate.get("status", "missing_gate"),
        "current_checks": checks,
        "thresholds": thresholds,
        "current_best_full_capture": best_full,
        "current_best_crop_candidate": best_crop,
        "system_token_level_test_count": system_manifest.get("token_level_test_count"),
        "needed_improvement": {
            "best_black_ratio_delta_to_threshold": needed_best_improvement,
            "mean_top3_black_ratio_delta_to_threshold": needed_top3_improvement,
        },
        "height_policy": {
            "review_height_m": 160,
            "uav_camera_band_m": [140, 160],
            "scenario_default_uav_altitudes_m": {"uav_01": 140, "uav_02": 150, "uav_03": 160},
            "note": "Keep UAV camera altitude separate from CesiumGeoreference readback.",
        },
        "real_cesium_constraints": [
            "Open the real Cesium MarineCity USD only.",
            "Use actor-only session overlays for S0/S1/S2.",
            "Do not create fake, proxy, placeholder, block, or fallback city geometry.",
            "Do not overwrite or save the base uavmarine.usd during capture.",
            "If Cesium tiles fail to render, fail with diagnostics rather than substituting geometry.",
        ],
        "scenarios": SCENARIOS,
        "commands": commands,
        "acceptance": {
            "main_full_frame_ready": [
                "real_cesium_ok == true",
                "system_smoke_ok == true",
                f"best_full_capture.best_black_ratio <= {full_black_max}",
                f"best_full_capture.mean_top3_black_ratio <= {mean_top3_max}",
            ],
            "crop_supplementary_only": [
                f"best_crop_candidate.black_ratio <= {thresholds.get('crop_black_max', 0.02)}",
                f"best_crop_candidate.area_ratio >= {thresholds.get('crop_area_min', 0.35)}",
                "Caption must explicitly say crop-only if used.",
            ],
        },
        "outputs_to_watch": {
            "pipeline_status": rel(PIPELINE_STATUS),
            "queue_log": "outputs/logs/marinecity_viewer160_pipeline/queue.log",
            "capture_quality_csv": "outputs/reports/live/marinecity_capture_quality/marinecity_capture_quality_rank.csv",
            "capture_quality_sheet": "outputs/reports/live/marinecity_capture_quality/marinecity_capture_quality_top8.png",
            "qualitative_gate": rel(GATE_PATH),
            "simulation_dashboard": "outputs/reports/live/marinecity_simulation_dashboard.png",
        },
        "next_after_pass": [
            "Promote the passing full-frame image into paper/figures/results/marinecity_system.",
            "Update paper/sections/07_marinecity_qualitative_figure_slots.tex from the regenerated selection manifest.",
            "Keep crop-only figures in supplementary unless the main caption clearly states crop-only framing.",
            "Use the reviewed 49-prompt AeroGraph candidate with a caveat; run external-provider replication before claiming final reasoner performance.",
        ],
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def build_markdown(plan: dict[str, Any]) -> str:
    thresholds = plan["thresholds"]
    full = plan["current_best_full_capture"]
    crop = plan["current_best_crop_candidate"]
    improvement = plan["needed_improvement"]
    token_count = plan.get("system_token_level_test_count") or "10+"
    if plan.get("status") == "main_full_frame_ready":
        why_needed = (
            f"The real-Cesium MarineCity pipeline and {token_count} token-level smoke tests are present. "
            "The current best full-frame capture now satisfies the main-paper qualitative gate; "
            "keep this runbook as the reproducible recapture and QA recipe."
        )
    else:
        why_needed = (
            f"The real-Cesium MarineCity pipeline and {token_count} token-level smoke tests are present, "
            "but the current best full-frame capture still contains too much black/void tile area "
            "for main-paper qualitative promotion."
        )
    lines = [
        "# MarineCity Clean Full-Frame Recapture Plan",
        "",
        f"Updated: `{plan['updated_at_kst']}`",
        f"Status: `{plan['status']}`",
        f"Source gate: `{plan['source_gate']}`",
        f"Source gate status: `{plan['source_gate_status']}`",
        "",
        "## Why This Is Needed",
        "",
        why_needed,
        "",
        "| Metric | Current | Target | Gap |",
        "| --- | ---: | ---: | ---: |",
        f"| Best full-frame black/void | `{fmt(full.get('best_black_ratio'))}` | `{fmt(thresholds.get('full_black_max'))}` | `{fmt(improvement.get('best_black_ratio_delta_to_threshold'))}` |",
        f"| Mean top-3 full-frame black/void | `{fmt(full.get('mean_top3_black_ratio'))}` | `{fmt(thresholds.get('mean_top3_black_max'))}` | `{fmt(improvement.get('mean_top3_black_ratio_delta_to_threshold'))}` |",
        f"| Best crop black/void | `{fmt(crop.get('black_ratio'))}` | `{fmt(thresholds.get('crop_black_max'))}` | supplementary-only |",
        "",
        "## Height And Camera Policy",
        "",
        "- User-visible MarineCity review height: `160 m`.",
        "- UAV/camera observation band: `140-160 m`.",
        "- Default S0 UAV schedule: `uav_01=140 m`, `uav_02=150 m`, `uav_03=160 m`.",
        "- Keep this separate from CesiumGeoreference readback.",
        "",
        "## Hard Constraints",
        "",
    ]
    for item in plan["real_cesium_constraints"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Scenario Targets",
            "",
            "| Scenario | Overlay | Output | Purpose |",
            "| --- | --- | --- | --- |",
        ]
    )
    for scenario in plan["scenarios"]:
        lines.append(
            f"| {scenario['id']} | `{scenario['overlay']}` | `{scenario['out_name']}` | {scenario['role']} |"
        )

    commands = plan["commands"]
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "Start or reopen the real-Cesium GUI at the 160 m review profile if the current GUI is not stable:",
            "",
            "```bash",
            commands["start_gui"],
            "```",
            "",
            "Run or reproduce the clean recapture + detector + rule-based reasoner queue:",
            "",
            "```bash",
            commands["recapture_queue"],
            "```",
            "",
            "Monitor while it runs:",
            "",
            "```bash",
            commands["monitor"],
            "```",
            "",
            "After the queue finishes, regenerate visual QA, gates, and dashboards:",
            "",
            "```bash",
            commands["qa_refresh"],
            "```",
            "",
            "## Acceptance",
            "",
            "Main full-frame qualitative figure is ready only when all of these are true:",
            "",
        ]
    )
    for item in plan["acceptance"]["main_full_frame_ready"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "Crop candidates remain supplementary-only unless explicitly captioned as crop-only framing evidence.", ""])
    lines.extend(["## Outputs To Watch", ""])
    for label, path in plan["outputs_to_watch"].items():
        lines.append(f"- `{label}`: `{path}`")
    lines.extend(["", "## Next After Pass", ""])
    for item in plan["next_after_pass"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    plan = build_plan()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DOC_COPY.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown = build_markdown(plan)
    OUT_MD.write_text(markdown, encoding="utf-8")
    DOC_COPY.write_text(markdown, encoding="utf-8")
    print(json.dumps({"json": rel(OUT_JSON), "markdown": rel(OUT_MD), "doc_copy": rel(DOC_COPY)}, indent=2))


if __name__ == "__main__":
    main()
