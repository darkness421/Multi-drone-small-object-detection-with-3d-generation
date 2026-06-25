"""Build a current ACCV workflow status snapshot from live artifacts."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = REPO_ROOT / "outputs/reports/live"
FINAL_TABLE = REPO_ROOT / "outputs/reports/final_detector_table_preview.csv"
UAVDET_ROOT = REPO_ROOT / "outputs/detectors/required_related_work_reimplementations"
UAVDET_SEEDS = [42, 123, 2026]
UAVDET_LOG = REPO_ROOT / "outputs/logs/required_related_work_models/uavdet_inspired_after_required.log"
TINYPERSON_LOG = REPO_ROOT / "outputs/logs/tinyperson_640/queue.log"
SYSTEM_MANIFEST = LIVE_DIR / "marinecity_system_test_10plus/manifest.json"
PROMPT_MANIFEST = LIVE_DIR / "aerograph_prompt_pack/manifest.json"
AEROGRAPH_DRY_RUN = REPO_ROOT / "outputs/reasoning/aerograph_prompt_pack_eval_dry_run/manifest.json"
SIM_DASHBOARD = LIVE_DIR / "marinecity_simulation_dashboard.png"
TRAIN_DASHBOARD = LIVE_DIR / "training_dashboard.png"
AEROGRAPH_PLACEHOLDER_TABLE = REPO_ROOT / "paper/tables/aerograph_reasoner_results_placeholder.tex"
MARINECITY_SESSION_OVERLAY_STATUS = Path("/home/oem/UAV/uav_marinecity/outputs/uavmarine_session_overlay_status_s0.json")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def last_log_line(path: Path) -> str:
    if not path.exists():
        return "missing"
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    return lines[-1] if lines else "empty"


def _f1(row: dict[str, str]) -> float:
    precision = float(row.get("metrics/precision(B)", 0.0) or 0.0)
    recall = float(row.get("metrics/recall(B)", 0.0) or 0.0)
    return 2 * precision * recall / max(1e-9, precision + recall)


def seed_from_path(path: Path) -> int | None:
    match = re.search(r"seed(\d+)", str(path))
    return int(match.group(1)) if match else None


def uavdet_result_files() -> dict[int, Path]:
    files: dict[int, Path] = {}
    if not UAVDET_ROOT.exists():
        return files
    for path in UAVDET_ROOT.glob("*uavdet_inspired_reimpl_visdrone_seed*/ultralytics/results.csv"):
        seed = seed_from_path(path)
        if seed is None:
            continue
        existing = files.get(seed)
        if existing is None or path.stat().st_mtime > existing.stat().st_mtime:
            files[seed] = path
    return files


def uavdet_log_state() -> dict[str, Any]:
    if not UAVDET_LOG.exists():
        return {"running_seed": None, "finished_seeds": []}
    running_seed: int | None = None
    finished: set[int] = set()
    for line in UAVDET_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        start = re.search(r"START UAVDet .* seed=(\d+)", line)
        finish = re.search(r"FINISH UAVDet .* seed=(\d+)", line)
        if start:
            running_seed = int(start.group(1))
        if finish:
            seed = int(finish.group(1))
            finished.add(seed)
            if running_seed == seed:
                running_seed = None
    return {"running_seed": running_seed, "finished_seeds": sorted(finished)}


def summarize_uavdet_seed(seed: int, path: Path) -> dict[str, Any]:
    rows = read_csv(path)
    if not rows:
        return {"seed": seed, "status": "missing_rows", "results": str(path.relative_to(REPO_ROOT))}
    best = max(rows, key=lambda row: float(row.get("metrics/mAP50-95(B)", 0.0) or 0.0))
    latest = rows[-1]
    latest_epoch = int(float(latest.get("epoch", 0) or 0))
    best_epoch = int(float(best.get("epoch", 0) or 0))
    return {
        "seed": seed,
        "status": "has_results",
        "results": str(path.relative_to(REPO_ROOT)),
        "latest_epoch": latest_epoch,
        "latest_ap": float(latest.get("metrics/mAP50-95(B)", 0.0) or 0.0),
        "latest_ap50": float(latest.get("metrics/mAP50(B)", 0.0) or 0.0),
        "latest_f1": _f1(latest),
        "best_epoch": best_epoch,
        "best_ap": float(best.get("metrics/mAP50-95(B)", 0.0) or 0.0),
        "best_ap50": float(best.get("metrics/mAP50(B)", 0.0) or 0.0),
        "best_precision": float(best.get("metrics/precision(B)", 0.0) or 0.0),
        "best_recall": float(best.get("metrics/recall(B)", 0.0) or 0.0),
        "epochs_since_best": max(0, latest_epoch - best_epoch),
        "complete_hint": latest_epoch >= 99,
    }


def latest_uavdet() -> dict[str, Any]:
    result_files = uavdet_result_files()
    log_state = uavdet_log_state()
    running_seed = log_state["running_seed"]
    finished_seeds = set(log_state["finished_seeds"])
    seed_rows: list[dict[str, Any]] = []
    for seed in UAVDET_SEEDS:
        path = result_files.get(seed)
        if path:
            row = summarize_uavdet_seed(seed, path)
            if seed in finished_seeds:
                row["status"] = "finished"
                row["complete_hint"] = True
            elif seed == running_seed:
                row["status"] = "running"
            seed_rows.append(row)
        elif seed == running_seed:
            seed_rows.append({"seed": seed, "status": "running_waiting_for_first_epoch", "results": ""})
        else:
            seed_rows.append({"seed": seed, "status": "pending", "results": ""})
    seeds_with_results = [row for row in seed_rows if row.get("status") == "has_results"]
    results_or_finished = [row for row in seed_rows if row.get("best_ap") is not None]
    started_seeds = [
        int(row["seed"])
        for row in seed_rows
        if row.get("status") in {"has_results", "finished", "running", "running_waiting_for_first_epoch"}
    ]
    completed_seeds = [
        int(row["seed"])
        for row in seed_rows
        if row.get("status") == "finished" or bool(row.get("complete_hint"))
    ]
    best_row = max(results_or_finished, key=lambda row: float(row.get("best_ap", 0.0) or 0.0), default={})
    return {
        "status": "all_seed_results_present" if len(completed_seeds) == len(UAVDET_SEEDS) else "running_or_incomplete",
        "planned_seeds": UAVDET_SEEDS,
        "seeds_with_results": [int(row["seed"]) for row in results_or_finished],
        "started_seeds": started_seeds,
        "started_seed_count": len(started_seeds),
        "completed_seed_count": len(completed_seeds),
        "completed_seeds": completed_seeds,
        "total_seed_count": len(UAVDET_SEEDS),
        "active_seed": running_seed,
        "seed_rows": seed_rows,
        "best_seed": best_row.get("seed"),
        "best_epoch": best_row.get("best_epoch"),
        "best_ap": best_row.get("best_ap"),
        "best_ap50": best_row.get("best_ap50"),
        "best_precision": best_row.get("best_precision"),
        "best_recall": best_row.get("best_recall"),
    }


def detector_rows(limit: int = 8) -> list[dict[str, Any]]:
    rows = read_csv(FINAL_TABLE)
    selected = []
    for row in rows[:limit]:
        selected.append(
            {
                "rank": row.get("rank", ""),
                "method": row.get("method", ""),
                "group": row.get("group", ""),
                "ap": float(row.get("AP", 0.0) or 0.0),
                "ap50": float(row.get("AP50", 0.0) or 0.0),
                "f1": float(row.get("F1", 0.0) or 0.0),
                "params_m": float(row.get("params_m", 0.0) or 0.0),
                "seeds": row.get("seeds", ""),
                "note": row.get("note", ""),
            }
        )
    return selected


def build_snapshot() -> dict[str, Any]:
    detectors = detector_rows()
    ours = next((row for row in detectors if row["method"].startswith("Ours:")), {})
    yolo11 = next((row for row in detectors if row["method"] == "YOLOv11l"), {})
    uavdet = latest_uavdet()
    prompt_manifest = read_json(PROMPT_MANIFEST)
    system_manifest = read_json(SYSTEM_MANIFEST)
    dry_run = read_json(AEROGRAPH_DRY_RUN)
    session_overlay = read_json(MARINECITY_SESSION_OVERLAY_STATUS)
    prim_status = session_overlay.get("prim_status", {}) or {}
    georef = session_overlay.get("georeference_readback", {}) or {}
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "detector": {
            "paper_facing_top_rows": detectors,
            "ours": ours,
            "yolov11l": yolo11,
            "uavdet_queue": uavdet,
            "ours_minus_yolov11l_ap": round(float(ours.get("ap", 0.0)) - float(yolo11.get("ap", 0.0)), 6)
            if ours and yolo11
            else None,
            "ours_minus_uavdet_best_ap": round(float(ours.get("ap", 0.0)) - float(uavdet.get("best_ap", 0.0)), 6)
            if ours and uavdet.get("best_ap") is not None
            else None,
        },
        "marinecity_system": {
            "scenario_count": system_manifest.get("scenario_count"),
            "token_level_test_count": system_manifest.get("token_level_test_count"),
            "artifact_status": system_manifest.get("status"),
            "dashboard": str(SIM_DASHBOARD.relative_to(REPO_ROOT)),
            "live_overlay_status": session_overlay.get("status"),
            "camera_set": session_overlay.get("camera_set"),
            "camera_profile": session_overlay.get("camera_profile"),
            "active_camera_path": session_overlay.get("active_camera_path"),
            "viewer160_eye": session_overlay.get("viewer160_eye"),
            "viewer160_target": session_overlay.get("viewer160_target"),
            "georeference_height": georef.get("cesium:georeferenceOrigin:height"),
            "google_photorealistic_tiles_valid": (prim_status.get("/Google_Photorealistic_3D_Tiles", {}) or {}).get("valid"),
            "cesium_world_terrain_valid": (prim_status.get("/Cesium_World_Terrain", {}) or {}).get("valid"),
            "substitute_city_geometry_created": session_overlay.get("substitute_city_geometry_created"),
        },
        "aerograph": {
            "prompt_pack_status": prompt_manifest.get("status"),
            "total_prompts": prompt_manifest.get("total_prompts"),
            "sample_prompts": prompt_manifest.get("sample_prompts"),
            "class_counts": prompt_manifest.get("class_counts"),
            "dry_run_status": dry_run.get("status"),
            "dry_run_summary": dry_run.get("summary"),
            "non_mock_status": "pending_provider_execution",
        },
        "queues": {
            "uavdet_log_tail": last_log_line(UAVDET_LOG),
            "tinyperson_log_tail": last_log_line(TINYPERSON_LOG),
            "tiny_person_gate": "waiting_for_uavdet_3seed_marker",
        },
        "dashboards": {
            "training": str(TRAIN_DASHBOARD.relative_to(REPO_ROOT)),
            "marinecity": str(SIM_DASHBOARD.relative_to(REPO_ROOT)),
        },
        "paper_ready_artifacts": {
            "detector_table": "paper/tables/main_detector_comparison_table.tex",
            "marinecity_system_table": "paper/tables/marinecity_system_scenario_table.tex",
            "aerograph_placeholder_table": str(AEROGRAPH_PLACEHOLDER_TABLE.relative_to(REPO_ROOT)),
            "aerograph_placeholder_exists": AEROGRAPH_PLACEHOLDER_TABLE.exists(),
        },
    }


def md_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Rank | Model | AP | AP50 | F1 | Params | Seeds |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['rank']} | {row['method']} | {row['ap']:.4f} | {row['ap50']:.4f} | "
            f"{row['f1']:.4f} | {row['params_m']:.2f}M | {row['seeds']} |"
        )
    return lines


def uavdet_seed_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Seed | Status | Latest Epoch | Best Epoch | Best AP | Best AP50 | Epochs Since Best |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row.get("best_ap") is None:
            lines.append(f"| {row.get('seed')} | {row.get('status')} | - | - | - | - | - |")
            continue
        lines.append(
            f"| {row['seed']} | {row['status']} | {row['latest_epoch']} | {row['best_epoch']} | "
            f"{row['best_ap']:.4f} | {row['best_ap50']:.4f} | {row['epochs_since_best']} |"
        )
    return lines


def write_markdown(path: Path, snapshot: dict[str, Any]) -> None:
    detector = snapshot["detector"]
    uavdet = detector["uavdet_queue"]
    system = snapshot["marinecity_system"]
    aerograph = snapshot["aerograph"]
    queues = snapshot["queues"]
    lines = [
        "# ACCV Workflow Status Snapshot",
        "",
        f"Updated: `{snapshot['updated_at_kst']}`",
        "",
        "## Detector Status",
        "",
        f"- Selected detector: `{detector['ours'].get('method', 'missing')}`",
        f"- Ours vs YOLOv11l AP gap: `{detector.get('ours_minus_yolov11l_ap')}`",
        f"- Ours vs UAVDet best-seed AP gap: `{detector.get('ours_minus_uavdet_best_ap')}`",
        f"- UAVDet queue: `{uavdet.get('status')}`; seeds started `{uavdet.get('started_seed_count')}/{uavdet.get('total_seed_count')}`; seeds completed `{uavdet.get('completed_seed_count')}/{uavdet.get('total_seed_count')}`",
        f"- UAVDet active seed: `{uavdet.get('active_seed')}`; best seed: `{uavdet.get('best_seed')}`; best AP: `{uavdet.get('best_ap')}`; best AP50: `{uavdet.get('best_ap50')}`",
        "",
        *md_table(detector["paper_facing_top_rows"]),
        "",
        "### UAVDet 3-Seed Queue",
        "",
        *uavdet_seed_table(uavdet.get("seed_rows", [])),
        "",
        "## MarineCity System",
        "",
        f"- Real-Cesium scenario count: `{system.get('scenario_count')}`",
        f"- Token-level system tests: `{system.get('token_level_test_count')}`",
        f"- Artifact status: `{system.get('artifact_status')}`",
        f"- Live overlay: `{system.get('live_overlay_status')}`; camera set `{system.get('camera_set')}`; profile `{system.get('camera_profile')}`",
        f"- Real Cesium: Google tiles `{system.get('google_photorealistic_tiles_valid')}`, terrain `{system.get('cesium_world_terrain_valid')}`, fake city `{system.get('substitute_city_geometry_created')}`",
        f"- Viewer160 camera: eye `{system.get('viewer160_eye')}`, target `{system.get('viewer160_target')}`, georef height `{system.get('georeference_height')}`",
        f"- Dashboard: `{system.get('dashboard')}`",
        "",
        "## AeroGraph Reasoner",
        "",
        f"- Prompt pack: `{aerograph.get('prompt_pack_status')}`, prompts `{aerograph.get('total_prompts')}`",
        f"- Prompt class counts: `{aerograph.get('class_counts')}`",
        f"- Dry-run status: `{aerograph.get('dry_run_status')}`",
        f"- Non-mock status: `{aerograph.get('non_mock_status')}`",
        "",
        "## Queue Gates",
        "",
        f"- UAVDet log tail: `{queues.get('uavdet_log_tail')}`",
        f"- TinyPerson log tail: `{queues.get('tinyperson_log_tail')}`",
        f"- TinyPerson gate: `{queues.get('tiny_person_gate')}`",
        "",
        "## Dashboard Links",
        "",
        f"- Training dashboard: `{snapshot['dashboards']['training']}`",
        f"- MarineCity dashboard: `{snapshot['dashboards']['marinecity']}`",
        "",
        "## Paper-Ready Artifacts",
        "",
        f"- Detector table: `{snapshot['paper_ready_artifacts']['detector_table']}`",
        f"- MarineCity system table: `{snapshot['paper_ready_artifacts']['marinecity_system_table']}`",
        f"- AeroGraph placeholder table: `{snapshot['paper_ready_artifacts']['aerograph_placeholder_table']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    snapshot = build_snapshot()
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    json_path = LIVE_DIR / "accv_workflow_status_snapshot.json"
    md_path = LIVE_DIR / "accv_workflow_status_snapshot.md"
    json_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(md_path, snapshot)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
