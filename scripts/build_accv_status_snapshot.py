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
TINYPERSON_TRANSFER_LOG = REPO_ROOT / "outputs/logs/tinyperson_640_transfer/queue.log"
TINYPERSON_EVAL_SWEEP_LOG = REPO_ROOT / "outputs/logs/tinyperson_eval_imgsz_sweep/queue.log"
SYSTEM_MANIFEST = LIVE_DIR / "marinecity_system_test_10plus/manifest.json"
MARINECITY_DETECTOR_REASONER_SMOKE = LIVE_DIR / "marinecity_detector_reasoner_smoke.json"
MARINECITY_CROSSVIEW_GRAPH_SUMMARY = REPO_ROOT / "outputs/graphs/marinecity_crossview_evidence_graph/summary.json"
PROMPT_MANIFEST = LIVE_DIR / "aerograph_prompt_pack/manifest.json"
REAL_CAPTURE_PROMPT_MANIFEST = LIVE_DIR / "aerograph_real_capture_prompt_pack/manifest.json"
REAL_CAPTURE_PROMPT_WEB_BATCH_MANIFEST = LIVE_DIR / "aerograph_real_capture_prompt_pack/web_batches/manifest.json"
REAL_CAPTURE_WEB_COLLECTION_PACKET = LIVE_DIR / "aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.md"
REAL_CAPTURE_WEB_COLLECTION_CHECKLIST = LIVE_DIR / "aerograph_real_capture_prompt_pack/aerograph_web_collection_checklist.csv"
REAL_CAPTURE_PROMPT_DRYRUN = REPO_ROOT / "outputs/reasoning/aerograph_real_capture_eval_dryrun/manifest.json"
REAL_CAPTURE_NONMOCK_SMOKE_STATUS = LIVE_DIR / "aerograph_real_capture_nonmock_smoke_status.json"
AEROGRAPH_WEB_BATCH_MANIFEST = LIVE_DIR / "aerograph_prompt_pack/web_batches/manifest.json"
AEROGRAPH_DRY_RUN = REPO_ROOT / "outputs/reasoning/aerograph_prompt_pack_eval_dryrun_latest/manifest.json"
AEROGRAPH_TABLE_MANIFEST = LIVE_DIR / "aerograph_reasoner_table_manifest.json"
AEROGRAPH_NONMOCK_READINESS = LIVE_DIR / "aerograph_nonmock_readiness_status.json"
SIM_DASHBOARD = LIVE_DIR / "marinecity_simulation_dashboard.png"
TRAIN_DASHBOARD = LIVE_DIR / "training_dashboard.png"
READINESS_AUDIT = LIVE_DIR / "accv_research_package_readiness_audit.md"
TRACKED_READINESS_AUDIT = REPO_ROOT / "docs/accv_research_package_readiness_audit_2026-06-25.md"
PAPER_ARTIFACT_MANIFEST = REPO_ROOT / "paper/figures/results/paper_artifact_readiness_manifest.md"
PAPER_ARTIFACT_CHECK = LIVE_DIR / "paper_artifact_readiness_check.json"
LATEX_PATCH_CHECK = LIVE_DIR / "latex_patch_integrity_check.json"
MARINECITY_QUALITATIVE_GATE = LIVE_DIR / "marinecity_qualitative_gate.json"
MARINECITY_CLEAN_RECAPTURE_PLAN = LIVE_DIR / "marinecity_clean_recapture_plan.json"
MARINECITY_SYSTEM_INTEGRATION_CHECK = LIVE_DIR / "marinecity_system_integration_check.json"
MARINECITY_3D_COMPLETION_READINESS = LIVE_DIR / "marinecity_3d_completion_readiness.json"
MARINECITY_NEURAL3D_DATASET_EXPORT = LIVE_DIR / "marinecity_neural3d_dataset_export.json"
MARINECITY_DEPTH_POINTCLOUD_SMOKE = LIVE_DIR / "marinecity_depth_pointcloud_smoke.json"
MARINECITY_3D_RUNNER_PREFLIGHT = LIVE_DIR / "marinecity_3d_runner_preflight.json"
AEROGRAPH_COLLECTION_PLAN = REPO_ROOT / "docs/aerograph_nonmock_collection_plan.md"
AEROGRAPH_PLACEHOLDER_TABLE = REPO_ROOT / "paper/tables/aerograph_reasoner_results_placeholder.tex"
MARINECITY_SESSION_OVERLAY_STATUS = Path("/home/oem/UAV/uav_marinecity/outputs/uavmarine_session_overlay_status_s0.json")
MARINECITY_TARGET_GEOREF_HEIGHT_M = 160
UAV_ALTITUDE_POLICY = {
    "band_m": [140, 160],
    "default_m": 160,
    "user_locked_review_height_m": 160,
    "verified_viewer160_recapture_m": {
        "uav_01": 140,
        "uav_02": 150,
        "uav_03": 160,
    },
    "note": "Use 140-160 m for UAV/camera observation; keep CesiumGeoreference readback logged separately.",
}


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


def tiny_person_gate_state() -> str:
    if not TINYPERSON_LOG.exists():
        return "not_started"
    lines = [
        line.strip()
        for line in TINYPERSON_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip()
    ]
    for line in reversed(lines):
        if "QUEUE_FINISHED TinyPerson 640 stress test" in line:
            return "finished_tinyperson_640_stress_test"
        if "Starting TinyPerson 640 job=" in line:
            match = re.search(r"job=([^ ]+) seed=(\d+)", line)
            if match:
                return f"running_tinyperson_640_{match.group(1)}_seed{match.group(2)}"
            return "running_tinyperson_640"
        if "Collecting TinyPerson 640 results" in line:
            return "collecting_tinyperson_640"
        if "TRAIN_OK TinyPerson job=" in line:
            match = re.search(r"job=([^ ]+) seed=(\d+)", line)
            if match:
                return f"last_train_ok_tinyperson_640_{match.group(1)}_seed{match.group(2)}"
            return "last_train_ok_tinyperson_640"
        if "TRAIN_FAILED TinyPerson job=" in line:
            match = re.search(r"job=([^ ]+) seed=(\d+)", line)
            if match:
                return f"last_train_failed_tinyperson_640_{match.group(1)}_seed{match.group(2)}"
            return "last_train_failed_tinyperson_640"
        if "TinyPerson data is ready" in line:
            return "data_ready_tinyperson_640"
        if "Waiting for wait_uavdet_1280" in line:
            return "waiting_for_uavdet_1280_marker"
    return "log_present_state_unknown"


def tiny_person_transfer_gate_state() -> str:
    if not TINYPERSON_TRANSFER_LOG.exists():
        return "not_started"
    lines = [
        line.strip()
        for line in TINYPERSON_TRANSFER_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip()
    ]
    for line in reversed(lines):
        if "QUEUE_FINISHED TinyPerson Ours transfer fine-tune" in line:
            return "finished_tinyperson_ours_transfer"
        if "Collecting TinyPerson transfer results" in line:
            return "collecting_tinyperson_ours_transfer"
        if "FINISH TinyPerson transfer seed=" in line:
            match = re.search(r"seed=(\d+)", line)
            return f"last_finished_tinyperson_ours_transfer_seed{match.group(1)}" if match else "last_finished_tinyperson_ours_transfer"
        if "START TinyPerson transfer seed=" in line:
            match = re.search(r"seed=(\d+)", line)
            return f"running_tinyperson_ours_transfer_seed{match.group(1)}" if match else "running_tinyperson_ours_transfer"
    return "log_present_state_unknown"


def tiny_person_eval_sweep_gate_state() -> str:
    if not TINYPERSON_EVAL_SWEEP_LOG.exists():
        return "not_started"
    lines = [
        line.strip()
        for line in TINYPERSON_EVAL_SWEEP_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip()
    ]
    for line in reversed(lines):
        if "QUEUE_FINISHED TinyPerson eval-only input-size sweep" in line:
            return "finished_tinyperson_eval_imgsz_sweep"
        if "FINISH TinyPerson eval sweep method=" in line:
            match = re.search(r"method=([^ ]+) seed=(\d+) imgsz=(\d+)", line)
            if match:
                return f"last_finished_eval_sweep_{match.group(1)}_seed{match.group(2)}_img{match.group(3)}"
            return "last_finished_tinyperson_eval_sweep"
        if "START TinyPerson eval sweep method=" in line:
            match = re.search(r"method=([^ ]+) seed=(\d+) imgsz=(\d+)", line)
            if match:
                return f"running_eval_sweep_{match.group(1)}_seed{match.group(2)}_img{match.group(3)}"
            return "running_tinyperson_eval_sweep"
    return "log_present_state_unknown"


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
    uavdet_table = next((row for row in detectors if row["method"].startswith("UAVDet")), {})
    uavdet = latest_uavdet()
    prompt_manifest = read_json(PROMPT_MANIFEST)
    real_capture_prompt_manifest = read_json(REAL_CAPTURE_PROMPT_MANIFEST)
    real_capture_web_batch_manifest = read_json(REAL_CAPTURE_PROMPT_WEB_BATCH_MANIFEST)
    real_capture_dryrun = read_json(REAL_CAPTURE_PROMPT_DRYRUN)
    real_capture_nonmock_smoke = read_json(REAL_CAPTURE_NONMOCK_SMOKE_STATUS)
    web_batch_manifest = read_json(AEROGRAPH_WEB_BATCH_MANIFEST)
    system_manifest = read_json(SYSTEM_MANIFEST)
    detector_reasoner_smoke = read_json(MARINECITY_DETECTOR_REASONER_SMOKE)
    crossview_graph = read_json(MARINECITY_CROSSVIEW_GRAPH_SUMMARY)
    dry_run = read_json(AEROGRAPH_DRY_RUN)
    aerograph_table = read_json(AEROGRAPH_TABLE_MANIFEST)
    aerograph_nonmock = read_json(AEROGRAPH_NONMOCK_READINESS)
    aerograph_coverage = (
        aerograph_nonmock.get("effective_response_coverage")
        or aerograph_nonmock.get("manual_response_coverage", {})
        or {}
    )
    paper_check = read_json(PAPER_ARTIFACT_CHECK)
    latex_check = read_json(LATEX_PATCH_CHECK)
    marinecity_qual = read_json(MARINECITY_QUALITATIVE_GATE)
    marinecity_recapture_plan = read_json(MARINECITY_CLEAN_RECAPTURE_PLAN)
    marinecity_integration = read_json(MARINECITY_SYSTEM_INTEGRATION_CHECK)
    marinecity_3d = read_json(MARINECITY_3D_COMPLETION_READINESS)
    marinecity_neural3d_dataset = read_json(MARINECITY_NEURAL3D_DATASET_EXPORT)
    marinecity_pointcloud = read_json(MARINECITY_DEPTH_POINTCLOUD_SMOKE)
    marinecity_runner_preflight = read_json(MARINECITY_3D_RUNNER_PREFLIGHT)
    session_overlay = read_json(MARINECITY_SESSION_OVERLAY_STATUS)
    prim_status = session_overlay.get("prim_status", {}) or {}
    georef = session_overlay.get("georeference_readback", {}) or {}
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "detector": {
            "paper_facing_top_rows": detectors,
            "ours": ours,
            "yolov11l": yolo11,
            "uavdet_final_table": uavdet_table,
            "uavdet_queue": uavdet,
            "ours_minus_yolov11l_ap": round(float(ours.get("ap", 0.0)) - float(yolo11.get("ap", 0.0)), 6)
            if ours and yolo11
            else None,
            "ours_minus_uavdet_final_ap": round(float(ours.get("ap", 0.0)) - float(uavdet_table.get("ap", 0.0)), 6)
            if ours and uavdet_table
            else None,
            "ours_minus_uavdet_queue_best_ap": round(float(ours.get("ap", 0.0)) - float(uavdet.get("best_ap", 0.0)), 6)
            if ours and uavdet.get("best_ap") is not None
            else None,
        },
        "marinecity_system": {
            "scenario_count": system_manifest.get("scenario_count"),
            "token_level_test_count": system_manifest.get("token_level_test_count"),
            "artifact_status": system_manifest.get("status"),
            "detector_reasoner_smoke_status": detector_reasoner_smoke.get("status"),
            "detector_reasoner_smoke_tokens": detector_reasoner_smoke.get("total_tokens"),
            "detector_reasoner_smoke_rows": detector_reasoner_smoke.get("rows", []),
            "detector_reasoner_smoke_report": str(MARINECITY_DETECTOR_REASONER_SMOKE.with_suffix(".md").relative_to(REPO_ROOT)),
            "detector_reasoner_smoke_contact_sheet": detector_reasoner_smoke.get("paper_contact_sheet"),
            "crossview_graph_status": crossview_graph.get("status"),
            "crossview_graph_claim_level": crossview_graph.get("claim_level"),
            "crossview_graph_token_count": crossview_graph.get("token_count"),
            "crossview_graph_hypothesis_count": crossview_graph.get("hypothesis_count"),
            "crossview_graph_multi_view_hypothesis_count": crossview_graph.get("multi_view_hypothesis_count"),
            "crossview_graph_support_edge_count": crossview_graph.get("support_edge_count"),
            "crossview_graph_conflict_edge_count": crossview_graph.get("conflict_edge_count"),
            "crossview_graph_missing_evidence_edge_count": crossview_graph.get("missing_evidence_edge_count"),
            "crossview_graph_report": "outputs/reports/live/marinecity_crossview_evidence_graph.md",
            "crossview_graph_table": "paper/tables/marinecity_crossview_evidence_graph_table.tex",
            "crossview_graph_figure": "paper/figures/results/marinecity_system/marinecity_crossview_evidence_graph.png",
            "integration_check_status": marinecity_integration.get("status"),
            "integration_check": str(MARINECITY_SYSTEM_INTEGRATION_CHECK.with_suffix(".md").relative_to(REPO_ROOT)),
            "integration_checks": marinecity_integration.get("checks", []),
            "integration_detector_classes": (marinecity_integration.get("detector", {}) or {}).get("tokens_by_class"),
            "integration_actor_classes": (marinecity_integration.get("actors", {}) or {}).get("actor_classes"),
            "neural_3d_completion_status": marinecity_3d.get("status"),
            "neural_3d_input_dataset_status": marinecity_neural3d_dataset.get("status"),
            "neural_3d_input_dataset_report": str(MARINECITY_NEURAL3D_DATASET_EXPORT.with_suffix(".md").relative_to(REPO_ROOT)),
            "neural_3d_input_dataset_frames": marinecity_neural3d_dataset.get("frame_count"),
            "neural_3d_input_dataset_split": {
                "train": marinecity_neural3d_dataset.get("train_frame_count"),
                "heldout": marinecity_neural3d_dataset.get("heldout_frame_count"),
            },
            "depth_pointcloud_smoke_status": marinecity_pointcloud.get("status"),
            "depth_pointcloud_smoke_report": str(MARINECITY_DEPTH_POINTCLOUD_SMOKE.with_suffix(".md").relative_to(REPO_ROOT)),
            "depth_pointcloud_point_count": marinecity_pointcloud.get("point_count"),
            "depth_pointcloud_preview": marinecity_pointcloud.get("preview"),
            "neural_3d_runner_preflight_status": marinecity_runner_preflight.get("status"),
            "neural_3d_runner_available": marinecity_runner_preflight.get("neural_runner_available"),
            "neural_3d_runner_preflight_report": str(MARINECITY_3D_RUNNER_PREFLIGHT.with_suffix(".md").relative_to(REPO_ROOT)),
            "neural_3d_metric_result_rows": marinecity_3d.get("metric_result_row_count"),
            "neural_3d_readiness_report": str(MARINECITY_3D_COMPLETION_READINESS.with_suffix(".md").relative_to(REPO_ROOT)),
            "neural_3d_claiming_rule": marinecity_3d.get("claiming_rule"),
            "dashboard": str(SIM_DASHBOARD.relative_to(REPO_ROOT)),
            "live_overlay_status": session_overlay.get("status"),
            "camera_set": session_overlay.get("camera_set"),
            "camera_profile": session_overlay.get("camera_profile"),
            "active_camera_path": session_overlay.get("active_camera_path"),
            "requested_georef_height": session_overlay.get("requested_georef_height"),
            "applied_georef_height": session_overlay.get("applied_georef_height"),
            "viewer_eye": session_overlay.get("viewer_eye") or session_overlay.get("viewer160_eye"),
            "viewer_target": session_overlay.get("viewer_target") or session_overlay.get("viewer160_target"),
            "viewer160_eye": session_overlay.get("viewer160_eye"),
            "viewer160_target": session_overlay.get("viewer160_target"),
            "uav_altitude_policy": UAV_ALTITUDE_POLICY,
            "target_georeference_height": MARINECITY_TARGET_GEOREF_HEIGHT_M,
            "georeference_height": georef.get("cesium:georeferenceOrigin:height"),
            "georeference_height_note": (
                "The user-verified MarineCity review height is 160 m, and the UAV/camera "
                "observation band is locked to 140-160 m. The live CesiumGeoreference "
                "readback is logged separately because it can lag until the next recapture/status export."
            ),
            "google_photorealistic_tiles_valid": (prim_status.get("/Google_Photorealistic_3D_Tiles", {}) or {}).get("valid"),
            "cesium_world_terrain_valid": (prim_status.get("/Cesium_World_Terrain", {}) or {}).get("valid"),
            "substitute_city_geometry_created": session_overlay.get("substitute_city_geometry_created"),
            "qualitative_gate_status": marinecity_qual.get("status"),
            "qualitative_gate_checks": marinecity_qual.get("checks"),
            "best_full_capture": marinecity_qual.get("best_full_capture"),
            "best_crop_candidate": marinecity_qual.get("best_crop_candidate"),
            "qualitative_claiming_rule": marinecity_qual.get("claiming_rule"),
            "clean_recapture_plan": str(MARINECITY_CLEAN_RECAPTURE_PLAN.relative_to(REPO_ROOT)),
            "clean_recapture_plan_status": marinecity_recapture_plan.get("status"),
            "clean_recapture_needed_improvement": marinecity_recapture_plan.get("needed_improvement"),
        },
        "aerograph": {
            "prompt_pack_status": prompt_manifest.get("status"),
            "total_prompts": prompt_manifest.get("total_prompts"),
            "sample_prompts": prompt_manifest.get("sample_prompts"),
            "class_counts": prompt_manifest.get("class_counts"),
            "real_capture_prompt_pack_status": real_capture_prompt_manifest.get("status"),
            "real_capture_prompt_count": real_capture_prompt_manifest.get("total_prompts"),
            "real_capture_prompt_class_counts": real_capture_prompt_manifest.get("class_counts"),
            "real_capture_web_batch_status": real_capture_web_batch_manifest.get("status"),
            "real_capture_web_batch_count": real_capture_web_batch_manifest.get("batch_count"),
            "real_capture_web_collection_packet": str(REAL_CAPTURE_WEB_COLLECTION_PACKET.relative_to(REPO_ROOT)),
            "real_capture_web_collection_packet_exists": REAL_CAPTURE_WEB_COLLECTION_PACKET.exists(),
            "real_capture_web_collection_checklist": str(REAL_CAPTURE_WEB_COLLECTION_CHECKLIST.relative_to(REPO_ROOT)),
            "real_capture_web_collection_checklist_exists": REAL_CAPTURE_WEB_COLLECTION_CHECKLIST.exists(),
            "real_capture_dryrun_status": real_capture_dryrun.get("status"),
            "real_capture_dryrun_paper_claim_allowed": real_capture_dryrun.get("paper_claim_allowed"),
            "real_capture_nonmock_smoke_status": real_capture_nonmock_smoke.get("status"),
            "real_capture_nonmock_smoke_selected_manifest": real_capture_nonmock_smoke.get("selected_manifest"),
            "real_capture_nonmock_smoke_expected_prompt_count": real_capture_nonmock_smoke.get("expected_prompt_count"),
            "web_batch_status": web_batch_manifest.get("status"),
            "web_batch_count": web_batch_manifest.get("batch_count"),
            "web_batch_dir": web_batch_manifest.get("out_dir"),
            "web_batch_import_command": web_batch_manifest.get("import_command"),
            "dry_run_status": dry_run.get("status"),
            "dry_run_summary": dry_run.get("summary"),
            "paper_table_status": aerograph_table.get("status"),
            "paper_table_selected_manifest": aerograph_table.get("selected_manifest"),
            "non_mock_status": aerograph_nonmock.get("status", "pending_provider_execution"),
            "non_mock_coverage_ratio": aerograph_coverage.get(
                "valid_coverage_ratio", aerograph_coverage.get("coverage_ratio")
            ),
            "non_mock_matched_responses": aerograph_coverage.get(
                "matched_valid_response_count",
                aerograph_coverage.get("matched_nonblank_response_count"),
            ),
            "non_mock_nonblank_responses": aerograph_coverage.get("matched_nonblank_response_count"),
            "non_mock_prompt_count": aerograph_coverage.get("prompt_count"),
            "reviewed_candidate_valid_count": aerograph_nonmock.get("reviewed_candidate_valid_count"),
            "external_provider_replication_ready": aerograph_nonmock.get("external_provider_replication_ready"),
            "full_manual_template": aerograph_nonmock.get("full_template"),
            "nonmock_readiness_report": str(AEROGRAPH_NONMOCK_READINESS.with_suffix(".md").relative_to(REPO_ROOT)),
            "nonmock_collection_plan": str(AEROGRAPH_COLLECTION_PLAN.relative_to(REPO_ROOT)),
            "nonmock_collection_plan_exists": AEROGRAPH_COLLECTION_PLAN.exists(),
        },
        "queues": {
            "uavdet_log_tail": last_log_line(UAVDET_LOG),
            "tinyperson_log_tail": last_log_line(TINYPERSON_LOG),
            "tiny_person_gate": tiny_person_gate_state(),
            "tinyperson_transfer_log_tail": last_log_line(TINYPERSON_TRANSFER_LOG),
            "tiny_person_transfer_gate": tiny_person_transfer_gate_state(),
            "tinyperson_eval_sweep_log_tail": last_log_line(TINYPERSON_EVAL_SWEEP_LOG),
            "tiny_person_eval_sweep_gate": tiny_person_eval_sweep_gate_state(),
        },
        "dashboards": {
            "training": str(TRAIN_DASHBOARD.relative_to(REPO_ROOT)),
            "marinecity": str(SIM_DASHBOARD.relative_to(REPO_ROOT)),
        },
        "paper_ready_artifacts": {
            "readiness_audit": str(READINESS_AUDIT.relative_to(REPO_ROOT)),
            "readiness_audit_exists": READINESS_AUDIT.exists(),
            "tracked_readiness_audit": str(TRACKED_READINESS_AUDIT.relative_to(REPO_ROOT)),
            "tracked_readiness_audit_exists": TRACKED_READINESS_AUDIT.exists(),
            "paper_artifact_manifest": str(PAPER_ARTIFACT_MANIFEST.relative_to(REPO_ROOT)),
            "paper_artifact_manifest_exists": PAPER_ARTIFACT_MANIFEST.exists(),
            "paper_artifact_check": str(PAPER_ARTIFACT_CHECK.relative_to(REPO_ROOT)),
            "paper_artifact_check_status": paper_check.get("status", "missing"),
            "paper_artifact_missing_required_count": paper_check.get("missing_required_count"),
            "paper_artifact_stale_claim_count": paper_check.get("stale_claim_count"),
            "latex_patch_check": str(LATEX_PATCH_CHECK.relative_to(REPO_ROOT)),
            "latex_patch_check_status": latex_check.get("status", "missing"),
            "detector_table": "paper/tables/main_detector_comparison_table.tex",
            "marinecity_system_table": "paper/tables/marinecity_system_scenario_table.tex",
            "marinecity_crossview_graph_table": "paper/tables/marinecity_crossview_evidence_graph_table.tex",
            "marinecity_crossview_graph_figure": "paper/figures/results/marinecity_system/marinecity_crossview_evidence_graph.png",
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
        f"- Ours vs UAVDet final-table AP gap: `{detector.get('ours_minus_uavdet_final_ap')}`",
        f"- Ours vs UAVDet queue-best AP gap: `{detector.get('ours_minus_uavdet_queue_best_ap')}`",
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
        f"- Real-capture detector/reasoner smoke: `{system.get('detector_reasoner_smoke_status')}`; tokens `{system.get('detector_reasoner_smoke_tokens')}`; report `{system.get('detector_reasoner_smoke_report')}`",
        f"- Detector preview sheet: `{system.get('detector_reasoner_smoke_contact_sheet')}`",
        f"- Cross-view evidence graph: `{system.get('crossview_graph_status')}`; hypotheses `{system.get('crossview_graph_hypothesis_count')}`; multi-view `{system.get('crossview_graph_multi_view_hypothesis_count')}`; edges support/conflict/missing `{system.get('crossview_graph_support_edge_count')}`/`{system.get('crossview_graph_conflict_edge_count')}`/`{system.get('crossview_graph_missing_evidence_edge_count')}`; claim `{system.get('crossview_graph_claim_level')}`",
        f"- Integration check: `{system.get('integration_check_status')}`; actor classes `{system.get('integration_actor_classes')}`; detector classes `{system.get('integration_detector_classes')}`; report `{system.get('integration_check')}`",
        f"- Neural 3D completion gate: `{system.get('neural_3d_completion_status')}`; metric rows `{system.get('neural_3d_metric_result_rows')}`; report `{system.get('neural_3d_readiness_report')}`",
        f"- Neural 3D input dataset: `{system.get('neural_3d_input_dataset_status')}`; frames `{system.get('neural_3d_input_dataset_frames')}`; split `{system.get('neural_3d_input_dataset_split')}`; report `{system.get('neural_3d_input_dataset_report')}`",
        f"- Depth point-cloud smoke: `{system.get('depth_pointcloud_smoke_status')}`; points `{system.get('depth_pointcloud_point_count')}`; preview `{system.get('depth_pointcloud_preview')}`; report `{system.get('depth_pointcloud_smoke_report')}`",
        f"- Neural 3D runner preflight: `{system.get('neural_3d_runner_preflight_status')}`; runner available `{system.get('neural_3d_runner_available')}`; report `{system.get('neural_3d_runner_preflight_report')}`",
        f"- Live overlay: `{system.get('live_overlay_status')}`; camera set `{system.get('camera_set')}`; profile `{system.get('camera_profile')}`",
        f"- Real Cesium: Google tiles `{system.get('google_photorealistic_tiles_valid')}`, terrain `{system.get('cesium_world_terrain_valid')}`, fake city `{system.get('substitute_city_geometry_created')}`",
        f"- UAV altitude policy: `{system.get('uav_altitude_policy')}`",
        f"- Viewer camera: eye `{system.get('viewer_eye')}`, target `{system.get('viewer_target')}`",
        f"- Cesium target georef height: `{system.get('target_georeference_height')}`; latest GUI readback `{system.get('georeference_height')}`, requested/applied `{system.get('requested_georef_height')}`/`{system.get('applied_georef_height')}`",
        f"- Georef note: {system.get('georeference_height_note')}",
        f"- Qualitative gate: `{system.get('qualitative_gate_status')}`",
        f"- Full-frame ready: `{(system.get('qualitative_gate_checks') or {}).get('full_frame_main_ready')}`; best full void `{(system.get('best_full_capture') or {}).get('best_black_ratio')}`; mean top-3 void `{(system.get('best_full_capture') or {}).get('mean_top3_black_ratio')}`",
        f"- Crop supplementary ready: `{(system.get('qualitative_gate_checks') or {}).get('crop_supplementary_ready')}`; best crop void `{(system.get('best_crop_candidate') or {}).get('black_ratio')}`; area `{(system.get('best_crop_candidate') or {}).get('area_ratio')}`",
        f"- Clean full-frame recapture plan: `{system.get('clean_recapture_plan')}`; status `{system.get('clean_recapture_plan_status')}`; needed improvement `{system.get('clean_recapture_needed_improvement')}`",
        f"- 3D claiming rule: {system.get('neural_3d_claiming_rule')}",
        f"- Dashboard: `{system.get('dashboard')}`",
        "",
        "## AeroGraph Reasoner",
        "",
        f"- Prompt pack: `{aerograph.get('prompt_pack_status')}`, prompts `{aerograph.get('total_prompts')}`",
        f"- Prompt class counts: `{aerograph.get('class_counts')}`",
        f"- Real-capture compact prompt pack: `{aerograph.get('real_capture_prompt_pack_status')}`, prompts `{aerograph.get('real_capture_prompt_count')}`, classes `{aerograph.get('real_capture_prompt_class_counts')}`",
        f"- Real-capture compact web batches: `{aerograph.get('real_capture_web_batch_status')}`, count `{aerograph.get('real_capture_web_batch_count')}`; dry-run `{aerograph.get('real_capture_dryrun_status')}`, paper-claim `{aerograph.get('real_capture_dryrun_paper_claim_allowed')}`",
        f"- Real-capture compact non-mock smoke: `{aerograph.get('real_capture_nonmock_smoke_status')}`; expected prompts `{aerograph.get('real_capture_nonmock_smoke_expected_prompt_count')}`; selected manifest `{aerograph.get('real_capture_nonmock_smoke_selected_manifest') or ''}`",
        f"- Real-capture compact web packet: `{aerograph.get('real_capture_web_collection_packet')}`; checklist `{aerograph.get('real_capture_web_collection_checklist')}`",
        f"- Web batches: `{aerograph.get('web_batch_status')}`, count `{aerograph.get('web_batch_count')}`, dir `{aerograph.get('web_batch_dir')}`",
        f"- Dry-run status: `{aerograph.get('dry_run_status')}`",
        f"- Paper table status: `{aerograph.get('paper_table_status')}`, selected manifest `{aerograph.get('paper_table_selected_manifest')}`",
        f"- Reasoner readiness status: `{aerograph.get('non_mock_status')}`",
        f"- Effective valid response coverage: `{aerograph.get('non_mock_matched_responses')}/{aerograph.get('non_mock_prompt_count')}`; ratio `{aerograph.get('non_mock_coverage_ratio')}`",
        f"- Reviewed-candidate coverage: `{aerograph.get('reviewed_candidate_valid_count')}/{aerograph.get('non_mock_prompt_count')}`",
        f"- External-provider replication ready: `{aerograph.get('external_provider_replication_ready')}`",
        f"- Full manual template: `{aerograph.get('full_manual_template')}`",
        f"- Non-mock readiness report: `{aerograph.get('nonmock_readiness_report')}`",
        f"- Non-mock collection plan: `{aerograph.get('nonmock_collection_plan')}`",
        "",
        "## Queue Gates",
        "",
        f"- UAVDet log tail: `{queues.get('uavdet_log_tail')}`",
        f"- TinyPerson log tail: `{queues.get('tinyperson_log_tail')}`",
        f"- TinyPerson gate: `{queues.get('tiny_person_gate')}`",
        f"- TinyPerson transfer log tail: `{queues.get('tinyperson_transfer_log_tail')}`",
        f"- TinyPerson transfer gate: `{queues.get('tiny_person_transfer_gate')}`",
        f"- TinyPerson eval-size log tail: `{queues.get('tinyperson_eval_sweep_log_tail')}`",
        f"- TinyPerson eval-size gate: `{queues.get('tiny_person_eval_sweep_gate')}`",
        "",
        "## Dashboard Links",
        "",
        f"- Training dashboard: `{snapshot['dashboards']['training']}`",
        f"- MarineCity dashboard: `{snapshot['dashboards']['marinecity']}`",
        "",
        "## Paper-Ready Artifacts",
        "",
        f"- Readiness audit: `{snapshot['paper_ready_artifacts']['readiness_audit']}`",
        f"- Tracked readiness audit: `{snapshot['paper_ready_artifacts']['tracked_readiness_audit']}`",
        f"- Paper artifact manifest: `{snapshot['paper_ready_artifacts']['paper_artifact_manifest']}`",
        f"- Paper artifact check: `{snapshot['paper_ready_artifacts']['paper_artifact_check']}`; status `{snapshot['paper_ready_artifacts']['paper_artifact_check_status']}`; missing `{snapshot['paper_ready_artifacts']['paper_artifact_missing_required_count']}`; stale claims `{snapshot['paper_ready_artifacts']['paper_artifact_stale_claim_count']}`",
        f"- LaTeX patch check: `{snapshot['paper_ready_artifacts']['latex_patch_check']}`; status `{snapshot['paper_ready_artifacts']['latex_patch_check_status']}`",
        f"- Detector table: `{snapshot['paper_ready_artifacts']['detector_table']}`",
        f"- MarineCity system table: `{snapshot['paper_ready_artifacts']['marinecity_system_table']}`",
        f"- MarineCity cross-view graph table: `{snapshot['paper_ready_artifacts']['marinecity_crossview_graph_table']}`",
        f"- MarineCity cross-view graph figure: `{snapshot['paper_ready_artifacts']['marinecity_crossview_graph_figure']}`",
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
