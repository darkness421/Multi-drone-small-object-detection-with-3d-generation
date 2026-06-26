"""Audit the current real-Cesium MarineCity system integration state.

The audit is intentionally conservative. It confirms only evidence backed by
existing artifacts and marks final 3D completion or non-mock LLM evaluation as
pending until their result files exist.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = REPO_ROOT / "outputs/reports/live"
BENCHMARK = REPO_ROOT / "outputs/experiments/marinecity_real_capture_benchmark.json"
DETECTOR_SUMMARY = REPO_ROOT / "outputs/evidence/marinecity_real_capture_detector_smoke/detector_smoke_summary.json"
SUPP_LOWCONF_DETECTOR_SUMMARY = (
    REPO_ROOT / "outputs/evidence/marinecity_real_capture_detector_smoke_conf005/detector_smoke_summary.json"
)
TOKENS_JSONL = REPO_ROOT / "outputs/evidence/marinecity_real_capture_detector_smoke/evidence_tokens.jsonl"
CROSSVIEW_SUMMARY = REPO_ROOT / "outputs/graphs/marinecity_crossview_evidence_graph/summary.json"
NONMOCK_SMOKE = LIVE_DIR / "aerograph_real_capture_nonmock_smoke_status.json"
NONMOCK_FINAL = LIVE_DIR / "aerograph_nonmock_readiness_status.json"
THREED_COMPARISON = REPO_ROOT / "outputs/experiments/3d_generation_comparison.csv"
TINYPERSON_SUMMARY = REPO_ROOT / "outputs/experiments/tinyperson_640/summary.csv"
SESSION_OVERLAY = Path("/home/oem/UAV/uav_marinecity/outputs/uavmarine_session_overlay_status_s0.json")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def localize_workspace_path(path_value: str) -> Path:
    if path_value.startswith("/workspace/uav_marinecity/"):
        return Path("/home/oem/UAV/uav_marinecity") / path_value.replace("/workspace/uav_marinecity/", "", 1)
    return Path(path_value)


def actor_layer_path(session: dict[str, Any]) -> Path:
    actor_value = str(session.get("actor_layer") or "")
    if actor_value:
        return localize_workspace_path(actor_value)
    return Path("/home/oem/UAV/uav_marinecity/uavmarine_multiuav_actor_overlay_s0_locked_roi.usda")


def parse_actor_layer(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
            "object_count": 0,
            "uav_count": 0,
            "actor_classes": [],
            "uav_ids": [],
            "camera_count": 0,
            "fake_city_keyword_found": False,
        }
    text = path.read_text(encoding="utf-8", errors="ignore")
    object_match = re.search(r"custom\s+int\s+com3d:object_count\s*=\s*(\d+)", text)
    uav_match = re.search(r"custom\s+int\s+com3d:uav_count\s*=\s*(\d+)", text)
    actor_classes = sorted(set(re.findall(r'custom\s+string\s+com3d:class_name\s*=\s*"([^"]+)"', text)))
    uav_ids = sorted(set(re.findall(r'def\s+Xform\s+"(uav_\d+)"', text)))
    camera_count = len(re.findall(r'def\s+Camera\s+"Camera"', text))
    fake_city_keyword_found = bool(
        re.search(r"com3d:(?:fake|proxy|synthetic|procedural|placeholder|substitute)_city[^=\n]*=\s*(?:true|1)", text, re.I)
        or re.search(r'def\s+Xform\s+"(?:Fake|Proxy|Synthetic|Procedural|Placeholder|Substitute)City"', text)
    )
    return {
        "exists": True,
        "path": str(path),
        "object_count": int(object_match.group(1)) if object_match else len(actor_classes),
        "uav_count": int(uav_match.group(1)) if uav_match else len(uav_ids),
        "actor_classes": actor_classes,
        "uav_ids": uav_ids,
        "camera_count": camera_count,
        "fake_city_keyword_found": fake_city_keyword_found,
    }


def token_class_counts(tokens: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for token in tokens:
        metadata = token.get("metadata", {}) or {}
        name = str(metadata.get("class_name") or token.get("class_id") or "unknown")
        counts[name] += 1
    return counts


def tiny_person_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return {"status": "missing", "row_count": 0}
    best = max(rows, key=lambda row: float(row.get("best_AP_mean", 0.0) or 0.0))
    ours = next((row for row in rows if row.get("method", "").startswith("ProposedSize-P2P4BalancedSelfAttnTinyFReLU")), {})
    return {
        "status": "complete_supplementary_stress_test",
        "row_count": len(rows),
        "all_seed_count": sorted(set(row.get("seed_count", "") for row in rows)),
        "best_method": best.get("method", ""),
        "best_ap": float(best.get("best_AP_mean", 0.0) or 0.0),
        "best_ap50": float(best.get("best_AP50_mean", 0.0) or 0.0),
        "ours_method": ours.get("method", ""),
        "ours_ap": float(ours.get("best_AP_mean", 0.0) or 0.0) if ours else None,
        "ours_ap50": float(ours.get("best_AP50_mean", 0.0) or 0.0) if ours else None,
        "claiming_rule": (
            "Use TinyPerson as supplementary domain-shift evidence only. "
            "The current sparse converted 640 split does not support a headline SAFR-YOLO improvement claim."
        ),
    }


def threed_status(rows: list[dict[str, str]], benchmark: dict[str, Any]) -> dict[str, Any]:
    valid_rows = [
        row
        for row in rows
        if any((row.get(metric, "") or "").strip() for metric in ["PSNR", "SSIM", "LPIPS", "FPS"])
        and (row.get("status", "") or "").lower() not in {"pending", "missing", "placeholder"}
    ]
    return {
        "status": "complete" if valid_rows else "pending_upstream_runner_connection",
        "result_row_count": len(valid_rows),
        "comparison_csv": str(THREED_COMPARISON.relative_to(REPO_ROOT)),
        "benchmark_external_runner_status": (benchmark.get("summary", {}) or {}).get(
            "external_neural_3d_runner_status", "missing"
        ),
        "claiming_rule": (
            "Current real-Cesium RGB/depth/pose captures are valid source evidence. "
            "Do not claim NeRF/Instant-NGP/Mip-NeRF/3DGS completion until metric rows exist."
        ),
    }


def pass_bool(value: bool) -> str:
    return "PASS" if value else "FAIL"


def build_report() -> dict[str, Any]:
    benchmark = read_json(BENCHMARK)
    detector = read_json(DETECTOR_SUMMARY)
    lowconf_detector = read_json(SUPP_LOWCONF_DETECTOR_SUMMARY)
    crossview = read_json(CROSSVIEW_SUMMARY)
    session = read_json(SESSION_OVERLAY)
    nonmock_smoke = read_json(NONMOCK_SMOKE)
    nonmock_final = read_json(NONMOCK_FINAL)
    actor = parse_actor_layer(actor_layer_path(session))
    tokens = read_jsonl(TOKENS_JSONL)
    class_counts = token_class_counts(tokens)
    frames = benchmark.get("frames", []) if isinstance(benchmark.get("frames"), list) else []
    scenarios = benchmark.get("scenarios", []) if isinstance(benchmark.get("scenarios"), list) else []
    summary = benchmark.get("summary", {}) or {}
    prim_status = session.get("prim_status", {}) or {}
    google_tiles = bool(summary.get("google_tiles_all_valid")) or bool(
        (prim_status.get("/Google_Photorealistic_3D_Tiles", {}) or {}).get("valid")
    )
    terrain = bool(summary.get("terrain_all_valid")) or bool(
        (prim_status.get("/Cesium_World_Terrain", {}) or {}).get("valid")
    )
    fake_city = bool(session.get("substitute_city_geometry_created")) or bool(actor.get("fake_city_keyword_found"))
    actor_classes = set(actor.get("actor_classes", []))
    vehicle_actor_ok = bool(actor_classes.intersection({"car", "van", "truck", "bus"}))
    person_actor_ok = bool(actor_classes.intersection({"pedestrian", "person", "people"}))
    camera_prims = sorted({str(frame.get("camera_prim", "")) for frame in frames if frame.get("camera_prim")})
    altitudes = [float(frame.get("altitude_m", 0.0) or 0.0) for frame in frames]
    yolo_tokens_ok = int(detector.get("token_count", 0) or 0) > 0 and len(tokens) > 0
    yolo_token_cameras_ok = all((token.get("metadata", {}) or {}).get("camera_prim") for token in tokens) if tokens else False
    detected_person_count = sum(class_counts.get(name, 0) for name in ["pedestrian", "person", "people"])
    lowconf_classes = Counter(lowconf_detector.get("tokens_by_class", {}) or {})
    lowconf_person_count = sum(int(lowconf_classes.get(name, 0) or 0) for name in ["pedestrian", "person", "people"])
    threed = threed_status(read_csv(THREED_COMPARISON), benchmark)
    tiny = tiny_person_summary(read_csv(TINYPERSON_SUMMARY))
    checks = [
        {
            "name": "real_cesium_stage",
            "status": pass_bool(bool(benchmark) and google_tiles and terrain and not fake_city),
            "evidence": f"google_tiles={google_tiles}, terrain={terrain}, fake_city={fake_city}",
        },
        {
            "name": "visdrone_actor_overlay",
            "status": pass_bool(actor.get("exists", False) and actor.get("object_count", 0) >= 6 and vehicle_actor_ok and person_actor_ok),
            "evidence": f"objects={actor.get('object_count')}, classes={','.join(actor.get('actor_classes', []))}",
        },
        {
            "name": "multi_uav_markers_and_cameras",
            "status": pass_bool(actor.get("uav_count", 0) >= 3 and len(camera_prims) >= 3),
            "evidence": f"uav_markers={actor.get('uav_count')}, capture_cameras={len(camera_prims)}",
        },
        {
            "name": "real_capture_rgb_depth_pose",
            "status": pass_bool(len(scenarios) == 3 and len(frames) == 9 and min(altitudes or [0]) >= 140 and max(altitudes or [999]) <= 160),
            "evidence": f"scenarios={len(scenarios)}, frames={len(frames)}, altitude_range={min(altitudes or [0])}-{max(altitudes or [0])}m",
        },
        {
            "name": "safr_yolo_from_uav_views",
            "status": pass_bool(yolo_tokens_ok and yolo_token_cameras_ok),
            "evidence": f"tokens={detector.get('token_count')}, device={detector.get('device')}, classes={dict(class_counts)}",
        },
        {
            "name": "pedestrian_detection_from_current_views",
            "status": "PASS"
            if detected_person_count > 0
            else "WARN"
            if person_actor_ok or lowconf_person_count > 0
            else "FAIL",
            "evidence": (
                f"pedestrian/person actors={person_actor_ok}, main_conf015_person_tokens={detected_person_count}, "
                f"supp_conf005_person_tokens={lowconf_person_count}. "
                "Use the low-confidence run only as a diagnostic/qualitative candidate unless promoted by a fixed protocol."
            ),
        },
        {
            "name": "crossview_evidence_graph",
            "status": pass_bool(crossview.get("status") == "marinecity_crossview_evidence_graph_smoke_ready"),
            "evidence": f"hypotheses={crossview.get('hypothesis_count')}, multi_view={crossview.get('multi_view_hypothesis_count')}",
        },
        {
            "name": "neural_3d_completion_benchmark",
            "status": "PASS" if threed["status"] == "complete" else "PENDING",
            "evidence": threed["claiming_rule"],
        },
        {
            "name": "external_llm_reasoner",
            "status": "PASS"
            if bool(nonmock_final.get("external_provider_replication_ready")) and nonmock_smoke.get("status", "").endswith("complete")
            else "PENDING",
            "evidence": (
                f"49-prompt external_ready={nonmock_final.get('external_provider_replication_ready')}, "
                f"23-prompt status={nonmock_smoke.get('status')}"
            ),
        },
        {
            "name": "tinyperson_640_supplement",
            "status": "PASS" if tiny.get("status") == "complete_supplementary_stress_test" else "PENDING",
            "evidence": tiny.get("claiming_rule", ""),
        },
    ]
    status = "marinecity_system_integration_smoke_ready_with_pending_final_gates"
    if any(row["status"] == "FAIL" for row in checks):
        status = "marinecity_system_integration_needs_attention"
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "checks": checks,
        "opened_stage": {
            "stage_path": scenarios[0].get("stage_path") if scenarios else session.get("base_stage"),
            "root_layer": scenarios[0].get("root_layer") if scenarios else session.get("root_layer"),
            "georeference_readback": scenarios[0].get("georeference_readback") if scenarios else session.get("georeference_readback"),
            "google_tiles": google_tiles,
            "terrain": terrain,
            "fake_or_substitute_city": fake_city,
        },
        "actors": actor,
        "captures": {
            "scenario_count": len(scenarios),
            "frame_count": len(frames),
            "camera_prims": camera_prims,
            "altitude_range_m": [min(altitudes), max(altitudes)] if altitudes else [],
            "mean_rgb_black_ratio": summary.get("mean_rgb_black_ratio"),
            "mean_depth_finite_ratio": summary.get("mean_depth_finite_ratio"),
        },
        "detector": {
            "status": detector.get("status", "missing"),
            "weights": detector.get("weights", ""),
            "device": detector.get("device", ""),
            "imgsz": detector.get("imgsz"),
            "conf": detector.get("conf"),
            "frame_count": detector.get("frame_count"),
            "token_count": detector.get("token_count"),
            "tokens_by_class": dict(class_counts),
            "tokens_by_uav": detector.get("tokens_by_uav", {}),
            "preview_contact_sheet": detector.get("preview_contact_sheet", ""),
            "supp_lowconf_conf": lowconf_detector.get("conf"),
            "supp_lowconf_token_count": lowconf_detector.get("token_count"),
            "supp_lowconf_tokens_by_class": lowconf_detector.get("tokens_by_class", {}),
            "supp_lowconf_preview_contact_sheet": lowconf_detector.get("preview_contact_sheet", ""),
        },
        "crossview_graph": crossview,
        "three_d_completion": threed,
        "llm_reasoner": {
            "real_capture_nonmock_smoke_status": nonmock_smoke.get("status", "missing"),
            "final_49_prompt_status": nonmock_final.get("status", "missing"),
            "external_provider_replication_ready": bool(nonmock_final.get("external_provider_replication_ready")),
            "claiming_rule": "AeroGraph is the drone-specific reasoner name. Current non-mock external-provider validation remains pending.",
        },
        "tinyperson_640": tiny,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# MarineCity System Integration Check",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        "",
        "## Gate Summary",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in report["checks"]:
        lines.append(f"| {row['name']} | {row['status']} | {row['evidence']} |")
    opened = report["opened_stage"]
    captures = report["captures"]
    detector = report["detector"]
    lines.extend(
        [
            "",
            "## Real-Cesium Stage",
            "",
            f"- Stage path: `{opened.get('stage_path')}`",
            f"- Root layer: `{opened.get('root_layer')}`",
            f"- Georeference readback: `{opened.get('georeference_readback')}`",
            f"- Google Photorealistic 3D Tiles: `{opened.get('google_tiles')}`",
            f"- Cesium terrain: `{opened.get('terrain')}`",
            f"- Fake/substitute city geometry: `{opened.get('fake_or_substitute_city')}`",
            "",
            "## Actors, UAVs, And Captures",
            "",
            f"- Actor layer: `{report['actors'].get('path')}`",
            f"- Actor classes: `{report['actors'].get('actor_classes')}`",
            f"- Object count: `{report['actors'].get('object_count')}`",
            f"- UAV marker count: `{report['actors'].get('uav_count')}`",
            f"- Camera prim count in captured frames: `{len(captures.get('camera_prims', []))}`",
            f"- Capture scenarios/frames: `{captures.get('scenario_count')}` / `{captures.get('frame_count')}`",
            f"- UAV camera altitude range: `{captures.get('altitude_range_m')}` m",
            f"- Mean RGB black ratio / depth finite ratio: `{captures.get('mean_rgb_black_ratio')}` / `{captures.get('mean_depth_finite_ratio')}`",
            "",
            "## SAFR-YOLO Smoke",
            "",
            f"- Detector status: `{detector.get('status')}`",
            f"- Device/img/conf: `{detector.get('device')}` / `{detector.get('imgsz')}` / `{detector.get('conf')}`",
            f"- Frame/token count: `{detector.get('frame_count')}` / `{detector.get('token_count')}`",
            f"- Tokens by class: `{detector.get('tokens_by_class')}`",
            f"- Preview sheet: `{detector.get('preview_contact_sheet')}`",
            "",
            "## Pending Final Gates",
            "",
            f"- 3D completion: `{report['three_d_completion'].get('status')}`; {report['three_d_completion'].get('claiming_rule')}",
            f"- LLM reasoner: `{report['llm_reasoner'].get('final_49_prompt_status')}`; external provider ready `{report['llm_reasoner'].get('external_provider_replication_ready')}`",
            f"- TinyPerson: `{report['tinyperson_640'].get('status')}`; best `{report['tinyperson_640'].get('best_method')}` AP `{report['tinyperson_640'].get('best_ap')}`; ours AP `{report['tinyperson_640'].get('ours_ap')}`",
            "",
            "Claiming rule: report the current MarineCity results as a real-Cesium system smoke/protocol validation. Do not claim completed neural 3D generation or external LLM validation until the pending gates pass.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    json_path = LIVE_DIR / "marinecity_system_integration_check.json"
    md_path = LIVE_DIR / "marinecity_system_integration_check.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(md_path, report)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
